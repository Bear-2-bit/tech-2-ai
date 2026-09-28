from langchain.agents import create_agent

from app.langchain_model import create_model
from app.langchain_tools import TOOLS


def create_my_agent():
    model = create_model()

    agent = create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=(
            "你是一个多工具智能体。"
            "需要工具时主动调用工具。"
            "拿到工具结果后继续完成用户任务。"
        ),
    )

    return agent