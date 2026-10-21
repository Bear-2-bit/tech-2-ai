from typing import Literal

from pydantic import BaseModel, Field

EvalType = Literal["llm", "sql", "rag", "agent", "workflow"]


class EvalRequest(BaseModel):
    types: list[EvalType] = Field(default_factory=lambda: ["sql"])
    limit: int = Field(default=5, ge=1, le=60)
    case_ids: list[str] | None = Field(default=None, max_length=60)


class GoldenCase(BaseModel):
    id: str
    type: EvalType
    input: str | dict
    expected: dict
