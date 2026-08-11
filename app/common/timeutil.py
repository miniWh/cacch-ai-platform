"""Application timezone helpers — default Asia/Shanghai.

DB columns use TIMESTAMP WITHOUT TIME ZONE and store Asia/Shanghai wall clock,
so IDE clients show the same digits regardless of session TimeZone.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.web.config import get_settings


def app_zone() -> ZoneInfo:
    return ZoneInfo(get_settings().app_timezone)


def now_app() -> datetime:
    """Current Asia/Shanghai wall clock (naive), for DB TIMESTAMP columns."""
    return datetime.now(app_zone()).replace(tzinfo=None)


def to_app_tz(value: datetime | None) -> datetime | None:
    """Normalize datetime to app timezone for API / display."""
    if value is None:
        return None
    if value.tzinfo is None:
        # DB stores naive Shanghai wall clock
        return value.replace(tzinfo=app_zone())
    return value.astimezone(app_zone())
