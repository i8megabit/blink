"""
Роутер для relink сервиса
"""

from fastapi import APIRouter

router = APIRouter(tags=["relink"])

@router.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "relink",
        "description": "Relink сервис reLink",
        "version": "1.0.0"
    } 