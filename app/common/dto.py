"""Common API DTOs."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    detail: str | None = None


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}


class PageMeta(BaseModel):
    total: int = Field(ge=0)
