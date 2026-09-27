from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from app.ai.tools.calculator import calculator
from app.dependencies import get_langchain_model


def main():
    model = get_langchain_model()

    tools = [
        calculator,
    ]

    model_with_tools = model.bind_tools(tools)

    def model_node(state: MessagesState) -> dict:
        response = model_with_tools.invoke(
            state["messages"]
        )

        return {
            "messages": [response],
        }

    def should_continue(
        state: MessagesState,
    ) -> Literal["tools", "end"]:
        last_message = state["messages"][-1]

        if last_message.tool_calls:
            return "tools"

        return "end"

    builder = StateGraph(MessagesState)

    builder.add_node(
        "model",
        model_node,
    )

    builder.add_node(
        "tools",
        ToolNode(tools),
    )

    builder.add_edge(
        START,
        "model",
    )

    builder.add_conditional_edges(
        "model",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    builder.add_edge(
        "tools",
        "model",
    )

    graph = builder.compile()

    result = graph.invoke({
        "messages": [
            SystemMessage(
                content=(
                    "你是一个工具型AI助手。"
                    "所有数学计算必须使用calculator工具。"
                )
            ),
            HumanMessage(
                content="先计算138乘以927，再把结果除以6。"
            ),
        ]
    })

    print("Messages:")

    for message in result["messages"]:
        print(
            type(message).__name__,
            "=>",
            message.content,
        )

        if getattr(message, "tool_calls", None):
            print(
                "Tool Calls:",
                message.tool_calls,
            )

    print("\nFinal Answer:")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()