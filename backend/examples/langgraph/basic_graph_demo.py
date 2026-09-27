from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


class NumberState(TypedDict):
    value: int


def double_node(state: NumberState) -> dict:
    return {
        "value": state["value"] * 2,
    }


def add_ten_node(state: NumberState) -> dict:
    return {
        "value": state["value"] + 10,
    }


def main():
    builder = StateGraph(NumberState)

    builder.add_node(
        "double",
        double_node,
    )

    builder.add_node(
        "add_ten",
        add_ten_node,
    )

    builder.add_edge(
        START,
        "double",
    )

    builder.add_edge(
        "double",
        "add_ten",
    )

    builder.add_edge(
        "add_ten",
        END,
    )

    graph = builder.compile()

    result = graph.invoke({
        "value": 5,
    })

    print(result)


if __name__ == "__main__":
    main()