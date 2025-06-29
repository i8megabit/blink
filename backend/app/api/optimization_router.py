"""
API роутер для управления оптимизациями reLink
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import logging
import asyncio

from ..llm.optimization_manager import (
    optimization_manager, 
    OptimizationLevel, 
    SystemHealth, 
    OptimizationMetrics
)
from ..llm.intelligent_model_router import IntelligentModelRouter, ModelType
from ..llm.advanced_chromadb_service import AdvancedChromaDBService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.on_event("startup")
async def startup_event():
    """Запуск менеджера оптимизаций при старте приложения"""
    try:
        await optimization_manager.start()
        logger.info("Менеджер оптимизаций запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска менеджера оптимизаций: {e}")


@router.on_event("shutdown")
async def shutdown_event():
    """Остановка менеджера оптимизаций при завершении приложения"""
    try:
        await optimization_manager.stop()
        logger.info("Менеджер оптимизаций остановлен")
    except Exception as e:
        logger.error(f"Ошибка остановки менеджера оптимизаций: {e}")


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """Получение состояния здоровья системы"""
    try:
        health = await optimization_manager.get_system_health()
        return {
            "status": "success",
            "data": {
                "cpu_usage": health.cpu_usage,
                "memory_usage": health.memory_usage,
                "gpu_usage": health.gpu_usage,
                "available_memory_mb": health.available_memory,
                "disk_usage": health.disk_usage,
                "load_average": health.load_average,
                "services": {
                    "ollama": health.ollama_status,
                    "chromadb": health.chromadb_status,
                    "redis": health.redis_status
                }
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения состояния системы: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_optimization_metrics() -> Dict[str, Any]:
    """Получение метрик оптимизации"""
    try:
        metrics = optimization_manager.get_optimization_metrics()
        
        return {
            "status": "success",
            "data": {
                "total_requests": metrics.total_requests,
                "avg_response_time": metrics.avg_response_time,
                "cache_hit_rate": metrics.cache_hit_rate,
                "model_utilization": metrics.model_utilization,
                "memory_efficiency": metrics.memory_efficiency,
                "cpu_efficiency": metrics.cpu_efficiency,
                "optimization_score": metrics.optimization_score,
                "optimization_stats": optimization_manager.optimization_stats
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def trigger_optimization(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Принудительный запуск оптимизации"""
    try:
        # Запуск оптимизации в фоне
        background_tasks.add_task(optimization_manager.optimize_system)
        
        return {
            "status": "success",
            "message": "Оптимизация запущена в фоновом режиме",
            "optimization_level": optimization_manager.optimization_level.value
        }
    except Exception as e:
        logger.error(f"Ошибка запуска оптимизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/sync")
async def trigger_sync_optimization() -> Dict[str, Any]:
    """Синхронная оптимизация (блокирующая)"""
    try:
        start_time = asyncio.get_event_loop().time()
        
        await optimization_manager.optimize_system()
        
        duration = asyncio.get_event_loop().time() - start_time
        
        return {
            "status": "success",
            "message": "Оптимизация завершена",
            "duration_seconds": duration,
            "optimization_level": optimization_manager.optimization_level.value
        }
    except Exception as e:
        logger.error(f"Ошибка синхронной оптимизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/status")
