"""Small live verification against configured services; never prints credentials or raw exceptions."""

import argparse
import asyncio
import json
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import public_error
from app.core.telemetry import span


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rag", action="store_true", help="真实本地模型入库、检索与回答")
    parser.add_argument("--business", action="store_true", help="真实 NL2SQL、Agent、Workflow 与少量评估")
    args = parser.parse_args()
    results = []

    async def check(name, work):
        try:
            async with asyncio.timeout(240):
                value = await work()
            results.append({"name": name, "passed": True, "summary": value})
        except Exception as exc:
            results.append(
                {"name": name, "passed": False, "error_type": type(exc).__name__, "detail": public_error(exc)}
            )
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)

    from app.modules.llm import langchain, native
    from app.modules.llm.schemas import ChatRequest

    for engine in (native, langchain):

        async def chat(engine=engine):
            value = await engine.chat(ChatRequest(messages=[{"role": "user", "content": "只回复OK"}], max_tokens=32))
            assert value["answer"]
            return {"model": value["model"], "finish_reason": value["finish_reason"]}

        async def stream(engine=engine):
            events = [
                item
                async for item in engine.stream(
                    ChatRequest(messages=[{"role": "user", "content": "只回复OK"}], max_tokens=32)
                )
            ]
            assert events[-1]["type"] == "done"
            return {"events": len(events), "finish_reason": events[-1]["finish_reason"]}

        async def extract(engine=engine):
            value = await engine.extract("使用Vue开发页面，优先级high。")
            assert value["result"]["priority"] == "high" and "Vue" in value["result"]["technologies"]
            return {"fields_valid": True, "attempts": value["attempts"]}

        for label, work in [("chat", chat), ("stream", stream), ("extract", extract)]:
            with span("smoke", f"{engine.__name__.split('.')[-1]}.{label}"):
                await check(f"{engine.__name__.split('.')[-1]}.{label}", work)

    if args.rag:
        from app.modules.rag.ingestion import ingest
        from app.modules.rag.retrieval import search
        from app.modules.rag.schemas import SearchRequest
        from app.modules.rag.service import ask

        async def ingestion():
            count = 0
            for path in sorted(get_settings().knowledge_dir.glob("*.md")):
                await ingest(path, path.name, {"category": path.stem.split("-")[0], "effective_from": "2025-04-01"})
                count += 1
            return {"documents": count}

        async def retrieval():
            value = await search(SearchRequest(query="机器人A标准保修期", top_k=5))
            assert "policy-warranty.md" in [doc["metadata"]["filename"] for doc in value["documents"]]
            return {"hits": len(value["documents"])}

        async def answer():
            value = await ask(SearchRequest(query="机器人A的标准保修期是多久？"))
            assert value["status"] == "success" and value["citations"]
            return {"status": value["status"], "citations": len(value["citations"])}

        for label, work in [("rag.ingestion", ingestion), ("rag.retrieval", retrieval), ("rag.answer", answer)]:
            with span("smoke", label):
                await check(label, work)

    if args.business:
        from app.modules.agent.schemas import AgentRequest
        from app.modules.agent.service import investigate
        from app.modules.engineering.evaluation import evaluate
        from app.modules.engineering.schemas import EvalRequest
        from app.modules.nl2sql.schemas import SQLRequest
        from app.modules.nl2sql.service import query
        from app.modules.workflow.graph import run_report
        from app.modules.workflow.schemas import ReportRequest

        async def sql():
            value = await query(SQLRequest(question="查询2026年9月华东完成订单数，只返回数量"))
            assert value["row_count"] == 1
            return {"rows": value["rows"]}

        async def agent():
            value = await investigate(AgentRequest(query="查询2026年9月华东完成订单数，并给出证据。"))
            assert value["status"] == "success" and value["evidence"]
            return {"status": value["status"], "tools": [step["tool"] for step in value["steps"]]}

        async def workflow():
            value = await run_report(ReportRequest(month="2026-09", department_id=1))
            assert value["quality_checks"]["passed"]
            return {"status": value["status"], "checks": value["quality_checks"]}

        async def evaluation():
            value = await evaluate(EvalRequest(types=["sql", "rag"], limit=2))
            return {"total": value["total"], "passed": value["passed"]}

        for label, work in [("nl2sql", sql), ("agent", agent), ("workflow", workflow), ("evaluation", evaluation)]:
            with span("smoke", label):
                await check(label, work)

    output = Path(__file__).resolve().parents[1] / "data" / "smoke-results.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    from app.resources import close_resources

    await close_resources()
    if native.get_client.cache_info().currsize:
        await native.get_client().close()
    if not all(result["passed"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
