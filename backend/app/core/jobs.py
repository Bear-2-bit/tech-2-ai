import asyncio
from collections.abc import Awaitable, Callable
from time import perf_counter

from app.core.config import get_settings
from app.core.errors import AppError, public_error
from app.core.store import get_store, now
from app.core.telemetry import current_run, finish_run, start_run, tracing_context


class Jobs:
    """Single-process jobs. Persist results; interrupted jobs are recovered by resubmission."""

    def __init__(self):
        self.tasks: dict[str, asyncio.Task] = {}

    def recover(self):
        get_store().execute(
            "UPDATE runs SET status='interrupted',finished_at=?,error='服务重启，请重新提交任务' "
            "WHERE status IN ('running','queued')",
            (now(),),
        )

    def submit(
        self,
        module: str,
        name: str,
        work: Callable[[], Awaitable],
        metadata: dict | None = None,
        timeout: float | None = None,
    ) -> dict:
        if len(self.tasks) >= get_settings().max_jobs:
            raise AppError("后台任务已满，请等待已有任务完成。", "busy", 429)
        run_id = start_run(module, name, metadata)
        task = asyncio.create_task(self._execute(run_id, work, timeout))
        self.tasks[run_id] = task

        def completed(task):
            self.tasks.pop(run_id, None)
            if task.cancelled():
                finish_run(run_id, "cancelled", 0, error="操作已取消")

        task.add_done_callback(completed)
        return {"run_id": run_id, "status": "running"}

    async def _execute(self, run_id: str, work: Callable[[], Awaitable], timeout: float | None):
        token = current_run.set(run_id)
        start = perf_counter()
        status, result, error = "success", None, None
        try:
            with tracing_context():
                async with asyncio.timeout(timeout or get_settings().operation_timeout_seconds):
                    result = await work()
            if isinstance(result, dict) and result.get("status") in {"incomplete", "needs_clarification"}:
                status = result["status"]
        except asyncio.CancelledError:
            status, error = "cancelled", "操作已取消"
        except Exception as exc:
            status = "timeout" if isinstance(exc, TimeoutError) else "error"
            error = f"{type(exc).__name__}: {public_error(exc)}"
        finally:
            current_run.reset(token)
            finish_run(run_id, status, (perf_counter() - start) * 1000, result, error)

    async def shutdown(self):
        for task in list(self.tasks.values()):
            task.cancel()
        if self.tasks:
            await asyncio.gather(*list(self.tasks.values()), return_exceptions=True)


jobs = Jobs()
