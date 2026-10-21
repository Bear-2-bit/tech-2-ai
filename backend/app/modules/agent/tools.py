import json
from typing import Literal

from app.core.errors import AppError
from app.core.telemetry import span


def create_tools(evidence: dict):
    from langchain_core.tools import tool
    from pydantic import ValidationError

    @tool
    async def query_business_data(question: str) -> str:
        """以自然语言查询机器人销售、订单、退款和售后数据库；必须明确统计年份和范围。返回只读 SQL 及证据 ID。"""
        from app.modules.nl2sql.schemas import SQLRequest
        from app.modules.nl2sql.service import query

        with span("agent", "tool.query_business_data"):
            try:
                result = await query(SQLRequest(question=question, max_rows=30))
                key = f"S{1 + sum(item.startswith('S') for item in evidence)}"
                evidence[key] = {"type": "sql", **result}
                return json.dumps({"evidence_id": key, **result}, ensure_ascii=False)
            except (AppError, ValidationError) as exc:
                return json.dumps(
                    {
                        "error": str(exc) if isinstance(exc, AppError) else "工具输入格式错误，请修正参数",
                        "code": getattr(exc, "code", "tool_input"),
                    },
                    ensure_ascii=False,
                )

    @tool
    async def search_knowledge(query: str, as_of: str = "2026-09-30") -> str:
        """检索企业政策、产品和指标定义；返回原始证据，不生成答案。as_of 为 YYYY-MM-DD 生效日期。"""
        from app.modules.rag.retrieval import search
        from app.modules.rag.schemas import SearchRequest

        with span("agent", "tool.search_knowledge"):
            try:
                result = await search(SearchRequest(query=query, top_k=4, as_of=as_of))
                for document in result["documents"]:
                    evidence[document["id"]] = {"type": "document", **document}
                return json.dumps(result, ensure_ascii=False)
            except (AppError, ValidationError) as exc:
                return json.dumps(
                    {
                        "error": str(exc) if isinstance(exc, AppError) else "日期格式应为 YYYY-MM-DD",
                        "code": getattr(exc, "code", "tool_input"),
                    },
                    ensure_ascii=False,
                )

    @tool
    def calculate(a: float, b: float, operation: Literal["add", "subtract", "multiply", "divide"]) -> str:
        """进行确定性四则运算。百分比先除再乘 100，除数不能为零。"""
        import math

        with span("agent", "tool.calculate"):
            if not math.isfinite(a) or not math.isfinite(b) or (operation == "divide" and b == 0):
                return '{"error":"输入需为有限数，且除数不能为零"}'
            result = {
                "add": lambda: a + b,
                "subtract": lambda: a - b,
                "multiply": lambda: a * b,
                "divide": lambda: a / b,
            }[operation]()
            if not math.isfinite(result):
                return '{"error":"计算结果超出有限数范围"}'
            key = f"C{1 + sum(item.startswith('C') for item in evidence)}"
            evidence[key] = {"type": "calculation", "a": a, "b": b, "operation": operation, "value": result}
            return json.dumps({"evidence_id": key, "value": result})

    return [query_business_data, search_knowledge, calculate]
