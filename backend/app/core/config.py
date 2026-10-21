from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="forbid")

    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    frontend_origin: str = "http://localhost:5173"
    llm_timeout_seconds: float = Field(default=45, gt=0)
    llm_max_retries: int = Field(default=1, ge=0, le=3)
    operation_timeout_seconds: float = Field(default=180, gt=0)
    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    reranker_model_name: str = "BAAI/bge-reranker-base"
    model_local_files_only: bool = True
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection_name: str = "tech2ai_documents_v2"
    qdrant_mode: Literal["local", "server"] = "local"
    qdrant_local_path: Path = BACKEND_DIR / "data" / "qdrant"
    database_path: Path = BACKEND_DIR / "data" / "business.db"
    app_database_path: Path = BACKEND_DIR / "data" / "app.db"
    knowledge_dir: Path = BACKEND_DIR / "data" / "knowledge"
    upload_dir: Path = BACKEND_DIR / "data" / "uploads"
    eval_dataset_path: Path = BACKEND_DIR / "data" / "eval" / "golden_cases.json"
    max_upload_mb: int = Field(default=10, ge=1, le=50)
    max_jobs: int = Field(default=4, ge=1, le=20)
    sql_timeout_seconds: float = Field(default=3, gt=0, le=30)
    log_level: str = "INFO"
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "tech-2-ai"
    langsmith_tracing: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
