from fastapi import APIRouter

from app.core.jobs import jobs
from app.core.store import get_store
from app.modules.workflow.schemas import ReportRequest

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


@router.post("/reports", status_code=202)
async def generate(request: ReportRequest):
    from app.modules.workflow.graph import run_report

    return jobs.submit("workflow", "monthly.report", lambda: run_report(request), request.model_dump())


@router.get("/reports")
def reports():
    return get_store().rows(
        "SELECT id,status,started_at,latency_ms,error,metadata FROM runs "
        "WHERE module='workflow' AND parent_id IS NULL ORDER BY started_at DESC LIMIT 30"
    )
