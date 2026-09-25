import sqlite3
from pathlib import Path

from pydantic import BaseModel

from app.ai.sql.sql_validator import validate_sql


class SQLExecutionResult(BaseModel):
    columns: list[str]
    rows: list[list]
    row_count: int
    truncated: bool


def execute_read_only_query(
    database_path: Path,
    sql: str,
    max_rows: int = 100,
) -> SQLExecutionResult:
    safe_sql = validate_sql(sql)

    database_uri = f"{database_path.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)

    try:
        cursor = connection.execute(safe_sql)

        columns = [
            description[0]
            for description in cursor.description
        ]

        raw_rows = cursor.fetchmany(max_rows + 1)

        truncated = len(raw_rows) > max_rows
        raw_rows = raw_rows[:max_rows]

        rows = [
            list(row)
            for row in raw_rows
        ]

        return SQLExecutionResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            truncated=truncated,
        )

    finally:
        connection.close()