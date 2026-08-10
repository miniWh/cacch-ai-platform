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


@lru_cache
def get_settings() -> Settings:
    return Settings()
