from app.ai.workflows.business_analysis import BusinessAnalysisWorkflow
from app.schemas.workflow import (
    BusinessAnalysisReport,
    WorkflowRequest,
    WorkflowResponse,
)


class WorkflowService:
    def __init__(
        self,
        workflow: BusinessAnalysisWorkflow,
    ):
        self.workflow = workflow

    async def run(
        self,
        request: WorkflowRequest,
    ) -> WorkflowResponse:
        result = await self.workflow.run(
            request.query
        )

        return WorkflowResponse(
            query=request.query,
            sql_question=result["sql_question"],
            rag_question=result["rag_question"],
            sql_result=result["sql_result"],
            rag_result=result["rag_result"],
            report=BusinessAnalysisReport.model_validate(
                result["report"]
            ),
        )