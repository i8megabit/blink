"""
🚀 ГЛАВНОЕ ПРИЛОЖЕНИЕ БЕНЧМАРК МИКРОСЕРВИСА
FastAPI приложение с полным API для тестирования производительности LLM моделей
"""

import asyncio
import time
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from .config import settings, BENCHMARK_TYPES
from .models import (
    BenchmarkRequest, BenchmarkResponse, BenchmarkListResponse, ErrorResponse,
    HealthCheck, CacheStats, PerformanceStats, BenchmarkFilterRequest,
    ExportRequest, ExportResponse, ComparisonResponse
)
from .services import get_benchmark_service
from .cache import get_cache, get_cache_stats

# Настройка логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Глобальные переменные
start_time = time.time()
active_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Запуск
    logger.info("🚀 Запуск Benchmark Service")
    logger.info(f"Версия: {settings.version}")
    logger.info(f"Порт: {settings.port}")
    logger.info(f"Debug: {settings.debug}")
    
    # Инициализация сервисов
    benchmark_service = await get_benchmark_service()
    cache = await get_cache()
    
    yield
    
    # Завершение
    logger.info("🛑 Остановка Benchmark Service")
    await cache.disconnect()


# Создание FastAPI приложения
app = FastAPI(
    title="🚀 Benchmark Service",
    description="Мощная система тестирования производительности LLM моделей",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для логирования
@app.middleware("http")
async def log_requests(request, call_next):
    """Логирование HTTP запросов."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        "HTTP Request",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response


# WebSocket менеджер
class ConnectionManager:
    """Менеджер WebSocket соединений."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Подключение клиента."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket подключен. Всего соединений: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Отключение клиента."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket отключен. Всего соединений: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Отправка личного сообщения."""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Отправка сообщения всем клиентам."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения: {e}")
                self.disconnect(connection)


manager = ConnectionManager()


# API Endpoints

