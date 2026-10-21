import asyncio
import importlib
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.core.errors import public_error
from app.core.telemetry import span, tracing_context
from app.modules.llm.schemas import ChatRequest, ExtractionRequest, Implementation

router = APIRouter(prefix="/api/llm", tags=["LLM"])


def implementation(name: Implementation):
    return importlib.import_module(f"app.modules.llm.{name}")


@router.post("/{engine}/chat")
async def chat(engine: Implementation, request: ChatRequest):
    with span("llm", f"{engine}.chat") as run_id, tracing_context():
        async with asyncio.timeout(get_settings().operation_timeout_seconds):
            result = await implementation(engine).chat(request)
    return {**result, "run_id": run_id}


@router.post("/{engine}/extract")
async def extract(engine: Implementation, request: ExtractionRequest):
    with span("llm", f"{engine}.extract") as run_id, tracing_context():
        async with asyncio.timeout(get_settings().operation_timeout_seconds):
            result = await implementation(engine).extract(request.text)
    return {**result, "run_id": run_id}


@router.post("/{engine}/stream")
async def stream(engine: Implementation, request: ChatRequest):
    async def events():
        try:
            with span("llm", f"{engine}.stream") as run_id, tracing_context():
                async with asyncio.timeout(get_settings().operation_timeout_seconds):
                    async for event in implementation(engine).stream(request):
                        yield "data: " + json.dumps({**event, "run_id": run_id}, ensure_ascii=False) + "\n\n"
        except Exception as exc:
            yield "data: " + json.dumps({"type": "error", "detail": public_error(exc)}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(
        events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
