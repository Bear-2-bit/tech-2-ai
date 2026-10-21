import asyncio
import json
from math import isclose
from time import perf_counter

from app.core.config import get_settings
from app.core.errors import AppError, public_error
from app.core.store import encode, get_store
from app.core.telemetry import current_run, span
from app.modules.engineering.schemas import EvalRequest, GoldenCase


def load_cases() -> list[GoldenCase]:
    return [
        GoldenCase.model_validate(item)
        for item in json.loads(get_settings().eval_dataset_path.read_text(encoding="utf-8"))
    ]


def equivalent(actual, expected, ordered=False) -> bool:
    if not ordered:
        actual, expected = sorted(actual, key=encode), sorted(expected, key=encode)
    if len(actual) != len(expected):
        return False
    for left, right in zip(actual, expected, strict=True):
        if len(left) != len(right):
            return False
        for value, reference in zip(left, right, strict=True):
            if isinstance(value, (int, float)) and isinstance(reference, (int, float)):
                if not isclose(value, reference, rel_tol=1e-6, abs_tol=1e-6):
                    return False
            elif value != reference:
                return False
    return True


async def run_case(case: GoldenCase) -> dict:
    if case.type == "sql":
        from app.modules.nl2sql.database import execute
        from app.modules.nl2sql.schemas import SQLRequest
        from app.modules.nl2sql.service import query

        actual = await query(SQLRequest(question=case.input, max_rows=500))
        reference = await asyncio.to_thread(execute, case.expected["sql"], 500)
        checks = {
            "execution_accuracy": equivalent(
                actual["rows"], reference["rows"], case.expected.get("ordered", False)
            ),
            "not_truncated": not actual["truncated"] and not reference["truncated"],
        }
        details = {"sql": actual["sql"], "actual_rows": actual["rows"], "expected_rows": reference["rows"]}
    elif case.type == "rag":
        from app.modules.rag.retrieval import search
        from app.modules.rag.schemas import SearchRequest

        actual = await search(SearchRequest(query=case.input, top_k=case.expected.get("top_k", 5)))
        sources = [doc["metadata"]["filename"] for doc in actual["documents"]]
        checks = {"hit_at_k": case.expected["source"] in sources}
        details = {"sources": sources, "expected_source": case.expected["source"]}
    elif case.type == "llm":
        from app.modules.llm import langchain, native

        engine = native if case.expected.get("engine") == "native" else langchain
        actual = await engine.extract(case.input)
        checks = {
            f"field.{key}": actual["result"].get(key) == value
            for key, value in case.expected["fields"].items()
        }
        details = {"result": actual["result"]}
    elif case.type == "agent":
        from app.modules.agent.schemas import AgentRequest
        from app.modules.agent.service import investigate

        actual = await investigate(AgentRequest(query=case.input))
        tools = {step["tool"] for step in actual["steps"]}
        checks = {
            "expected_status": actual["status"] == case.expected.get("status", "success"),
            "required_tools": set(case.expected.get("tools", [])) <= tools,
            "valid_evidence": all(
                key in actual["evidence"] for finding in actual["findings"] for key in finding["evidence_ids"]
            ),
        }
        text = actual["answer"] + encode(actual["findings"])
        for term in case.expected.get("contains", []):
            checks[f"answer.{term}"] = term in text
        details = {"answer": actual["answer"], "tools": sorted(tools), "status": actual["status"]}
    else:
        from app.modules.workflow.graph import run_report
        from app.modules.workflow.schemas import ReportRequest

        actual = await run_report(ReportRequest.model_validate(case.input))
        checks = {
            "report_quality": actual["quality_checks"]["passed"],
            "structured_report": len(actual["report"]["findings"]) >= 2,
        }
        details = {"metrics": actual["metrics"], "quality_checks": actual["quality_checks"]}
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "score": sum(checks.values()) / len(checks),
        "details": details,
    }


async def evaluate(request: EvalRequest) -> dict:
    cases = [
        case
        for case in load_cases()
        if case.type in request.types and (request.case_ids is None or case.id in request.case_ids)
    ][: request.limit]
    if not cases:
        raise AppError("没有匹配的评估用例。", "eval_empty")
    results = []
    run_id = current_run.get()
    for case in cases:
        start = perf_counter()
        try:
            with span("engineering", "eval.case", {"case_id": case.id, "type": case.type}):
                async with asyncio.timeout(120):
                    result = await run_case(case)
            result["error"] = None
        except Exception as exc:
            result = {"passed": False, "score": 0, "checks": {}, "details": {}, "error": public_error(exc)}
        result.update(case_id=case.id, type=case.type, latency_ms=round((perf_counter() - start) * 1000, 2))
        get_store().execute(
            "INSERT OR REPLACE INTO eval_results VALUES(?,?,?)", (run_id, case.id, encode(result))
        )
        results.append(result)
    return {
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "average_score": round(sum(item["score"] for item in results) / len(results), 4),
        "results": results,
        "versions": {
            "application": "2.0.0",
            "dataset": "robot-ops-2026.09-v2",
            "prompt": "v2",
            "model": get_settings().deepseek_model,
            "index_versions": [
                row["id"] for row in get_store().rows("SELECT id FROM documents WHERE status='ready'")
            ],
        },
    }
