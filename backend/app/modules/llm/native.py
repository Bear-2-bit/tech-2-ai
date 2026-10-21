from functools import lru_cache
from time import perf_counter

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.store import get_store
from app.core.telemetry import current_run
from app.modules.llm.schemas import EXTRACTION_PROMPT, ChatRequest, ExtractedTask
from app.resources import api_key


@lru_cache
def get_client():
    from openai import AsyncOpenAI

    settings = get_settings()
    return AsyncOpenAI(
        api_key=api_key(),
        base_url=settings.deepseek_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


def usage_dict(usage):
    if usage is None:
        return None
    result = {key: getattr(usage, key) for key in ("prompt_tokens", "completion_tokens", "total_tokens")}
    if current_run.get():
        get_store().usage(current_run.get(), result["prompt_tokens"], result["completion_tokens"])
    return result


def options(messages, temperature=0, max_tokens=1000, response_format="text") -> dict:
    return {
        "model": get_settings().deepseek_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": response_format},
        "extra_body": {"thinking": {"type": "disabled"}},
    }


async def chat(request: ChatRequest) -> dict:
    start = perf_counter()
    response = await get_client().chat.completions.create(
        **options(request.messages_payload(), request.temperature, request.max_tokens)
    )
    choice = response.choices[0]
    if choice.message.content is None:
        raise AppError("模型没有返回文本。", "llm_output", 502)
    return {
        "answer": choice.message.content,
        "model": response.model,
        "finish_reason": choice.finish_reason,
        "usage": usage_dict(response.usage),
        "latency_ms": round((perf_counter() - start) * 1000, 2),
    }


async def stream(request: ChatRequest):
    start = perf_counter()
    response = await get_client().chat.completions.create(
        **options(request.messages_payload(), request.temperature, request.max_tokens),
        stream=True,
        stream_options={"include_usage": True},
    )
    finish_reason, usage, model = None, None, get_settings().deepseek_model
    try:
        async for chunk in response:
            model = chunk.model or model
            if chunk.usage:
                usage = usage_dict(chunk.usage)
            if chunk.choices:
                choice = chunk.choices[0]
                finish_reason = choice.finish_reason or finish_reason
                if choice.delta.content:
                    yield {"type": "delta", "content": choice.delta.content}
        if finish_reason is None:
            raise AppError("模型流提前断开，没有收到结束状态。", "stream_incomplete", 502)
        yield {
            "type": "done",
            "model": model,
            "finish_reason": finish_reason,
            "usage": usage,
            "latency_ms": round((perf_counter() - start) * 1000, 2),
        }
    finally:
        await response.close()


async def extract(text: str) -> dict:
    messages = [{"role": "system", "content": EXTRACTION_PROMPT}, {"role": "user", "content": text}]
    start = perf_counter()
    total_usage = None
    for attempt in range(1, 3):
        response = await get_client().chat.completions.create(
            **options(messages, max_tokens=1000, response_format="json_object")
        )
        choice = response.choices[0]
        usage = usage_dict(response.usage)
        if usage:
            total_usage = {key: (total_usage or {}).get(key, 0) + value for key, value in usage.items()}
        try:
            if choice.finish_reason != "stop":
                raise AppError("结构化输出未完整结束，请缩短输入。", "llm_output", 502)
            result = ExtractedTask.model_validate_json(choice.message.content or "")
            return {
                "result": result.model_dump(),
                "model": response.model,
                "finish_reason": choice.finish_reason,
                "usage": total_usage,
                "latency_ms": round((perf_counter() - start) * 1000, 2),
                "attempts": attempt,
            }
        except ValidationError as exc:
            if attempt == 2:
                raise AppError("两次输出均未通过结构校验。", "structured_output", 502) from exc
            fields = [".".join(map(str, item["loc"])) for item in exc.errors()]
            messages.extend(
                [
                    {"role": "assistant", "content": choice.message.content or ""},
                    {"role": "user", "content": f"字段 {fields} 校验失败，请重新输出完整 JSON。"},
                ]
            )
