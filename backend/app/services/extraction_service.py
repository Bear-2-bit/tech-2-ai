import logging

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


logger = logging.getLogger(__name__)


MAX_ATTEMPTS = 2


SYSTEM_PROMPT = """
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

        messages = [
            LLMMessage(
                role="system",
                content=SYSTEM_PROMPT,
            ),

            LLMMessage(
                role="user",
                content=request.text,
            ),
        ]


        # 统计所有尝试真正消耗的资源
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        total_latency_ms = 0.0

        last_error = None
        last_response = None


        for attempt in range(
            1,
            MAX_ATTEMPTS + 1,
        ):

            llm_request = LLMRequest(
                messages=messages,

                temperature=0.0,

                max_tokens=500,

                response_format="json_object",
            )


            llm_response = (
                await self.llm_provider.chat(
                    llm_request
                )
            )

            last_response = llm_response


            # 累计真实Token和耗时
            total_prompt_tokens += (
                llm_response
                .usage
                .prompt_tokens
            )

            total_completion_tokens += (
                llm_response
                .usage
                .completion_tokens
            )

            total_tokens += (
                llm_response
                .usage
                .total_tokens
            )

            total_latency_ms += (
                llm_response.latency_ms
            )


            try:
                # 同时完成：
                #
                # JSON解析
                # +
                # Pydantic Schema验证
                extracted_task = (
                    ExtractedTask
                    .model_validate_json(
                        llm_response.content
                    )
                )


                return ExtractionResponse(
                    result=extracted_task,

                    model=llm_response.model,

                    finish_reason=(
                        llm_response
                        .finish_reason
                    ),

                    usage=ExtractionTokenUsage(
                        prompt_tokens=(
                            total_prompt_tokens
                        ),

                        completion_tokens=(
                            total_completion_tokens
                        ),

                        total_tokens=(
                            total_tokens
                        ),
                    ),

                    latency_ms=(
                        total_latency_ms
                    ),

                    attempts=attempt,
                )


            except ValidationError as exc:

                last_error = exc

                logger.warning(
                    "Structured output "
                    "validation failed "
                    "attempt=%s/%s "
                    "error_count=%s",
                    attempt,
                    MAX_ATTEMPTS,
                    exc.error_count(),
                )


                # 已经是最后一次
                # 不再继续请求模型
                if attempt == MAX_ATTEMPTS:
                    break


                # 把模型刚才错误的回答
                # 放回上下文
                messages.append(
                    LLMMessage(
                        role="assistant",
                        content=(
                            llm_response.content
                        ),
                    )
                )


                # 告诉模型：
                # 刚才哪里没有通过验证
                messages.append(
                    LLMMessage(
                        role="user",
                        content=(
                            "你刚才输出的 JSON "
                            "没有通过程序校验。\n\n"
                            "校验错误如下：\n"
                            f"{str(exc)}\n\n"
                            "请修正错误，重新输出"
                            "完整 JSON。\n"
                            "只输出 JSON，"
                            "不要输出解释。"
                        ),
                    )
                )


        raise LLMUpstreamError(
            "LLM structured output "
            "validation failed"
        ) from last_error