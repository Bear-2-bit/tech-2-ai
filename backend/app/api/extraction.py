from fastapi import (
    APIRouter,
    Depends,
)

from app.dependencies import (
    get_extraction_service,
)
from app.schemas.extraction import (
    ExtractionRequest,
    ExtractionResponse,
)
from app.services.extraction_service import (
    ExtractionService,
)


router = APIRouter(
    prefix="/api/extraction",
    tags=["Extraction"],
)


@router.post(
    "",
    response_model=ExtractionResponse,
)
async def create_extraction(
    request: ExtractionRequest,

    extraction_service: ExtractionService = Depends(
        get_extraction_service
    ),

) -> ExtractionResponse:

    return await extraction_service.extract(
        request
    )