async def get_models_status() -> Dict[str, Any]:
    """Получение статуса моделей"""
    try:
        router_stats = optimization_manager.model_router.get_router_stats()
        
        return {
            "status": "success",
            "data": {
                "available_models": router_stats["available_models"],
                "model_performance": router_stats["model_performance"],
                "usage_stats": router_stats["usage_stats"]
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/preload")
async def preload_models(models: Optional[List[str]] = None) -> Dict[str, Any]:
    """Предзагрузка моделей"""
    try:
        if models is None:
            # Автоматический выбор моделей на основе уровня оптимизации
            if optimization_manager.optimization_level == OptimizationLevel.BASIC:
                models = ["qwen2.5:0.5b"]
            elif optimization_manager.optimization_level == OptimizationLevel.STANDARD:
                models = ["qwen2.5:0.5b", "qwen2.5:1.5b"]
            elif optimization_manager.optimization_level == OptimizationLevel.ADVANCED:
                models = ["qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b"]
            else:  # EXPERT
                models = ["qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b"]
        
        await optimization_manager.model_router.preload_models(models)
        
        return {
            "status": "success",
            "message": f"Модели {models} предзагружены",
            "preloaded_models": models
        }
    except Exception as e:
        logger.error(f"Ошибка предзагрузки моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chromadb/status")
async def get_chromadb_status() -> Dict[str, Any]:
    """Получение статуса ChromaDB"""
    try:
        health = await optimization_manager.chromadb_service.health_check()
        stats = optimization_manager.chromadb_service.get_performance_stats()
        
        return {
            "status": "success",
            "data": {
                "health": health,
                "performance_stats": stats
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса ChromaDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chromadb/optimize")
async def optimize_chromadb() -> Dict[str, Any]:
    """Оптимизация ChromaDB"""
    try:
        await optimization_manager.chromadb_service.optimize_collections()
        
        return {
            "status": "success",
            "message": "ChromaDB оптимизирован"
        }
    except Exception as e:
        logger.error(f"Ошибка оптимизации ChromaDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/level")
async def set_optimization_level(level: str) -> Dict[str, Any]:
    """Установка уровня оптимизации"""
    try:
        # Валидация уровня
        try:
            optimization_level = OptimizationLevel(level)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Неверный уровень оптимизации. Доступные: {[l.value for l in OptimizationLevel]}"
            )
        
        # Обновление уровня
        optimization_manager.optimization_level = optimization_level
        
        # Перезапуск с новыми настройками
        await optimization_manager.stop()
        await optimization_manager.start()
        
        return {
            "status": "success",
            "message": f"Уровень оптимизации изменен на {level}",
            "new_level": level
        }
    except Exception as e:
        logger.error(f"Ошибка изменения уровня оптимизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/level")
async def get_optimization_level() -> Dict[str, Any]:
    """Получение текущего уровня оптимизации"""
    try:
        return {
            "status": "success",
            "data": {
                "current_level": optimization_manager.optimization_level.value,
                "auto_optimize": optimization_manager.auto_optimize,
                "optimization_interval": optimization_manager.optimization_interval
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения уровня оптимизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/auto-optimize")
async def set_auto_optimize(enabled: bool) -> Dict[str, Any]:
    """Включение/выключение автоматической оптимизации"""
    try:
        optimization_manager.auto_optimize = enabled
        
        if enabled and not optimization_manager.background_task_running:
            # Запуск фоновой оптимизации
            asyncio.create_task(optimization_manager._background_optimization_loop())
        
        return {
            "status": "success",
            "message": f"Автоматическая оптимизация {'включена' if enabled else 'выключена'}",
            "auto_optimize": enabled
        }
    except Exception as e:
        logger.error(f"Ошибка изменения автоматической оптимизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/interval")
async def set_optimization_interval(interval_seconds: int) -> Dict[str, Any]:
    """Установка интервала оптимизации"""
    try:
        if interval_seconds < 60:
            raise HTTPException(
                status_code=400, 
                detail="Интервал оптимизации должен быть не менее 60 секунд"
            )
        
        optimization_manager.optimization_interval = interval_seconds
        
        return {
            "status": "success",
            "message": f"Интервал оптимизации изменен на {interval_seconds} секунд",
            "interval_seconds": interval_seconds
        }
    except Exception as e:
        logger.error(f"Ошибка изменения интервала оптимизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_optimized_request(
    prompt: str,
    context: str = "",
    collection_name: Optional[str] = None,
    query_texts: Optional[List[str]] = None,
    n_results: int = 10,
    preferred_model: Optional[str] = None
) -> Dict[str, Any]:
    """Обработка запроса с интеллектуальной оптимизацией"""
    try:
        result = await optimization_manager.process_request(
            prompt=prompt,
            context=context,
            collection_name=collection_name,
            query_texts=query_texts,
            n_results=n_results,
            preferred_model=preferred_model
        )
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Ошибка обработки оптимизированного запроса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/status")
async def get_cache_status() -> Dict[str, Any]:
    """Получение статуса кешей"""
    try:
        # Статус кеша роутера моделей
        router_cache_size = len(optimization_manager.model_router.local_cache)
        
        # Статус кеша ChromaDB
        chromadb_cache_size = len(optimization_manager.chromadb_service.local_cache)
        redis_available = optimization_manager.chromadb_service.redis_available
        
        return {
            "status": "success",
            "data": {
                "model_router_cache": {
                    "size": router_cache_size,
                    "max_size": optimization_manager.model_router.max_cache_size
                },
                "chromadb_cache": {
                    "local_size": chromadb_cache_size,
                    "max_size": optimization_manager.chromadb_service.max_cache_size,
                    "redis_available": redis_available
                }
            }
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса кешей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_caches() -> Dict[str, Any]:
    """Очистка всех кешей"""
    try:
        # Очистка кеша роутера моделей
        optimization_manager.model_router.local_cache.clear()
        
        # Очистка кеша ChromaDB
        await optimization_manager.chromadb_service._cleanup_cache()
        
        return {
            "status": "success",
            "message": "Все кеши очищены"
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кешей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/report")
async def get_performance_report() -> Dict[str, Any]:
    """Получение детального отчета о производительности"""
    try:
        # Сбор всех метрик
        system_health = await optimization_manager.get_system_health()
        optimization_metrics = optimization_manager.get_optimization_metrics()
        router_stats = optimization_manager.model_router.get_router_stats()
        chromadb_stats = optimization_manager.chromadb_service.get_performance_stats()
        
        # Анализ производительности
        performance_analysis = {
            "system_health": {
                "status": "healthy" if system_health.cpu_usage < 80 and system_health.memory_usage < 85 else "warning",
                "cpu_usage": system_health.cpu_usage,
                "memory_usage": system_health.memory_usage,
                "available_memory_mb": system_health.available_memory
            },
            "optimization_score": optimization_metrics.optimization_score,
            "cache_efficiency": optimization_metrics.cache_hit_rate,
            "model_performance": {
                "total_requests": router_stats["usage_stats"]["total_requests"],
                "success_rate": router_stats["usage_stats"]["successful_routes"] / router_stats["usage_stats"]["total_requests"] if router_stats["usage_stats"]["total_requests"] > 0 else 0,
                "error_rate": router_stats["usage_stats"]["errors"] / router_stats["usage_stats"]["total_requests"] if router_stats["usage_stats"]["total_requests"] > 0 else 0
            },
            "chromadb_performance": {
                "total_queries": chromadb_stats["total_queries"],
                "avg_query_time": chromadb_stats["avg_query_time"],
                "cache_hit_rate": chromadb_stats["cache_hit_rate"]
            },
            "recommendations": []
        }
        
        # Генерация рекомендаций
        if system_health.cpu_usage > 80:
            performance_analysis["recommendations"].append("Высокое использование CPU - рассмотрите увеличение ресурсов")
        
        if system_health.memory_usage > 85:
            performance_analysis["recommendations"].append("Высокое использование памяти - очистите кеши или увеличьте RAM")
        
        if optimization_metrics.cache_hit_rate < 0.5:
            performance_analysis["recommendations"].append("Низкий hit rate кеша - рассмотрите увеличение размера кеша")
        
        if performance_analysis["model_performance"]["error_rate"] > 0.1:
            performance_analysis["recommendations"].append("Высокий уровень ошибок моделей - проверьте доступность Ollama")
        
        return {
            "status": "success",
            "data": performance_analysis
        }
    except Exception as e:
        logger.error(f"Ошибка получения отчета о производительности: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 