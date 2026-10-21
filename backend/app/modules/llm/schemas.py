from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Implementation = Literal["native", "langchain"]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=60)
    system_prompt: str = Field(default="你是一名 AI 应用工程老师，回答简洁准确。", max_length=4000)
    temperature: float = Field(default=0.3, ge=0, le=2)
    max_tokens: int = Field(default=1000, ge=16, le=8000)

    def messages_payload(self) -> list[dict]:
        history = [message.model_dump() for message in self.messages]
        return ([{"role": "system", "content": self.system_prompt}] if self.system_prompt else []) + history


class ExtractionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)


class ExtractedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1)
    priority: Literal["low", "medium", "high"]
    deadline: str | None = None
    technologies: list[str] = Field(default_factory=list)


EXTRACTION_PROMPT = """你是任务信息抽取器，只提取原文明示信息，不补充事实。
输出 JSON：title、priority、deadline、technologies。
priority 只能为 low/medium/high，未说明时为 medium。无截止时间时 deadline=null。
technologies 只包含原文明示的技术名称。不要输出 Markdown。"""
