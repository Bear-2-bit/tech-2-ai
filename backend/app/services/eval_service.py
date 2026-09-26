import json
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from app.ai.evaluation.specialized_metrics import (
    contains_all_score,
    execution_accuracy,
    tool_selection_accuracy,
)
from app.schemas.agent import AgentRequest
from app.schemas.eval import (
    EvalCaseResult,
    EvalReport,
    EvalRunRequest,
    GoldenCase,
)
from app.schemas.rag import RAGRequest
from app.schemas.sql import SQLRequest
from app.schemas.workflow import WorkflowRequest
from app.services.agent_service import AgentService
from app.services.rag_service import RAGService
from app.services.sql_service import SQLService
from app.services.workflow_service import WorkflowService


class EvaluationService:
    def __init__(
        self,
        get_rag_service: Callable[[], RAGService],
        get_sql_service: Callable[[], SQLService],
        get_agent_service: Callable[[], AgentService],
        get_workflow_service: Callable[[], WorkflowService],
    ):
        self.get_rag_service = get_rag_service
        self.get_sql_service = get_sql_service
        self.get_agent_service = get_agent_service
        self.get_workflow_service = get_workflow_service

        self.dataset_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "eval"
            / "golden_cases.json"
        )

    def _load_cases(self) -> list[GoldenCase]:
        data = json.loads(
            self.dataset_path.read_text(
                encoding="utf-8"
            )
        )

        return [
            GoldenCase.model_validate(item)
            for item in data
        ]

    async def _eval_sql(
        self,
        case: GoldenCase,
    ) -> tuple[float, dict]:
        service = self.get_sql_service()

        result = await service.query(
            SQLRequest(
                question=case.input,
                max_rows=50,
            )
        )

        data = result.model_dump()

        actual_rows = [
            list(row)
            for row in data["rows"]
        ]

        expected_rows = case.expected["rows"]

        score = execution_accuracy(
            actual_rows=actual_rows,
            expected_rows=expected_rows,
        )

        return score, {
            "sql": data.get("sql"),
            "actual_rows": actual_rows,
            "expected_rows": expected_rows,
        }

    async def _eval_agent(
        self,
        case: GoldenCase,
    ) -> tuple[float, dict]:
        service = self.get_agent_service()

        result = await service.run(
            AgentRequest(
                query=case.input,
            )
        )

        actual_tools = []

        for step in result.steps:
            if step.tool_name:
                actual_tools.append(
                    step.tool_name
                )

            for tool_call in step.tool_calls:
                name = tool_call.get("name")

                if name:
                    actual_tools.append(name)

        actual_tools = list(
            dict.fromkeys(actual_tools)
        )

        expected_tools = case.expected["tools"]

        score = tool_selection_accuracy(
            actual_tools=actual_tools,
            expected_tools=expected_tools,
        )

        return score, {
            "actual_tools": actual_tools,
            "expected_tools": expected_tools,
            "answer": result.answer,
        }

    async def _eval_workflow(
        self,
        case: GoldenCase,
    ) -> tuple[float, dict]:
        service = self.get_workflow_service()

        result = await service.run(
            WorkflowRequest(
                query=case.input,
            )
        )

        report = result.report.model_dump()

        report_text = json.dumps(
            report,
            ensure_ascii=False,
        )

        expected_terms = case.expected[
            "contains"
        ]

        score = contains_all_score(
            actual=report_text,
            expected_terms=expected_terms,
        )

        return score, {
            "expected_terms": expected_terms,
            "report": report,
        }

    async def _eval_rag(
        self,
        case: GoldenCase,
    ) -> tuple[float, dict]:
        service = self.get_rag_service()

        top_k = case.expected.get(
            "top_k",
            3,
        )

        result = await service.rag(
            RAGRequest(
                query=case.input,
                top_k=top_k,
            )
        )

        data = result.model_dump()

        documents = (
            data.get("retrieved_documents")
            or data.get("documents")
            or []
        )

        documents_text = json.dumps(
            documents,
            ensure_ascii=False,
        )

        expected_source = case.expected[
            "source_contains"
        ]

        score = (
            1.0
            if expected_source.lower()
            in documents_text.lower()
            else 0.0
        )

        return score, {
            "expected_source": expected_source,
            "documents": documents,
        }

    async def _run_case(
        self,
        case: GoldenCase,
    ) -> EvalCaseResult:
        start = perf_counter()

        try:
            if case.type == "sql":
                score, details = await self._eval_sql(case)

            elif case.type == "agent":
                score, details = await self._eval_agent(case)

            elif case.type == "workflow":
                score, details = await self._eval_workflow(case)

            elif case.type == "rag":
                score, details = await self._eval_rag(case)

            else:
                raise ValueError(
                    f"Unsupported eval type: {case.type}"
                )

            error = None

        except Exception as exc:
            score = 0.0
            details = {}
            error = str(exc)

        latency_ms = (
            perf_counter() - start
        ) * 1000

        return EvalCaseResult(
            case_id=case.id,
            type=case.type,
            passed=score == 1.0,
            score=score,
            latency_ms=round(
                latency_ms,
                2,
            ),
            details=details,
            error=error,
        )

    async def run(
        self,
        request: EvalRunRequest,
    ) -> EvalReport:
        cases = self._load_cases()

        if request.types:
            cases = [
                case
                for case in cases
                if case.type in request.types
            ]

        results = []

        for case in cases:
            result = await self._run_case(case)
            results.append(result)

        total = len(results)

        passed = sum(
            result.passed
            for result in results
        )

        average_score = (
            sum(
                result.score
                for result in results
            ) / total
            if total
            else 0.0
        )

        return EvalReport(
            total=total,
            passed=passed,
            failed=total - passed,
            average_score=round(
                average_score,
                4,
            ),
            results=results,
        )