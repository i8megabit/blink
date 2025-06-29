"""
Роутер для testing сервиса
"""

from fastapi import APIRouter

router = APIRouter(tags=["testing"])

@router.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "testing",
        "description": "Testing сервис reLink",
        "version": "1.0.0"
    } 