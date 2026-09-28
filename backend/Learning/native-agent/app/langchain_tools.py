from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool


@tool
def calculator(
    operation: str,
    a: float,
    b: float,
) -> float:
    """执行基础数学运算。

    operation 只能是：
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


@tool
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


TOOLS = [
    calculator,
    get_current_time,
]