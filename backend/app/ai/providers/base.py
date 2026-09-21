from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


@dataclass
class LLMMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMRequest:
    messages: list[LLMMessage]
    temperature: float
    max_tokens: int


@dataclass
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMResponse:
    content: str
    model: str
    finish_reason: str | None
    usage: LLMUsage


class LLMProvider(ABC):

    @abstractmethod
    async def chat(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        pass