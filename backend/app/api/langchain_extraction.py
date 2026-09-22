from fastapi import (
    APIRouter,
    Depends,
)

from app.dependencies import (
    get_langchain_extraction_service,
)
from app.schemas.extraction import (
    ExtractedTask,
    ExtractionRequest,
)
from app.services.langchain_extraction_service import (
    LangChainExtractionService,
)


router = APIRouter(
    prefix="/api/extraction/langchain",
    tags=["LangChain Extraction"],
)


@router.post(
    "",
    response_model=ExtractedTask,
)
async def create_langchain_extraction(
    request: ExtractionRequest,

    extraction_service:
        LangChainExtractionService = Depends(
            get_langchain_extraction_service
        ),

) -> ExtractedTask:

    return await extraction_service.extract(
        request
    )