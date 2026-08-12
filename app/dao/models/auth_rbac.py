"""认证、组织、角色、菜单等 RBAC 相关 ORM 模型。

映射 AI 平台自有的权限与账号表（``cacch_ai_*`` 前缀），
涵盖组织架构、菜单、角色、用户账号、会话与审计日志。
"""

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

# SQLite 需 INTEGER 主键以支持 AUTOINCREMENT；PostgreSQL 仍使用 BIGINT
_BigIntPK = BigInteger().with_variant(Integer, "sqlite")
_BigInt = BigInteger().with_variant(Integer, "sqlite")


class Org(Base):
    """组织/部门表（``cacch_ai_org``）。

    存储树形组织架构，支持父子层级与排序。
    """

    __tablename__ = f"{AI_TABLE_PREFIX}org"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}org.id"), nullable=True
    )  # 上级组织 ID，根节点为 NULL
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 组织编码
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # 组织名称
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # 排序权重
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active"
    )  # active / disabled
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
    """前端菜单/路由表（``cacch_ai_menu``）。

    定义工作台侧边栏菜单项及其路由、图标与可分配性。
    """

    __tablename__ = f"{AI_TABLE_PREFIX}menu"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # 菜单唯一标识
    title: Mapped[str] = mapped_column(String(64), nullable=False)  # 显示标题
    path: Mapped[str] = mapped_column(String(128), nullable=False)  # 前端路由路径
    icon: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assignable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )  # 是否可分配给角色/用户
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
    """角色表（``cacch_ai_role``）。

    定义系统角色及其菜单权限集合的关联主体。
    """

    __tablename__ = f"{AI_TABLE_PREFIX}role"
    __table_args__ = (UniqueConstraint("code", name=f"uq_{AI_TABLE_PREFIX}role_code"),)

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)  # 角色编码，全局唯一
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # 角色名称
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # 系统内置角色，不可删除
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
    """角色-菜单关联表（``cacch_ai_role_menu``）。

    多对多关系：记录某角色可访问的菜单项。
    """

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
    """平台用户账号表（``cacch_ai_user``）。

    存储登录凭证、所属组织/角色、账号状态及安全相关字段。
    """

    __tablename__ = f"{AI_TABLE_PREFIX}user"
    __table_args__ = (
        UniqueConstraint("staff_no", name=f"uq_{AI_TABLE_PREFIX}user_staff_no"),
        UniqueConstraint("mobile", name=f"uq_{AI_TABLE_PREFIX}user_mobile"),
    )

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    staff_no: Mapped[str] = mapped_column(String(64), nullable=False)  # 工号
    mobile: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # 手机号（登录账号）
    name: Mapped[str] = mapped_column(String(128), nullable=False)  # 姓名
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    staff_status: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # HR 在职状态，如 IN_SERVICE
    org_id: Mapped[int] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}org.id"), nullable=False
    )
    role_id: Mapped[int | None] = mapped_column(
        _BigInt, ForeignKey(f"{AI_TABLE_PREFIX}role.id"), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # 密码哈希
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )  # 首次登录须改密
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # 令牌版本，递增可强制全端下线
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )  # 账号锁定截止时间
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
    """用户-菜单关联表（``cacch_ai_user_menu``）。

    为用户单独追加菜单权限，与角色菜单取并集。
    """

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
    """认证会话表（``cacch_ai_auth_session``）。

    记录 Refresh Token 哈希、过期与撤销信息，支持多端登录管理。
    """

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
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 创建会话时的用户 token_version
    remember_today: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # 「今日免登录」标记
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )  # 非 NULL 表示会话已撤销
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )


class AuditLog(Base):
    """操作审计日志表（``cacch_ai_audit_log``）。

    记录用户关键操作（登录、改密、权限变更等）及结果。
    """

    __tablename__ = f"{AI_TABLE_PREFIX}audit_log"

    id: Mapped[int] = mapped_column(_BigIntPK, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        _BigInt, nullable=True
    )  # 操作者用户 ID
    actor_staff_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # 操作类型，如 login.success
    target_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # 目标实体类型
    target_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # 目标实体 ID
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    detail_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )  # 附加详情（JSON）
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=now_app,
        server_default=func.now(),
    )
