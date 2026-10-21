import asyncio
from datetime import date
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.jobs import jobs
from app.core.store import get_store
from app.core.telemetry import span, tracing_context
from app.modules.rag.ingestion import delete_document, ingest, list_documents
from app.modules.rag.schemas import SearchRequest

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.get("/status")
def status():
    documents = list_documents()
    ready = [row for row in documents if row["status"] == "ready"]
    return {
        "document_count": len(ready),
        "chunk_count": sum(row["chunk_count"] for row in ready),
        "status": "ready" if ready else "knowledge_empty",
        "embedding_model": get_settings().embedding_model_name,
        "processing": sum(row["status"] == "processing" for row in documents),
    }


@router.get("/documents")
def documents():
    return list_documents()


@router.post("/documents", status_code=202)
async def upload(
    file: Annotated[UploadFile, File()],
    category: Annotated[str, Form(max_length=100)] = "general",
    product_code: Annotated[str, Form(max_length=100)] = "",
    effective_from: Annotated[date, Form()] = date(2025, 4, 1),
    effective_to: Annotated[date | None, Form()] = None,
):
    filename = Path((file.filename or "document").replace("\\", "/")).name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".md", ".txt", ".pdf"} or len(filename) > 200:
        raise AppError("仅支持文件名不超过 200 字符的 PDF、TXT、Markdown。")
    if effective_to and effective_to < effective_from:
        raise AppError("失效日期不能早于生效日期。")
    folder = get_settings().upload_dir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid4()}{suffix}"
    try:
        total = 0
        with path.open("wb") as target:
            while data := await file.read(1024 * 256):
                total += len(data)
                if total > get_settings().max_upload_mb * 1024 * 1024:
                    raise AppError("文件超过上传大小限制。", "upload_limit", 413)
                target.write(data)
        metadata = {
            "category": category[:100],
            "product_code": product_code[:100],
            "effective_from": effective_from.isoformat(),
        }
        if effective_to:
            metadata["effective_to"] = effective_to.isoformat()
        return jobs.submit("rag", "document.ingest", lambda: ingest(path, filename, metadata, remove_file=True))
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


@router.get("/documents/{version_id}/source")
def source(version_id: str):
    rows = get_store().rows("SELECT id,filename,status FROM documents WHERE id=?", (version_id,))
    if not rows or rows[0]["status"] not in {"ready", "superseded"}:
        raise AppError("文档原件不可用。", "not_found", 404)
    row = rows[0]
    path = get_settings().knowledge_dir / "originals" / (row["id"] + Path(row["filename"]).suffix.lower())
    if not path.is_file():
        raise AppError("文档原件不存在。", "not_found", 404)
    return FileResponse(path, filename=row["filename"])


@router.delete("/documents/{document_id}")
def delete(document_id: str):
    with span("rag", "document.delete"):
        return delete_document(document_id)


@router.post("/search")
async def search(request: SearchRequest):
    from app.modules.rag.retrieval import search as retrieve

    with tracing_context():
        async with asyncio.timeout(get_settings().operation_timeout_seconds):
            return await retrieve(request)


@router.post("/ask")
async def ask(request: SearchRequest):
    from app.modules.rag.service import ask as answer

    with tracing_context():
        async with asyncio.timeout(get_settings().operation_timeout_seconds):
            return await answer(request)


@router.post("/seed", status_code=202)
async def seed():
    async def import_files():
        results = []
        for path in sorted(get_settings().knowledge_dir.glob("*.md")):
            results.append(
                await ingest(path, path.name, {"category": path.stem.split("-")[0], "effective_from": "2025-04-01"})
            )
        return {"documents": results, "count": len(results)}

    return jobs.submit("rag", "knowledge.seed", import_files)
