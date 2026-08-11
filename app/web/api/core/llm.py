"""LLM / Embedding smoke & probe APIs (Doubao via gateway)."""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.common.dto import ok
from app.core.llm.errors import LlmConfigError
from app.core.llm.gateway import LlmGateway
from app.core.llm.profiles import build_profiles
from app.core.llm.types import CallMeta, ChatMessage
from app.web.config import Settings, get_settings
from app.web.middleware.auth import require_bearer

router = APIRouter(prefix="/llm", tags=["core-llm"])


class ChatSmokeRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    profile_id: str = "rag_chat"
    system: str | None = Field(default=None, max_length=2000)


class EmbedSmokeRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=16)
    profile_id: str = "embed_default"


def _gateway(settings: Settings = Depends(get_settings)) -> LlmGateway:
    return LlmGateway(settings)


@router.post("/chat", dependencies=[Depends(require_bearer)])
def smoke_chat(
    payload: ChatSmokeRequest,
    gateway: LlmGateway = Depends(_gateway),
) -> dict[str, Any]:
    messages: list[ChatMessage] = []
    if payload.system:
        messages.append(ChatMessage(role="system", content=payload.system))
    messages.append(ChatMessage(role="user", content=payload.prompt))
    result = gateway.chat(
        messages,
        payload.profile_id,
        CallMeta(capability="smoke", request_id="smoke-chat"),
    )
    return ok(
        {
            "content": result.content,
            "model": result.model,
            "profile_id": result.profile_id,
            "provider": result.provider,
            "usage": {
                "prompt_tokens": result.usage.prompt_tokens,
                "completion_tokens": result.usage.completion_tokens,
                "total_tokens": result.usage.total_tokens,
            },
        }
    )


@router.post("/embed", dependencies=[Depends(require_bearer)])
def smoke_embed(
    payload: EmbedSmokeRequest,
    gateway: LlmGateway = Depends(_gateway),
) -> dict[str, Any]:
    vectors = gateway.embed_batch(
        payload.texts,
        payload.profile_id,
        CallMeta(capability="smoke", request_id="smoke-embed"),
    )
    return ok(
        {
            "count": len(vectors),
            "dims": [len(v) for v in vectors],
            "preview": [v[:8] for v in vectors],
        }
    )


@router.get("/profiles", dependencies=[Depends(require_bearer)])
def list_profiles(
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    try:
        profiles = build_profiles(settings)
    except LlmConfigError as exc:
        return ok({"configured": False, "error": exc.message, "items": []})

    items = [
        {
            "alias": alias,
            "profile_id": p.profile_id,
            "kind": p.kind,
            "provider": p.provider,
            "model": p.model,
            "base_url": p.base_url,
            "embedding_dim": p.embedding_dim,
            "fallback_profile_id": p.fallback_profile_id,
        }
        for alias, p in profiles.items()
    ]
    return ok({"configured": True, "items": items})
