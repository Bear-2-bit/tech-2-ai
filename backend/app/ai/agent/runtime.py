from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langgraph.errors import GraphRecursionError


class AgentRuntime:
    def __init__(
        self,
        model: BaseChatModel,
        tools: list[BaseTool],
    ):
        self.agent = create_agent(
            model=model,
            tools=tools,
            system_prompt="""
你是一个企业AI助手。

根据用户目标自主选择合适工具：

- 数学计算使用 calculator
- 企业知识库、文档资料使用 knowledge_search
- 销售、订单、统计等结构化数据使用 database_query

可以根据前一步工具结果继续调用其他工具。
不要编造工具没有返回的信息。
""",
            middleware=[
                ToolCallLimitMiddleware(
                    run_limit=6,
                    exit_behavior="end",
                ),
            ],
        )

    async def run(
        self,
        query: str,
    ) -> list[BaseMessage]:
        try:
            result = await self.agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": query,
                        }
                    ]
                },
                {
                    "recursion_limit": 20,
                },
            )

        except GraphRecursionError as exc:
            raise RuntimeError(
                "Agent exceeded maximum execution steps"
            ) from exc

        return result["messages"]