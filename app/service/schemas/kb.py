"""知识库相关 Pydantic 请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_serializer


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求体。"""

    name: str = Field(min_length=1, max_length=128, description="知识库名称")
    description: str | None = Field(default=None, max_length=512, description="描述")
    embedding_model: str = Field(min_length=1, max_length=128, description="向量模型")
    embedding_dim: int = Field(default=2048, gt=0, description="向量维度")
    status: int = Field(default=1, description="状态：1 启用")


class KnowledgeBaseOut(BaseModel):
    """知识库详情输出。"""

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
    """知识库列表响应。"""

    items: list[KnowledgeBaseOut]
    total: int
