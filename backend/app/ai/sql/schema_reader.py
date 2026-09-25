import sqlite3
from pathlib import Path


def read_database_schema(database_path: Path) -> str:
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    tables = cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """).fetchall()

    schema_parts = []

    for (table_name,) in tables:
        columns = cursor.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        column_lines = [
            f"- {column[1]} {column[2]}"
            for column in columns
        ]

        schema_parts.append(
            f"Table: {table_name}\n" + "\n".join(column_lines)
        )

    connection.close()

    return "\n\n".join(schema_parts)

if __name__ == "__main__":
    schema = read_database_schema("data/business.db")
    print(schema)
    
