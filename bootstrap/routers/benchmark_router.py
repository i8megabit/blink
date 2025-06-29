"""
Роутер для benchmark сервиса
"""

from fastapi import APIRouter

router = APIRouter(tags=["benchmark"])

@router.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "benchmark",
        "description": "Benchmark сервис reLink",
        "version": "1.0.0"
    } 