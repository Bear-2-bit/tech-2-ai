import json

from app.deepseek import DeepSeekClient
from app.tools import TOOL_REGISTRY
from app.tools import TOOL_SCHEMAS


class Agent:
    def __init__(
        self,
        llm: DeepSeekClient,
        max_steps: int = 10,
    ):
        self.llm = llm
        self.max_steps = max_steps

    def run(self, user_input: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个多工具智能体。"
                    "需要工具时调用工具，"
                    "获得工具结果后继续完成任务。"
                ),
            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        for _ in range(self.max_steps):
            message = self.llm.chat(
                messages=messages,
                tools=TOOL_SCHEMAS,
            )

            tool_calls = message.get("tool_calls")

            if not tool_calls:
                return message.get("content", "")

            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": tool_calls,
                }
            )

            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                print(tool_name)
                raw_arguments = (
                    tool_call["function"]["arguments"]
                )

                try:
                    arguments = json.loads(raw_arguments)

                    tool = TOOL_REGISTRY.get(tool_name)

                    if tool is None:
                        raise ValueError(
                            f"不存在工具: {tool_name}"
                        )

                    result = tool(**arguments)

                    tool_result = {
                        "success": True,
                        "data": result,
                    }

                except Exception as exc:
                    tool_result = {
                        "success": False,
                        "error": str(exc),
                    }

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(
                            tool_result,
                            ensure_ascii=False,
                        ),
                    }
                )

        raise RuntimeError(
            f"Agent 超过最大执行步数 {self.max_steps}"
        )