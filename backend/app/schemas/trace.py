from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TraceSummary(BaseModel):
    trace_id: str
    langsmith_trace_id: str | None = None

    name: str
    status: Literal["success", "error"]

    started_at: datetime
    latency_ms: float

    input_tokens: int
    output_tokens: int
    total_tokens: int

    input_preview: str
    error: str | None = None