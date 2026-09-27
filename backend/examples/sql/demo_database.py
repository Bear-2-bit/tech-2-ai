import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/business.db")


def init_demo_database() -> None:
    DATABASE_PATH.parent.mkdir(exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.executescript("""
    CREATE TABLE IF NOT EXISTS sales_orders (
        id INTEGER PRIMARY KEY,
        department TEXT NOT NULL,
        product TEXT NOT NULL,
        amount REAL NOT NULL,
        order_date TEXT NOT NULL
    );

    DELETE FROM sales_orders;

    INSERT INTO sales_orders (department, product, amount, order_date) VALUES
    ('华东', '机器人A', 120000, '2026-01-10'),
    ('华南', '机器人B', 80000, '2026-01-15'),
    ('华东', '机器人C', 150000, '2026-02-02'),
    ('华北', '机器人A', 95000, '2026-02-18'),
    ('华南', '机器人C', 130000, '2026-03-05');
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    init_demo_database()
    print(f"Database created: {DATABASE_PATH}")