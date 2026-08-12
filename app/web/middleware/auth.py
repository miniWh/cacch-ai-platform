"""认证依赖注入：用户访问令牌或服务 API_AUTH_TOKEN。"""

from dataclasses import dataclass

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.common.exceptions import UnauthorizedError
from app.dao.database import get_db
from app.service.auth_service import AuthService, CurrentUser
from app.web.config import Settings, get_settings


def get_auth_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    """FastAPI 依赖：构造 AuthService 实例。"""
    return AuthService(db, settings)


def require_user(
    authorization: str | None = Header(default=None),
    service: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    """FastAPI 依赖：解析 Bearer 令牌并返回当前用户。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise UnauthorizedError("missing bearer token")
    return service.resolve_bearer(token)


def require_bearer(
    user: CurrentUser = Depends(require_user),
) -> CurrentUser:
    """向后兼容的依赖名，RAG 路由使用。"""
    return user


def require_business_user(
    user: CurrentUser = Depends(require_user),
) -> CurrentUser:
    """要求用户已完成强制改密，可访问业务 API。"""
    user.require_business_access()
    return user


def client_meta(request: Request) -> tuple[str | None, str | None]:
    """从请求中提取客户端 IP 与 User-Agent。"""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


@dataclass
class ServiceGate:
    """仅允许服务令牌访问的门禁（用于 bootstrap 等）。"""

    settings: Settings

    def __call__(self, authorization: str | None = Header(default=None)) -> None:
        if not authorization or not authorization.startswith("Bearer "):
            raise UnauthorizedError("missing bearer token")
        token = authorization.removeprefix("Bearer ").strip()
        if token != self.settings.api_auth_token:
            raise UnauthorizedError("service token required")
