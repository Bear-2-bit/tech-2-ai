"""Reproducible business fixtures; existing databases are backed up before replacement."""

import argparse
import random
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path

from app.core.config import get_settings

DDL = """
PRAGMA foreign_keys=ON;
CREATE TABLE departments(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT NOT NULL, industry TEXT NOT NULL);
CREATE TABLE products(id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, unit_price_cents INTEGER NOT NULL);
CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id),
 department_id INTEGER NOT NULL REFERENCES departments(id), order_date TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('completed','cancelled','pending')));
CREATE TABLE order_items(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
 product_id INTEGER NOT NULL REFERENCES products(id), quantity INTEGER NOT NULL CHECK(quantity>0),
 unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents>=0));
CREATE TABLE refunds(id INTEGER PRIMARY KEY, order_item_id INTEGER NOT NULL REFERENCES order_items(id),
 amount_cents INTEGER NOT NULL CHECK(amount_cents>0), refund_date TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('completed','pending')), reason TEXT NOT NULL);
CREATE TABLE service_tickets(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
 product_id INTEGER NOT NULL REFERENCES products(id), opened_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('open','resolved')), category TEXT NOT NULL);
CREATE TABLE sales_targets(id INTEGER PRIMARY KEY, department_id INTEGER NOT NULL REFERENCES departments(id),
 month TEXT NOT NULL, metric_key TEXT NOT NULL CHECK(metric_key='net_sales'), amount_cents INTEGER NOT NULL,
 UNIQUE(department_id,month,metric_key));
CREATE INDEX orders_date ON orders(order_date,department_id);
CREATE INDEX item_order ON order_items(order_id);
CREATE INDEX refund_date ON refunds(refund_date);
"""


def seed_database(path: Path, fixture: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.parent / "backups" / f"{path.stem}-{datetime.now():%Y%m%d-%H%M%S-%f}.db"
        backup.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(backup)) as target:
            source.backup(target)
    temporary = path.with_suffix(".seed.tmp")
    temporary.unlink(missing_ok=True)
    rng = random.Random(20260930)
    with closing(sqlite3.connect(temporary)) as db:
        db.executescript(DDL)
        db.executemany("INSERT INTO departments VALUES(?,?)", enumerate(["华东", "华南", "华北", "华中"], 1))
        db.executemany(
            "INSERT INTO customers VALUES(?,?,?)",
            [(i, f"演示客户{i:03}", ["医院", "康养", "教育"][i % 3]) for i in range(1, 121)],
        )
        products = [
            (1, "ROBOT-A", "机器人A", 12000000),
            (2, "ROBOT-B", "机器人B", 8000000),
            (3, "ROBOT-C", "机器人C", 15000000),
            (4, "SERVICE", "年度维护", 500000),
        ]
        db.executemany("INSERT INTO products VALUES(?,?,?,?)", products)
        if fixture:
            db.executemany(
                "INSERT INTO orders VALUES(?,?,?,?,?)",
                [
                    (1, 1, 1, "2026-08-10", "completed"),
                    (2, 2, 1, "2026-09-10", "completed"),
                    (3, 3, 2, "2026-09-12", "completed"),
                    (4, 4, 1, "2026-09-15", "cancelled"),
                ],
            )
            db.executemany(
                "INSERT INTO order_items VALUES(?,?,?,?,?)",
                [
                    (1, 1, 1, 2, 12000000),
                    (2, 2, 1, 1, 12000000),
                    (3, 2, 2, 1, 8000000),
                    (4, 3, 2, 1, 8000000),
                    (5, 4, 3, 1, 15000000),
                ],
            )
            db.executemany(
                "INSERT INTO refunds VALUES(?,?,?,?,?,?)",
                [
                    (1, 2, 2000000, "2026-09-20", "completed", "交付延期"),
                    (2, 2, 1000000, "2026-09-21", "pending", "待审核"),
                ],
            )
            db.execute("INSERT INTO service_tickets VALUES(1,2,1,'2026-09-18','open','安装调试')")
            db.executemany(
                "INSERT INTO sales_targets VALUES(?,?,?,?,?)",
                [(1, 1, "2026-09", "net_sales", 20000000), (2, 2, "2026-09", "net_sales", 10000000)],
            )
        else:
            order_id = item_id = refund_id = ticket_id = target_id = 0
            for offset in range(18):
                year, month = divmod(2025 * 12 + 3 + offset, 12)
                month += 1
                for department in range(1, 5):
                    target_id += 1
                    db.execute(
                        "INSERT INTO sales_targets VALUES(?,?,?,?,?)",
                        (
                            target_id,
                            department,
                            f"{year}-{month:02}",
                            "net_sales",
                            300000000,
                        ),
                    )
                    count = 12 if (year, month, department) == (2026, 9, 1) else rng.randint(17, 27)
                    for _ in range(count):
                        order_id += 1
                        day = date(year, month, rng.randint(1, 26))
                        status = rng.choices(["completed", "cancelled", "pending"], [90, 6, 4])[0]
                        db.execute(
                            "INSERT INTO orders VALUES(?,?,?,?,?)",
                            (
                                order_id,
                                rng.randint(1, 120),
                                department,
                                day.isoformat(),
                                status,
                            ),
                        )
                        for _ in range(rng.randint(1, 3)):
                            item_id += 1
                            product = rng.choice(products)
                            quantity = rng.randint(1, 3)
                            price = product[3] * rng.randint(90, 100) // 100
                            db.execute(
                                "INSERT INTO order_items VALUES(?,?,?,?,?)",
                                (item_id, order_id, product[0], quantity, price),
                            )
                            elevated = (year, month, department, product[0]) == (2026, 9, 1, 1)
                            if status == "completed" and rng.random() < (0.6 if elevated else 0.07):
                                refund_id += 1
                                refund_day = min(day + timedelta(days=2), date(2026, 9, 30))
                                db.execute(
                                    "INSERT INTO refunds VALUES(?,?,?,?,?,?)",
                                    (
                                        refund_id,
                                        item_id,
                                        price,
                                        refund_day.isoformat(),
                                        "completed",
                                        "交付延期"
                                        if elevated
                                        else rng.choice(["客户变更", "安装问题", "产品退回"]),
                                    ),
                                )
                            if status == "completed" and rng.random() < (0.5 if elevated else 0.08):
                                ticket_id += 1
                                db.execute(
                                    "INSERT INTO service_tickets VALUES(?,?,?,?,?,?)",
                                    (
                                        ticket_id,
                                        order_id,
                                        product[0],
                                        day.isoformat(),
                                        rng.choice(["open", "resolved"]),
                                        "安装调试"
                                        if elevated
                                        else rng.choice(["维护咨询", "使用培训", "安装调试"]),
                                    ),
                                )
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        db.execute("PRAGMA user_version=2")
        db.commit()
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true", help="生成人工可核对的小数据集")
    parser.add_argument("--output", type=Path, default=get_settings().database_path)
    args = parser.parse_args()
    seed_database(args.output, args.fixture)
    print(f"业务数据库已生成：{args.output}；种子 20260930；旧文件已备份。")


if __name__ == "__main__":
    main()
