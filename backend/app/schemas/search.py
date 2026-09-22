from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)


class SearchDocument(BaseModel):
    content: str
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    documents: list[SearchDocument]