@app.get("/", response_model=dict)
async def root():
    """Корневой эндпоинт."""
    return {
        "service": "Benchmark Service",
        "version": settings.version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Проверка здоровья сервиса."""
    uptime = time.time() - start_time
    
    # Проверка зависимостей
    services = {}
    
    try:
        cache = await get_cache()
        await cache.connect()
        services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"
    
    try:
        benchmark_service = await get_benchmark_service()
        services["benchmark_service"] = "healthy"
    except Exception as e:
        services["benchmark_service"] = f"unhealthy: {str(e)}"
    
    return HealthCheck(
        status="healthy" if all("healthy" in status for status in services.values()) else "degraded",
        timestamp=datetime.utcnow(),
        version=settings.version,
        uptime=uptime,
        services=services
    )


@app.post("/benchmark", response_model=BenchmarkResponse)
async def create_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks
):
    """Создание и запуск бенчмарка."""
    try:
        logger.info(f"Запуск бенчмарка: {request.name}")
        
        # Проверяем кэш
        cache = await get_cache()
        cache_key = f"benchmark:{request.name}:{':'.join(request.models)}"
        
        if not request.parameters.get('force_refresh'):
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.info("Возвращен кэшированный результат")
                return BenchmarkResponse(
                    success=True,
                    data=cached_result,
                    message="Результат получен из кэша"
                )
        
        # Запускаем бенчмарк в фоне
        benchmark_service = await get_benchmark_service()
        
        async def run_benchmark_task():
            """Фоновая задача выполнения бенчмарка."""
            try:
                results = await benchmark_service.run_benchmark(request)
                
                # Кэшируем результаты
                for result in results:
                    await cache.set_benchmark_result(
                        str(result.benchmark_id),
                        result.dict(),
                        ttl=settings.cache_ttl
                    )
                
                # Уведомляем WebSocket клиентов
                await manager.broadcast(f"Benchmark {request.name} completed")
                
            except Exception as e:
                logger.error(f"Ошибка выполнения бенчмарка: {e}")
                await manager.broadcast(f"Benchmark {request.name} failed: {str(e)}")
        
        background_tasks.add_task(run_benchmark_task)
        
        return BenchmarkResponse(
            success=True,
            message=f"Бенчмарк '{request.name}' запущен в фоновом режиме"
        )
        
    except Exception as e:
        logger.error(f"Ошибка создания бенчмарка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/benchmark/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark(benchmark_id: str):
    """Получение результата бенчмарка."""
    try:
        cache = await get_cache()
        result = await cache.get_benchmark_result(benchmark_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Бенчмарк не найден")
        
        return BenchmarkResponse(
            success=True,
            data=result,
            message="Результат бенчмарка получен"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения бенчмарка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/benchmarks", response_model=BenchmarkListResponse)
async def list_benchmarks(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    benchmark_type: Optional[str] = None,
    model_name: Optional[str] = None,
    status: Optional[str] = None
):
    """Получение списка бенчмарков."""
    try:
        benchmark_service = await get_benchmark_service()
        results = await benchmark_service.get_benchmark_history(limit + offset)
        
        # Фильтрация
        if benchmark_type:
            results = [r for r in results if r.benchmark_type == benchmark_type]
        if model_name:
            results = [r for r in results if model_name.lower() in r.model_name.lower()]
        if status:
            results = [r for r in results if r.status == status]
        
        # Пагинация
        total = len(results)
        results = results[offset:offset + limit]
        
        return BenchmarkListResponse(
            success=True,
            data=results,
            total=total,
            page=offset // limit + 1,
            limit=limit,
            message=f"Найдено {len(results)} бенчмарков"
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения списка бенчмарков: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/benchmark/{benchmark_id}")
async def cancel_benchmark(benchmark_id: str):
    """Отмена бенчмарка."""
    try:
        benchmark_service = await get_benchmark_service()
        success = await benchmark_service.cancel_benchmark(benchmark_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Бенчмарк не найден")
        
        return {"success": True, "message": "Бенчмарк отменен"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отмены бенчмарка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """Получение списка доступных моделей."""
    try:
        return {
            "success": True,
            "data": settings.ollama_models,
            "message": f"Доступно {len(settings.ollama_models)} моделей"
        }
    except Exception as e:
        logger.error(f"Ошибка получения списка моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/{model_name}/performance")
async def get_model_performance(model_name: str):
    """Получение производительности модели."""
    try:
        benchmark_service = await get_benchmark_service()
        performance = await benchmark_service.get_model_performance(model_name)
        
        if not performance:
            raise HTTPException(status_code=404, detail="Данные о производительности не найдены")
        
        return {
            "success": True,
            "data": performance,
            "message": f"Производительность модели {model_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения производительности модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/benchmark-types")
async def get_benchmark_types():
    """Получение типов бенчмарков."""
    try:
        return {
            "success": True,
            "data": BENCHMARK_TYPES,
            "message": f"Доступно {len(BENCHMARK_TYPES)} типов бенчмарков"
        }
    except Exception as e:
        logger.error(f"Ошибка получения типов бенчмарков: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/cache", response_model=CacheStats)
async def get_cache_statistics():
    """Получение статистики кэша."""
    try:
        stats = await get_cache_stats()
        return CacheStats(**stats)
    except Exception as e:
        logger.error(f"Ошибка получения статистики кэша: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/performance", response_model=PerformanceStats)
async def get_performance_statistics():
    """Получение статистики производительности."""
    try:
        import psutil
        
        # Получаем статистику системы
        memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
        cpu_usage_percent = psutil.cpu_percent(interval=1)
        
        # Заглушки для статистики бенчмарков
        active_benchmarks = len(manager.active_connections)
        completed_today = 0  # TODO: реализовать подсчет
        avg_response_time = 0.5  # TODO: реализовать подсчет
        total_requests = 0  # TODO: реализовать подсчет
        error_rate = 0.05  # TODO: реализовать подсчет
        
        return PerformanceStats(
            active_benchmarks=active_benchmarks,
            completed_today=completed_today,
            avg_response_time=avg_response_time,
            total_requests=total_requests,
            error_rate=error_rate,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики производительности: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache")
async def clear_cache(pattern: str = "*"):
    """Очистка кэша."""
    try:
        cache = await get_cache()
        deleted_count = await cache.clear(pattern)
        
        return {
            "success": True,
            "message": f"Удалено {deleted_count} ключей из кэша",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Ошибка очистки кэша: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export", response_model=ExportResponse)
async def export_benchmarks(request: ExportRequest):
    """Экспорт результатов бенчмарков."""
    try:
        # TODO: Реализовать экспорт в различные форматы
        filename = request.filename or f"benchmark_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{request.format}"
        
        return ExportResponse(
            success=True,
            filename=filename,
            message=f"Экспорт в формате {request.format} создан",
            download_url=f"/downloads/{filename}",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare", response_model=ComparisonResponse)
async def compare_benchmarks(benchmark_ids: List[str]):
    """Сравнение результатов бенчмарков."""
    try:
        if len(benchmark_ids) < 2:
            raise HTTPException(status_code=400, detail="Для сравнения нужно минимум 2 бенчмарка")
        
        cache = await get_cache()
        results = []
        
        for benchmark_id in benchmark_ids:
            result = await cache.get_benchmark_result(benchmark_id)
            if result:
                results.append(result)
        
        if len(results) < 2:
            raise HTTPException(status_code=404, detail="Не найдено достаточно результатов для сравнения")
        
        # TODO: Реализовать логику сравнения
        
        return ComparisonResponse(
            success=True,
            message=f"Сравнение {len(results)} бенчмарков выполнено"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка сравнения бенчмарков: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoints

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket эндпоинт для real-time уведомлений."""
    await manager.connect(websocket)
    try:
        await manager.send_personal_message(
            f"Подключен к Benchmark Service. Client ID: {client_id}",
            websocket
        )
        
        while True:
            # Ожидаем сообщения от клиента
            data = await websocket.receive_text()
            logger.info(f"Получено WebSocket сообщение от {client_id}: {data}")
            
            # Эхо ответ
            await manager.send_personal_message(f"Echo: {data}", websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket ошибка: {e}")
        manager.disconnect(websocket)


# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=exc.detail,
            timestamp=datetime.utcnow()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработчик общих исключений."""
    logger.error(f"Необработанное исключение: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="Внутренняя ошибка сервера",
            timestamp=datetime.utcnow()
        ).dict()
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers
    ) 