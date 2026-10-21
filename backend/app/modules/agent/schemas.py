from typing import Literal

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


class Finding(BaseModel):
    statement: str
    evidence_ids: list[str] = Field(default_factory=list)


class Investigation(BaseModel):
    status: Literal["success", "incomplete", "needs_clarification"]
    answer: str
    findings: list[Finding] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
