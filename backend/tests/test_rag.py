import asyncio
import hashlib

import pytest
from langchain_core.embeddings import Embeddings
from qdrant_client import QdrantClient

from app.core.errors import AppError
from app.modules.rag import ingestion
from app.modules.rag.retrieval import eligible_versions, search
from app.modules.rag.schemas import SearchRequest


class TestEmbeddings(Embeddings):
    """Only for deterministic infrastructure tests; never used by the application."""

    __test__ = False

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        digest = hashlib.sha256(text.encode()).digest()
        return [(value + 1) / 256 for value in digest[:8]]


@pytest.fixture
def index(monkeypatch):
    client = QdrantClient(":memory:")
    monkeypatch.setattr(ingestion, "get_qdrant", lambda: client)
    monkeypatch.setattr(ingestion, "get_embeddings", TestEmbeddings)
    yield client
    client.close()


async def test_first_ingestion_duplicate_update_and_delete(index, environment):
    path = environment / "policy.md"
    path.write_text("# 保修政策\n机器人A保修12个月。", encoding="utf-8")
    first = await ingestion.ingest(path, path.name)
    repeated = await ingestion.ingest(path, path.name)
    assert repeated["duplicate"] and repeated["version_id"] == first["version_id"]
    assert len(ingestion.list_documents()) == 1
    result = await search(SearchRequest(query="保修"))
    assert result["documents"][0]["metadata"]["version_id"] == first["version_id"]
    path.write_text("# 保修政策\n机器人A保修18个月，新版。", encoding="utf-8")
    updated = await ingestion.ingest(path, path.name)
    assert updated["version"] == 2
    result = await search(SearchRequest(query="保修"))
    assert {doc["metadata"]["version_id"] for doc in result["documents"]} == {updated["version_id"]}
    assert {row["status"] for row in ingestion.list_documents()} == {"ready", "superseded"}
    ingestion.delete_document(first["document_id"])
    assert not (await search(SearchRequest(query="保修")))["documents"]
    assert index.count(ingestion.get_settings().qdrant_collection_name).count == 0


async def test_failed_replacement_keeps_previous_version(index, environment):
    path = environment / "policy.md"
    path.write_text("有效原文", encoding="utf-8")
    first = await ingestion.ingest(path, path.name)
    path.write_text("", encoding="utf-8")
    with pytest.raises(AppError, match="没有可提取文字"):
        await ingestion.ingest(path, path.name)
    assert eligible_versions(SearchRequest(query="原文")) == [first["version_id"]]


async def test_effective_date_selects_matching_version(index, environment):
    path = environment / "policy.md"
    path.write_text("旧政策", encoding="utf-8")
    old = await ingestion.ingest(path, path.name, {"effective_from": "2025-04-01", "effective_to": "2026-06-30"})
    path.write_text("新政策", encoding="utf-8")
    new = await ingestion.ingest(path, path.name, {"effective_from": "2026-07-01"})
    assert eligible_versions(SearchRequest(query="政策", as_of="2026-06-01")) == [old["version_id"]]
    assert eligible_versions(SearchRequest(query="政策", as_of="2026-09-30")) == [new["version_id"]]


async def test_delete_failure_hides_document_and_can_retry(index, environment, monkeypatch):
    path = environment / "policy.md"
    path.write_text("待删除文档", encoding="utf-8")
    first = await ingestion.ingest(path, path.name)
    original = ingestion.delete_vectors

    def fail(*args):
        raise RuntimeError("offline")

    monkeypatch.setattr(ingestion, "delete_vectors", fail)
    with pytest.raises(RuntimeError):
        ingestion.delete_document(first["document_id"])
    assert not eligible_versions(SearchRequest(query="文档"))
    monkeypatch.setattr(ingestion, "delete_vectors", original)
    assert ingestion.delete_document(first["document_id"])["status"] == "deleted"


async def test_cancelled_ingestion_does_not_publish(index, environment, monkeypatch):
    import threading

    entered, release = threading.Event(), threading.Event()
    original = ingestion.load_chunks

    def slow(*args):
        entered.set()
        release.wait(5)
        return original(*args)

    monkeypatch.setattr(ingestion, "load_chunks", slow)
    path = environment / "policy.md"
    path.write_text("取消任务", encoding="utf-8")
    task = asyncio.create_task(ingestion.ingest(path, path.name))
    await asyncio.to_thread(entered.wait, 5)
    task.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not eligible_versions(SearchRequest(query="取消"))


async def test_invalid_citation_is_marked_incomplete(monkeypatch):
    from langchain_core.runnables import RunnableLambda

    from app.modules.rag import service
    from app.modules.rag.schemas import GroundedAnswer

    async def retrieved(request):
        return {
            "query": request.query,
            "rewritten_query": request.query,
            "documents": [{"id": "valid-id", "content": "证据", "metadata": {}}],
        }

    class Model:
        def with_structured_output(self, *args, **kwargs):
            return RunnableLambda(lambda _: GroundedAnswer(answer="答案[invalid-id]", citation_ids=["valid-id"]))

    monkeypatch.setattr(service, "search", retrieved)
    monkeypatch.setattr(service, "get_model", Model)
    result = await service.ask(SearchRequest(query="问题"))
    assert result["status"] == "incomplete"
    assert result["invalid_citation_ids"] == ["invalid-id"]
