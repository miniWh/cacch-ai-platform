"""应用时区与时间处理工具，默认 Asia/Shanghai。

数据库列使用 TIMESTAMP WITHOUT TIME ZONE，存储上海本地墙钟时间，
以便 IDE 客户端在不同时区下仍显示相同数字。
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.web.config import get_settings


def app_zone() -> ZoneInfo:
    """返回配置中的应用时区对象。"""
    return ZoneInfo(get_settings().app_timezone)


def now_app() -> datetime:
    """获取当前应用时区的墙钟时间（无时区信息），用于写入数据库 TIMESTAMP 列。"""
    return datetime.now(app_zone()).replace(tzinfo=None)


def to_app_tz(value: datetime | None) -> datetime | None:
    """将 datetime 规范化为应用时区，供 API 返回或前端展示。

    Args:
        value: 待转换的时间；``None`` 时原样返回。

    Returns:
        带应用时区信息的 datetime，或 ``None``。
    """
    if value is None:
        return None
    if value.tzinfo is None:
        # 数据库存储的是无时区的上海墙钟时间
        return value.replace(tzinfo=app_zone())
    return value.astimezone(app_zone())
