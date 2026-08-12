"""Auth / org / role / menu ORM models."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.common.db_naming import AI_TABLE_PREFIX
from app.common.timeutil import now_app
from app.dao.models.base import Base

# SQLite needs INTEGER PK for AUTOINCREMENT; PostgreSQL keeps BIGINT
_BigIntPK = BigInteger().with_variant(Integer, "sqlite")
_BigInt = BigInteger().with_variant(Integer, "sqlite")


class Org(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}org"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}org.id"), nullable=True
    )
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    remark: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        onupdate=now_app,
        server_default=func.now(),
    )


class Menu(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}menu"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    path: Mapped[str] = mapped_column(String(128), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assignable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    remark: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        onupdate=now_app,
        server_default=func.now(),
    )


class Role(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}role"
    __table_args__ = (UniqueConstraint("code", name=f"uq_{AI_TABLE_PREFIX}role_code"),)

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        onupdate=now_app,
        server_default=func.now(),
    )


class RoleMenu(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}role_menu"

    role_id: Mapped[int] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}role.id"), primary_key=True
    )
    menu_id: Mapped[str] = mapped_column(
        String(64), ForeignKey(f"{AI_TABLE_PREFIX}menu.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )


class UserAccount(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}user"
    __table_args__ = (
        UniqueConstraint("staff_no", name=f"uq_{AI_TABLE_PREFIX}user_staff_no"),
        UniqueConstraint("mobile", name=f"uq_{AI_TABLE_PREFIX}user_mobile"),
    )

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    staff_no: Mapped[str] = mapped_column(String(64), nullable=False)
    mobile: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    staff_status: Mapped[str] = mapped_column(String(32), nullable=False)
    org_id: Mapped[int] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}org.id"), nullable=False
    )
    role_id: Mapped[int | None] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}role.id"), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}user.id"), nullable=True
    )
    remark: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        onupdate=now_app,
        server_default=func.now(),
    )


class UserMenu(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}user_menu"

    user_id: Mapped[int] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}user.id"), primary_key=True
    )
    menu_id: Mapped[str] = mapped_column(
        String(64), ForeignKey(f"{AI_TABLE_PREFIX}menu.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )


class AuthSession(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}auth_session"
    __table_args__ = (
        UniqueConstraint(
            "refresh_token_hash", name=f"uq_{AI_TABLE_PREFIX}auth_session_refresh"
        ),
    )

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}user.id"), nullable=False
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False)
    remember_today: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )


class AuditLog(Base):
    __tablename__ = f"{AI_TABLE_PREFIX}audit_log"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(_BigInt, nullable=True)
    actor_staff_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    detail_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
