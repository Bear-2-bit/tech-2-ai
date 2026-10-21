class AppError(Exception):
    def __init__(self, message: str, code: str = "invalid_request", status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def public_error(exc: BaseException) -> str:
    if isinstance(exc, AppError):
        return str(exc)
    if isinstance(exc, TimeoutError):
        return "操作超时，请缩小任务范围后重试。"
    return "操作失败，请使用运行 ID 查看脱敏错误记录。"
