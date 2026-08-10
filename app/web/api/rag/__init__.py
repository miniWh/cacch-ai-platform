"""RAG API routers."""

from fastapi import APIRouter

from app.web.api.rag.sources import router as sources_router

router = APIRouter()
router.include_router(sources_router)
