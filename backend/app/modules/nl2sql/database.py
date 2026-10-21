import sqlite3
from contextlib import contextmanager
from pathlib import Path
from time import monotonic

from app.core.config import get_settings
from app.core.errors import AppError

TABLES = {
    "departments",
    "customers",
    "products",
    "orders",
    "order_items",
    "refunds",
    "service_tickets",
    "sales_targets",
}
DESCRIPTIONS = {
    "departments": "销售部门与区域",
    "customers": "演示客户及行业",
    "products": "产品目录，价格是参考价",
    "orders": "订单主表，按 order_date 统计完成订单",
    "order_items": "成交明细，成交单价与数量在这里",
    "refunds": "退款事实，按 refund_date 统计已完成退款",
    "service_tickets": "售后工单，按 opened_at 统计新增",
    "sales_targets": "部门月度净销售目标，month 格式 YYYY-MM",
}
ENUMS = {
    ("orders", "status"): {"completed": "已完成", "cancelled": "已取消", "pending": "待完成"},
    ("refunds", "status"): {"completed": "退款完成", "pending": "待退款"},
    ("service_tickets", "status"): {"open": "未关闭", "resolved": "已解决/已关闭"},
    ("sales_targets", "metric_key"): {"net_sales": "净销售额"},
}
METRICS = """金额字段均为整数分，展示人民币时除以 100.0。
销售额=统计期内 status='completed' 订单的 order_items.quantity*unit_price_cents 之和，日期按 orders.order_date。
退款额=统计期内 status='completed' 退款的 amount_cents 之和，日期按 refunds.refund_date，可能来自往期订单。
净销售额=本期销售额-本期退款额；完成订单数只统计 completed；客单价=销售额/完成订单数。
目标 metric_key='net_sales'，目标达成率=净销售额/目标额；上期为零时环比为 null。
不要直接连接两个一对多表后求和，先分别聚合订单明细和退款，避免重复计算。
退款率按金额计算=本期退款额/本期销售额，不代表同一订单群体的退货概率。
演示数据范围为 2025-04 至 2026-09；未明确年份时先澄清，不能用系统当前日期替代数据范围。
关系：orders.customer_id→customers.id；orders.department_id→departments.id；order_items.order_id→orders.id；
order_items.product_id→products.id；refunds.order_item_id→order_items.id；service_tickets.order_id→orders.id；
service_tickets.product_id→products.id；sales_targets.department_id→departments.id。"""


@contextmanager
def connect(path: Path | None = None):
    path = path or get_settings().database_path
    if not path.is_file():
        raise AppError("业务数据库未初始化，请运行 python -m scripts.seed。", "database_missing", 503)
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        yield db
    finally:
        db.close()


def schema(path: Path | None = None) -> dict:
    with connect(path) as db:
        tables = []
        for name in sorted(TABLES):
            columns = db.execute(f'PRAGMA table_info("{name}")').fetchall()
            if not columns:
                raise AppError("业务数据库仍为旧版，请备份后运行初始化脚本。", "database_version", 503)
            tables.append(
                {
                    "name": name,
                    "description": DESCRIPTIONS[name],
                    "columns": [
                        {"name": row[1], "type": row[2], "values": ENUMS.get((name, row[1]))}
                        for row in columns
                    ],
                    "row_count": db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0],
                }
            )
    return {"tables": tables, "metric_definitions": METRICS, "dataset_version": "robot-ops-2026.09-v2"}


def validate_sql(sql: str) -> str:
    import sqlglot
    from sqlglot import exp

    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.ParseError as exc:
        raise AppError("SQL 语法无效。", "sql_invalid") from exc
    if len(statements) != 1 or not isinstance(
        statements[0], (exp.Select, exp.Union, exp.Intersect, exp.Except)
    ):
        raise AppError("只允许一条 SELECT 查询。", "sql_forbidden")
    tree = statements[0]
    forbidden = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter, exp.Command, exp.Into)
    if any(isinstance(node, forbidden) for node in tree.walk()):
        raise AppError("查询包含不允许的操作。", "sql_forbidden")
    ctes = {node.alias_or_name.lower() for node in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        if table.name.lower() not in TABLES | ctes or table.db or table.catalog:
            raise AppError("只能查询已公开的业务表。", "sql_forbidden")
    return tree.sql(dialect="sqlite")


def execute(sql: str, max_rows: int = 100, path: Path | None = None, parameters=()) -> dict:
    safe_sql = validate_sql(sql)
    deadline = monotonic() + get_settings().sql_timeout_seconds
    with connect(path) as db:

        def authorize(action, name, column, database, trigger):
            if action == sqlite3.SQLITE_READ and name.lower() not in TABLES:
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_FUNCTION and (column or "").lower() in {
                "load_extension",
                "readfile",
                "writefile",
            }:
                return sqlite3.SQLITE_DENY
            allowed = {
                sqlite3.SQLITE_SELECT,
                sqlite3.SQLITE_READ,
                sqlite3.SQLITE_FUNCTION,
                sqlite3.SQLITE_RECURSIVE,
            }
            return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY

        db.set_authorizer(authorize)
        db.set_progress_handler(lambda: int(monotonic() > deadline), 1000)
        try:
            cursor = db.execute(safe_sql, parameters)
            rows = cursor.fetchmany(max_rows + 1)
            return {
                "columns": [item[0] for item in cursor.description],
                "rows": [list(row) for row in rows[:max_rows]],
                "row_count": min(len(rows), max_rows),
                "truncated": len(rows) > max_rows,
            }
        except sqlite3.DatabaseError as exc:
            code = "sql_timeout" if "interrupted" in str(exc).lower() else "sql_execution"
            message = (
                "查询超过执行预算。"
                if code == "sql_timeout"
                else "SQL 无法执行，请检查字段、关联关系和统计口径。"
            )
            raise AppError(message, code) from exc
