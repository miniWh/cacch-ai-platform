"""密码哈希、校验与随机密码生成。"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import string

_ITERATIONS = 120_000
_PREFIX = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    """使用 PBKDF2-SHA256 对明文密码进行哈希。

    Args:
        password: 明文密码。

    Returns:
        含算法前缀、迭代次数、盐与摘要的可存储字符串。
    """
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS
    )
    return f"{_PREFIX}${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """验证明文密码是否与存储哈希匹配。

    Args:
        password: 待验证的明文密码。
        password_hash: ``hash_password`` 生成的哈希字符串。

    Returns:
        匹配返回 ``True``，格式错误或摘要不一致返回 ``False``。
    """
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
    """校验密码强度是否符合平台策略。

    Args:
        password: 待校验的明文密码。

    Returns:
        不符合要求时返回中文错误说明，符合要求时返回 ``None``。
    """
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
    """生成满足强度策略的随机密码。

    Args:
        length: 密码长度，默认 12。

    Returns:
        随机密码字符串。
    """
    alphabet = string.ascii_letters + string.digits
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if validate_password_strength(pwd) is None:
            return pwd
