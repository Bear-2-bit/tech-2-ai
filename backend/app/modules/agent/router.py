from fastapi import APIRouter

from app.core.jobs import jobs
from app.core.store import get_store
from app.modules.agent.schemas import AgentRequest
from app.modules.agent.service import create_session, get_session

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.get("/sessions")
def sessions():
    return get_store().rows("SELECT id,title,updated_at FROM sessions ORDER BY updated_at DESC LIMIT 50")


@router.post("/sessions", status_code=201)
def new_session():
    return create_session()


@router.get("/sessions/{session_id}")
def session(session_id: str):
    row = get_session(session_id)
    return {"id": row["id"], "title": row["title"], "turns": row["messages"]["turns"]}


@router.post("/runs", status_code=202)
async def run(request: AgentRequest):
    from app.modules.agent.service import investigate

    if request.session_id:
        get_session(request.session_id)
    else:
        request = request.model_copy(update={"session_id": create_session(request.query)["id"]})
    return {
        **jobs.submit("agent", "agent.run", lambda: investigate(request), {"session_id": request.session_id}),
        "session_id": request.session_id,
    }
