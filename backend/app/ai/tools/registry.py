from app.ai.tools.calculator import calculator
from app.ai.tools.text_length import text_length


tools = [
    calculator,
    text_length,
]


tool_registry = {
    tool.name: tool
    for tool in tools
}