import logging
from time import perf_counter

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
        timeout: float,
        max_retries: int,
    ):
        self.model = model

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )


    async def chat(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        start_time = perf_counter()

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


        latency_ms = (
            perf_counter() - start_time
        ) * 1000


        choice = response.choices[0]

        if choice.message.content is None:
            raise LLMUpstreamError(
                "LLM response does not contain content"
            )

        if response.usage is None:
            raise LLMUpstreamError(
                "LLM response does not contain usage"
            )


        logger.info(
            "LLM call succeeded "
            "model=%s latency_ms=%.2f "
            "tokens=%s finish_reason=%s",
            response.model,
            latency_ms,
            response.usage.total_tokens,
            choice.finish_reason,
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

            latency_ms=latency_ms,
        )