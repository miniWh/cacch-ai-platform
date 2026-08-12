"""数据库引擎与会话工厂。

负责创建 SQLAlchemy 引擎、会话工厂，以及初始化 AI 业务表结构。
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.common.db_naming import AI_TABLE_PREFIX, assert_only_ai_tables
from app.dao.models import (  # noqa: F401 — register metadata
    AuditLog,
    AuthSession,
    ChatMessage,
    ChatSession,
    KnowledgeBase,
    Menu,
    Org,
    Role,
    RoleMenu,
    SourceSite,
    UserAccount,
    UserMenu,
)
from app.dao.models.base import Base
from app.web.config import get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """获取（或懒加载创建）全局数据库引擎。

    根据配置中的 ``database_url`` 创建连接；SQLite 启用外键约束，
    PostgreSQL 在连接时设置应用时区。
    """
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        connect_args: dict[str, object] = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            settings.database_url,
            future=True,
            connect_args=connect_args,
        )
        if settings.database_url.startswith("sqlite"):

            @event.listens_for(_engine, "connect")
            def _set_sqlite_fk(dbapi_conn: object, _: object) -> None:
                cursor = dbapi_conn.cursor()  # type: ignore[attr-defined]
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        elif settings.database_url.startswith("postgresql"):

            @event.listens_for(_engine, "connect")
            def _set_pg_timezone(dbapi_conn: object, _: object) -> None:
                # SET TIME ZONE 不支持参数绑定；时区名先经 ZoneInfo 校验
                from zoneinfo import ZoneInfo

                tz = settings.app_timezone
                ZoneInfo(tz)  # invalid → raises
                if any(c in tz for c in ("'", ";", "--", "/*")):
                    raise ValueError(f"unsafe timezone: {tz}")
                cursor = dbapi_conn.cursor()  # type: ignore[attr-defined]
                cursor.execute(f"SET TIME ZONE '{tz}'")
                cursor.close()

        _SessionLocal = sessionmaker(
            bind=_engine, autoflush=False, autocommit=False, future=True
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """返回绑定到全局引擎的会话工厂。"""
    get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def init_db() -> None:
    """创建 AI 业务表（仅 ``cacch_ai_`` 前缀白名单表）。

    在共享数据库场景下绝不对外部业务表执行 DDL。
    """
    assert_only_ai_tables(set(Base.metadata.tables.keys()))
    engine = get_engine()
    # 显式只建白名单表，避免误带入其他 metadata
    tables = [
        Base.metadata.tables[name]
        for name in sorted(Base.metadata.tables.keys())
        if name.startswith(AI_TABLE_PREFIX)
    ]
    Base.metadata.create_all(bind=engine, tables=tables)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入用：提供请求级数据库会话。

    正常结束时提交，异常时回滚，最终关闭会话。
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine() -> None:
    """测试辅助：释放引擎并重置，以便切换 ``DATABASE_URL``。"""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
