"""基于 HMAC 的访问令牌签发与校验。"""

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
    """访问令牌解析后的声明载荷。"""

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
    """签发 HMAC 签名的访问令牌。

    Args:
        secret: HMAC 密钥。
        user_id: 用户 ID。
        session_id: 会话 ID。
        token_version: 令牌版本号，用于强制失效旧令牌。
        expires_at_ts: 过期时间（Unix 秒级时间戳）。

    Returns:
        ``body.signature`` 格式的 URL-safe Base64 令牌字符串。
    """
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
    """校验并解析访问令牌。

    Args:
        token: 待校验的令牌字符串。
        secret: 与签发时相同的 HMAC 密钥。

    Returns:
        校验通过且未过期时返回 ``AccessTokenClaims``，否则 ``None``。
    """
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
    """对原始刷新令牌做 SHA-256 哈希，用于持久化存储。

    Args:
        raw: 明文刷新令牌。

    Returns:
        十六进制哈希字符串。
    """
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
