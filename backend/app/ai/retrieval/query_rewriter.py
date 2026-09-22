from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek


class QueryRewriter:
    def __init__(self, model: ChatDeepSeek):
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                    你是一个知识库检索查询改写器。

                    请把用户问题改写成更适合语义检索的独立查询。

                    要求：
                    1. 保持用户原始意图不变。
                    2. 删除无意义口语表达。
                    3. 必要时补充明确的技术术语。
                    4. 不回答问题。
                    5. 只输出改写后的查询，不要解释。
                """,
            ),
            (
                "human",
                "{query}",
            ),
        ])

        self.chain = prompt | model | StrOutputParser()

    async def rewrite(self, query: str) -> str:
        rewritten_query = await self.chain.ainvoke({"query": query})
        rewritten_query = rewritten_query.strip()

        return rewritten_query or query