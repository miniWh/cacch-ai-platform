"""RAG API routers."""

from fastapi import APIRouter

from app.web.api.rag.kb import router as kb_router
from app.web.api.rag.sessions import router as sessions_router
from app.web.api.rag.sources import router as sources_router

router = APIRouter()
router.include_router(kb_router)
router.include_router(sources_router)
router.include_router(sessions_router)
