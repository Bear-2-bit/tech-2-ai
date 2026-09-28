from datetime import datetime
from zoneinfo import ZoneInfo


def calculator(
    operation: str,
    a: float,
    b: float,
) -> float:
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

    raise ValueError(f"不支持的 operation: {operation}")


def get_current_time(timezone: str) -> str:
    now = datetime.now(ZoneInfo(timezone))

    return now.strftime("%Y-%m-%d %H:%M:%S")


TOOL_REGISTRY = {
    "calculator": calculator,
    "get_current_time": get_current_time,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "执行基础数学运算",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": [
                            "add",
                            "subtract",
                            "multiply",
                            "divide",
                        ],
                        "description": "数学运算类型",
                    },
                    "a": {
                        "type": "number",
                    },
                    "b": {
                        "type": "number",
                    },
                },
                "required": [
                    "operation",
                    "a",
                    "b",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "查询指定 IANA 时区当前时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": (
                            "IANA timezone，例如 "
                            "Asia/Shanghai、America/New_York"
                        ),
                    }
                },
                "required": [
                    "timezone",
                ],
            },
        },
    },
]