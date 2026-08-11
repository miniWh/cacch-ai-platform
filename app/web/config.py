"""Application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "cacch-ai-platform"
    api_auth_token: str = "dev-token"
    database_url: str = "postgresql+psycopg://esb:esb@10.80.86.93:5432/cdb"
    probe_timeout_seconds: float = 8.0
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
    return Settings()
