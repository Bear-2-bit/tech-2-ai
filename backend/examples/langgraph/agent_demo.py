from langchain.agents import create_agent

from app.ai.tools.calculator import calculator
from app.dependencies import get_langchain_model


def main():
    model = get_langchain_model()

    agent = create_agent(
        model=model,
        tools=[calculator],
        system_prompt="""
你是一个工具型AI助手。

所有数学计算都必须使用 calculator 工具完成，
不要自己直接计算。
""",
    )

    result = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "先计算138乘以927，再把得到的结果除以6。",
            }
        ]
    })

    print("完整 Messages:")

    for message in result["messages"]:
        print(
            type(message).__name__,
            "=>",
            message.content,
        )

    print("\nFinal Answer:")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()