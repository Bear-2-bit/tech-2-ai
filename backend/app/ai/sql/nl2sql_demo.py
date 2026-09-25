from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from pydantic import BaseModel, Field

from app.ai.sql.schema_reader import read_database_schema
from app.core.config import settings


DATABASE_PATH = Path("data/business.db")


class SQLGenerationResult(BaseModel):
    sql: str = Field(description="生成的SQLite查询语句")
    explanation: str = Field(description="SQL的简短说明")


def main():
    schema = read_database_schema(DATABASE_PATH)

    model = ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        api_base=settings.deepseek_base_url,
        temperature=0,
        max_tokens=500,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )

    structured_model = model.with_structured_output(
        SQLGenerationResult,
        method="json_mode",
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
    你是一个SQLite SQL生成器。

    只能根据提供的数据库Schema生成SQL。

    规则：
    1. 只能生成SELECT查询。
    2. 不允许INSERT、UPDATE、DELETE、DROP、ALTER、CREATE。
    3. 只能使用Schema中真实存在的表和字段。
    4. 不要猜测不存在的字段。
    5. sql字段只返回一条SQLite查询语句。
    6. 请严格以JSON格式返回，必须包含sql和explanation两个字段。

    Database Schema:

    {schema}
    """,
        ),
        (
            "human",
            "{question}",
        ),
    ])

    chain = prompt | structured_model

    question = "查询销售额最高的三个部门"

    result = chain.invoke({
        "schema": schema,
        "question": question,
    })

    print("Database Schema:")
    print(schema)

    print("\nQuestion:")
    print(question)

    print("\nSQL:")
    print(result.sql)

    print("\nExplanation:")
    print(result.explanation)


if __name__ == "__main__":
    main()