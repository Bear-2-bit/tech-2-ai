from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    query: str = Field(min_length=1)


class AgentStep(BaseModel):
    message_type: str
    content: str
    tool_name: str | None = None
    tool_calls: list[dict] = Field(default_factory=list)


class AgentResponse(BaseModel):
    query: str
    answer: str
    steps: list[AgentStep]