"""应用层共享异常类型。"""


class AppError(Exception):
    """应用异常基类，携带可映射到 API 响应的业务错误码。"""

    def __init__(self, message: str, *, code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(AppError):
    """资源不存在（HTTP 404 语义）。"""

    def __init__(self, message: str = "resource not found") -> None:
        super().__init__(message, code=404)


class ValidationAppError(AppError):
    """请求参数或业务校验失败（HTTP 400 语义）。"""

    def __init__(self, message: str) -> None:
        super().__init__(message, code=400)


class UnauthorizedError(AppError):
    """未认证或凭证无效（HTTP 401 语义）。"""

    def __init__(self, message: str = "unauthorized") -> None:
        super().__init__(message, code=401)


class ForbiddenError(AppError):
    """已认证但无权限（HTTP 403 语义）。"""

    def __init__(self, message: str = "forbidden") -> None:
        super().__init__(message, code=403)
