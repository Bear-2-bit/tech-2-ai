from fastapi import APIRouter, Depends

from app.dependencies import get_chat_service
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.services.chat_service import ChatService


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

    chat_service: ChatService = Depends(
        get_chat_service
    ),

) -> ChatResponse:

    return await chat_service.chat(request)