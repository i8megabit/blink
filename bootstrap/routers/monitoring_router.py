"""
Роутер для monitoring сервиса
"""

from fastapi import APIRouter

router = APIRouter(tags=["monitoring"])

@router.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "monitoring",
        "description": "Monitoring сервис reLink",
        "version": "1.0.0"
    } 