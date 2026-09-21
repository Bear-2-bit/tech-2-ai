import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
)

from app.ai.providers.base import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)
from app.core.exceptions import (
    LLMTimeoutError,
    LLMUpstreamError,
)


logger = logging.getLogger(__name__)


class DeepSeekProvider(LLMProvider):

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
    ):
        self.model = model

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,

            # Phase 2.2 再正式学习配置
            timeout=30.0,

            # SDK默认会自动重试。
            # 现在先关闭，Phase 2.2 专门研究Retry。
            max_retries=0,
        )


    async def chat(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        try:
            response = await self.client.chat.completions.create(
                model=self.model,

                messages=[
                    {
                        "role": message.role,
                        "content": message.content,
                    }
                    for message in request.messages
                ],

                temperature=request.temperature,

                max_tokens=request.max_tokens,

                stream=False,

                extra_body={
                    "thinking": {
                        "type": "disabled",
                    }
                },
            )

        except APITimeoutError as exc:
            logger.exception(
                "LLM request timed out"
            )

            raise LLMTimeoutError(
                "LLM request timed out"
            ) from exc

        except APIConnectionError as exc:
            logger.exception(
                "Failed to connect to LLM service"
            )

            raise LLMUpstreamError(
                "Failed to connect to LLM service"
            ) from exc

        except APIStatusError as exc:
            logger.exception(
                "LLM returned HTTP status: %s",
                exc.status_code,
            )

            raise LLMUpstreamError(
                f"LLM returned status {exc.status_code}"
            ) from exc


        choice = response.choices[0]

        if choice.message.content is None:
            raise LLMUpstreamError(
                "LLM response does not contain content"
            )

        if response.usage is None:
            raise LLMUpstreamError(
                "LLM response does not contain usage"
            )


        return LLMResponse(
            content=choice.message.content,

            model=response.model,

            finish_reason=choice.finish_reason,

            usage=LLMUsage(
                prompt_tokens=(
                    response.usage.prompt_tokens
                ),
                completion_tokens=(
                    response.usage.completion_tokens
                ),
                total_tokens=(
                    response.usage.total_tokens
                ),
            ),
        )