from fastapi import APIRouter, Depends

from app.dependencies import get_rag_service
from app.schemas.rag import RAGRequest, RAGResponse
from app.services.rag_service import RAGService


router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("", response_model=RAGResponse)
async def rag(
    request: RAGRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGResponse:
    return await rag_service.rag(request)