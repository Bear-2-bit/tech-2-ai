import asyncio
import hashlib
import json
import shutil
import threading
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.core.config import get_settings
from app.core.errors import AppError, public_error
from app.core.store import encode, get_store, now
from app.core.telemetry import span
from app.resources import get_embeddings, get_qdrant

_index_lock = threading.Lock()


def vector_store(ensure: bool = False):
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client.models import Distance, VectorParams

    settings = get_settings()
    client = get_qdrant()
    try:
        exists = client.collection_exists(settings.qdrant_collection_name)
        if not exists and not ensure:
            raise AppError("知识索引尚未创建，请先入库文档。", "knowledge_empty", 409)
        embeddings = get_embeddings()
        if not exists:
            size = len(embeddings.embed_query("维度检查"))
            client.create_collection(
                settings.qdrant_collection_name,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )
        return QdrantVectorStore(
            client=client, collection_name=settings.qdrant_collection_name, embedding=embeddings
        )
    except AppError:
        raise
    except Exception as exc:
        raise AppError(
            "向量索引连接或模型维度校验失败，请检查 Qdrant 与模型配置。", "vector_unavailable", 503
        ) from exc


def load_chunks(path: Path, filename: str, metadata: dict) -> list:
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        if len(reader.pages) > 200:
            raise AppError("PDF 最多支持 200 页，请拆分后上传。", "document_limit")
        documents = [
            Document(page_content=page.extract_text() or "", metadata={"page": i + 1})
            for i, page in enumerate(reader.pages)
        ]
    else:
        try:
            documents = [Document(page_content=path.read_text(encoding="utf-8-sig"))]
        except UnicodeError as exc:
            raise AppError("文本文件需要采用 UTF-8 编码。", "document_encoding") from exc
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=650, chunk_overlap=100, separators=["\n\n", "\n", "。", "；", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    if not chunks:
        raise AppError("文档没有可提取文字；扫描 PDF 需要先做 OCR。", "document_empty")
    if len(chunks) > 2000:
        raise AppError("文档片段过多，请拆分文件。", "document_limit")
    for index, chunk in enumerate(chunks):
        chunk.metadata.update(metadata, source=filename, filename=filename, chunk_index=index)
    return chunks


def _ingest(path: Path, filename: str, metadata: dict, cancelled: threading.Event) -> dict:
    store = get_store()
    metadata = {
        **metadata,
        "embedding_model": get_settings().embedding_model_name,
        "splitter_version": "650-100-v2",
    }
    document_id = str(uuid5(NAMESPACE_URL, "tech2ai/" + filename.casefold()))
    fingerprint = hashlib.sha256(path.read_bytes() + encode(metadata).encode()).hexdigest()
    version_id = str(uuid4())
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        rows = db.execute(
            "SELECT * FROM documents WHERE document_id=? ORDER BY version DESC", (document_id,)
        ).fetchall()
        for row in rows:
            if row["status"] == "ready" and row["content_hash"] == fingerprint:
                return {
                    "document_id": document_id,
                    "version_id": row["id"],
                    "chunk_count": row["chunk_count"],
                    "duplicate": True,
                }
        if any(row["status"] in {"processing", "deleting"} for row in rows):
            raise AppError("同名文档正在处理，请等待完成。", "document_busy", 409)
        version = rows[0]["version"] + 1 if rows else 1
        db.execute(
            "INSERT INTO documents VALUES(?,?,?,?,?,'processing',0,?,?,NULL)",
            (
                version_id,
                document_id,
                filename,
                fingerprint,
                version,
                encode(metadata),
                now(),
            ),
        )
    original = get_settings().knowledge_dir / "originals" / (version_id + path.suffix.lower())
    try:
        with span("rag", "ingestion.parse"):
            chunks = load_chunks(
                path, filename, {**metadata, "document_id": document_id, "version_id": version_id}
            )
        for chunk in chunks:
            chunk.metadata["chunk_id"] = str(
                uuid5(NAMESPACE_URL, f"{version_id}/{chunk.metadata['chunk_index']}")
            )
        if cancelled.is_set():
            raise AppError("入库已取消。", "cancelled")
        with _index_lock, span("rag", "ingestion.embed"):
            index = vector_store(ensure=True)
            for start in range(0, len(chunks), 32):
                if cancelled.is_set():
                    raise AppError("入库已取消。", "cancelled")
                batch = chunks[start : start + 32]
                index.add_documents(batch, ids=[chunk.metadata["chunk_id"] for chunk in batch])
        if cancelled.is_set():
            raise AppError("入库已取消。", "cancelled")
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, original)
        with store.connection() as db:
            db.execute(
                "UPDATE documents SET status='superseded' WHERE document_id=? AND status='ready'",
                (document_id,),
            )
            db.execute(
                "UPDATE documents SET status='ready',chunk_count=? WHERE id=?", (len(chunks), version_id)
            )
        return {
            "document_id": document_id,
            "version_id": version_id,
            "version": version,
            "chunk_count": len(chunks),
            "duplicate": False,
        }
    except Exception as exc:
        original.unlink(missing_ok=True)
        store.execute(
            "UPDATE documents SET status='error',error=? WHERE id=?", (public_error(exc), version_id)
        )
        try:
            delete_vectors("version_id", version_id)
        except Exception:
            store.event(None, "入库失败后的残留索引将在文档删除时清理。", "WARNING")
        raise


async def ingest(path: Path, filename: str, metadata: dict | None = None, remove_file: bool = False):
    cancelled = threading.Event()
    worker = asyncio.create_task(asyncio.to_thread(_ingest, path, filename, metadata or {}, cancelled))
    try:
        return await asyncio.shield(worker)
    except asyncio.CancelledError:
        cancelled.set()
        try:
            await worker
        except Exception:
            pass
        raise
    finally:
        if remove_file:
            path.unlink(missing_ok=True)


def delete_vectors(field: str, value: str):
    from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue

    client = get_qdrant()
    collection = get_settings().qdrant_collection_name
    if client.collection_exists(collection):
        client.delete(
            collection,
            points_selector=FilterSelector(
                filter=Filter(must=[FieldCondition(key=f"metadata.{field}", match=MatchValue(value=value))])
            ),
            wait=True,
        )


def delete_document(document_id: str):
    store = get_store()
    rows = store.rows("SELECT id,filename,status FROM documents WHERE document_id=?", (document_id,))
    if not rows:
        raise AppError("文档不存在。", "not_found", 404)
    with store.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        states = db.execute("SELECT status FROM documents WHERE document_id=?", (document_id,)).fetchall()
        if any(row["status"] == "processing" for row in states):
            raise AppError("请等待入库完成后删除文档。", "document_busy", 409)
        db.execute("UPDATE documents SET status='deleting' WHERE document_id=?", (document_id,))
    delete_vectors("document_id", document_id)
    for row in rows:
        path = get_settings().knowledge_dir / "originals" / (row["id"] + Path(row["filename"]).suffix.lower())
        path.unlink(missing_ok=True)
    store.execute("UPDATE documents SET status='deleted' WHERE document_id=?", (document_id,))
    return {"document_id": document_id, "status": "deleted"}


def list_documents() -> list[dict]:
    rows = get_store().rows("SELECT * FROM documents ORDER BY created_at DESC")
    for row in rows:
        row["metadata"] = json.loads(row["metadata"])
    return rows
