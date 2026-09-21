import logging

import httpx

from app.core.config import settings
from app.core.exceptions import LLMTimeoutError, LLMUpstreamError
from app.schemas.chat import ChatRequest, ChatResponse, TokenUsage


logger = logging.getLogger(__name__)


async def chat(request: ChatRequest) -> ChatResponse:
    messages = []

    # 1. system prompt
    if request.system_prompt:
        messages.append(
            {
                "role": "system",
                "content": request.system_prompt,
            }
        )

    # 2. 完整聊天历史
    for message in request.messages:
        messages.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    # 3. DeepSeek 请求体
    body = {
        "model": settings.deepseek_model,
        "messages": messages,
        "thinking": {
            "type": "disabled",
        },
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    # 4. 调用 DeepSeek
    try:
        async with httpx.AsyncClient(
            base_url=settings.deepseek_base_url,
            timeout=10.0,
        ) as client:
            response = await client.post(
                "/chat/completions",
                headers=headers,
                json=body,
            )

            response.raise_for_status()

    except httpx.TimeoutException as exc:
        logger.exception("LLM request timed out")

        raise LLMTimeoutError(
            "LLM request timed out"
        ) from exc

    except httpx.HTTPStatusError as exc:
        logger.exception(
            "LLM returned HTTP status: %s",
            exc.response.status_code,
        )

        raise LLMUpstreamError(
            f"LLM returned status {exc.response.status_code}"
        ) from exc

    except httpx.RequestError as exc:
        logger.exception(
            "Failed to connect to LLM service"
        )

        raise LLMUpstreamError(
            "Failed to connect to LLM service"
        ) from exc

    # 5. 解析模型响应
    try:
        data = response.json()

        choice = data["choices"][0]
        usage = data["usage"]

        return ChatResponse(
            answer=choice["message"]["content"],
            model=data["model"],
            finish_reason=choice["finish_reason"],
            usage=TokenUsage(
                prompt_tokens=usage["prompt_tokens"],
                completion_tokens=usage["completion_tokens"],
                total_tokens=usage["total_tokens"],
            ),
        )

    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.exception(
            "Invalid response returned by LLM service"
        )

        raise LLMUpstreamError(
            "Invalid response returned by LLM service"
        ) from exc