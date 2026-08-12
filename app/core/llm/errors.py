"""LLM 与 Embedding 相关异常类型。"""

from app.common.exceptions import AppError


class LlmError(AppError):
    """上游模型服务或网关调用失败。"""

    def __init__(self, message: str, *, code: int = 502) -> None:
        super().__init__(message, code=code)


class LlmConfigError(AppError):
    """Profile 或 provider 配置错误（HTTP 400 语义）。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code=400)


class LlmProviderError(LlmError):
    """模型提供商 HTTP/API 层错误。"""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message, code=502)
        self.status_code = status_code
