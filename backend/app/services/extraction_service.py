import json

from pydantic import ValidationError

from app.ai.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMRequest,
)
from app.core.exceptions import (
    LLMUpstreamError,
)
from app.schemas.extraction import (
    ExtractedTask,
    ExtractionRequest,
    ExtractionResponse,
    ExtractionTokenUsage,
)


class ExtractionService:

    def __init__(
        self,
        llm_provider: LLMProvider,
    ):
        self.llm_provider = llm_provider


    async def extract(
        self,
        request: ExtractionRequest,
    ) -> ExtractionResponse:

        system_prompt = """
你是一个任务信息抽取器。

请从用户提供的自然语言中抽取任务信息。

必须只输出 JSON，不要输出解释文字。

JSON 格式必须为：

{
  "title": "任务标题",
  "priority": "low 或 medium 或 high",
  "deadline": "截止时间，没有则为 null",
  "technologies": ["明确出现的技术名称"]
}

规则：

1. priority 只能是 low、medium、high。
2. 如果没有明确优先级，使用 medium。
3. 如果没有截止时间，deadline 为 null。
4. technologies 只提取原文明确出现的技术。
5. 不要添加用户没有提供的信息。
"""


        llm_request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content=system_prompt,
                ),

                LLMMessage(
                    role="user",
                    content=request.text,
                ),
            ],

            temperature=0.0,

            max_tokens=500,

            response_format="json_object",
        )


        llm_response = (
            await self.llm_provider.chat(
                llm_request
            )
        )


        try:
            data = json.loads(
                llm_response.content
            )

            extracted_task = (
                ExtractedTask.model_validate(
                    data
                )
            )

        except (
            json.JSONDecodeError,
            ValidationError,
            TypeError,
        ) as exc:

            raise LLMUpstreamError(
                "Invalid structured output "
                "returned by LLM"
            ) from exc


        return ExtractionResponse(
            result=extracted_task,

            model=llm_response.model,

            finish_reason=(
                llm_response.finish_reason
            ),

            usage=ExtractionTokenUsage(
                prompt_tokens=(
                    llm_response
                    .usage
                    .prompt_tokens
                ),

                completion_tokens=(
                    llm_response
                    .usage
                    .completion_tokens
                ),

                total_tokens=(
                    llm_response
                    .usage
                    .total_tokens
                ),
            ),

            latency_ms=(
                llm_response.latency_ms
            ),
        )