import json

from fastapi import APIRouter, Query

from app.core.errors import AppError
from app.core.jobs import jobs
from app.core.store import get_store
from app.modules.engineering.schemas import EvalRequest

router = APIRouter(prefix="/api/engineering", tags=["Engineering"])


@router.get("/runs")
def runs(module: str | None = None, limit: int = Query(50, ge=1, le=200)):
    where, parameters = (" AND module=?", [module]) if module else ("", [])
    return get_store().rows(
        "SELECT id,parent_id,module,name,status,started_at,latency_ms,input_tokens,output_tokens,error,metadata "
        "FROM runs WHERE parent_id IS NULL" + where + " ORDER BY started_at DESC LIMIT ?",
        [*parameters, limit],
    )


@router.get("/runs/{run_id}")
def run(run_id: str):
    result = get_store().run(run_id)
    if not result:
        raise AppError("运行记录不存在。", "not_found", 404)
    result["spans"] = get_store().rows(
        "WITH RECURSIVE tree AS (SELECT * FROM runs WHERE parent_id=? UNION ALL "
        "SELECT r.* FROM runs r JOIN tree t ON r.parent_id=t.id) "
        "SELECT id,parent_id,module,name,status,started_at,latency_ms,input_tokens,output_tokens,error,metadata FROM tree ORDER BY started_at",
        (run_id,),
    )
    result["events"] = get_store().rows(
        "SELECT * FROM events WHERE run_id=? OR run_id IN (SELECT id FROM runs WHERE parent_id=?) ORDER BY id",
        (run_id, run_id),
    )
    result["eval_results"] = [
        json.loads(row["payload"])
        for row in get_store().rows("SELECT payload FROM eval_results WHERE run_id=?", (run_id,))
    ]
    return result


@router.post("/runs/{run_id}/cancel", status_code=202)
async def cancel(run_id: str):
    task = jobs.tasks.get(run_id)
    if not task:
        raise AppError("运行已结束或不属于当前进程。", "not_running", 409)
    task.cancel()
    return {"run_id": run_id, "status": "cancelling"}


@router.get("/logs")
def logs(limit: int = Query(100, ge=1, le=300), run_id: str | None = None):
    where, parameters = (" WHERE run_id=?", [run_id]) if run_id else ("", [])
    return get_store().rows(
        "SELECT * FROM events" + where + " ORDER BY id DESC LIMIT ?", [*parameters, limit]
    )


@router.get("/evaluations/cases")
def cases():
    from app.modules.engineering.evaluation import load_cases

    return [{"id": case.id, "type": case.type, "input": case.input} for case in load_cases()]


@router.post("/evaluations", status_code=202)
async def evaluate(request: EvalRequest):
    from app.modules.engineering.evaluation import evaluate as run_evaluation

    return jobs.submit(
        "engineering", "evaluation.run", lambda: run_evaluation(request), request.model_dump(), timeout=900
    )
