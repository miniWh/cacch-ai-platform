"""认证 RBAC 相关仓储。

封装组织、菜单、角色、用户、会话及审计日志的数据库读写操作。
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.common.timeutil import now_app
from app.dao.models.auth_rbac import (
    AuditLog,
    AuthSession,
    Menu,
    Org,
    Role,
    RoleMenu,
    UserAccount,
    UserMenu,
)


class AuthRbacRepository:
    """认证与权限管理仓储。

    提供 RBAC 各实体的 CRUD 及关联关系维护方法。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # --- org ---
    def list_orgs(self) -> list[Org]:
        """按排序权重与 ID 升序列出全部组织。"""
        return list(
            self._session.scalars(
                select(Org).order_by(Org.sort_order.asc(), Org.id.asc())
            )
        )

    def get_org(self, org_id: int) -> Org | None:
        """按主键查询组织。"""
        return self._session.get(Org, org_id)

    def add_org(self, org: Org) -> Org:
        """新增组织并 flush 以获取自增 ID。"""
        self._session.add(org)
        self._session.flush()
        return org

    # --- menu ---
    def list_menus(self, *, active_only: bool = False) -> list[Menu]:
        """列出菜单；``active_only=True`` 时仅返回启用项。"""
        stmt = select(Menu).order_by(Menu.sort_order.asc(), Menu.id.asc())
        if active_only:
            stmt = stmt.where(Menu.status == "active")
        return list(self._session.scalars(stmt))

    def get_menu(self, menu_id: str) -> Menu | None:
        """按菜单 ID 查询。"""
        return self._session.get(Menu, menu_id)

    def add_menu(self, menu: Menu) -> Menu:
        """新增菜单并 flush。"""
        self._session.add(menu)
        self._session.flush()
        return menu

    # --- role ---
    def list_roles(self) -> list[Role]:
        """按 ID 升序列出全部角色。"""
        return list(self._session.scalars(select(Role).order_by(Role.id.asc())))

    def get_role(self, role_id: int) -> Role | None:
        """按主键查询角色。"""
        return self._session.get(Role, role_id)

    def get_role_by_code(self, code: str) -> Role | None:
        """按角色编码查询。"""
        return self._session.scalar(select(Role).where(Role.code == code))

    def add_role(self, role: Role) -> Role:
        """新增角色并 flush。"""
        self._session.add(role)
        self._session.flush()
        return role

    def list_role_menu_ids(self, role_id: int) -> list[str]:
        """返回角色已分配的菜单 ID 列表。"""
        return list(
            self._session.scalars(
                select(RoleMenu.menu_id).where(RoleMenu.role_id == role_id)
            )
        )

    def replace_role_menus(self, role_id: int, menu_ids: list[str]) -> None:
        """全量替换角色的菜单关联。"""
        self._session.execute(delete(RoleMenu).where(RoleMenu.role_id == role_id))
        for mid in menu_ids:
            self._session.add(RoleMenu(role_id=role_id, menu_id=mid))
        self._session.flush()

    # --- user ---
    def count_users(self) -> int:
        """统计用户总数。"""
        return len(list(self._session.scalars(select(UserAccount.id))))

    def get_user(self, user_id: int) -> UserAccount | None:
        """按主键查询用户。"""
        return self._session.get(UserAccount, user_id)

    def get_user_by_mobile(self, mobile: str) -> UserAccount | None:
        """按手机号查询用户。"""
        return self._session.scalar(
            select(UserAccount).where(UserAccount.mobile == mobile)
        )

    def get_user_by_staff_no(self, staff_no: str) -> UserAccount | None:
        """按工号查询用户。"""
        return self._session.scalar(
            select(UserAccount).where(UserAccount.staff_no == staff_no)
        )

    def list_users(
        self,
        *,
        keyword: str | None = None,
        org_id: int | None = None,
        status: str | None = None,
    ) -> list[UserAccount]:
        """按关键词、组织、状态筛选用户列表（ID 降序）。"""
        stmt = select(UserAccount).order_by(UserAccount.id.desc())
        if org_id is not None:
            stmt = stmt.where(UserAccount.org_id == org_id)
        if status:
            stmt = stmt.where(UserAccount.status == status)
        if keyword:
            like = f"%{keyword.strip()}%"
            stmt = stmt.where(
                (UserAccount.mobile.like(like))
                | (UserAccount.name.like(like))
                | (UserAccount.staff_no.like(like))
            )
        return list(self._session.scalars(stmt))

    def add_user(self, user: UserAccount) -> UserAccount:
        """新增用户并 flush。"""
        self._session.add(user)
        self._session.flush()
        return user

    def list_user_menu_ids(self, user_id: int) -> list[str]:
        """返回用户额外分配的菜单 ID 列表。"""
        return list(
            self._session.scalars(
                select(UserMenu.menu_id).where(UserMenu.user_id == user_id)
            )
        )

    def replace_user_menus(self, user_id: int, menu_ids: list[str]) -> None:
        """全量替换用户的额外菜单关联。"""
        self._session.execute(delete(UserMenu).where(UserMenu.user_id == user_id))
        for mid in menu_ids:
            self._session.add(UserMenu(user_id=user_id, menu_id=mid))
        self._session.flush()

    # --- session ---
    def add_session(self, session: AuthSession) -> AuthSession:
        """新增认证会话并 flush。"""
        self._session.add(session)
        self._session.flush()
        return session

    def get_session(self, session_id: int) -> AuthSession | None:
        """按主键查询认证会话。"""
        return self._session.get(AuthSession, session_id)

    def revoke_session(self, session: AuthSession) -> None:
        """撤销单个认证会话。"""
        session.revoked_at = now_app()
        self._session.flush()

    def revoke_user_sessions(self, user_id: int) -> None:
        """撤销指定用户的全部有效会话。"""
        now = now_app()
        rows = self._session.scalars(
            select(AuthSession).where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
        )
        for row in rows:
            row.revoked_at = now
        self._session.flush()

    # --- audit ---
    def add_audit(self, log: AuditLog) -> None:
        """写入一条审计日志。"""
        self._session.add(log)
        self._session.flush()
