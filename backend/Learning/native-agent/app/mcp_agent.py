import sys
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from app.langchain_model import create_model

async def create_my_agent():
    model = create_model()

    server_path = (
        r"C:\Users\34074\Desktop\tech-2-ai\backend\Learning\native-agent\app\mcp_server.py"
    )

    # mcp_config = {
    #     "tools": {
    #         "transport": "stdio",
    #         "command": sys.executable,
    #         "args": [server_path],
    #     }
    # }

    mcp_config = {
        "tools": {
            "url": "http://localhost:8000/mcp",   # 关键：用 url 替代 command/args
            # transport 可以省略，MCPAdapter 会根据 url 自动推断为 HTTP
            # 如果显式指定，写 "http" 或 "streamable-http"
        }
    }

    async with MCPAdapter(mcp_config) as adapter:
        # 从 MCP 服务器发现并聚合工具
        tools = await adapter.list_tools()

        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=(
                "你是一个多工具智能体。"
                "需要使用工具时主动调用工具，"
                "获得工具结果后继续完成任务。"
            ),
        )

        return agent