"""Source site schemas (Pydantic)."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator


class RegionCode(StrEnum):
    US = "US"
    EU = "EU"
    UK = "UK"
    AU = "AU"
    JP = "JP"
    CN = "CN"
    INT = "INT"


class SiteCategory(StrEnum):
    REGISTRATION = "registration"
    EVALUATION = "evaluation"
    STANDARD = "standard"
    DATABASE = "database"


class CrawlMode(StrEnum):
    MANUAL = "manual"
    SINGLE_PAGE = "single_page"
    LIST_HARVEST = "list_harvest"
    CONNECTOR = "connector"


class SiteStatus(StrEnum):
    ACTIVE = "active"
    BROKEN = "broken"
    PENDING_URL = "pending_url"
    DISABLED = "disabled"


class SourceSiteCreate(BaseModel):
    site_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    name: str = Field(min_length=1, max_length=256)
    region: RegionCode
    category: SiteCategory
    entry_url: str | None = Field(default=None, max_length=1024)
    crawl_mode: CrawlMode = CrawlMode.MANUAL
    allowed_domains: list[str] = Field(default_factory=list)
    rate_limit_qps: float | None = Field(default=None, gt=0)
    status: SiteStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("entry_url")
    @classmethod
    def normalize_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("allowed_domains")
    @classmethod
    def normalize_domains(cls, value: list[str]) -> list[str]:
        return [d.strip().lower() for d in value if d and d.strip()]

    @model_validator(mode="after")
    def resolve_status(self) -> Self:
        if self.status is None:
            self.status = (
                SiteStatus.PENDING_URL if not self.entry_url else SiteStatus.ACTIVE
            )
        if not self.entry_url and self.status == SiteStatus.ACTIVE:
            self.status = SiteStatus.PENDING_URL
        return self


class SourceSiteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    region: RegionCode | None = None
    category: SiteCategory | None = None
    entry_url: str | None = Field(default=None, max_length=1024)
    crawl_mode: CrawlMode | None = None
    allowed_domains: list[str] | None = None
    rate_limit_qps: float | None = Field(default=None, gt=0)
    status: SiteStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("entry_url")
    @classmethod
    def normalize_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("allowed_domains")
    @classmethod
    def normalize_domains(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [d.strip().lower() for d in value if d and d.strip()]


class SourceSiteOut(BaseModel):
    site_id: str
    kb_id: int
    name: str
    region: str
    category: str
    entry_url: str | None
    crawl_mode: str
    allowed_domains: list[Any]
    rate_limit_qps: float | None
    status: str
    notes: str | None
    last_probe_at: datetime | None
    last_probe_status: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer(
        "last_probe_at", "created_at", "updated_at", when_used="json"
    )
    def _serialize_dt(self, value: datetime | None) -> str | None:
        from app.common.timeutil import to_app_tz

        converted = to_app_tz(value)
        return converted.isoformat() if converted is not None else None


class SourceListOut(BaseModel):
    items: list[SourceSiteOut]
    total: int


class ProbeRequest(BaseModel):
    site_ids: list[str] | None = None


class ProbeResultItem(BaseModel):
    site_id: str
    name: str
    status: str
    last_probe_status: str | None
    last_probe_at: datetime | None

    @field_serializer("last_probe_at", when_used="json")
    def _serialize_probe_at(self, value: datetime | None) -> str | None:
        from app.common.timeutil import to_app_tz

        converted = to_app_tz(value)
        return converted.isoformat() if converted is not None else None


class ProbeResponse(BaseModel):
    results: list[ProbeResultItem]
