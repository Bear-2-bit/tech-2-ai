from typing import Any

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    id: str
    input: str
    expected: Any


class EvalResult(BaseModel):
    case_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    actual: Any
    expected: Any