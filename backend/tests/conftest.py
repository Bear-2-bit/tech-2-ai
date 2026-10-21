import pytest

from app.core.config import get_settings
from app.core.store import get_store
from scripts.seed import seed_database


@pytest.fixture(autouse=True)
def environment(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "business.db"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("KNOWLEDGE_DIR", str(tmp_path / "knowledge"))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    get_settings.cache_clear()
    get_store.cache_clear()
    seed_database(tmp_path / "business.db", fixture=True)
    yield tmp_path
    get_store.cache_clear()
    get_settings.cache_clear()
