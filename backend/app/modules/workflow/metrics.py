from datetime import date

from app.core.errors import AppError
from app.modules.nl2sql.database import execute
from app.modules.workflow.schemas import ReportRequest


def period(month: str) -> tuple[str, str]:
    year, number = map(int, month.split("-"))
    return date(year, number, 1).isoformat(), date(year + (number == 12), number % 12 + 1, 1).isoformat()


def previous_month(month: str) -> str:
    year, number = map(int, month.split("-"))
    return f"{year - (number == 1)}-{number - 1 if number > 1 else 12:02}"


def metrics(month: str, department_id: int | None = None, path=None) -> dict:
    start, end = period(month)
    condition = " AND o.department_id=?" if department_id else ""
    parameters = (start, end, department_id) if department_id else (start, end)
    sales = execute(
        "SELECT COUNT(DISTINCT o.id),COALESCE(SUM(i.quantity*i.unit_price_cents),0) "
        "FROM orders o JOIN order_items i ON i.order_id=o.id "
        "WHERE o.status='completed' AND o.order_date>=? AND o.order_date<?" + condition,
        path=path,
        parameters=parameters,
    )["rows"][0]
    refunds = execute(
        "SELECT COALESCE(SUM(r.amount_cents),0) FROM refunds r "
        "JOIN order_items i ON r.order_item_id=i.id JOIN orders o ON i.order_id=o.id "
        "WHERE r.status='completed' AND r.refund_date>=? AND r.refund_date<?" + condition,
        path=path,
        parameters=parameters,
    )["rows"][0][0]
    tickets = execute(
        "SELECT COUNT(*) FROM service_tickets t JOIN orders o ON t.order_id=o.id "
        "WHERE t.opened_at>=? AND t.opened_at<?" + condition,
        path=path,
        parameters=parameters,
    )["rows"][0][0]
    target = execute(
        "SELECT COALESCE(SUM(amount_cents),0) FROM sales_targets WHERE month=? AND metric_key='net_sales'"
        + (" AND department_id=?" if department_id else ""),
        path=path,
        parameters=(month, department_id) if department_id else (month,),
    )["rows"][0][0]
    net = sales[1] - refunds
    return {
        "month": month,
        "sales_cents": sales[1],
        "refund_cents": refunds,
        "net_sales_cents": net,
        "order_count": sales[0],
        "ticket_count": tickets,
        "target_cents": target,
        "attainment": round(net / target, 6) if target else None,
        "average_order_cents": round(sales[1] / sales[0], 2) if sales[0] else None,
    }


def collect(request: ReportRequest, path=None) -> dict:
    if not "2025-05" <= request.month <= "2026-09":
        raise AppError("可生成含环比的报告范围为 2025-05 至 2026-09。", "report_period")
    current = metrics(request.month, request.department_id, path)
    previous = metrics(previous_month(request.month), request.department_id, path)
    previous_net = previous["net_sales_cents"]
    current["net_growth"] = (
        round((current["net_sales_cents"] - previous_net) / abs(previous_net), 6) if previous_net else None
    )
    return {
        "current": current,
        "previous": previous,
        "department_id": request.department_id,
        "dataset_version": "robot-ops-2026.09-v2",
    }
