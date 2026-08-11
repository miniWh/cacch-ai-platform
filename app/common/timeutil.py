"""Application timezone helpers — default Asia/Shanghai."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.web.config import get_settings


def app_zone() -> ZoneInfo:
    return ZoneInfo(get_settings().app_timezone)


def now_app() -> datetime:
    """Current time in configured app timezone (aware)."""
    return datetime.now(app_zone())


def to_app_tz(value: datetime | None) -> datetime | None:
    """Normalize datetime to app timezone for API / display."""
    if value is None:
        return None
    if value.tzinfo is None:
        # Treat naive as already in app TZ
        return value.replace(tzinfo=app_zone())
    return value.astimezone(app_zone())
