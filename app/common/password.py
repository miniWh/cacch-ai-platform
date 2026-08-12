"""Password hashing and random password generation."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import string

_ITERATIONS = 120_000
_PREFIX = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS
    )
    return f"{_PREFIX}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        prefix, iterations_s, salt, digest_hex = password_hash.split("$", 3)
        if prefix != _PREFIX:
            return False
        iterations = int(iterations_s)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def validate_password_strength(password: str) -> str | None:
    """Return error message or None if ok."""
    if len(password) < 8:
        return "密码长度至少 8 位"
    if not re.search(r"[A-Z]", password):
        return "密码须包含大写字母"
    if not re.search(r"[a-z]", password):
        return "密码须包含小写字母"
    if not re.search(r"[0-9]", password):
        return "密码须包含数字"
    return None


def generate_random_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if validate_password_strength(pwd) is None:
            return pwd
