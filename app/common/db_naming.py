"""Database naming and AI-table isolation rules."""

# Shared DB 中所有本平台物理表统一前缀，避免与其他业务表冲突。
AI_TABLE_PREFIX = "cacch_ai_"

# 当前已登记的 AI 表（不含前缀的逻辑名 → 物理名在模型 __tablename__）
AI_PHYSICAL_TABLES: frozenset[str] = frozenset(
    {
        f"{AI_TABLE_PREFIX}knowledge_base",
        f"{AI_TABLE_PREFIX}source_site",
        f"{AI_TABLE_PREFIX}chat_session",
        f"{AI_TABLE_PREFIX}chat_message",
        f"{AI_TABLE_PREFIX}org",
        f"{AI_TABLE_PREFIX}menu",
        f"{AI_TABLE_PREFIX}role",
        f"{AI_TABLE_PREFIX}role_menu",
        f"{AI_TABLE_PREFIX}user",
        f"{AI_TABLE_PREFIX}user_menu",
        f"{AI_TABLE_PREFIX}auth_session",
        f"{AI_TABLE_PREFIX}audit_log",
    }
)


def is_ai_table(table_name: str) -> bool:
    return table_name.startswith(AI_TABLE_PREFIX)


def assert_only_ai_tables(table_names: list[str] | set[str] | frozenset[str]) -> None:
    """Raise if metadata contains tables outside the AI allowlist."""
    unexpected = sorted({n for n in table_names if not is_ai_table(n)})
    if unexpected:
        raise RuntimeError(
            "禁止对非 AI 表执行结构变更或注册到 ORM metadata："
            f"{', '.join(unexpected)}；仅允许前缀 `{AI_TABLE_PREFIX}`"
        )
    unknown = sorted(set(table_names) - AI_PHYSICAL_TABLES)
    if unknown:
        # 新表需先加入 AI_PHYSICAL_TABLES 白名单
        raise RuntimeError(
            "发现未列入 AI 表白名单的表，请先在 "
            f"app.common.db_naming.AI_PHYSICAL_TABLES 登记：{', '.join(unknown)}"
        )
