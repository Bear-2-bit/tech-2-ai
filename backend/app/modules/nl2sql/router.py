import asyncio

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.telemetry import tracing_context
from app.modules.nl2sql.database import schema
from app.modules.nl2sql.schemas import SQLRequest

router = APIRouter(prefix="/api/nl2sql", tags=["NL2SQL"])


@router.get("/schema")
def get_schema():
    return schema()


@router.post("/query")
async def query(request: SQLRequest):
    from app.modules.nl2sql.service import query as run_query

    with tracing_context():
        async with asyncio.timeout(get_settings().operation_timeout_seconds):
            return await run_query(request)
