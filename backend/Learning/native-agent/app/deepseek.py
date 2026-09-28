import os

import httpx
from dotenv import load_dotenv


load_dotenv()


class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = os.getenv("DEEPSEEK_MODEL")

        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY 未配置")

        if not self.model:
            raise RuntimeError("DEEPSEEK_MODEL 未配置")

        self.client = httpx.Client(
            base_url="https://api.deepseek.com",
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    def chat(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> dict:
        response = self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            },
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]