"""认证与 RBAC 初始数据幂等种子（菜单、角色、根组织）。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.dao.models.auth_rbac import Menu, Org, Role
from app.dao.repositories.auth_repository import AuthRbacRepository

_DEFAULT_MENUS: list[tuple[str, str, str, str | None, int]] = [
    ("chat", "对话台", "/chat", "chat", 10),
    ("sites", "站点清单", "/sites", "list", 20),
    ("documents", "文档与任务", "/documents", "document", 30),
    ("settings", "应用配置", "/settings", "setting", 40),
    ("menus", "菜单管理", "/menus", "menu", 50),
    ("orgs", "组织管理", "/orgs", "menu", 60),
    ("roles", "角色管理", "/roles", "menu", 70),
    ("users", "账号管理", "/users", "menu", 80),
]

_ROLE_MENUS: dict[str, list[str]] = {
    "user": ["chat"],
    "ops": ["chat", "sites", "documents", "settings"],
    "admin": [
        "chat",
        "sites",
        "documents",
        "settings",
        "menus",
        "orgs",
        "roles",
        "users",
    ],
}


def ensure_auth_seed(session: Session) -> None:
    """幂等写入默认菜单、系统角色及根组织；已存在则更新元数据。"""
    repo = AuthRbacRepository(session)
    for mid, title, path, icon, sort in _DEFAULT_MENUS:
        existing = repo.get_menu(mid)
        if existing is None:
            repo.add_menu(
                Menu(
                    id=mid,
                    title=title,
                    path=path,
                    icon=icon,
                    sort_order=sort,
                    assignable=True,
                    status="active",
                )
            )
        else:
            existing.title = title
            existing.path = path
            existing.icon = icon
            existing.sort_order = sort
            existing.status = "active"

    role_defs = [
        ("user", "普通用户", "默认可访问对话台"),
        ("ops", "运维", "对话台 + 站点/文档等运维菜单"),
        ("admin", "管理员", "含组织/角色/账号等管理菜单"),
    ]
    for code, name, desc in role_defs:
        role = repo.get_role_by_code(code)
        if role is None:
            role = repo.add_role(
                Role(
                    code=code,
                    name=name,
                    description=desc,
                    is_system=True,
                    status="active",
                )
            )
        repo.replace_role_menus(role.id, _ROLE_MENUS[code])

    orgs = repo.list_orgs()
    if not any(o.code == "ROOT" for o in orgs):
        repo.add_org(
            Org(
                parent_id=None,
                code="ROOT",
                name="根组织",
                sort_order=0,
                status="active",
                remark="默认根节点",
            )
        )
    session.commit()
