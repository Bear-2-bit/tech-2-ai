import sqlite3
from contextlib import closing

import pytest

from app.core.errors import AppError
from app.modules.nl2sql.database import execute, schema
from app.modules.workflow.metrics import collect, previous_month
from app.modules.workflow.schemas import ReportRequest
from scripts.seed import seed_database


def test_schema_has_relationship_domain():
    definition = schema()
    assert len(definition["tables"]) == 8
    assert "退款" in definition["metric_definitions"]
    tickets = next(table for table in definition["tables"] if table["name"] == "service_tickets")
    assert next(column for column in tickets["columns"] if column["name"] == "status")["values"]["open"] == "未关闭"


def test_explicit_department_scope_is_preserved():
    from app.modules.nl2sql.service import scope_issues

    assert scope_issues("查询华南退款", "SELECT SUM(amount_cents) FROM refunds")
    assert not scope_issues("查询华南订单", "SELECT COUNT(*) FROM orders WHERE department_id=2")
    assert not scope_issues(
        "查询华南订单", "SELECT COUNT(*) FROM orders o JOIN departments d ON o.department_id=d.id WHERE d.name='华南'"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM orders",
        "SELECT * FROM orders; SELECT * FROM products",
        "PRAGMA database_list",
        "SELECT * FROM sqlite_master",
        "SELECT * FROM main.orders",
        "ATTACH DATABASE 'a.db' AS a",
        "SELECT * FROM sessions",
        "CREATE TABLE test(id)",
        "SELECT * INTO x FROM orders",
    ],
)
def test_reject_unsafe_sql(sql):
    with pytest.raises(AppError):
        execute(sql)


def test_literals_are_not_mistaken_for_sql_operations():
    assert execute("SELECT 'delete; drop' AS label")["rows"] == [["delete; drop"]]


def test_cte_and_read_only_queries():
    result = execute("WITH done AS (SELECT id FROM orders WHERE status='completed') SELECT COUNT(*) FROM done")
    assert result["rows"] == [[3]]
    assert execute("SELECT id FROM orders ORDER BY id", max_rows=2)["truncated"]


def test_sql_errors_are_explained_without_raw_values():
    with pytest.raises(AppError, match="SQL 无法执行"):
        execute("SELECT missing_column FROM orders")


def test_expensive_query_is_interrupted(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "sql_timeout_seconds", 0.001)
    with pytest.raises(AppError) as error:
        execute("WITH RECURSIVE x(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM x WHERE n<100000000) SELECT SUM(n) FROM x")
    assert error.value.code == "sql_timeout"


def test_monthly_metrics_do_not_multiply_joined_amounts():
    result = collect(ReportRequest(month="2026-09", department_id=1))
    current = result["current"]
    assert current["sales_cents"] == 20000000
    assert current["refund_cents"] == 2000000
    assert current["net_sales_cents"] == 18000000
    assert current["order_count"] == 1
    assert current["attainment"] == 0.9
    assert current["net_growth"] == -0.25
    assert current["ticket_count"] == 1


def test_all_departments_use_weighted_target():
    current = collect(ReportRequest(month="2026-09"))["current"]
    assert current["net_sales_cents"] == 26000000
    assert current["attainment"] == round(26000000 / 30000000, 6)


def test_previous_zero_is_unknown():
    assert collect(ReportRequest(month="2026-09", department_id=2))["current"]["net_growth"] is None
    assert previous_month("2026-01") == "2025-12"


def test_seed_is_reproducible_and_preserves_existing_file(environment):
    output = environment / "other.db"
    seed_database(output, fixture=True)
    with closing(sqlite3.connect(output)) as db:
        first = db.execute("SELECT * FROM orders").fetchall()
    seed_database(output, fixture=True)
    with closing(sqlite3.connect(output)) as db:
        assert first == db.execute("SELECT * FROM orders").fetchall()
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
    assert list((environment / "backups").glob("other-*.db"))
