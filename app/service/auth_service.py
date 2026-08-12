"""认证与 RBAC 领域服务：登录、密码、组织/角色/用户管理。"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.common.access_token import (
    hash_refresh_token,
    issue_access_token,
    parse_access_token,
)
from app.common.exceptions import (
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationAppError,
)
from app.common.password import (
    generate_random_password,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.common.timeutil import app_zone, now_app
from app.dao.models.auth_rbac import AuditLog, AuthSession, Org, Role, UserAccount
from app.dao.repositories.auth_repository import AuthRbacRepository
from app.dao.repositories.hr_person_repository import (
    PersonDetailRepository,
    PersonDetailRow,
)
from app.service.schemas.auth import (
    AuthUserOut,
    BootstrapAdminRequest,
    ChangePasswordRequest,
    HrPreviewOut,
    LoginOut,
    LoginRequest,
    MenuListOut,
    MenuOut,
    OrgCreate,
    OrgListOut,
    OrgOut,
    OrgUpdate,
    ResetPasswordOut,
    ResetPasswordRequest,
    RoleCreate,
    RoleListOut,
    RoleOut,
    RoleUpdate,
    UserCreate,
    UserCreateOut,
    UserListOut,
    UserOut,
    UserUpdate,
)
from app.web.config import Settings, get_settings

_IN_SERVICE = "IN_SERVICE"
_MAX_FAILED = 5
_LOCK_MINUTES = 15
_ADMIN_MENUS = frozenset({"menus", "orgs", "roles", "users"})


@dataclass
class CurrentUser:
    """当前请求上下文中的已认证用户（或服务账号）。"""

    id: int
    staff_no: str
    mobile: str
    name: str
    email: str | None
    must_change_password: bool
    menu_ids: list[str]
    token_version: int
    session_id: int | None = None
    is_service: bool = False

    def require_menu(self, menu_id: str) -> None:
        """校验当前用户拥有指定菜单权限；服务账号跳过。"""
        if self.is_service:
            return
        if menu_id not in self.menu_ids:
            raise ForbiddenError(f"missing menu permission: {menu_id}")

    def require_business_access(self) -> None:
        """校验用户已完成强制改密，可访问业务功能；服务账号跳过。"""
        if self.is_service:
            return
        if self.must_change_password:
            raise ForbiddenError("must change password before continuing")


class AuthService:
    """认证、会话、组织/角色/用户及审计日志业务逻辑。"""

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        *,
        hr: PersonDetailRepository | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._repo = AuthRbacRepository(session)
        self._hr = hr or PersonDetailRepository(session)

    # ------------------------------------------------------------------ login
    def login(
        self,
        payload: LoginRequest,
        *,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> LoginOut:
        """手机号密码登录，签发访问令牌并创建会话。"""
        user = self._repo.get_user_by_mobile(payload.mobile.strip())
        if user is None:
            self._audit(
                None, "login_fail", success=False, detail={"reason": "unknown_mobile"}
            )
            raise UnauthorizedError("账号或密码错误")

        if user.locked_until and user.locked_until > now_app():
            raise UnauthorizedError("账号已锁定，请稍后再试")

        if user.status != "active":
            raise UnauthorizedError("账号已停用")

        org = self._repo.get_org(user.org_id)
        if org is None or org.status != "active":
            raise UnauthorizedError("所属组织不可用")

        if not verify_password(payload.password, user.password_hash):
            user.failed_login_count += 1
            if user.failed_login_count >= _MAX_FAILED:
                user.locked_until = now_app() + timedelta(minutes=_LOCK_MINUTES)
                user.failed_login_count = 0
            self._session.commit()
            self._audit(
                user,
                "login_fail",
                success=False,
                detail={"reason": "bad_password"},
                client_ip=client_ip,
            )
            raise UnauthorizedError("账号或密码错误")

        hr_status = self._hr.get_staff_status(user.staff_no)
        if hr_status is not None and hr_status != _IN_SERVICE:
            self._audit(
                user,
                "login_fail",
                success=False,
                detail={"reason": "not_in_service"},
                client_ip=client_ip,
            )
            raise UnauthorizedError("账号非在职状态，无法登录")

        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = now_app()

        expires_at = self._session_expiry(payload.remember_today)
        refresh_raw = secrets.token_urlsafe(32)
        auth_session = self._repo.add_session(
            AuthSession(
                user_id=user.id,
                refresh_token_hash=hash_refresh_token(refresh_raw),
                token_version=user.token_version,
                remember_today=payload.remember_today,
                expires_at=expires_at,
                user_agent=(user_agent or "")[:512] or None,
                client_ip=client_ip,
            )
        )
        token = issue_access_token(
            secret=self._token_secret(),
            user_id=user.id,
            session_id=auth_session.id,
            token_version=user.token_version,
            expires_at_ts=int(expires_at.replace(tzinfo=app_zone()).timestamp()),
        )
        menu_ids = self._repo.list_user_menu_ids(user.id)
        self._session.commit()
        self._audit(user, "login_ok", client_ip=client_ip)
        self._session.commit()
        return LoginOut(
            access_token=token,
            expires_at=expires_at,
            must_change_password=user.must_change_password,
            user=AuthUserOut(
                id=user.id,
                staff_no=user.staff_no,
                mobile=user.mobile,
                name=user.name,
                email=user.email,
                must_change_password=user.must_change_password,
                menu_ids=menu_ids,
            ),
        )

    def logout(self, current: CurrentUser) -> None:
        """撤销当前会话并记录登出审计。"""
        if current.is_service or current.session_id is None:
            return
        session = self._repo.get_session(current.session_id)
        if session is not None and session.revoked_at is None:
            self._repo.revoke_session(session)
        user = self._repo.get_user(current.id)
        if user is not None:
            self._audit(user, "logout")
        self._session.commit()

    def me(self, current: CurrentUser) -> AuthUserOut:
        """返回当前登录用户资料与菜单权限。"""
        if current.is_service:
            return AuthUserOut(
                id=0,
                staff_no="service",
                mobile="",
                name="服务账号",
                email=None,
                must_change_password=False,
                menu_ids=list(_ADMIN_MENUS)
                + ["chat", "sites", "documents", "settings"],
            )
        user = self._repo.get_user(current.id)
        if user is None:
            raise UnauthorizedError("user not found")
        return AuthUserOut(
            id=user.id,
            staff_no=user.staff_no,
            mobile=user.mobile,
            name=user.name,
            email=user.email,
            must_change_password=user.must_change_password,
            menu_ids=self._repo.list_user_menu_ids(user.id),
        )

    def change_password(
        self, current: CurrentUser, payload: ChangePasswordRequest
    ) -> None:
        """用户修改密码，并使全部旧会话失效。"""
        if current.is_service:
            raise ValidationAppError("service account cannot change password")
        user = self._repo.get_user(current.id)
        if user is None:
            raise UnauthorizedError("user not found")
        if not verify_password(payload.old_password, user.password_hash):
            raise ValidationAppError("原密码不正确")
        err = validate_password_strength(payload.new_password)
        if err:
            raise ValidationAppError(err)
        if payload.old_password == payload.new_password:
            raise ValidationAppError("新密码不能与旧密码相同")
        user.password_hash = hash_password(payload.new_password)
        user.must_change_password = False
        user.password_changed_at = now_app()
        user.token_version += 1
        self._repo.revoke_user_sessions(user.id)
        self._audit(user, "password_change")
        self._session.commit()

    def resolve_bearer(self, token: str) -> CurrentUser:
        """解析 Bearer 令牌：服务令牌或用户 JWT，返回 CurrentUser。"""
        if token == self._settings.api_auth_token:
            return CurrentUser(
                id=0,
                staff_no="service",
                mobile="",
                name="服务账号",
                email=None,
                must_change_password=False,
                menu_ids=[],
                token_version=0,
                is_service=True,
            )
        claims = parse_access_token(token, secret=self._token_secret())
        if claims is None:
            raise UnauthorizedError("invalid token")
        user = self._repo.get_user(claims.user_id)
        if user is None or user.status != "active":
            raise UnauthorizedError("invalid token")
        if user.token_version != claims.token_version:
            raise UnauthorizedError("token revoked")
        session = self._repo.get_session(claims.session_id)
        if (
            session is None
            or session.revoked_at is not None
            or session.expires_at < now_app()
            or session.user_id != user.id
        ):
            raise UnauthorizedError("session expired")
        org = self._repo.get_org(user.org_id)
        if org is None or org.status != "active":
            raise UnauthorizedError("org disabled")
        return CurrentUser(
            id=user.id,
            staff_no=user.staff_no,
            mobile=user.mobile,
            name=user.name,
            email=user.email,
            must_change_password=user.must_change_password,
            menu_ids=self._repo.list_user_menu_ids(user.id),
            token_version=user.token_version,
            session_id=session.id,
        )

    # ------------------------------------------------------------------ menus
    def list_menus(self) -> MenuListOut:
        """列出全部启用中的可分配菜单。"""
        items = [
            MenuOut.model_validate(m) for m in self._repo.list_menus(active_only=True)
        ]
        return MenuListOut(items=items)

    # ------------------------------------------------------------------ orgs
    def list_orgs(self) -> OrgListOut:
        """列出全部组织。"""
        return OrgListOut(
            items=[OrgOut.model_validate(o) for o in self._repo.list_orgs()]
        )

    def create_org(self, current: CurrentUser, payload: OrgCreate) -> OrgOut:
        """创建组织节点。"""
        current.require_menu("orgs")
        current.require_business_access()
        if (
            payload.parent_id is not None
            and self._repo.get_org(payload.parent_id) is None
        ):
            raise NotFoundError("parent org not found")
        if payload.status not in ("active", "disabled"):
            raise ValidationAppError("invalid org status")
        org = self._repo.add_org(
            Org(
                parent_id=payload.parent_id,
                code=payload.code,
                name=payload.name.strip(),
                sort_order=payload.sort_order,
                status=payload.status,
                remark=payload.remark,
            )
        )
        self._audit(current, "org_create", target_type="org", target_id=str(org.id))
        self._session.commit()
        self._session.refresh(org)
        return OrgOut.model_validate(org)

    def update_org(
        self, current: CurrentUser, org_id: int, payload: OrgUpdate
    ) -> OrgOut:
        """部分更新组织信息。"""
        current.require_menu("orgs")
        current.require_business_access()
        org = self._repo.get_org(org_id)
        if org is None:
            raise NotFoundError("org not found")
        data = payload.model_dump(exclude_unset=True)
        if "status" in data and data["status"] not in ("active", "disabled"):
            raise ValidationAppError("invalid org status")
        if "parent_id" in data and data["parent_id"] is not None:
            if data["parent_id"] == org_id:
                raise ValidationAppError("org cannot be its own parent")
            if self._repo.get_org(data["parent_id"]) is None:
                raise NotFoundError("parent org not found")
        for key, value in data.items():
            setattr(
                org,
                key,
                value.strip() if isinstance(value, str) and key == "name" else value,
            )
        self._audit(current, "org_update", target_type="org", target_id=str(org.id))
        self._session.commit()
        self._session.refresh(org)
        return OrgOut.model_validate(org)

    # ------------------------------------------------------------------ roles
    def list_roles(self) -> RoleListOut:
        """列出全部角色及其菜单权限。"""
        items: list[RoleOut] = []
        for role in self._repo.list_roles():
            items.append(
                RoleOut(
                    id=role.id,
                    code=role.code,
                    name=role.name,
                    description=role.description,
                    status=role.status,
                    menu_ids=self._repo.list_role_menu_ids(role.id),
                )
            )
        return RoleListOut(items=items)

    def create_role(self, current: CurrentUser, payload: RoleCreate) -> RoleOut:
        """创建自定义角色并绑定菜单。"""
        current.require_menu("roles")
        current.require_business_access()
        if self._repo.get_role_by_code(payload.code.strip()) is not None:
            raise ValidationAppError("role code already exists")
        menu_ids = self._validate_menu_ids(payload.menu_ids)
        role = self._repo.add_role(
            Role(
                code=payload.code.strip(),
                name=payload.name.strip(),
                description=payload.description,
                is_system=False,
                status="active",
            )
        )
        self._repo.replace_role_menus(role.id, menu_ids)
        self._audit(current, "role_create", target_type="role", target_id=str(role.id))
        self._session.commit()
        return RoleOut(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            status=role.status,
            menu_ids=menu_ids,
        )

    def update_role(
        self, current: CurrentUser, role_id: int, payload: RoleUpdate
    ) -> RoleOut:
        """部分更新角色及菜单绑定。"""
        current.require_menu("roles")
        current.require_business_access()
        role = self._repo.get_role(role_id)
        if role is None:
            raise NotFoundError("role not found")
        data = payload.model_dump(exclude_unset=True)
        menu_ids = data.pop("menu_ids", None)
        if "status" in data and data["status"] not in ("active", "disabled"):
            raise ValidationAppError("invalid role status")
        for key, value in data.items():
            setattr(role, key, value)
        if menu_ids is not None:
            validated = self._validate_menu_ids(menu_ids)
            self._repo.replace_role_menus(role.id, validated)
        else:
            validated = self._repo.list_role_menu_ids(role.id)
        self._audit(current, "role_update", target_type="role", target_id=str(role.id))
        self._session.commit()
        self._session.refresh(role)
        return RoleOut(
            id=role.id,
            code=role.code,
            name=role.name,
            description=role.description,
            status=role.status,
            menu_ids=validated,
        )

    # ------------------------------------------------------------------ users
    def preview_hr(self, current: CurrentUser, mobile: str) -> HrPreviewOut:
        """根据手机号预览 HR 人员信息，用于开户前校验。"""
        current.require_menu("users")
        current.require_business_access()
        person = self._require_hr_person(mobile.strip())
        return HrPreviewOut(
            staff_no=person.staff_no,
            mobile=person.mobile,
            name=person.name,
            email=person.email,
            staff_status=person.staff_status,
        )

    def list_users(
        self,
        current: CurrentUser,
        *,
        keyword: str | None = None,
        org_id: int | None = None,
        status: str | None = None,
    ) -> UserListOut:
        """按关键字、组织、状态筛选用户列表。"""
        current.require_menu("users")
        current.require_business_access()
        users = self._repo.list_users(keyword=keyword, org_id=org_id, status=status)
        return UserListOut(
            items=[self._user_out(u) for u in users],
            total=len(users),
        )

    def create_user(self, current: CurrentUser, payload: UserCreate) -> UserCreateOut:
        """为在职 HR 人员开户并分配组织、角色与菜单。"""
        current.require_menu("users")
        current.require_business_access()
        person = self._require_hr_person(payload.mobile.strip())
        if person.staff_status != _IN_SERVICE:
            raise ValidationAppError("仅支持在职人员开户（staffStatus=IN_SERVICE）")
        if self._repo.get_user_by_mobile(person.mobile) is not None:
            raise ValidationAppError("该手机号已开户")
        if self._repo.get_user_by_staff_no(person.staff_no) is not None:
            raise ValidationAppError("该用户 ID 已开户")
        org = self._repo.get_org(payload.org_id)
        if org is None:
            raise NotFoundError("org not found")
        if org.status != "active":
            raise ValidationAppError("不能挂靠已停用组织")

        menu_ids = payload.menu_ids
        if menu_ids is None and payload.role_id is not None:
            role = self._repo.get_role(payload.role_id)
            if role is None or role.status != "active":
                raise NotFoundError("role not found")
            menu_ids = self._repo.list_role_menu_ids(role.id)
        if menu_ids is None:
            menu_ids = ["chat"]
        menu_ids = self._validate_menu_ids(menu_ids)

        plain = self._resolve_new_password(payload.password, payload.generate_password)
        actor_id = None if current.is_service else current.id
        user = self._repo.add_user(
            UserAccount(
                staff_no=person.staff_no,
                mobile=person.mobile,
                name=person.name,
                email=person.email,
                staff_status=person.staff_status,
                org_id=payload.org_id,
                role_id=payload.role_id,
                password_hash=hash_password(plain),
                must_change_password=True,
                status="active",
                created_by=actor_id,
                remark=payload.remark,
            )
        )
        self._repo.replace_user_menus(user.id, menu_ids)
        self._audit(
            current,
            "user_create",
            target_type="user",
            target_id=str(user.id),
            detail={"staff_no": user.staff_no},
        )
        self._session.commit()
        self._session.refresh(user)
        return UserCreateOut(user=self._user_out(user), plain_password=plain)

    def update_user(
        self, current: CurrentUser, user_id: int, payload: UserUpdate
    ) -> UserOut:
        """部分更新用户组织、角色、菜单或状态。"""
        current.require_menu("users")
        current.require_business_access()
        user = self._repo.get_user(user_id)
        if user is None:
            raise NotFoundError("user not found")
        data = payload.model_dump(exclude_unset=True)
        menu_ids = data.pop("menu_ids", None)
        if "status" in data:
            if data["status"] not in ("active", "disabled"):
                raise ValidationAppError("invalid user status")
            if data["status"] == "disabled":
                user.token_version += 1
                self._repo.revoke_user_sessions(user.id)
        if "org_id" in data:
            org = self._repo.get_org(data["org_id"])
            if org is None:
                raise NotFoundError("org not found")
            if org.status != "active" and data.get("status", user.status) == "active":
                raise ValidationAppError("不能挂靠已停用组织")
            user.org_id = data["org_id"]
        if "role_id" in data:
            if data["role_id"] is not None:
                role = self._repo.get_role(data["role_id"])
                if role is None:
                    raise NotFoundError("role not found")
            user.role_id = data["role_id"]
            if menu_ids is None and data["role_id"] is not None:
                menu_ids = self._repo.list_role_menu_ids(data["role_id"])
        if "remark" in data:
            user.remark = data["remark"]
        if "status" in data:
            user.status = data["status"]
        if menu_ids is not None:
            self._repo.replace_user_menus(user.id, self._validate_menu_ids(menu_ids))
        self._audit(current, "user_update", target_type="user", target_id=str(user.id))
        self._session.commit()
        self._session.refresh(user)
        return self._user_out(user)

    def reset_password(
        self, current: CurrentUser, user_id: int, payload: ResetPasswordRequest
    ) -> ResetPasswordOut:
        """管理员重置用户密码并强制下次登录改密。"""
        current.require_menu("users")
        current.require_business_access()
        user = self._repo.get_user(user_id)
        if user is None:
            raise NotFoundError("user not found")
        plain = self._resolve_new_password(payload.password, payload.generate_password)
        user.password_hash = hash_password(plain)
        user.must_change_password = True
        user.password_changed_at = now_app()
        user.token_version += 1
        self._repo.revoke_user_sessions(user.id)
        self._audit(
            current, "password_reset", target_type="user", target_id=str(user.id)
        )
        self._session.commit()
        return ResetPasswordOut(plain_password=plain)

    def bootstrap_admin(self, payload: BootstrapAdminRequest) -> UserCreateOut:
        """系统无用户时创建首个管理员；调用方须使用服务令牌。"""
        if self._repo.count_users() > 0:
            raise ValidationAppError("users already exist; bootstrap disabled")
        person = self._require_hr_person(payload.mobile.strip())
        if person.staff_status != _IN_SERVICE:
            raise ValidationAppError("仅支持在职人员开户（staffStatus=IN_SERVICE）")
        err = validate_password_strength(payload.password)
        if err:
            raise ValidationAppError(err)
        orgs = self._repo.list_orgs()
        if not orgs:
            raise ValidationAppError("no org seeded")
        org_id = payload.org_id or next(o.id for o in orgs if o.code == "ROOT")
        if self._repo.get_org(org_id) is None:
            raise NotFoundError("org not found")
        admin_role = self._repo.get_role_by_code("admin")
        menu_ids = (
            self._repo.list_role_menu_ids(admin_role.id)
            if admin_role
            else list(_ADMIN_MENUS) + ["chat"]
        )
        user = self._repo.add_user(
            UserAccount(
                staff_no=person.staff_no,
                mobile=person.mobile,
                name=person.name,
                email=person.email,
                staff_status=person.staff_status,
                org_id=org_id,
                role_id=admin_role.id if admin_role else None,
                password_hash=hash_password(payload.password),
                must_change_password=True,
                status="active",
            )
        )
        self._repo.replace_user_menus(user.id, menu_ids)
        self._audit(
            None,
            "bootstrap_admin",
            target_type="user",
            target_id=str(user.id),
            detail={"staff_no": user.staff_no},
        )
        self._session.commit()
        self._session.refresh(user)
        return UserCreateOut(user=self._user_out(user), plain_password=payload.password)

    # ------------------------------------------------------------------ helpers
    def _token_secret(self) -> str:
        """返回 JWT 签名密钥，未配置时回退到 API 服务令牌。"""
        return self._settings.auth_token_secret or self._settings.api_auth_token

    def _session_expiry(self, remember_today: bool) -> datetime:
        """计算会话过期时间：今日有效或固定小时数。"""
        now = now_app()
        if remember_today:
            # Asia/Shanghai natural day end
            zoned = now.replace(tzinfo=app_zone())
            end = zoned.replace(hour=23, minute=59, second=59, microsecond=0)
            return end.replace(tzinfo=None)
        return now + timedelta(hours=self._settings.auth_access_token_hours)

    def _require_hr_person(self, mobile: str) -> PersonDetailRow:
        """按手机号查找 HR 人员，不存在则禁止开户。"""
        person = self._hr.find_by_mobile(mobile)
        if person is None:
            raise ValidationAppError("persondetail 中不存在该手机号，禁止开户")
        return person

    def _validate_menu_ids(self, menu_ids: list[str]) -> list[str]:
        """去重并校验菜单 ID 均存在且启用。"""
        unique = list(dict.fromkeys(menu_ids))
        for mid in unique:
            menu = self._repo.get_menu(mid)
            if menu is None or menu.status != "active":
                raise ValidationAppError(f"invalid menu_id: {mid}")
        return unique

    def _resolve_new_password(
        self, password: str | None, generate_password: bool
    ) -> str:
        """解析新密码：随机生成或校验强度后返回明文。"""
        if generate_password or not password:
            return generate_random_password()
        err = validate_password_strength(password)
        if err:
            raise ValidationAppError(err)
        return password

    def _user_out(self, user: UserAccount) -> UserOut:
        """用户 ORM 实体转 API 输出模型（含组织/角色名称）。"""
        org = self._repo.get_org(user.org_id)
        role = self._repo.get_role(user.role_id) if user.role_id else None
        return UserOut(
            id=user.id,
            staff_no=user.staff_no,
            mobile=user.mobile,
            name=user.name,
            email=user.email,
            staff_status=user.staff_status,
            org_id=user.org_id,
            org_name=org.name if org else None,
            role_id=user.role_id,
            role_name=role.name if role else None,
            status=user.status,
            must_change_password=user.must_change_password,
            menu_ids=self._repo.list_user_menu_ids(user.id),
            last_login_at=user.last_login_at,
        )

    def _audit(
        self,
        actor: CurrentUser | UserAccount | None,
        action: str,
        *,
        success: bool = True,
        target_type: str | None = None,
        target_id: str | None = None,
        detail: dict[str, Any] | None = None,
        client_ip: str | None = None,
    ) -> None:
        """写入审计日志记录。"""
        actor_user_id, actor_staff_no = self._actor_ids(actor)
        self._repo.add_audit(
            AuditLog(
                actor_user_id=actor_user_id,
                actor_staff_no=actor_staff_no,
                action=action,
                target_type=target_type,
                target_id=target_id,
                success=success,
                detail_json=detail,
                client_ip=client_ip,
            )
        )

    @staticmethod
    def _actor_ids(
        actor: CurrentUser | UserAccount | None,
    ) -> tuple[int | None, str | None]:
        """从操作者对象提取 user_id 与 staff_no；服务账号或无操作者返回 None。"""
        if isinstance(actor, CurrentUser):
            if actor.is_service:
                return None, None
            return actor.id, actor.staff_no
        if isinstance(actor, UserAccount):
            return actor.id, actor.staff_no
        return None, None
