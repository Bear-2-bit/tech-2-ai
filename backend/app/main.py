from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(
    BASE_DIR / ".env",
    override=False,
)

import logging

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.responses import (
    JSONResponse,
)

from app.api.chat import (
    router as chat_router,
)
from app.api.extraction import (
    router as extraction_router,
)
from app.api.langchain_extraction import (
    router as langchain_extraction_router,
)
from app.api.search import router as search_router

from app.api.rag import router as rag_router

from app.api.sql import router as sql_router

from app.api.agent import router as agent_router

from app.api.workflow import router as workflow_router

from app.api.eval import router as eval_router

from app.api.traces import router as traces_router

from app.core.config import settings
from app.core.exceptions import (
    LLMTimeoutError,
    LLMUpstreamError,
)


logging.basicConfig(
    level=logging.INFO,

    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    ),
)


app = FastAPI(
    title="tech-2-ai",
    version="0.1.0",
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        settings.frontend_origin,
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================
# Routers
# =========================

app.include_router(
    chat_router
)

app.include_router(
    extraction_router
)

app.include_router(
    langchain_extraction_router
)
app.include_router(search_router)

app.include_router(rag_router)

app.include_router(sql_router)

app.include_router(agent_router)

app.include_router(workflow_router)

app.include_router(eval_router)

app.include_router(traces_router)
# =========================
# LLM Timeout
# =========================

@app.exception_handler(
    LLMTimeoutError
)
async def llm_timeout_handler(
    request: Request,
    exc: LLMTimeoutError,
):
    return JSONResponse(
        status_code=504,

        content={
            "detail":
                "LLM service timeout",
        },
    )


# =========================
# LLM Upstream Error
# =========================

@app.exception_handler(
    LLMUpstreamError
)
async def llm_upstream_handler(
    request: Request,
    exc: LLMUpstreamError,
):
    return JSONResponse(
        status_code=502,

        content={
            "detail":
                "LLM service unavailable",
        },
    )


# =========================
# Health Check
# =========================

@app.get("/health")
async def health():
    return {
        "status": "ok",
    }