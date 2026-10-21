import asyncio
import logging
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from app.core.errors import AppError, public_error
from app.core.store import encode, get_store, now

current_run: ContextVar[str | None] = ContextVar("current_run", default=None)
request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_outcome: ContextVar[dict | None] = ContextVar("outcome", default=None)
logger = logging.getLogger(__name__)


def set_outcome(status: str):
    state = _outcome.get()
    if state is not None:
        state["status"] = status


def start_run(module: str, name: str, metadata: dict | None = None, parent_id: str | None = None) -> str:
    run_id = str(uuid4())
    get_store().execute(
        "INSERT INTO runs(id,parent_id,module,name,status,started_at,metadata) VALUES(?,?,?,?,?,?,?)",
        (
            run_id,
            parent_id,
            module,
            name,
            "running",
            now(),
            encode({"request_id": request_id.get(), **(metadata or {})}),
        ),
    )
    get_store().event(run_id, f"{name} 开始")
    return run_id


def finish_run(run_id: str, status: str, latency: float, result=None, error: str | None = None):
    get_store().execute(
        "UPDATE runs SET status=?,finished_at=?,latency_ms=?,result=?,error=? WHERE id=?",
        (status, now(), round(latency, 2), encode(result) if result is not None else None, error, run_id),
    )
    get_store().event(
        run_id, f"运行结束：{status}" + (f"；{error}" if error else ""), "ERROR" if error else "INFO"
    )


@contextmanager
def span(module: str, name: str, metadata: dict | None = None, run_id: str | None = None):
    identifier = run_id or start_run(module, name, metadata, current_run.get())
    token = current_run.set(identifier)
    outcome = {}
    outcome_token = _outcome.set(outcome)
    start = perf_counter()
    status, error = "success", None
    try:
        yield identifier
    except (asyncio.CancelledError, GeneratorExit):
        status, error = "cancelled", "操作已取消"
        raise
    except Exception as exc:
        status = "timeout" if isinstance(exc, TimeoutError) else "error"
        error = f"{type(exc).__name__}: {public_error(exc)}"
        logger.warning("operation_failed run_id=%s type=%s", identifier, type(exc).__name__)
        raise
    finally:
        current_run.reset(token)
        _outcome.reset(outcome_token)
        if status == "success":
            status = outcome.get("status", status)
        try:
            finish_run(identifier, status, (perf_counter() - start) * 1000, error=error)
        except Exception:
            logger.error("telemetry_write_failed run_id=%s", identifier)


def tracing_context():
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.langsmith_tracing:
        return nullcontext()
    if not settings.langsmith_api_key:
        raise AppError("启用 LangSmith 时需要配置 LANGSMITH_API_KEY。", "configuration", 503)
    from langsmith import Client
    from langsmith import tracing_context as context

    return context(
        enabled=True,
        project_name=settings.langsmith_project,
        client=Client(api_key=settings.langsmith_api_key.get_secret_value()),
    )
