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
    default_kb_embedding_model: str = "default-embedding"
    default_kb_embedding_dim: int = 2048
    # 业务时区（写入/展示统一用此时区）
    app_timezone: str = "Asia/Shanghai"


@lru_cache
def get_settings() -> Settings:
    return Settings()
