from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from pydantic import BaseModel, Field

from app.ai.sql.schema_reader import read_database_schema
from app.ai.sql.sql_executor import execute_read_only_query
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
6. 请严格返回JSON，包含sql和explanation两个字段。

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

    generated = chain.invoke({
        "schema": schema,
        "question": question,
    })

    print("Generated SQL:")
    print(generated.sql)

    result = execute_read_only_query(
        database_path=DATABASE_PATH,
        sql=generated.sql,
    )

    print("\nColumns:")
    print(result.columns)

    print("\nRows:")
    for row in result.rows:
        print(row)

    print("\nRow Count:")
    print(result.row_count)


if __name__ == "__main__":
    main()