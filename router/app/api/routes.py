from fastapi import APIRouter, Depends
from bootstrap.llm_router import get_llm_router
from bootstrap.rag_service import get_rag_service
from bootstrap.ollama_client import get_ollama_client
from bootstrap.monitoring import get_service_monitor
import uuid

router = APIRouter(tags=["router"])

@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "router",
        "description": "LLM Router - интеллектуальная маршрутизация запросов к оптимальным моделям"
    }

@router.get("/api/v1/endpoints")
async def get_endpoints():
    """Получение списка эндпоинтов"""
    return {
        "service": "router",
        "endpoints": [
            "/health",
            "/api/v1/endpoints"
        ]
    }

@router.get("/api/v1/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    monitor = get_service_monitor()
    return monitor.get_metrics_summary()
