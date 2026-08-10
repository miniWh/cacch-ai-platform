"""FastAPI application entry."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.dto import fail
from app.common.exceptions import AppError
from app.dao.database import init_db
from app.web.api.rag import router as rag_router
from app.web.config import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        status = 401 if exc.code == 401 else 200
        return JSONResponse(
            status_code=status,
            content=fail(exc.code, exc.message),
        )

    @application.get("/api/v1/health")
    def health() -> dict:
        return {"code": 0, "message": "ok", "data": {"status": "ok"}}

    application.include_router(rag_router)
    return application


app = create_app()
