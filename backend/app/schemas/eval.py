from typing import Any, Literal

from pydantic import BaseModel, Field


EvalType = Literal[
    "rag",
    "sql",
    "agent",
    "workflow",
]


class GoldenCase(BaseModel):
    id: str
    type: EvalType
    input: str
    expected: dict[str, Any]


class EvalRunRequest(BaseModel):
    types: list[EvalType] | None = None


class EvalCaseResult(BaseModel):
    case_id: str
    type: EvalType
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    latency_ms: float
    details: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class EvalReport(BaseModel):
    total: int
    passed: int
    failed: int
    average_score: float
    results: list[EvalCaseResult]