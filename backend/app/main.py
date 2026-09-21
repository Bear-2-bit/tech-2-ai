import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.core.config import settings
from app.core.exceptions import LLMTimeoutError, LLMUpstreamError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


app = FastAPI(
    title="tech-2-ai",
    version="0.1.0",
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Router
app.include_router(chat_router)


# LLM 超时
@app.exception_handler(LLMTimeoutError)
async def llm_timeout_handler(
    request: Request,
    exc: LLMTimeoutError,
):
    return JSONResponse(
        status_code=504,
        content={
            "detail": "LLM service timeout",
        },
    )


# LLM 上游服务异常
@app.exception_handler(LLMUpstreamError)
async def llm_upstream_handler(
    request: Request,
    exc: LLMUpstreamError,
):
    return JSONResponse(
        status_code=502,
        content={
            "detail": "LLM service unavailable",
        },
    )


# Health Check
@app.get("/health")
async def health():
    return {
        "status": "ok",
    }