"""
🧠 Основное приложение LLM Tuning микросервиса
Маршрутизация, RAG, динамический тюнинг и мониторинг
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
from typing import Dict, Any, List

from .config import settings
from .database import get_db, init_db
from .services import (
    ModelService, 
    RouterService, 
    RAGService, 
    TuningService,
    MonitoringService
)
from .models import (
    LLMModelCreate, LLMModelUpdate, LLMModelResponse,
    RouteCreate, RouteResponse,
    TuningSessionCreate, TuningSessionResponse,
    RAGQuery, RAGResponse,
    RouteRequest, RouteResponse as RouterResponse,
    PerformanceMetrics
)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.monitoring.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Инициализация при запуске
    logger.info("🚀 Запуск LLM Tuning микросервиса...")
    
    # Инициализация базы данных
    await init_db()
    logger.info("✅ База данных инициализирована")
    
    # Инициализация сервисов
    app.state.model_service = ModelService()
    app.state.router_service = RouterService()
    app.state.rag_service = RAGService()
    app.state.tuning_service = TuningService()
    app.state.monitoring_service = MonitoringService()
    
    logger.info("✅ Сервисы инициализированы")
    logger.info(f"🎯 RAG включен: {settings.rag.enabled}")
    logger.info(f"⚡ Тюнинг включен: {settings.tuning.enabled}")
    logger.info(f"🛣️ Маршрутизация включена: {settings.router.enabled}")
    
    yield
    
    # Очистка при остановке
    logger.info("🛑 Остановка LLM Tuning микросервиса...")


# Создание FastAPI приложения
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    docs_url=settings.api.docs_url if settings.debug else None,
    redoc_url=settings.api.redoc_url if settings.debug else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware для мониторинга
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Middleware для мониторинга запросов"""
    start_time = time.time()
    
    # Логирование запроса
    logger.info(f"📥 {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Логирование ответа
        process_time = time.time() - start_time
        logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        
        # Добавление времени обработки в заголовки
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # Логирование ошибки
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - ERROR ({process_time:.3f}s): {str(e)}")
        raise


# Health check
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "llm-tuning",
        "version": settings.api.version,
        "environment": settings.environment,
        "features": {
            "rag_enabled": settings.rag.enabled,
            "tuning_enabled": settings.tuning.enabled,
            "router_enabled": settings.router.enabled
        }
    }


# API Routes

## Модели LLM
@app.post("/api/v1/models", response_model=LLMModelResponse)
async def create_model(
    model_data: LLMModelCreate,
    db=Depends(get_db),
    model_service: ModelService = Depends(lambda: app.state.model_service)
):
    """Создание новой модели LLM"""
    try:
        model = await model_service.create_model(db, model_data)
        logger.info(f"✅ Создана модель: {model.name}")
        return model
    except Exception as e:
        logger.error(f"❌ Ошибка создания модели: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/models", response_model=List[LLMModelResponse])
