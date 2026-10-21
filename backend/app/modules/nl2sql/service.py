import asyncio
import json

from app.core.errors import AppError
from app.core.telemetry import span
from app.modules.nl2sql.database import execute, schema, validate_sql
from app.modules.nl2sql.schemas import GeneratedSQL, SQLRequest
from app.resources import get_model, model_config


def scope_issues(question: str, sql: str) -> list[str]:
    """Catch dropped explicit department constraints before executing an otherwise valid query."""
    import sqlglot
    from sqlglot import exp

    tree = sqlglot.parse_one(validate_sql(sql), read="sqlite")
    literals = {node.this for node in tree.find_all(exp.Literal) if node.is_string}
    department_ids = {
        node.right.this
        for node in tree.find_all(exp.EQ)
        if isinstance(node.left, exp.Column)
        and node.left.name == "department_id"
        and isinstance(node.right, exp.Literal)
    }
    return [
        f"查询遗漏了用户明确指定的部门：{name}"
        for identifier, name in enumerate(["华东", "华南", "华北", "华中"], 1)
        if name in question and name not in literals and str(identifier) not in department_ids
    ]


async def query(request: SQLRequest) -> dict:
    from langchain_core.prompts import ChatPromptTemplate

    with span("nl2sql", "sql.query") as run_id:
        definition = await asyncio.to_thread(schema)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是 SQLite 查询生成器。只查询提供的表，遵守指标定义与字段枚举，不得臆测状态值。"
                    "必须保留用户明确的时间、部门和状态条件。多个期间和指标可使用CTE分别聚合后一次返回。"
                    "输出 sql 和 explanation。\n{schema}\n修正要求：{errors}",
                ),
                ("human", "{question}"),
            ]
        )
        chain = prompt | get_model().with_structured_output(GeneratedSQL, method="function_calling")
        errors = []
        for _ in range(2):
            generated = await chain.ainvoke(
                {
                    "schema": json.dumps(definition, ensure_ascii=False),
                    "question": request.question,
                    "errors": errors,
                },
                config=model_config(),
            )
            errors = scope_issues(request.question, generated.sql)
            if not errors:
                break
        if errors:
            raise AppError("模型未保留用户明确指定的查询范围，请重新描述问题。", "sql_scope", 502)
        with span("nl2sql", "sql.execute"):
            result = await asyncio.to_thread(execute, generated.sql, request.max_rows)
        return {
            "question": request.question,
            "sql": generated.sql,
            "explanation": generated.explanation,
            "run_id": run_id,
            **result,
        }
