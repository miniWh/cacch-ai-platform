"""Core platform API routers."""

from fastapi import APIRouter

from app.web.api.core.llm import router as llm_router

router = APIRouter(prefix="/api/v1/core")
router.include_router(llm_router)
