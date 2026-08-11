"""Knowledge base schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    embedding_model: str = Field(min_length=1, max_length=128)
    embedding_dim: int = Field(default=2048, gt=0)
    status: int = Field(default=1)


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: str | None
    embedding_model: str
    embedding_dim: int
    status: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at", "updated_at", when_used="json")
    def _serialize_dt(self, value: datetime | None) -> str | None:
        from app.common.timeutil import to_app_tz

        converted = to_app_tz(value)
        return converted.isoformat() if converted is not None else None


class KnowledgeBaseListOut(BaseModel):
    items: list[KnowledgeBaseOut]
    total: int
