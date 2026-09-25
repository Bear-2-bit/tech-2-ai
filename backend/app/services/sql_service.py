import asyncio
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek

from app.ai.sql.schema_reader import read_database_schema
from app.ai.sql.sql_executor import execute_read_only_query
from app.schemas.sql import SQLGenerationResult, SQLRequest, SQLResponse


class SQLService:
    def __init__(
        self,
        database_path: Path,
        model: ChatDeepSeek,
    ):
        self.database_path = database_path

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
5. sql字段只能包含一条SQLite查询语句。
6. 不要使用Markdown代码块。
7. SQL必须直接以SELECT开头。
8. 不允许使用WITH或CTE。
9. 严格返回JSON，包含sql和explanation两个字段。

Database Schema:

{schema}
""",
            ),
            (
                "human",
                "{question}",
            ),
        ])

        self.chain = prompt | structured_model

    async def query(self, request: SQLRequest) -> SQLResponse:
        schema = read_database_schema(self.database_path)

        generated = await self.chain.ainvoke({
            "schema": schema,
            "question": request.question,
        })
        print("Generated SQL:", generated.sql)

        execution = await asyncio.to_thread(
            execute_read_only_query,
            self.database_path,
            generated.sql,
            request.max_rows,
        )

        return SQLResponse(
            question=request.question,
            sql=generated.sql,
            explanation=generated.explanation,
            columns=execution.columns,
            rows=execution.rows,
            row_count=execution.row_count,
            truncated=execution.truncated,
        )