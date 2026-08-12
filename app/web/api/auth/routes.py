"""Auth HTTP APIs."""

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
    ip, ua = client_meta(request)
    data = service.login(payload, client_ip=ip, user_agent=ua)
    return ok(data.model_dump(mode="json"))


@router.post("/logout")
def logout(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    service.logout(user)
    return ok({"ok": True})


@router.get("/me")
def me(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.me(user)
    return ok(data.model_dump(mode="json"))


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    service.change_password(user, payload)
    return ok({"ok": True})


@router.post("/bootstrap", dependencies=[Depends(_require_service_token)])
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.bootstrap_admin(payload)
    return ok(data.model_dump(mode="json"))


@router.get("/menus")
def list_menus(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    _ = user
    data = service.list_menus()
    return ok(data.model_dump(mode="json"))


@router.get("/orgs")
def list_orgs(
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
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
    data = service.create_org(user, payload)
    return ok(data.model_dump(mode="json"))


@router.patch("/orgs/{org_id}")
def update_org(
    org_id: int,
    payload: OrgUpdate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.update_org(user, org_id, payload)
    return ok(data.model_dump(mode="json"))


@router.post("/roles")
def create_role(
    payload: RoleCreate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.create_role(user, payload)
    return ok(data.model_dump(mode="json"))


@router.patch("/roles/{role_id}")
def update_role(
    role_id: int,
    payload: RoleUpdate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
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
    data = service.list_users(user, keyword=keyword, org_id=org_id, status=status)
    return ok(data.model_dump(mode="json"))


@router.post("/users/preview-hr")
def preview_hr(
    payload: HrPreviewRequest,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.preview_hr(user, payload.mobile)
    return ok(data.model_dump(mode="json"))


@router.post("/users")
def create_user(
    payload: UserCreate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.create_user(user, payload)
    return ok(data.model_dump(mode="json"))


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.update_user(user, user_id, payload)
    return ok(data.model_dump(mode="json"))


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    user: CurrentUser = Depends(require_user),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    data = service.reset_password(user, user_id, payload)
    return ok(data.model_dump(mode="json"))
