from typing import Any

from pydantic import BaseModel, Field


class RAGRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)


class RAGDocument(BaseModel):
    content: str
    metadata: dict[str, Any]
    rerank_score: float


class RAGCitation(BaseModel):
    index: int
    source: str
    page: str | None = None
    chunk_index: int | None = None


class RAGResponse(BaseModel):
    query: str
    rewritten_query: str
    answer: str
    retrieved_documents: list[RAGDocument]
    citations: list[RAGCitation]


class KnowledgeIngestionResponse(BaseModel):
    filename: str
    document_count: int
    chunk_count: int