import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import AppError, public_error
from app.core.jobs import jobs
from app.core.logging import configure_logging
from app.core.store import get_store
from app.core.telemetry import request_id
from app.modules.agent.router import router as agent_router
from app.modules.engineering.router import router as engineering_router
from app.modules.llm.router import router as llm_router
from app.modules.nl2sql.router import router as nl2sql_router
from app.modules.rag.router import router as rag_router
from app.modules.workflow.router import router as workflow_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    jobs.recover()
    get_store().execute(
        "UPDATE documents SET status='error',error='服务中断，请重新上传' WHERE status='processing'"
    )
    yield
    await jobs.shutdown()
    from app.resources import close_resources

    await close_resources()
    from app.modules.llm.native import get_client

    if get_client.cache_info().currsize:
        await get_client().close()
        get_client.cache_clear()


app = FastAPI(title="tech-2-ai · 机器人企业运营工作台", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = str(uuid4())
    token = request_id.set(request.state.request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response
    finally:
        request_id.reset(token)


@app.exception_handler(AppError)
async def app_error(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status,
        content={
            "detail": str(exc),
            "code": exc.code,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "输入格式错误，请检查必填项与取值范围。",
            "code": "validation",
            "fields": [".".join(map(str, error["loc"])) for error in exc.errors()],
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    identifier = getattr(request.state, "request_id", None)
    logging.getLogger("app").error("request_failed request_id=%s type=%s", identifier, type(exc).__name__)
    is_timeout = isinstance(exc, TimeoutError) or "timeout" in type(exc).__name__.lower()
    status = 504 if is_timeout else 502 if type(exc).__module__.startswith(("openai", "httpx")) else 500
    return JSONResponse(
        status_code=status,
        content={
            "detail": public_error(exc),
            "code": "timeout" if is_timeout else "service_error",
            "request_id": identifier,
        },
    )


for router in (llm_router, rag_router, nl2sql_router, agent_router, workflow_router, engineering_router):
    app.include_router(router)


@app.get("/health", tags=["System"])
def health():
    from app.resources import loaded_resources

    return {
        "status": "ok",
        "version": "2.0.0",
        "mode": "single-process",
        "loaded_resources": loaded_resources(),
    }
