"""通用 API 响应与分页相关的数据传输对象。"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """标准错误响应体。"""

    detail: str | None = None


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    """构造成功响应字典。

    Args:
        data: 业务数据，可为任意 JSON 可序列化对象。
        message: 提示信息，默认 ``ok``。

    Returns:
        含 ``code=0``、``message`` 与 ``data`` 字段的字典。
    """
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict[str, Any]:
    """构造失败响应字典。

    Args:
        code: 业务错误码，非零表示失败。
        message: 面向用户的错误说明。
        data: 可选附加数据。

    Returns:
        含 ``code``、``message`` 与 ``data`` 字段的字典。
    """
    return {"code": code, "message": message, "data": data}


class PageMeta(BaseModel):
    """分页元信息。"""

    total: int = Field(ge=0)
