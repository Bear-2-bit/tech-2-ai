from fastapi import APIRouter, Depends

from app.dependencies import get_agent_service
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent_service import AgentService


router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
)


@router.post("", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    return await agent_service.run(request)