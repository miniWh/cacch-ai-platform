"""应用配置：从环境变量与 .env 加载运行时参数。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """平台全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "cacch-ai-platform"
    api_auth_token: str = "dev-token"
    # HMAC secret for user access tokens; empty → fall back to api_auth_token
    auth_token_secret: str = ""
    auth_access_token_hours: int = 8
    database_url: str = "postgresql+psycopg://esb:esb@10.80.86.93:5432/cdb"
    probe_timeout_seconds: float = 8.0
    # 站点抓取（sync 落盘；不写业务库 / 向量库）
    fetch_timeout_seconds: float = 20.0
    fetch_max_bytes: int = 2_000_000
    fetch_user_agent: str = "CACCH-AI-Platform/0.1 (+internal; site-fetch; contact=ops)"
    # 落盘根目录（相对仓库或绝对路径）；结构 kb_{id}/{site_id}/{run_id}/
    crawl_storage_dir: str = "data/crawl"
    # list_harvest 最多跟进的同域列表页数（不含入口页）
    crawl_max_list_pages: int = 20
    # 单次同步最多下载附件数
    crawl_max_attachments: int = 50
    # Open EFSA Questions API：每页条数、最多拉取页数
    crawl_open_efsa_page_size: int = 20
    crawl_open_efsa_max_pages: int = 5
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    default_kb_name: str = "默认知识库"
    default_kb_embedding_model: str = "text-embedding-v4"
    default_kb_embedding_dim: int = 2048
    # 业务时区（写入/展示统一用此时区）
    app_timezone: str = "Asia/Shanghai"

    # --- 阿里云百炼 / 通义（OpenAI 兼容）---
    llm_provider: str = "qwen"
    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = ""
    llm_temperature: float = 0.2
    llm_max_tokens: int | None = None
    llm_timeout_seconds: float = 60.0
    llm_fallback_profile_id: str = ""
    llm_fallback_model: str = ""

    # --- Embedding（默认同 LLM 密钥；维度锁定后勿随意更换）---
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = ""
    embedding_dim: int = 2048
    embedding_timeout_seconds: float = 60.0


@lru_cache
def get_settings() -> Settings:
    """获取单例配置对象（进程内缓存）。"""
    return Settings()
