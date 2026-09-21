import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.exceptions import (
    LLMTimeoutError,
    LLMUpstreamError,
)
from app.dependencies import get_chat_service
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.services.chat_service import ChatService


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


# 普通非流式接口
@router.post(
    "",
    response_model=ChatResponse,
)
async def create_chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(
        get_chat_service
    ),
) -> ChatResponse:

    return await chat_service.chat(request)


# 流式接口
@router.post("/stream")
async def create_chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(
        get_chat_service
    ),
):

    async def event_generator():

        try:
            async for chunk in chat_service.stream_chat(
                request
            ):

                data = {
                    "type": chunk.type,
                    "content": chunk.content,
                    "model": chunk.model,
                    "finish_reason": chunk.finish_reason,
                    "latency_ms": chunk.latency_ms,
                    "usage": None,
                }

                if chunk.usage:
                    data["usage"] = {
                        "prompt_tokens": (
                            chunk.usage.prompt_tokens
                        ),
                        "completion_tokens": (
                            chunk.usage.completion_tokens
                        ),
                        "total_tokens": (
                            chunk.usage.total_tokens
                        ),
                    }

                yield (
                    "data: "
                    + json.dumps(
                        data,
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )

        except LLMTimeoutError:

            yield (
                'event: error\n'
                'data: {"detail":"LLM service timeout"}\n\n'
            )

        except LLMUpstreamError:

            yield (
                'event: error\n'
                'data: {"detail":"LLM service unavailable"}\n\n'
            )


    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )