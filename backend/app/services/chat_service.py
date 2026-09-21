from app.ai.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMRequest,
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


        # Chat业务数据
        # ↓
        # 通用LLM请求
        llm_request = LLMRequest(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )


        # 调用统一LLM能力
        llm_response = await self.llm_provider.chat(
            llm_request
        )


        # 通用LLM结果
        # ↓
        # Chat业务响应
        return ChatResponse(
            answer=llm_response.content,

            model=llm_response.model,

            finish_reason=(
                llm_response.finish_reason
            ),

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
        )