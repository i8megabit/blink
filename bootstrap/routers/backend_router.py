"""
Роутер для backend сервиса
"""

from fastapi import APIRouter

router = APIRouter(tags=["backend"])

@router.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "backend",
        "description": "Backend сервис reLink",
        "version": "1.0.0"
    } 