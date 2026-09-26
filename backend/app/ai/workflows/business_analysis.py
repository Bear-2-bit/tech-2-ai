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

from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langsmith import get_current_run_tree, set_run_metadata, traceable

from app.ai.tracing.store import TraceStore
from app.schemas.trace import TraceSummary

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
        trace_store: TraceStore,
    ):
        self.sql_service = sql_service
        self.rag_service = rag_service
        self.trace_store = trace_store

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

        builder.add_node(
            "planner",
            self._planner_node,
        )

        builder.add_node(
            "sql",
            self._sql_node,
        )

        builder.add_node(
            "rag",
            self._rag_node,
        )

        builder.add_node(
            "synthesis",
            self._synthesis_node,
        )

        builder.add_edge(
            START,
            "planner",
        )

        builder.add_edge(
            "planner",
            "sql",
        )

        builder.add_edge(
            "planner",
            "rag",
        )

        builder.add_edge(
            ["sql", "rag"],
            "synthesis",
        )

        builder.add_edge(
            "synthesis",
            END,
        )

        return builder.compile()

    @traceable(
        name="workflow.planner",
        run_type="chain",
        tags=[
            "workflow",
            "planner",
        ],
    )
    async def _planner_node(
        self,
        state: WorkflowState,
    ) -> dict:
        plan = await self.plan_chain.ainvoke({
            "query": state["query"],
        })

        set_run_metadata(
            sql_question=plan.sql_question,
            rag_question=plan.rag_question,
        )

        return {
            "sql_question": plan.sql_question,
            "rag_question": plan.rag_question,
        }

    @traceable(
        name="workflow.sql",
        run_type="chain",
        tags=[
            "workflow",
            "sql",
            "nl2sql",
        ],
    )
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

        data = result.model_dump()

        set_run_metadata(
            sql_question=state["sql_question"],
            generated_sql=data.get("sql"),
            row_count=len(
                data.get("rows", [])
            ),
        )

        return {
            "sql_result": data,
        }

    @traceable(
        name="workflow.rag",
        run_type="chain",
        tags=[
            "workflow",
            "rag",
        ],
    )
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

        data = result.model_dump()

        documents = (
            data.get("retrieved_documents")
            or data.get("documents")
            or []
        )

        set_run_metadata(
            rag_question=state["rag_question"],
            top_k=3,
            document_count=len(documents),
        )

        return {
            "rag_result": data,
        }

    @traceable(
        name="workflow.synthesis",
        run_type="chain",
        tags=[
            "workflow",
            "synthesis",
        ],
    )
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

        data = report.model_dump()

        set_run_metadata(
            report_title=data.get("title"),
            finding_count=len(
                data.get("key_findings", [])
            ),
            recommendation_count=len(
                data.get(
                    "recommendations",
                    [],
                )
            ),
        )

        return {
            "report": data,
        }

    @traceable(
        name="business_analysis",
        run_type="chain",
        tags=[
            "workflow",
            "business-analysis",
        ],
        metadata={
            "workflow": "business_analysis",
        },
    )
    async def run(
        self,
        query: str,
    ) -> WorkflowState:
        trace_id = str(uuid4())

        current_run = get_current_run_tree()

        langsmith_trace_id = (
            str(current_run.trace_id)
            if current_run
            else None
        )

        set_run_metadata(
            app_trace_id=trace_id,
        )

        usage_callback = UsageMetadataCallbackHandler()

        started_at = datetime.now(timezone.utc)
        start = perf_counter()

        status = "success"
        error = None

        try:
            result = await self.graph.ainvoke(
                {
                    "query": query,
                },
                config={
                    "callbacks": [
                        usage_callback,
                    ],
                },
            )

            return result

        except Exception as exc:
            status = "error"
            error = (
                f"{type(exc).__name__}: {exc}"
            )

            raise

        finally:
            latency_ms = (
                perf_counter() - start
            ) * 1000

            usage = usage_callback.usage_metadata

            input_tokens = sum(
                item.get("input_tokens", 0) or 0
                for item in usage.values()
            )

            output_tokens = sum(
                item.get("output_tokens", 0) or 0
                for item in usage.values()
            )

            total_tokens = sum(
                item.get("total_tokens", 0) or 0
                for item in usage.values()
            )

            set_run_metadata(
                app_trace_id=trace_id,
                status=status,
                latency_ms=round(latency_ms, 2),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )

            self.trace_store.add(
                TraceSummary(
                    trace_id=trace_id,
                    langsmith_trace_id=langsmith_trace_id,
                    name="business_analysis",
                    status=status,
                    started_at=started_at,
                    latency_ms=round(
                        latency_ms,
                        2,
                    ),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    input_preview=query[:120],
                    error=error,
                )
            )