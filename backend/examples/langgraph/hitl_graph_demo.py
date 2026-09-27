from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ReviewState(TypedDict):
    topic: str
    draft: str
    approved: bool


def generate_node(state: ReviewState) -> dict:
    return {
        "draft": f"关于「{state['topic']}」的自动生成报告。"
    }


def review_node(state: ReviewState) -> dict:
    decision = interrupt({
        "question": "是否批准这份报告？",
        "draft": state["draft"],
    })

    return {
        "approved": decision == "approve"
    }


def route_after_review(state: ReviewState) -> str:
    if state["approved"]:
        return "publish"

    return "end"


def publish_node(state: ReviewState) -> dict:
    print("报告已发布：")
    print(state["draft"])

    return {}


def build_graph():
    builder = StateGraph(ReviewState)

    builder.add_node("generate", generate_node)
    builder.add_node("review", review_node)
    builder.add_node("publish", publish_node)

    builder.add_edge(START, "generate")
    builder.add_edge("generate", "review")

    builder.add_conditional_edges(
        "review",
        route_after_review,
        {
            "publish": "publish",
            "end": END,
        },
    )

    builder.add_edge("publish", END)

    checkpointer = InMemorySaver()

    return builder.compile(
        checkpointer=checkpointer
    )


def main():
    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": "report-001"
        }
    }

    result = graph.invoke(
        {
            "topic": "2026年销售情况",
            "draft": "增长5%，员工福利大大增加",
            "approved": False,
        },
        config,
    )

    print("第一次执行：")
    print(result)

    result = graph.invoke(
        Command(resume="approve"),
        config,
    )

    print("\n恢复执行：")
    print(result)


if __name__ == "__main__":
    main()