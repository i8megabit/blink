from fastapi import APIRouter

from .routes import links

router = APIRouter()
router.include_router(links.router, prefix="/links", tags=["links"])
