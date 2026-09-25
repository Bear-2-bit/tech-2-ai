from fastapi import APIRouter, Depends

from app.dependencies import get_workflow_service
from app.schemas.workflow import WorkflowRequest, WorkflowResponse
from app.services.workflow_service import WorkflowService


router = APIRouter(
    prefix="/api/workflow",
    tags=["workflow"],
)


@router.post(
    "",
    response_model=WorkflowResponse,
)
async def run_workflow(
    request: WorkflowRequest,
    workflow_service: WorkflowService = Depends(
        get_workflow_service
    ),
) -> WorkflowResponse:
    return await workflow_service.run(request)