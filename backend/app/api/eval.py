from fastapi import APIRouter, Depends

from app.dependencies import get_eval_service
from app.schemas.eval import (
    EvalReport,
    EvalRunRequest,
)
from app.services.eval_service import EvaluationService


router = APIRouter(
    prefix="/api/eval",
    tags=["evaluation"],
)


@router.post(
    "",
    response_model=EvalReport,
)
async def run_evaluation(
    request: EvalRunRequest,
    service: EvaluationService = Depends(
        get_eval_service
    ),
) -> EvalReport:
    return await service.run(request)