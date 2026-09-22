import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import get_knowledge_ingestion_service, get_rag_service
from app.schemas.rag import KnowledgeIngestionResponse, RAGRequest, RAGResponse
from app.services.knowledge_ingestion_service import KnowledgeIngestionService
from app.services.rag_service import RAGService


router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("", response_model=RAGResponse)
async def rag(
    request: RAGRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGResponse:
    return await rag_service.rag(request)


@router.post("/index", response_model=KnowledgeIngestionResponse)
def index_document(
    file: UploadFile = File(...),
    ingestion_service: KnowledgeIngestionService = Depends(get_knowledge_ingestion_service),
) -> KnowledgeIngestionResponse:
    filename = file.filename or "uploaded_file"
    suffix = Path(filename).suffix.lower()

    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Only PDF, TXT and Markdown files are supported")

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = Path(temp_file.name)

    try:
        return ingestion_service.ingest_file(
            file_path=temp_path,
            original_filename=filename,
        )
    finally:
        temp_path.unlink(missing_ok=True)