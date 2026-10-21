from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app.core.errors import AppError
from app.modules.llm import langchain, native
from app.modules.llm.schemas import ChatRequest
from app.modules.workflow.graph import validate_report
from app.modules.workflow.metrics import collect
from app.modules.workflow.schemas import MetricFinding, Narrative, ReportRequest


def request():
    return ChatRequest(messages=[{"role": "user", "content": "你好"}])


async def test_native_stream_requires_finish_and_closes_on_cancel(monkeypatch):
    class Stream:
        closed = False

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.closed:
                raise StopAsyncIteration
            self.closed = True
            return SimpleNamespace(
                model="test",
                usage=None,
                choices=[
                    SimpleNamespace(
                        finish_reason=None,
                        delta=SimpleNamespace(content="部分回答"),
                    )
                ],
            )

        async def close(self):
            self.closed = True

    stream = Stream()

    async def create(**kwargs):
        return stream

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(native, "get_client", lambda: client)
    values = []
    with pytest.raises(AppError, match="提前断开"):
        async for value in native.stream(request()):
            values.append(value)
    assert values == [{"type": "delta", "content": "部分回答"}]
    assert stream.closed


async def test_native_extract_retries_validation_only_and_accumulates_usage(monkeypatch):
    responses = iter(['{"priority":"bad"}', '{"title":"任务","priority":"medium","deadline":null,"technologies":[]}'])
    seen = []

    async def create(**kwargs):
        seen.append(kwargs)
        return SimpleNamespace(
            model="test",
            usage=SimpleNamespace(prompt_tokens=5, completion_tokens=3, total_tokens=8),
            choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=next(responses)))],
        )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(native, "get_client", lambda: client)
    result = await native.extract("一个任务")
    assert result["attempts"] == 2
    assert result["usage"]["total_tokens"] == 16
    assert len(seen) == 2


async def test_langchain_chat_and_extraction_normalize_response(monkeypatch):
    class Model:
        model_name = "test"

        def bind(self, **kwargs):
            return self

        async def ainvoke(self, *args, **kwargs):
            return AIMessage(
                content="你好",
                response_metadata={"finish_reason": "stop"},
                usage_metadata={
                    "input_tokens": 2,
                    "output_tokens": 1,
                    "total_tokens": 3,
                },
            )

    monkeypatch.setattr(langchain, "get_model", Model)
    response = await langchain.chat(request())
    assert response["answer"] == "你好"
    assert response["usage"]["total_tokens"] == 3


def test_report_check_rejects_fabricated_number_and_unsupported_advice():
    from app.modules.workflow.schemas import Advice

    data = collect(ReportRequest(month="2026-09", department_id=1))
    report = Narrative(
        title="复盘",
        summary="净销售额下降999999元",
        findings=[
            MetricFinding(metric="net_growth", interpretation="环比下降"),
            MetricFinding(metric="order_count", interpretation="订单变化"),
        ],
        recommendations=[Advice(action="执行某政策", evidence_ids=["missing"])],
    )
    checks = validate_report(report, data, [])
    assert len(checks) == 2


def test_report_accepts_currency_unit_conversion():
    data = collect(ReportRequest(month="2026-09", department_id=1))
    report = Narrative(
        title="复盘",
        summary="本期净销售额18万元",
        findings=[
            MetricFinding(metric="sales_cents", interpretation="完成销售20万元"),
            MetricFinding(metric="order_count", interpretation="订单1单"),
        ],
    )
    assert validate_report(report, data, []) == []


async def test_workflow_runs_parallel_branches_and_marks_missing_knowledge(monkeypatch):
    from app.modules.workflow import graph

    async def empty_search(request):
        return {"documents": []}

    report = Narrative(
        title="月报",
        summary="需要继续核查",
        findings=[
            MetricFinding(metric="sales_cents", interpretation="查看销售变化"),
            MetricFinding(metric="order_count", interpretation="关注订单"),
        ],
        uncertainties=["缺少政策证据"],
    )

    class Model:
        def with_structured_output(self, *args, **kwargs):
            return RunnableLambda(lambda _: {"parsed": report, "parsing_error": None})

    monkeypatch.setattr(graph, "search", empty_search)
    monkeypatch.setattr(graph, "get_model", Model)
    result = await graph.run_report(ReportRequest(month="2026-09", department_id=1))
    assert result["status"] == "incomplete"
    assert result["metrics"]["current"]["net_sales_cents"] == 18000000
    assert "没有可用的知识依据" in result["quality_checks"]["issues"]
