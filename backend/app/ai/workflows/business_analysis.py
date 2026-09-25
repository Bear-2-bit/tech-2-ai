import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.schemas.rag import RAGRequest
from app.schemas.sql import SQLRequest
from app.schemas.workflow import AnalysisPlan, BusinessAnalysisReport
from app.services.rag_service import RAGService
from app.services.sql_service import SQLService


class WorkflowState(TypedDict, total=False):
    query: str

    sql_question: str
    rag_question: str

    sql_result: dict
    rag_result: dict

    report: dict


class BusinessAnalysisWorkflow:
    def __init__(
        self,
        model: ChatDeepSeek,
        sql_service: SQLService,
        rag_service: RAGService,
    ):
        self.sql_service = sql_service
        self.rag_service = rag_service

        plan_model = model.with_structured_output(
            AnalysisPlan,
            method="function_calling",
        )

        plan_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
你是企业经营分析任务规划器。

请把用户任务拆成两个子问题：

1. sql_question
用于查询结构化业务数据库，
例如销售额、部门排名、订单统计等。

2. rag_question
用于查询企业知识库，
例如经营经验、业务规则、分析方法、建议依据等。

严格返回JSON。
""",
            ),
            (
                "human",
                "{query}",
            ),
        ])

        self.plan_chain = plan_prompt | plan_model

        report_model = model.with_structured_output(
            BusinessAnalysisReport,
            method="function_calling",
        )

        report_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
请生成经营分析报告。

要求：
1. 数据事实必须来自数据库结果。
2. 建议优先依据知识库结果。
3. 如果知识库没有相关内容，明确说明证据不足，不要编造知识库内容。
4. 不要虚构输入中不存在的数据。
5. 严格按照提供的结构化字段返回结果。
""",
            ),
            (
                "human",
                """
用户任务：
{query}

数据库结果：
{sql_result}

知识库结果：
{rag_result}
""",
            ),
        ])

        self.report_chain = report_prompt | report_model

        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(WorkflowState)

        builder.add_node("planner", self._planner_node)
        builder.add_node("sql", self._sql_node)
        builder.add_node("rag", self._rag_node)
        builder.add_node("synthesis", self._synthesis_node)

        builder.add_edge(START, "planner")

        builder.add_edge("planner", "sql")
        builder.add_edge("planner", "rag")

        builder.add_edge(
            ["sql", "rag"],
            "synthesis",
        )

        builder.add_edge("synthesis", END)

        return builder.compile()

    async def _planner_node(
        self,
        state: WorkflowState,
    ) -> dict:
        plan = await self.plan_chain.ainvoke({
            "query": state["query"],
        })

        return {
            "sql_question": plan.sql_question,
            "rag_question": plan.rag_question,
        }

    async def _sql_node(
        self,
        state: WorkflowState,
    ) -> dict:
        result = await self.sql_service.query(
            SQLRequest(
                question=state["sql_question"],
                max_rows=50,
            )
        )

        return {
            "sql_result": result.model_dump(),
        }

    async def _rag_node(
        self,
        state: WorkflowState,
    ) -> dict:
        result = await self.rag_service.rag(
            RAGRequest(
                query=state["rag_question"],
                top_k=3,
            )
        )

        return {
            "rag_result": result.model_dump(),
        }

    async def _synthesis_node(
        self,
        state: WorkflowState,
    ) -> dict:
        report = await self.report_chain.ainvoke({
            "query": state["query"],
            "sql_result": json.dumps(
                state["sql_result"],
                ensure_ascii=False,
            ),
            "rag_result": json.dumps(
                state["rag_result"],
                ensure_ascii=False,
            ),
        })

        return {
            "report": report.model_dump(),
        }

    async def run(
        self,
        query: str,
    ) -> WorkflowState:
        return await self.graph.ainvoke({
            "query": query,
        })