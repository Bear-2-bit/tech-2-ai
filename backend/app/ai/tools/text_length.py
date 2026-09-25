from langchain_core.tools import tool


@tool
def text_length(text: str) -> int:
    """计算一段文本包含的字符数量。"""
    return len(text)