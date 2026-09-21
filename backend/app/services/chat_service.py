from typing import AsyncIterator

from app.ai.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMRequest,
    LLMStreamChunk,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    TokenUsage,
)


class ChatService:

    def __init__(
        self,
        llm_provider: LLMProvider,
    ):
        self.llm_provider = llm_provider


    # =========================
    # 普通非流式聊天
    # =========================
    async def chat(
        self,
        request: ChatRequest,
    ) -> ChatResponse:

        messages = []

        # system prompt
        if request.system_prompt:
            messages.append(
                LLMMessage(
                    role="system",
                    content=request.system_prompt,
                )
            )

        # 多轮聊天历史
        for message in request.messages:
            messages.append(
                LLMMessage(
                    role=message.role,
                    content=message.content,
                )
            )

        # ChatRequest
        # ↓
        # LLMRequest
        llm_request = LLMRequest(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # 调用普通非流式 LLM
        llm_response = await self.llm_provider.chat(
            llm_request
        )

        # LLMResponse
        # ↓
        # ChatResponse
        return ChatResponse(
            answer=llm_response.content,
            model=llm_response.model,
            finish_reason=llm_response.finish_reason,

            usage=TokenUsage(
                prompt_tokens=(
                    llm_response.usage.prompt_tokens
                ),
                completion_tokens=(
                    llm_response.usage.completion_tokens
                ),
                total_tokens=(
                    llm_response.usage.total_tokens
                ),
            ),

            latency_ms=llm_response.latency_ms,
        )


    # =========================
    # 流式聊天
    # =========================
    async def stream_chat(
        self,
        request: ChatRequest,
    ) -> AsyncIterator[LLMStreamChunk]:

        messages = []

        # system prompt
        if request.system_prompt:
            messages.append(
                LLMMessage(
                    role="system",
                    content=request.system_prompt,
                )
            )

        # 多轮聊天历史
        for message in request.messages:
            messages.append(
                LLMMessage(
                    role=message.role,
                    content=message.content,
                )
            )

        # ChatRequest
        # ↓
        # LLMRequest
        llm_request = LLMRequest(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # DeepSeek 每产生一个 chunk
        # 就立即向 Router 往上传
        async for chunk in self.llm_provider.stream_chat(
            llm_request
        ):
            yield chunk