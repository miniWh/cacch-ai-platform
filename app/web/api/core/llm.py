"""LLM / Embedding HTTP API：对话台与冒烟测试。"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from typing import Any, Literal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.common.dto import ok
from app.core.llm.errors import LlmConfigError, LlmError
from app.core.llm.gateway import LlmGateway
from app.core.llm.profiles import build_profiles
from app.core.llm.types import CallMeta, ChatMessage
from app.web.config import Settings, get_settings
from app.web.middleware.auth import require_business_user

router = APIRouter(prefix="/llm", tags=["core-llm"])

DEFAULT_ASSISTANT_SYSTEM = (
    "你是企业知识库助手，当前业务场景为农药登记与评审资料问答。\n"
    "规则：\n"
    "1. 仅依据对话上下文与已知信息谨慎回答；信息不足时明确说明无法确定，禁止编造。\n"
    "2. 禁止编造登记号、批准状态、毒性结论等关键法规结论。\n"
    "3. 可用中文或英文作答，优先跟随用户提问语言。\n"
    "4. 回答末尾简要提醒：仅供辅助参考，请核对原文/官网。"
)


class ChatSmokeRequest(BaseModel):
    """单轮对话冒烟测试请求体。"""

    prompt: str = Field(min_length=1, max_length=4000, description="用户提示词")
    profile_id: str = Field(default="rag_chat", description="LLM 配置别名")
    system: str | None = Field(default=None, max_length=2000, description="系统提示词")


class EmbedSmokeRequest(BaseModel):
    """向量化冒烟测试请求体。"""

    texts: list[str] = Field(min_length=1, max_length=16, description="待嵌入文本列表")
    profile_id: str = Field(default="embed_default", description="Embedding 配置别名")


class ChatMessageIn(BaseModel):
    """对话消息输入。"""

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=16000, description="消息内容")


class ChatCompletionsRequest(BaseModel):
    """多轮对话补全请求体。"""

    messages: list[ChatMessageIn] = Field(
        min_length=1, max_length=40, description="消息列表"
    )
    profile_id: str = Field(default="rag_chat", description="LLM 配置别名")
    stream: bool = Field(default=True, description="是否 SSE 流式返回")
    # 未传 system 时使用默认助手人设
    system: str | None = Field(default=None, max_length=4000, description="系统提示词")


def _gateway(settings: Settings = Depends(get_settings)) -> LlmGateway:
    """FastAPI 依赖：构造 LlmGateway。"""
    return LlmGateway(settings)


def _to_messages(
    payload: ChatCompletionsRequest,
) -> list[ChatMessage]:
    """将 API 请求体转换为网关内部消息列表（补全默认 system）。"""
    messages: list[ChatMessage] = []
    has_system = any(m.role == "system" for m in payload.messages)
    system_text = (
        payload.system if payload.system is not None else DEFAULT_ASSISTANT_SYSTEM
    )
    if system_text and not has_system:
        messages.append(ChatMessage(role="system", content=system_text))
    for m in payload.messages:
        messages.append(ChatMessage(role=m.role, content=m.content))
    return messages


@router.post("/chat", dependencies=[Depends(require_business_user)])
def smoke_chat(
    payload: ChatSmokeRequest,
    gateway: LlmGateway = Depends(_gateway),
) -> dict[str, Any]:
    """单轮 LLM 对话冒烟测试。"""
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


@router.post("/chat/completions", dependencies=[Depends(require_business_user)])
def chat_completions(
    payload: ChatCompletionsRequest,
    gateway: LlmGateway = Depends(_gateway),
) -> Any:
    """对话台主接口：支持多轮；stream=true 时返回 SSE。"""
    messages = _to_messages(payload)
    request_id = f"chat-{uuid.uuid4().hex[:12]}"
    meta = CallMeta(capability="chat", request_id=request_id)

    if not payload.stream:
        result = gateway.chat(messages, payload.profile_id, meta)
        return ok(
            {
                "content": result.content,
                "model": result.model,
                "profile_id": result.profile_id,
                "provider": result.provider,
                "request_id": request_id,
                "usage": {
                    "prompt_tokens": result.usage.prompt_tokens,
                    "completion_tokens": result.usage.completion_tokens,
                    "total_tokens": result.usage.total_tokens,
                },
            }
        )

    def event_stream() -> Iterator[str]:
        try:
            for token in gateway.chat_stream(messages, payload.profile_id, meta):
                yield (
                    "data: "
                    + json.dumps(
                        {"type": "token", "content": token},
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "done",
                        "request_id": request_id,
                        "profile_id": payload.profile_id,
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )
        except LlmError as exc:
            yield (
                "data: "
                + json.dumps(
                    {"type": "error", "message": exc.message, "code": exc.code},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
        except Exception as exc:  # noqa: BLE001
            yield (
                "data: "
                + json.dumps(
                    {"type": "error", "message": str(exc), "code": 502},
                    ensure_ascii=False,
                )
                + "\n\n"
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-Id": request_id,
        },
    )


@router.post("/embed", dependencies=[Depends(require_business_user)])
def smoke_embed(
    payload: EmbedSmokeRequest,
    gateway: LlmGateway = Depends(_gateway),
) -> dict[str, Any]:
    """批量文本向量化冒烟测试。"""
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


@router.get("/profiles", dependencies=[Depends(require_business_user)])
def list_profiles(
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """列出已配置的 LLM / Embedding 配置项。"""
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
