from app.ai.agent.runtime import AgentRuntime
from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
    AgentStep,
)


class AgentService:
    def __init__(
        self,
        runtime: AgentRuntime,
    ):
        self.runtime = runtime

    async def run(
        self,
        request: AgentRequest,
    ) -> AgentResponse:
        messages = await self.runtime.run(
            request.query
        )

        steps = []

        for message in messages:
            steps.append(
                AgentStep(
                    message_type=type(message).__name__,
                    content=str(message.content),
                    tool_name=getattr(
                        message,
                        "name",
                        None,
                    ),
                    tool_calls=getattr(
                        message,
                        "tool_calls",
                        None,
                    ) or [],
                )
            )

        return AgentResponse(
            query=request.query,
            answer=str(
                messages[-1].content
            ),
            steps=steps,
        )