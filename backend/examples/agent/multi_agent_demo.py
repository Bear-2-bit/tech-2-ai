import asyncio

from langchain.agents import create_agent

from app.ai.tools.calculator import calculator
from app.ai.tools.database_query import database_query
from app.ai.tools.knowledge_search import knowledge_search
from app.dependencies import get_langchain_model


async def main():
    model = get_langchain_model()

    agent = create_agent(
        model=model,
        tools=[
            calculator,
            knowledge_search,
            database_query,
        ],
        system_prompt="""
你是一个企业AI助手。

你可以根据用户问题自主选择工具：

- 数学计算使用 calculator
- 企业知识库、文档资料使用 knowledge_search
- 销售、订单、统计等数据库问题使用 database_query

需要多个工具时，可以根据前一步结果继续调用其他工具。
不要编造工具没有返回的信息。
""",
    )

    result = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": "查询数据库中销售额最高的部门，并计算它的销售额占全部销售额的百分比。",
            }
        ]
    })

    print("Agent Messages:")

    for message in result["messages"]:
        print(
            type(message).__name__,
            "=>",
            message.content,
        )

        if getattr(message, "tool_calls", None):
            print("Tool Calls:", message.tool_calls)

    print("\nFinal Answer:")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())