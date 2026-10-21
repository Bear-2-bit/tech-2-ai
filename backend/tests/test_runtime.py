import asyncio
import json
import subprocess
import sys

from fastapi.testclient import TestClient

from app.core.jobs import Jobs
from app.core.store import get_store
from app.core.telemetry import current_run, span
from app.main import app


def test_cold_import_does_not_load_ml_libraries():
    code = "import sys; from app.main import app; print(any(n in sys.modules for n in ['torch','sentence_transformers','transformers','langchain_huggingface']))"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=15, check=True)
    assert result.stdout.strip() == "False"


def test_api_local_functions_and_six_modules():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        paths = client.get("/openapi.json").json()["paths"]
        for module in ["llm", "rag", "nl2sql", "agent", "workflow", "engineering"]:
            assert any(path.startswith(f"/api/{module}/") for path in paths)
        assert len(client.get("/api/nl2sql/schema").json()["tables"]) == 8
        assert client.get("/api/rag/status").json()["status"] == "knowledge_empty"
        assert client.post("/api/rag/search", json={"query": "空库问题"}).json()["documents"] == []
        answer = client.post("/api/rag/ask", json={"query": "空库问题"})
        assert answer.json()["status"] == "incomplete"
        trace = client.get(f"/api/engineering/runs/{answer.json()['run_id']}").json()
        assert trace["status"] == "incomplete"
        assert trace["metadata"]["request_id"] == answer.headers["X-Request-ID"]
        assert len(client.get("/api/engineering/evaluations/cases").json()) == 48


def test_invalid_input_and_missing_key(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "deepseek_api_key", None)
    with TestClient(app) as client:
        invalid = client.post("/api/llm/native/chat", json={"messages": []})
        assert invalid.status_code == 422
        assert "input" not in str(invalid.json())
        response = client.post("/api/llm/native/chat", json={"messages": [{"role": "user", "content": "hello"}]})
        assert response.status_code == 503
        assert response.json()["code"] == "configuration"


async def test_job_persists_success_and_nested_spans():
    manager = Jobs()

    async def work():
        with span("test", "child"):
            get_store().usage(current_run.get(), 7, 4)
        return {"ok": True}

    created = manager.submit("test", "run", work)
    await manager.tasks[created["run_id"]]
    result = get_store().run(created["run_id"])
    assert result["status"] == "success"
    assert result["result"] == {"ok": True}
    assert result["input_tokens"] == 7
    assert result["output_tokens"] == 4


async def test_job_timeout_cancel_and_recovery():
    manager = Jobs()

    async def wait():
        await asyncio.sleep(20)

    created = manager.submit("test", "timeout", wait, timeout=0.01)
    await manager.tasks[created["run_id"]]
    assert get_store().run(created["run_id"])["status"] == "timeout"
    created = manager.submit("test", "cancel", wait)
    task = manager.tasks[created["run_id"]]
    await asyncio.sleep(0)
    task.cancel()
    await task
    assert get_store().run(created["run_id"])["status"] == "cancelled"
    with span("test", "old") as run_id:
        pass
    get_store().execute("UPDATE runs SET status='running' WHERE id=?", (run_id,))
    manager.recover()
    assert get_store().run(run_id)["status"] == "interrupted"


async def test_failed_case_does_not_abort_evaluation(monkeypatch):
    from app.modules.engineering import evaluation
    from app.modules.engineering.schemas import EvalRequest, GoldenCase

    monkeypatch.setattr(
        evaluation,
        "load_cases",
        lambda: [
            GoldenCase(id="a", type="sql", input="a", expected={}),
            GoldenCase(id="b", type="sql", input="b", expected={}),
        ],
    )

    async def run_case(case):
        if case.id == "a":
            raise RuntimeError("secret-value")
        return {"checks": {"ok": True}, "passed": True, "score": 1, "details": {}}

    monkeypatch.setattr(evaluation, "run_case", run_case)
    with span("engineering", "eval"):
        result = await evaluation.evaluate(EvalRequest(limit=2))
    assert result["total"] == 2 and result["passed"] == 1
    assert "secret-value" not in json.dumps(result)
