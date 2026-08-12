"""Auth / RBAC Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class LoginRequest(BaseModel):
    mobile: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)
    remember_today: bool = False


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AuthUserOut(BaseModel):
    id: int
    staff_no: str
    mobile: str
    name: str
    email: str | None
    must_change_password: bool
    menu_ids: list[str]


class LoginOut(BaseModel):
    access_token: str
    expires_at: datetime
    must_change_password: bool
    user: AuthUserOut

    @field_serializer("expires_at", when_used="json")
    def _ser_exp(self, value: datetime) -> str:
        from app.common.timeutil import to_app_tz

        converted = to_app_tz(value)
        return converted.isoformat() if converted else ""


class MenuOut(BaseModel):
    id: str
    title: str
    path: str
    icon: str | None
    sort_order: int
    status: str

    model_config = {"from_attributes": True}


class MenuListOut(BaseModel):
    items: list[MenuOut]


class OrgCreate(BaseModel):
    parent_id: int | None = None
    code: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    sort_order: int = 0
    status: str = "active"
    remark: str | None = Field(default=None, max_length=512)


class OrgUpdate(BaseModel):
    parent_id: int | None = None
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    sort_order: int | None = None
    status: str | None = None
    remark: str | None = Field(default=None, max_length=512)


class OrgOut(BaseModel):
    id: int
    parent_id: int | None
    code: str | None
    name: str
    sort_order: int
    status: str
    remark: str | None

    model_config = {"from_attributes": True}


class OrgListOut(BaseModel):
    items: list[OrgOut]


class RoleCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=256)
    menu_ids: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=256)
    status: str | None = None
    menu_ids: list[str] | None = None


class RoleOut(BaseModel):
    id: int
    code: str
    name: str
    description: str | None
    status: str
    menu_ids: list[str]


class RoleListOut(BaseModel):
    items: list[RoleOut]


class HrPreviewRequest(BaseModel):
    mobile: str = Field(min_length=1, max_length=32)


class HrPreviewOut(BaseModel):
    staff_no: str
    mobile: str
    name: str
    email: str | None
    staff_status: str


class UserCreate(BaseModel):
    mobile: str = Field(min_length=1, max_length=32)
    org_id: int = Field(gt=0)
    role_id: int | None = None
    menu_ids: list[str] | None = None
    password: str | None = Field(default=None, max_length=128)
    generate_password: bool = False
    remark: str | None = Field(default=None, max_length=512)


class UserUpdate(BaseModel):
    org_id: int | None = Field(default=None, gt=0)
    role_id: int | None = None
    menu_ids: list[str] | None = None
    status: str | None = None
    remark: str | None = Field(default=None, max_length=512)


class ResetPasswordRequest(BaseModel):
    password: str | None = Field(default=None, max_length=128)
    generate_password: bool = True


class UserOut(BaseModel):
    id: int
    staff_no: str
    mobile: str
    name: str
    email: str | None
    staff_status: str
    org_id: int
    org_name: str | None = None
    role_id: int | None
    role_name: str | None = None
    status: str
    must_change_password: bool
    menu_ids: list[str]
    last_login_at: datetime | None = None

    @field_serializer("last_login_at", when_used="json")
    def _ser_dt(self, value: datetime | None) -> str | None:
        from app.common.timeutil import to_app_tz

        converted = to_app_tz(value)
        return converted.isoformat() if converted else None


class UserCreateOut(BaseModel):
    user: UserOut
    plain_password: str


class ResetPasswordOut(BaseModel):
    plain_password: str


class UserListOut(BaseModel):
    items: list[UserOut]
    total: int


class BootstrapAdminRequest(BaseModel):
    mobile: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    org_id: int | None = None
