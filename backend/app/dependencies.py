from functools import lru_cache
from pathlib import Path

from langchain_deepseek import ChatDeepSeek

from app.ai.providers.deepseek import DeepSeekProvider
from app.ai.retrieval.query_rewriter import QueryRewriter
from app.ai.retrieval.reranker import Reranker
from app.ai.vector_store import get_vector_store as create_vector_store
from app.core.config import settings
from app.services.chat_service import ChatService
from app.services.extraction_service import ExtractionService
from app.services.knowledge_ingestion_service import KnowledgeIngestionService
from app.services.langchain_extraction_service import LangChainExtractionService
from app.services.rag_service import RAGService
from app.services.search_service import SearchService
from app.services.sql_service import SQLService


# =========================
# Phase 1-3 手写 LLM Provider
# =========================

@lru_cache
def get_llm_provider() -> DeepSeekProvider:
    return DeepSeekProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


# =========================
# Chat Service
# =========================

@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(
        llm_provider=get_llm_provider(),
    )


# =========================
# Phase 3 手写 Extraction
# =========================

@lru_cache
def get_extraction_service() -> ExtractionService:
    return ExtractionService(
        llm_provider=get_llm_provider(),
    )


# =========================
# Phase 4 LangChain Model
# =========================

@lru_cache
def get_langchain_model() -> ChatDeepSeek:
    return ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        api_base=settings.deepseek_base_url,
        temperature=0.0,
        max_tokens=500,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


# =========================
# Phase 4 LangChain Extraction
# =========================

@lru_cache
def get_langchain_extraction_service() -> LangChainExtractionService:
    return LangChainExtractionService(
        model=get_langchain_model(),
    )


# =========================
# Phase 5 Vector Store
# =========================

@lru_cache
def get_cached_vector_store():
    return create_vector_store()


# =========================
# Phase 5 Search Service
# =========================

@lru_cache
def get_search_service() -> SearchService:
    return SearchService(
        vector_store=get_cached_vector_store(),
    )


# =========================
# Phase 6 Query Rewriter
# =========================

@lru_cache
def get_query_rewriter() -> QueryRewriter:
    return QueryRewriter(
        model=get_langchain_model(),
    )


# =========================
# Phase 6 Reranker
# =========================

@lru_cache
def get_reranker() -> Reranker:
    return Reranker(
        model_name=settings.reranker_model_name,
    )


# =========================
# Phase 6 RAG Service
# =========================

@lru_cache
def get_rag_service() -> RAGService:
    return RAGService(
        vector_store=get_cached_vector_store(),
        model=get_langchain_model(),
        query_rewriter=get_query_rewriter(),
        reranker=get_reranker(),
    )


# =========================
# Phase 6 Knowledge Ingestion
# =========================

@lru_cache
def get_knowledge_ingestion_service() -> KnowledgeIngestionService:
    return KnowledgeIngestionService(
        vector_store=get_cached_vector_store(),
    )


# =========================
# Phase 8 SQL Service
# =========================

@lru_cache
def get_sql_service() -> SQLService:
    return SQLService(
        database_path=Path("data/business.db"),
        model=get_langchain_model(),
    )