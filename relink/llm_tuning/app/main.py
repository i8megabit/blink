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
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy import select, and_
from sqlalchemy.sql import func

from .config import settings
from .database import get_db, init_db
from .services import (
    ModelService, 
    RouterService, 
    RAGService, 
    TuningService,
    MonitoringService,
    ABTestingService,
    AutoOptimizationService,
    QualityAssessmentService,
    SystemHealthService
)
from .models import (
    LLMModelCreate, LLMModelUpdate, LLMModelResponse,
    RouteCreate, RouteResponse,
    TuningSessionCreate, TuningSessionResponse,
    RAGQuery, RAGResponse,
    RouteRequest, RouteResponse as RouterResponse,
    PerformanceMetrics,
    ABTestCreate, ABTestUpdate, ABTestResponse,
    ModelOptimizationCreate, ModelOptimizationResponse,
    QualityAssessmentCreate, QualityAssessmentResponse,
    SystemHealthResponse,
    ModelStatsResponse, SystemStatsResponse
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
    app.state.ab_testing_service = ABTestingService()
    app.state.auto_optimization_service = AutoOptimizationService()
    app.state.quality_assessment_service = QualityAssessmentService()
    app.state.system_health_service = SystemHealthService()
    
    logger.info("✅ Сервисы инициализированы")
    logger.info(f"🎯 RAG включен: {settings.rag.enabled}")
    logger.info(f"⚡ Тюнинг включен: {settings.tuning.enabled}")
    logger.info(f"🛣️ Маршрутизация включена: {settings.router.enabled}")
    logger.info(f"🧪 A/B тестирование включено: {settings.tuning.ab_testing_enabled}")
    
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


# A/B Тестирование
@app.post("/api/v1/ab-tests", response_model=ABTestResponse)
async def create_ab_test(
    test_data: ABTestCreate,
    db=Depends(get_db),
    ab_testing_service: ABTestingService = Depends(lambda: app.state.ab_testing_service)
):
    """Создание нового A/B теста"""
    try:
        test = await ab_testing_service.create_ab_test(test_data.dict())
        logger.info(f"✅ Создан A/B тест: {test.name}")
        return test
    except Exception as e:
        logger.error(f"❌ Ошибка создания A/B теста: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/ab-tests", response_model=List[ABTestResponse])
async def list_ab_tests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    model_id: Optional[int] = None,
    db=Depends(get_db),
    ab_testing_service: ABTestingService = Depends(lambda: app.state.ab_testing_service)
):
    """Список A/B тестов"""
    try:
        tests = await ab_testing_service.list_ab_tests(
            skip=skip, limit=limit, status=status, model_id=model_id
        )
        return tests
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка A/B тестов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ab-tests/{test_id}", response_model=ABTestResponse)
async def get_ab_test(
    test_id: int,
    db=Depends(get_db),
    ab_testing_service: ABTestingService = Depends(lambda: app.state.ab_testing_service)
):
    """Получение A/B теста по ID"""
    try:
        test = await ab_testing_service.get_ab_test(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="A/B тест не найден")
        return test
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения A/B теста {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/ab-tests/{test_id}", response_model=ABTestResponse)
async def update_ab_test(
    test_id: int,
    test_data: ABTestUpdate,
    db=Depends(get_db),
    ab_testing_service: ABTestingService = Depends(lambda: app.state.ab_testing_service)
):
    """Обновление A/B теста"""
    try:
        # Получаем тест
        test = await ab_testing_service.get_ab_test(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="A/B тест не найден")
        
        # Обновляем поля
        update_data = test_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test, field, value)
        
        await db.commit()
        await db.refresh(test)
        
        logger.info(f"✅ Обновлен A/B тест: {test.name}")
        return test
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка обновления A/B теста {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ab-tests/{test_id}/select-model")
async def select_model_for_ab_test(
    test_id: int,
    request_type: str,
    user_id: Optional[str] = None,
    db=Depends(get_db),
    ab_testing_service: ABTestingService = Depends(lambda: app.state.ab_testing_service)
):
    """Выбор модели для запроса в рамках A/B теста"""
    try:
        model_name, variant = await ab_testing_service.select_model_for_request(
            test_id, request_type, user_id
        )
        return {
            "model_name": model_name,
            "variant": variant,
            "test_id": test_id
        }
    except Exception as e:
        logger.error(f"❌ Ошибка выбора модели для A/B теста: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/ab-tests/{test_id}/record-result")
async def record_ab_test_result(
    test_id: int,
    model_variant: str,
    metrics: Dict[str, Any],
    db=Depends(get_db),
    ab_testing_service: ABTestingService = Depends(lambda: app.state.ab_testing_service)
):
    """Запись результатов A/B теста"""
    try:
        await ab_testing_service.record_ab_test_result(test_id, model_variant, metrics)
        return {"message": "Результаты A/B теста записаны"}
    except Exception as e:
        logger.error(f"❌ Ошибка записи результатов A/B теста: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Автоматическая оптимизация
@app.post("/api/v1/optimization", response_model=ModelOptimizationResponse)
async def optimize_model(
    optimization_data: ModelOptimizationCreate,
    db=Depends(get_db),
    auto_optimization_service: AutoOptimizationService = Depends(lambda: app.state.auto_optimization_service)
):
    """Запуск автоматической оптимизации модели"""
    try:
        optimization = await auto_optimization_service.optimize_model(
            optimization_data.model_id,
            optimization_data.optimization_type,
            optimization_data.target_metrics
        )
        logger.info(f"✅ Запущена оптимизация модели {optimization_data.model_id}")
        return optimization
    except Exception as e:
        logger.error(f"❌ Ошибка запуска оптимизации: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/optimization/{optimization_id}", response_model=ModelOptimizationResponse)
async def get_optimization(
    optimization_id: int,
    db=Depends(get_db),
    auto_optimization_service: AutoOptimizationService = Depends(lambda: app.state.auto_optimization_service)
):
    """Получение информации об оптимизации"""
    try:
        optimization = await auto_optimization_service._get_optimization(optimization_id)
        if not optimization:
            raise HTTPException(status_code=404, detail="Оптимизация не найдена")
        return optimization
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения оптимизации {optimization_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Оценка качества
@app.post("/api/v1/quality/assess", response_model=QualityAssessmentResponse)
async def assess_quality(
    assessment_data: QualityAssessmentCreate,
    db=Depends(get_db),
    quality_assessment_service: QualityAssessmentService = Depends(lambda: app.state.quality_assessment_service)
):
    """Оценка качества ответа модели"""
    try:
        assessment = await quality_assessment_service.assess_quality(
            assessment_data.model_id,
            assessment_data.request_text,
            assessment_data.response_text,
            assessment_data.context_documents
        )
        logger.info(f"✅ Оценка качества выполнена для модели {assessment_data.model_id}")
        return assessment
    except Exception as e:
        logger.error(f"❌ Ошибка оценки качества: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/quality/stats/{model_id}")
async def get_quality_stats(
    model_id: int,
    days: int = 30,
    db=Depends(get_db),
    quality_assessment_service: QualityAssessmentService = Depends(lambda: app.state.quality_assessment_service)
):
    """Получение статистики качества модели"""
    try:
        stats = await quality_assessment_service.get_quality_stats(model_id, days)
        return stats
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики качества: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Мониторинг здоровья системы
@app.get("/api/v1/health/system", response_model=SystemHealthResponse)
async def get_system_health(
    db=Depends(get_db),
    system_health_service: SystemHealthService = Depends(lambda: app.state.system_health_service)
):
    """Получение состояния здоровья системы"""
    try:
        health = await system_health_service.collect_system_health()
        return health
    except Exception as e:
        logger.error(f"❌ Ошибка получения состояния здоровья системы: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health/system/history")
async def get_system_health_history(
    hours: int = 24,
    db=Depends(get_db)
):
    """Получение истории состояния здоровья системы"""
    try:
        from datetime import datetime, timedelta
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = select(SystemHealth).where(
            SystemHealth.timestamp >= start_time
        ).order_by(SystemHealth.timestamp.desc())
        
        result = await db.execute(stmt)
        health_records = result.scalars().all()
        
        return {
            "records": [
                {
                    "timestamp": record.timestamp.isoformat(),
                    "cpu_usage": record.cpu_usage,
                    "memory_usage": record.memory_usage,
                    "disk_usage": record.disk_usage,
                    "ollama_status": record.ollama_status,
                    "rag_status": record.rag_status,
                    "response_time_avg": record.response_time_avg,
                    "error_rate": record.error_rate,
                    "alerts_count": len(record.alerts)
                }
                for record in health_records
            ]
        }
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории здоровья системы: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Расширенная статистика
@app.get("/api/v1/stats/models/{model_id}", response_model=ModelStatsResponse)
async def get_model_stats(
    model_id: int,
    days: int = 30,
    db=Depends(get_db)
):
    """Получение статистики модели"""
    try:
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Получаем модель
        model = await db.get(LLMModel, model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        # Получаем метрики
        stmt = select(PerformanceMetrics).where(
            and_(
                PerformanceMetrics.model_id == model_id,
                PerformanceMetrics.timestamp >= start_date
            )
        )
        
        result = await db.execute(stmt)
        metrics = result.scalars().all()
        
        if not metrics:
            return ModelStatsResponse(
                model_id=model_id,
                model_name=model.name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time=0.0,
                avg_quality_score=0.0,
                total_tokens_generated=0,
                total_tokens_processed=0,
                error_rate=0.0,
                last_used=None,
                performance_trend=[]
            )
        
        # Рассчитываем статистику
        total_requests = len(metrics)
        successful_requests = len([m for m in metrics if m.success])
        failed_requests = total_requests - successful_requests
        avg_response_time = np.mean([m.response_time for m in metrics if m.response_time])
        avg_quality_score = np.mean([m.user_feedback for m in metrics if m.user_feedback])
        total_tokens_generated = sum([m.tokens_generated for m in metrics if m.tokens_generated])
        total_tokens_processed = sum([m.tokens_processed for m in metrics if m.tokens_processed])
        error_rate = failed_requests / total_requests if total_requests > 0 else 0.0
        last_used = max([m.timestamp for m in metrics])
        
        # Тренд производительности (по дням)
        performance_trend = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_metrics = [m for m in metrics if day_start <= m.timestamp < day_end]
            if day_metrics:
                performance_trend.append({
                    "date": day_start.date().isoformat(),
                    "requests": len(day_metrics),
                    "avg_response_time": np.mean([m.response_time for m in day_metrics if m.response_time]),
                    "success_rate": len([m for m in day_metrics if m.success]) / len(day_metrics)
                })
        
        return ModelStatsResponse(
            model_id=model_id,
            model_name=model.name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            avg_quality_score=avg_quality_score,
            total_tokens_generated=total_tokens_generated,
            total_tokens_processed=total_tokens_processed,
            error_rate=error_rate,
            last_used=last_used,
            performance_trend=performance_trend
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики модели {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats/system", response_model=SystemStatsResponse)
async def get_system_stats(
    db=Depends(get_db),
    system_health_service: SystemHealthService = Depends(lambda: app.state.system_health_service)
):
    """Получение общей статистики системы"""
    try:
        # Получаем текущее состояние здоровья
        health = await system_health_service.collect_system_health()
        
        # Подсчитываем модели и маршруты
        models_stmt = select(func.count(LLMModel.id))
        active_models_stmt = select(func.count(LLMModel.id)).where(LLMModel.is_available == True)
        routes_stmt = select(func.count(ModelRoute.id))
        active_routes_stmt = select(func.count(ModelRoute.id)).where(ModelRoute.is_active == True)
        documents_stmt = select(func.count(RAGDocument.id))
        
        models_result = await db.execute(models_stmt)
        active_models_result = await db.execute(active_models_stmt)
        routes_result = await db.execute(routes_stmt)
        active_routes_result = await db.execute(active_routes_stmt)
        documents_result = await db.execute(documents_stmt)
        
        total_models = models_result.scalar() or 0
        active_models = active_models_result.scalar() or 0
        total_routes = routes_result.scalar() or 0
        active_routes = active_routes_result.scalar() or 0
        total_documents = documents_result.scalar() or 0
        
        # Получаем топ моделей
        top_models_stmt = select(LLMModel).order_by(LLMModel.avg_response_time.asc()).limit(5)
        top_models_result = await db.execute(top_models_stmt)
        top_models = top_models_result.scalars().all()
        
        top_models_stats = []
        for model in top_models:
            stats = await get_model_stats(model.id, days=1, db=db)
            top_models_stats.append(stats)
        
        return SystemStatsResponse(
            total_models=total_models,
            active_models=active_models,
            total_routes=total_routes,
            active_routes=active_routes,
            total_documents=total_documents,
            total_requests_today=health.total_requests,
            avg_response_time=health.response_time_avg,
            error_rate=health.error_rate,
            system_health=health,
            top_models=top_models_stats
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики системы: {e}")
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