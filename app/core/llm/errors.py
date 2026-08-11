"""LLM / Embedding related errors."""

from app.common.exceptions import AppError


class LlmError(AppError):
    """Upstream model or gateway failure."""

    def __init__(self, message: str, *, code: int = 502) -> None:
        super().__init__(message, code=code)


class LlmConfigError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=400)


class LlmProviderError(LlmError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message, code=502)
        self.status_code = status_code
