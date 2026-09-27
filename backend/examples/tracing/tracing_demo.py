from langsmith import traceable

from app.dependencies import get_langchain_model


@traceable(
    name="prepare_question",
    run_type="chain",
)
def prepare_question(question: str) -> str:
    return f"请简洁回答：{question}"


@traceable(
    name="answer_question",
    run_type="chain",
)
async def answer_question(question: str) -> str:
    model = get_langchain_model()

    prepared = prepare_question(question)

    response = await model.ainvoke(
        prepared
    )

    return str(response.content)


async def main():
    result = await answer_question(
        "什么是RAG？"
    )

    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())