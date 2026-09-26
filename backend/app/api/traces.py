from fastapi import APIRouter, Depends

from app.ai.tracing.store import TraceStore
from app.dependencies import get_trace_store
from app.schemas.trace import TraceSummary


router = APIRouter(
    prefix="/api/traces",
    tags=["traces"],
)


@router.get(
    "",
    response_model=list[TraceSummary],
)
async def list_traces(
    trace_store: TraceStore = Depends(
        get_trace_store
    ),
) -> list[TraceSummary]:
    return trace_store.list()