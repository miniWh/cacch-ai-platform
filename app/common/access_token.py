"""HMAC access tokens for user sessions."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(raw: str) -> bytes:
    pad = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + pad)


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: int
    session_id: int
    token_version: int
    exp: int


def issue_access_token(
    *,
    secret: str,
    user_id: int,
    session_id: int,
    token_version: int,
    expires_at_ts: int,
) -> str:
    payload = {
        "uid": user_id,
        "sid": session_id,
        "tv": token_version,
        "exp": expires_at_ts,
    }
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _b64encode(
        hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{body}.{sig}"


def parse_access_token(token: str, *, secret: str) -> AccessTokenClaims | None:
    try:
        body, sig = token.split(".", 1)
        expected = _b64encode(
            hmac.new(
                secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256
            ).digest()
        )
        if not hmac.compare_digest(sig, expected):
            return None
        payload: dict[str, Any] = json.loads(_b64decode(body).decode("utf-8"))
        exp = int(payload["exp"])
        if exp < int(time.time()):
            return None
        return AccessTokenClaims(
            user_id=int(payload["uid"]),
            session_id=int(payload["sid"]),
            token_version=int(payload["tv"]),
            exp=exp,
        )
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
