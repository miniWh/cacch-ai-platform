"""Shared exceptions."""


class AppError(Exception):
    """Base application error with API-facing code."""

    def __init__(self, message: str, *, code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str = "resource not found") -> None:
        super().__init__(message, code=404)


class ValidationAppError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code=400)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "unauthorized") -> None:
        super().__init__(message, code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "forbidden") -> None:
        super().__init__(message, code=403)