async def list_models(
    skip: int = 0,
    limit: int = 100,
    provider: str = None,
    status: str = None,
    db=Depends(get_db),
    model_service: ModelService = Depends(lambda: app.state.model_service)
):
    """Список моделей LLM"""
    try:
        models = await model_service.list_models(db, skip=skip, limit=limit, provider=provider, status=status)
        return models
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/models/{model_id}", response_model=LLMModelResponse)
async def get_model(
    model_id: int,
    db=Depends(get_db),
    model_service: ModelService = Depends(lambda: app.state.model_service)
):
    """Получение модели по ID"""
    try:
        model = await model_service.get_model(db, model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения модели {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/models/{model_id}", response_model=LLMModelResponse)
async def update_model(
    model_id: int,
    model_data: LLMModelUpdate,
    db=Depends(get_db),
    model_service: ModelService = Depends(lambda: app.state.model_service)
):
    """Обновление модели LLM"""
    try:
        model = await model_service.update_model(db, model_id, model_data)
        if not model:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        logger.info(f"✅ Обновлена модель: {model.name}")
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка обновления модели {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/models/{model_id}")
async def delete_model(
    model_id: int,
    db=Depends(get_db),
    model_service: ModelService = Depends(lambda: app.state.model_service)
):
    """Удаление модели LLM"""
    try:
        success = await model_service.delete_model(db, model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        logger.info(f"✅ Удалена модель: {model_id}")
        return {"message": "Модель успешно удалена"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка удаления модели {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


## Маршрутизация
@app.post("/api/v1/route", response_model=RouterResponse)
async def route_request(
    request_data: RouteRequest,
    db=Depends(get_db),
    router_service: RouterService = Depends(lambda: app.state.router_service)
):
    """Маршрутизация запроса к оптимальной модели"""
    try:
        start_time = time.time()
        route_result = await router_service.route_request(db, request_data)
        process_time = time.time() - start_time
        
        logger.info(f"🛣️ Маршрутизация: {request_data.query[:50]}... -> {route_result.model_name} ({process_time:.3f}s)")
        
        return route_result
    except Exception as e:
        logger.error(f"❌ Ошибка маршрутизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/routes", response_model=RouteResponse)
async def create_route(
    route_data: RouteCreate,
    db=Depends(get_db),
    router_service: RouterService = Depends(lambda: app.state.router_service)
):
    """Создание нового маршрута"""
    try:
        route = await router_service.create_route(db, route_data)
        logger.info(f"✅ Создан маршрут: {route.name}")
        return route
    except Exception as e:
        logger.error(f"❌ Ошибка создания маршрута: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/routes", response_model=List[RouteResponse])
async def list_routes(
    skip: int = 0,
    limit: int = 100,
    strategy: str = None,
    db=Depends(get_db),
    router_service: RouterService = Depends(lambda: app.state.router_service)
):
    """Список маршрутов"""
    try:
        routes = await router_service.list_routes(db, skip=skip, limit=limit, strategy=strategy)
        return routes
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка маршрутов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


## RAG система
@app.post("/api/v1/rag/query", response_model=RAGResponse)
async def rag_query(
    query_data: RAGQuery,
    db=Depends(get_db),
    rag_service: RAGService = Depends(lambda: app.state.rag_service)
):
    """RAG запрос с контекстом"""
    if not settings.rag.enabled:
        raise HTTPException(status_code=400, detail="RAG система отключена")
    
    try:
        start_time = time.time()
        response = await rag_service.query(db, query_data)
        process_time = time.time() - start_time
        
        logger.info(f"🧠 RAG запрос: {query_data.query[:50]}... ({process_time:.3f}s)")
        
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка RAG запроса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/rag/documents")
async def add_document(
    title: str,
    content: str,
    source: str = None,
    document_type: str = None,
    tags: List[str] = [],
    db=Depends(get_db),
    rag_service: RAGService = Depends(lambda: app.state.rag_service)
):
    """Добавление документа в RAG систему"""
    if not settings.rag.enabled:
        raise HTTPException(status_code=400, detail="RAG система отключена")
    
    try:
        document_id = await rag_service.add_document(db, title, content, source, document_type, tags)
        logger.info(f"✅ Добавлен документ в RAG: {title}")
        return {"document_id": document_id, "message": "Документ успешно добавлен"}
    except Exception as e:
        logger.error(f"❌ Ошибка добавления документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


## Тюнинг моделей
@app.post("/api/v1/tuning/sessions", response_model=TuningSessionResponse)
async def create_tuning_session(
    session_data: TuningSessionCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    tuning_service: TuningService = Depends(lambda: app.state.tuning_service)
):
    """Создание сессии тюнинга"""
    if not settings.tuning.enabled:
        raise HTTPException(status_code=400, detail="Тюнинг отключен")
    
    try:
        session = await tuning_service.create_session(db, session_data)
        
        # Запуск тюнинга в фоне
        background_tasks.add_task(tuning_service.run_tuning, db, session.id)
        
        logger.info(f"✅ Создана сессия тюнинга: {session.name}")
        return session
    except Exception as e:
        logger.error(f"❌ Ошибка создания сессии тюнинга: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/tuning/sessions", response_model=List[TuningSessionResponse])
async def list_tuning_sessions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    model_id: int = None,
    db=Depends(get_db),
    tuning_service: TuningService = Depends(lambda: app.state.tuning_service)
):
    """Список сессий тюнинга"""
    try:
        sessions = await tuning_service.list_sessions(db, skip=skip, limit=limit, status=status, model_id=model_id)
        return sessions
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка сессий тюнинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tuning/sessions/{session_id}", response_model=TuningSessionResponse)
async def get_tuning_session(
    session_id: int,
    db=Depends(get_db),
    tuning_service: TuningService = Depends(lambda: app.state.tuning_service)
):
    """Получение сессии тюнинга"""
    try:
        session = await tuning_service.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Сессия тюнинга не найдена")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения сессии тюнинга {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tuning/optimize")
async def optimize_model(
    model_id: int,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    tuning_service: TuningService = Depends(lambda: app.state.tuning_service)
):
    """Автоматическая оптимизация модели"""
    if not settings.tuning.enabled:
        raise HTTPException(status_code=400, detail="Тюнинг отключен")
    
    try:
        # Запуск оптимизации в фоне
        background_tasks.add_task(tuning_service.optimize_model, db, model_id)
        
        logger.info(f"✅ Запущена оптимизация модели: {model_id}")
        return {"message": "Оптимизация запущена", "model_id": model_id}
    except Exception as e:
        logger.error(f"❌ Ошибка запуска оптимизации модели {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


## Мониторинг и метрики
@app.post("/api/v1/metrics")
async def record_metrics(
    metrics: PerformanceMetrics,
    db=Depends(get_db),
    monitoring_service: MonitoringService = Depends(lambda: app.state.monitoring_service)
):
    """Запись метрик производительности"""
    try:
        await monitoring_service.record_metrics(db, metrics)
        return {"message": "Метрики записаны"}
    except Exception as e:
        logger.error(f"❌ Ошибка записи метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics/summary")
async def get_metrics_summary(
    model_id: int = None,
    time_range: str = "24h",
    db=Depends(get_db),
    monitoring_service: MonitoringService = Depends(lambda: app.state.monitoring_service)
):
    """Получение сводки метрик"""
    try:
        summary = await monitoring_service.get_metrics_summary(db, model_id, time_range)
        return summary
    except Exception as e:
        logger.error(f"❌ Ошибка получения сводки метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/models/status")
async def get_models_status(
    db=Depends(get_db),
    model_service: ModelService = Depends(lambda: app.state.model_service)
):
    """Статус всех моделей"""
    try:
        status = await model_service.get_models_status(db)
        return status
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error(f"❌ Необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "detail": str(exc) if settings.debug else "Произошла ошибка при обработке запроса"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        workers=4
    ) 