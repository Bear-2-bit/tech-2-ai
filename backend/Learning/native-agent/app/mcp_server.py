from datetime import datetime
from zoneinfo import ZoneInfo

from mcp.server import MCPServer


mcp = MCPServer(
    "tech-2-ai-tools",
    version="1.0.0",
)


@mcp.tool()
def calculator(
    operation: str,
    a: float,
    b: float,
) -> float:
    """执行基础数学运算。

    operation 可选：
    add、subtract、multiply、divide。
    """

    if operation == "add":
        return a + b

    if operation == "subtract":
        return a - b

    if operation == "multiply":
        return a * b

    if operation == "divide":
        if b == 0:
            raise ValueError("除数不能为 0")

        return a / b

    raise ValueError(
        f"不支持的 operation: {operation}"
    )


@mcp.tool()
def get_current_time(timezone: str) -> str:
    """查询指定 IANA 时区的当前时间。

    例如：
    Asia/Shanghai
    America/New_York
    """

    now = datetime.now(
        ZoneInfo(timezone)
    )

    return now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )


if __name__ == "__main__":
    # mcp.run()
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",   # 监听所有网络接口，局域网内其他机器也能访问
        port=8000,        # 监听端口，默认也是 8000
    )