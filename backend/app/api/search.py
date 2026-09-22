from fastapi import APIRouter, Depends

from app.dependencies import get_search_service
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService


router = APIRouter(prefix="/api/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    return await search_service.search(request)