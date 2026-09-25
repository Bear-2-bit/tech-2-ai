import re


FORBIDDEN_KEYWORDS = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "attach",
    "detach",
    "pragma",
    "vacuum",
]


def validate_sql(sql: str) -> str:
    sql = sql.strip()

    if sql.endswith(";"):
        sql = sql[:-1].strip()

    if ";" in sql:
        raise ValueError("Only one SQL statement is allowed")

    if not re.match(r"^select\b", sql, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed")

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", sql, re.IGNORECASE):
            raise ValueError(f"Forbidden SQL keyword: {keyword}")

    return sql