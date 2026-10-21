from time import perf_counter

from app.core.errors import AppError
from app.modules.llm.schemas import EXTRACTION_PROMPT, ChatRequest, ExtractedTask
from app.resources import get_model, model_config


def response_info(message, start: float) -> dict:
    usage = message.usage_metadata
    return {
        "model": message.response_metadata.get("model_name", get_model().model_name),
        "finish_reason": message.response_metadata.get("finish_reason"),
        "usage": {
            "prompt_tokens": usage["input_tokens"],
            "completion_tokens": usage["output_tokens"],
            "total_tokens": usage["total_tokens"],
        }
        if usage
        else None,
        "latency_ms": round((perf_counter() - start) * 1000, 2),
    }


async def chat(request: ChatRequest) -> dict:
    start = perf_counter()
    response = (
        await get_model()
        .bind(temperature=request.temperature, max_tokens=request.max_tokens)
        .ainvoke(request.messages_payload(), config=model_config())
    )
    return {"answer": response.content, **response_info(response, start)}


async def stream(request: ChatRequest):
    start, combined = perf_counter(), None
    iterator = (
        get_model()
        .bind(temperature=request.temperature, max_tokens=request.max_tokens)
        .astream(request.messages_payload(), config=model_config())
    )
    try:
        async for chunk in iterator:
            combined = chunk if combined is None else combined + chunk
            if isinstance(chunk.content, str) and chunk.content:
                yield {"type": "delta", "content": chunk.content}
        if combined is None or not combined.response_metadata.get("finish_reason"):
            raise AppError("模型流提前断开，没有收到结束状态。", "stream_incomplete", 502)
        yield {"type": "done", **response_info(combined, start)}
    finally:
        await iterator.aclose()


async def extract(text: str) -> dict:
    from langchain_core.prompts import ChatPromptTemplate

    start = perf_counter()
    prompt = ChatPromptTemplate.from_messages([("system", EXTRACTION_PROMPT), ("human", "{text}")])
    chain = prompt | get_model().with_structured_output(ExtractedTask, method="function_calling", include_raw=True)
    response = await chain.ainvoke({"text": text}, config=model_config())
    if response["parsing_error"] or response["parsed"] is None:
        raise AppError("框架结构化输出未通过校验。", "structured_output", 502)
    return {"result": response["parsed"].model_dump(), "attempts": 1, **response_info(response["raw"], start)}
