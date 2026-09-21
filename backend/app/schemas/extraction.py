from typing import Literal

from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    text: str = Field(min_length=1)


class ExtractedTask(BaseModel):
    title: str

    priority: Literal[
        "low",
        "medium",
        "high",
    ]

    deadline: str | None = None

    technologies: list[str] = Field(
        default_factory=list
    )


class ExtractionTokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ExtractionResponse(BaseModel):
    result: ExtractedTask

    model: str

    finish_reason: str | None

    usage: ExtractionTokenUsage

    latency_ms: float

    attempts: int