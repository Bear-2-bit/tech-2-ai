from langchain_deepseek import (
    ChatDeepSeek,
)

from app.ai.providers.deepseek import (
    DeepSeekProvider,
)
from app.core.config import settings

from app.services.chat_service import (
    ChatService,
)
from app.services.extraction_service import (
    ExtractionService,
)
from app.services.langchain_extraction_service import (
    LangChainExtractionService,
)
from app.ai.vector_store import get_vector_store
from app.services.search_service import SearchService

from app.services.rag_service import RAGService

from app.services.knowledge_ingestion_service import KnowledgeIngestionService

# =========================
# Phase 1-3 手写 LLM Provider
# =========================

llm_provider = DeepSeekProvider(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    model=settings.deepseek_model,
    timeout=settings.llm_timeout_seconds,
    max_retries=settings.llm_max_retries,
)


# =========================
# Chat Service
# =========================

chat_service = ChatService(
    llm_provider=llm_provider,
)


def get_chat_service() -> ChatService:
    return chat_service


# =========================
# Phase 3 手写 Extraction
# =========================

extraction_service = ExtractionService(
    llm_provider=llm_provider,
)


def get_extraction_service() -> ExtractionService:
    return extraction_service


# =========================
# Phase 4 LangChain Model
# =========================

langchain_model = ChatDeepSeek(
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

langchain_extraction_service = (
    LangChainExtractionService(
        model=langchain_model,
    )
)


def get_langchain_extraction_service(
) -> LangChainExtractionService:

    return langchain_extraction_service



vector_store = get_vector_store()
search_service = SearchService(vector_store=vector_store)


def get_search_service() -> SearchService:
    return search_service


rag_service = RAGService(
    vector_store=vector_store,
    model=langchain_model,
)


def get_rag_service() -> RAGService:
    return rag_service


knowledge_ingestion_service = KnowledgeIngestionService(vector_store=vector_store)

def get_knowledge_ingestion_service() -> KnowledgeIngestionService:
    return knowledge_ingestion_service