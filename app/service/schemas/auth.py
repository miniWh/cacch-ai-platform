"""认证与 RBAC 相关 Pydantic 请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class LoginRequest(BaseModel):
    """登录请求体。"""

    mobile: str = Field(min_length=1, max_length=32, description="手机号")
    password: str = Field(min_length=1, max_length=128, description="密码")
    remember_today: bool = Field(default=False, description="今日有效（至当日 23:59）")


class ChangePasswordRequest(BaseModel):
    """修改密码请求体。"""

    old_password: str = Field(min_length=1, max_length=128, description="原密码")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")


class AuthUserOut(BaseModel):
    """当前用户基本信息与菜单权限。"""

    id: int
    staff_no: str
    mobile: str
    name: str
    email: str | None
    must_change_password: bool
    menu_ids: list[str]


class LoginOut(BaseModel):
    """登录成功响应。"""

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
    """菜单项输出。"""

    id: str
    title: str
    path: str
    icon: str | None
    sort_order: int
    status: str

    model_config = {"from_attributes": True}


class MenuListOut(BaseModel):
    """菜单列表响应。"""

    items: list[MenuOut]


class OrgCreate(BaseModel):
    """创建组织请求体。"""

    parent_id: int | None = Field(default=None, description="父组织 ID")
    code: str | None = Field(default=None, max_length=64, description="组织编码")
    name: str = Field(min_length=1, max_length=128, description="组织名称")
    sort_order: int = Field(default=0, description="排序")
    status: str = Field(default="active", description="状态：active / disabled")
    remark: str | None = Field(default=None, max_length=512, description="备注")


class OrgUpdate(BaseModel):
    """更新组织请求体（部分字段）。"""

    parent_id: int | None = None
    code: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=128)
    sort_order: int | None = None
    status: str | None = None
    remark: str | None = Field(default=None, max_length=512)


class OrgOut(BaseModel):
    """组织详情输出。"""

    id: int
    parent_id: int | None
    code: str | None
    name: str
    sort_order: int
    status: str
    remark: str | None

    model_config = {"from_attributes": True}


class OrgListOut(BaseModel):
    """组织列表响应。"""

    items: list[OrgOut]


class RoleCreate(BaseModel):
    """创建角色请求体。"""

    code: str = Field(min_length=1, max_length=64, description="角色编码")
    name: str = Field(min_length=1, max_length=64, description="角色名称")
    description: str | None = Field(default=None, max_length=256, description="描述")
    menu_ids: list[str] = Field(default_factory=list, description="绑定的菜单 ID 列表")


class RoleUpdate(BaseModel):
    """更新角色请求体（部分字段）。"""

    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=256)
    status: str | None = None
    menu_ids: list[str] | None = None


class RoleOut(BaseModel):
    """角色详情输出。"""

    id: int
    code: str
    name: str
    description: str | None
    status: str
    menu_ids: list[str]


class RoleListOut(BaseModel):
    """角色列表响应。"""

    items: list[RoleOut]


class HrPreviewRequest(BaseModel):
    """HR 人员预览请求体。"""

    mobile: str = Field(min_length=1, max_length=32, description="手机号")


class HrPreviewOut(BaseModel):
    """HR 人员预览响应。"""

    staff_no: str
    mobile: str
    name: str
    email: str | None
    staff_status: str


class UserCreate(BaseModel):
    """创建用户（开户）请求体。"""

    mobile: str = Field(min_length=1, max_length=32, description="HR 手机号")
    org_id: int = Field(gt=0, description="挂靠组织 ID")
    role_id: int | None = Field(
        default=None, description="角色 ID（可选，用于继承菜单）"
    )
    menu_ids: list[str] | None = Field(default=None, description="直接分配的菜单 ID")
    password: str | None = Field(default=None, max_length=128, description="初始密码")
    generate_password: bool = Field(default=False, description="是否随机生成密码")
    remark: str | None = Field(default=None, max_length=512, description="备注")


class UserUpdate(BaseModel):
    """更新用户请求体（部分字段）。"""

    org_id: int | None = Field(default=None, gt=0)
    role_id: int | None = None
    menu_ids: list[str] | None = None
    status: str | None = None
    remark: str | None = Field(default=None, max_length=512)


class ResetPasswordRequest(BaseModel):
    """重置密码请求体。"""

    password: str | None = Field(default=None, max_length=128, description="新密码")
    generate_password: bool = Field(default=True, description="是否随机生成密码")


class UserOut(BaseModel):
    """用户详情输出。"""

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
    """创建用户成功响应（含明文初始密码）。"""

    user: UserOut
    plain_password: str


class ResetPasswordOut(BaseModel):
    """重置密码成功响应（含明文新密码）。"""

    plain_password: str


class UserListOut(BaseModel):
    """用户列表响应。"""

    items: list[UserOut]
    total: int


class BootstrapAdminRequest(BaseModel):
    """首次引导创建管理员请求体（须服务令牌）。"""

    mobile: str = Field(min_length=1, max_length=32, description="HR 手机号")
    password: str = Field(min_length=8, max_length=128, description="初始密码")
    org_id: int | None = Field(default=None, description="组织 ID，默认 ROOT")
