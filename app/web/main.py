"""FastAPI 应用入口与生命周期。"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.common.dto import fail
from app.common.exceptions import AppError
from app.dao.database import get_session_factory, init_db
from app.service.auth_seed import ensure_auth_seed
from app.service.kb_service import KnowledgeBaseService
from app.web.api.auth import router as auth_router
from app.web.api.core import router as core_router
from app.web.api.rag import router as rag_router
from app.web.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """应用启动时初始化数据库、认证种子与默认知识库。"""
    init_db()
    session = get_session_factory()()
    try:
        ensure_auth_seed(session)
        KnowledgeBaseService(session).ensure_default_kb()
    finally:
        session.close()
    yield


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。"""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        status = exc.code if exc.code in (401, 403) else 200
        return JSONResponse(
            status_code=status,
            content=fail(exc.code, exc.message),
        )

    @application.get("/api/v1/health")
    def health() -> dict:
        """健康检查接口。"""
        return {"code": 0, "message": "ok", "data": {"status": "ok"}}

    application.include_router(auth_router)
    application.include_router(rag_router)
    application.include_router(core_router)
    return application


app = create_app()
