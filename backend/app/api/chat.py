from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def create_chat(
    request: ChatRequest,
) -> ChatResponse:
    return await chat(request)