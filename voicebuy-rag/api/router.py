from fastapi import APIRouter
from api import voice, search

router = APIRouter()
router.include_router(voice.router,  prefix="/voice",  tags=["Voice & RAG"])
router.include_router(search.router, prefix="/search", tags=["Search"])
