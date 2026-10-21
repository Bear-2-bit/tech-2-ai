from datetime import date

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    rerank: bool = False
    rewrite: bool = False
    category: str | None = None
    product_code: str | None = None
    as_of: date | None = None


class GroundedAnswer(BaseModel):
    answer: str
    citation_ids: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
