from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    # =========================
    # DeepSeek
    # =========================

    deepseek_api_key: str

    deepseek_base_url: str = (
        "https://api.deepseek.com"
    )

    deepseek_model: str = (
        "deepseek-flash"
    )


    # =========================
    # Frontend
    # =========================

    frontend_origin: str = (
        "http://localhost:5173"
    )


    # =========================
    # LLM Engineering
    # =========================

    llm_timeout_seconds: float = 30.0

    llm_max_retries: int = 2


    # =========================
    # Embedding
    # =========================

    embedding_model_name: str = (
        "BAAI/bge-small-zh-v1.5"
    )

    reranker_model_name: str = (
        "BAAI/bge-reranker-base"
    )

    # =========================
    # Qdrant
    # =========================

    qdrant_url: str = (
        "http://127.0.0.1:6333"
    )

    qdrant_collection_name: str = (
        "tech2ai_documents"
    )


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()