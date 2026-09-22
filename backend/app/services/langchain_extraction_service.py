from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_deepseek import ChatDeepSeek

from app.schemas.extraction import (
    ExtractedTask,
    ExtractionRequest,
)


class LangChainExtractionService:

    def __init__(
        self,
        model: ChatDeepSeek,
    ):
        prompt = (
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """
你是一个任务信息抽取器。

只根据用户提供的内容抽取信息。

规则：

1. priority 只能是 low、medium、high。
2. 如果没有明确优先级，使用 medium。
3. 如果没有截止时间，deadline 为 null。
4. technologies 只提取原文明示的技术。
5. 不要补充用户没有提供的信息。
""",
                    ),
                    (
                        "human",
                        "{text}",
                    ),
                ]
            )
        )


        structured_model = (
            model.with_structured_output(
                ExtractedTask
            )
        )


        self.chain = (
            prompt
            | structured_model
        )


    async def extract(
        self,
        request: ExtractionRequest,
    ) -> ExtractedTask:

        result = await self.chain.ainvoke(
            {
                "text": request.text,
            }
        )

        return result