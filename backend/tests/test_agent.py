from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from app.modules.agent.schemas import AgentRequest
from app.modules.agent.service import get_session, investigate


class ToolModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


async def test_agent_executes_real_tool_loop_and_preserves_followup(monkeypatch):
    from app.modules.agent import service
    from app.modules.nl2sql import service as sql_service

    async def query(request):
        return {
            "sql": "SELECT COUNT(*) FROM orders",
            "rows": [[4]],
            "columns": ["count"],
            "row_count": 1,
            "truncated": False,
        }

    report = {
        "status": "success",
        "answer": "华东完成订单已查询。",
        "findings": [
            {"statement": "完成订单数量已核实", "evidence_ids": ["S1"]},
        ],
        "uncertainties": [],
        "next_steps": [],
    }
    model = ToolModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "call-1", "name": "query_business_data", "args": {"question": "查询2026年9月华东完成订单数"}}
                ],
            ),
            AIMessage(content="", tool_calls=[{"id": "call-2", "name": "Investigation", "args": report}]),
        ]
    )
    monkeypatch.setattr(service, "get_model", lambda: model)
    monkeypatch.setattr(sql_service, "query", query)
    result = await investigate(AgentRequest(query="查询2026年9月华东完成订单数"))
    assert result["status"] == "success"
    assert result["steps"][0]["tool"] == "query_business_data"
    assert result["evidence"]["S1"]["rows"] == [[4]]
    session = get_session(result["session_id"])
    assert len(session["messages"]["turns"]) == 1
    assert len(session["messages"]["history"]) >= 4
    followup = await investigate(AgentRequest(query="把刚才的结果再解释一下", session_id=result["session_id"]))
    assert followup["session_id"] == result["session_id"]
    assert "S1" in followup["evidence"]


async def test_agent_invalid_evidence_cannot_report_success(monkeypatch):
    from app.modules.agent import service

    model = ToolModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-1",
                        "name": "Investigation",
                        "args": {
                            "status": "success",
                            "answer": "虚构结论",
                            "findings": [{"statement": "没有实际依据", "evidence_ids": ["missing"]}],
                            "uncertainties": [],
                            "next_steps": [],
                        },
                    }
                ],
            )
        ]
    )
    monkeypatch.setattr(service, "get_model", lambda: model)
    result = await investigate(AgentRequest(query="查询订单"))
    assert result["status"] == "incomplete"


async def test_agent_budget_preserves_executed_steps_and_partial_evidence(monkeypatch):
    from app.modules.agent import service
    from app.modules.nl2sql import service as sql_service

    async def query(request):
        return {"rows": [[4]], "columns": ["count"], "row_count": 1, "truncated": False}

    model = ToolModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": f"call-{i}",
                        "name": "query_business_data",
                        "args": {"question": "查询2026年9月华东订单数"},
                    }
                ],
            )
            for i in range(12)
        ]
    )
    monkeypatch.setattr(service, "get_model", lambda: model)
    monkeypatch.setattr(sql_service, "query", query)
    result = await investigate(AgentRequest(query="持续调查"))
    assert result["status"] == "incomplete"
    assert len(result["evidence"]) == len(result["steps"]) == 8
