class LLMError(Exception):
    """LLM 相关异常的基类。"""


class LLMTimeoutError(LLMError):
    """调用 LLM 超时。"""


class LLMUpstreamError(LLMError):
    """LLM 上游服务异常。"""