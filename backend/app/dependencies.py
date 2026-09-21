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


# =========================
# LLM Provider
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
# Extraction Service
# =========================

extraction_service = ExtractionService(
    llm_provider=llm_provider,
)


def get_extraction_service() -> ExtractionService:
    return extraction_service