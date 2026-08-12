"""认证 HTTP API 路由。"""

from fastapi import APIRouter, Depends, Header, Query, Request

from app.common.dto import ok
from app.common.exceptions import UnauthorizedError
from app.service.auth_service import AuthService, CurrentUser
from app.service.schemas.auth import (
    BootstrapAdminRequest,
    ChangePasswordRequest,
    HrPreviewRequest,
    LoginRequest,
    OrgCreate,
    OrgUpdate,
    ResetPasswordRequest,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserUpdate,
)
from app.web.config import Settings, get_settings
from app.web.middleware.auth import client_meta, get_auth_service, require_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _require_service_token(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """内部依赖：校验请求携带平台服务令牌。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.api_auth_token:
        raise UnauthorizedError("service token required")


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """用户登录，返回访问令牌与用户资料。"""
    ip, ua = client_meta(request)
    data = service.login(payload, client_ip=ip, user_agent=ua)
    return ok(data.model_dump(mode="json"))


@router.post("/logout")
def logout(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """登出当前会话。"""
    service.logout(user)
    return ok({"ok": True})


@router.get("/me")
def me(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """获取当前登录用户信息。"""
    data = service.me(user)
    return ok(data.model_dump(mode="json"))


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """修改当前用户密码。"""
    service.change_password(user, payload)
    return ok({"ok": True})


@router.post("/bootstrap", dependencies=[Depends(_require_service_token)])
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """首次引导创建管理员（须服务令牌，系统无用户时可用）。"""
    data = service.bootstrap_admin(payload)
    return ok(data.model_dump(mode="json"))


@router.get("/menus")
def list_menus(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """列出全部可分配菜单。"""
    _ = user
    data = service.list_menus()
    return ok(data.model_dump(mode="json"))


@router.get("/orgs")
def list_orgs(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """列出组织（需组织或用户管理菜单权限）。"""
    user.require_business_access()
    if not user.is_service and not (
        "orgs" in user.menu_ids or "users" in user.menu_ids
    ):
        from app.common.exceptions import ForbiddenError

        raise ForbiddenError("missing menu permission: orgs")
    data = service.list_orgs()
    return ok(data.model_dump(mode="json"))


@router.get("/roles")
def list_roles(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """列出角色（需角色或用户管理菜单权限）。"""
    user.require_business_access()
    if not user.is_service and not (
        "roles" in user.menu_ids or "users" in user.menu_ids
    ):
        from app.common.exceptions import ForbiddenError

        raise ForbiddenError("missing menu permission: roles")
    data = service.list_roles()
    return ok(data.model_dump(mode="json"))


@router.post("/orgs")
def create_org(
    payload: OrgCreate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """创建组织。"""
    data = service.create_org(user, payload)
    return ok(data.model_dump(mode="json"))


@router.patch("/orgs/{org_id}")
def update_org(
    org_id: int,
    payload: OrgUpdate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """更新指定组织。"""
    data = service.update_org(user, org_id, payload)
    return ok(data.model_dump(mode="json"))


@router.post("/roles")
def create_role(
    payload: RoleCreate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """创建角色。"""
    data = service.create_role(user, payload)
    return ok(data.model_dump(mode="json"))


@router.patch("/roles/{role_id}")
def update_role(
    role_id: int,
    payload: RoleUpdate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """更新指定角色。"""
    data = service.update_role(user, role_id, payload)
    return ok(data.model_dump(mode="json"))


@router.get("/users")
def list_users(
    keyword: str | None = Query(default=None),
    org_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """分页/筛选列出用户账号。"""
    data = service.list_users(user, keyword=keyword, org_id=org_id, status=status)
    return ok(data.model_dump(mode="json"))


@router.post("/users/preview-hr")
def preview_hr(
    payload: HrPreviewRequest,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """开户前预览 HR 人员信息。"""
    data = service.preview_hr(user, payload.mobile)
    return ok(data.model_dump(mode="json"))


@router.post("/users")
def create_user(
    payload: UserCreate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """为在职人员创建平台账号。"""
    data = service.create_user(user, payload)
    return ok(data.model_dump(mode="json"))


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """更新指定用户。"""
    data = service.update_user(user, user_id, payload)
    return ok(data.model_dump(mode="json"))


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """管理员重置用户密码。"""
    data = service.reset_password(user, user_id, payload)
    return ok(data.model_dump(mode="json"))
