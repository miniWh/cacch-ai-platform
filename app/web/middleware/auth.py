"""Auth dependency — MVP Bearer token."""

from fastapi import Depends, Header

from app.common.exceptions import UnauthorizedError
from app.web.config import Settings, get_settings


def require_bearer(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.api_auth_token:
        raise UnauthorizedError("invalid token")
