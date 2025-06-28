"""
Основное приложение микросервиса мониторинга
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models import (
    HealthResponse, MetricsResponse, AlertsResponse, ServicesResponse,
    Alert, AlertCreate, AlertUpdate, AlertStatus, AlertSeverity,
    MetricsQuery, AlertsQuery, Service, ServiceStatus
)
from .services import (
    MetricsCollector, AlertService, HealthCheckService, DashboardService
)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.logging.level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные для сервисов
redis_client: redis.Redis = None
db_session: AsyncSession = None
metrics_collector: MetricsCollector = None
alert_service: AlertService = None
health_checker: HealthCheckService = None
dashboard_service: DashboardService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global redis_client, db_session, metrics_collector, alert_service, health_checker, dashboard_service
    
    # Инициализация Redis
    logger.info("Initializing Redis connection...")
    redis_client = redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        decode_responses=True
    )
    
    # Проверка подключения к Redis
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    
    # Инициализация базы данных
    logger.info("Initializing database connection...")
    try:
        engine = create_async_engine(
            settings.database.url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow
        )
        
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Тестовое подключение
        async with async_session() as session:
            await session.execute("SELECT 1")
        
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    # Инициализация сервисов
    logger.info("Initializing services...")
    metrics_collector = MetricsCollector()
    alert_service = AlertService()
    health_checker = HealthCheckService()
    dashboard_service = DashboardService()
    
    # Инициализация сервисов с зависимостями
    await metrics_collector.initialize(redis_client, None)  # TODO: передать session
    await alert_service.initialize(redis_client)
    await dashboard_service.initialize(redis_client)
    
    logger.info("All services initialized successfully")
    
    # Запуск фоновой задачи сбора метрик
    asyncio.create_task(metrics_collection_task())
    
    yield
    
    # Очистка ресурсов
    logger.info("Shutting down monitoring service...")
    if redis_client:
        await redis_client.close()
    logger.info("Monitoring service shutdown complete")


# Создание FastAPI приложения
app = FastAPI(
    title=settings.app_name,
    description="Мощный микросервис мониторинга для reLink",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Фоновая задача сбора метрик
async def metrics_collection_task():
    """Фоновая задача для регулярного сбора метрик"""
    while True:
        try:
            logger.debug("Collecting metrics...")
            
            # Сбор метрик
            metrics = await metrics_collector.collect_all_metrics()
            
            # Сохранение метрик в Redis
            if redis_client:
                await redis_client.setex(
                    f"{settings.redis.prefix}latest_metrics",
                    settings.redis.ttl,
                    str(metrics)
                )
            
            # Проверка алертов
            if alert_service:
                alerts = await alert_service.check_thresholds(metrics)
                if alerts:
                    await alert_service.save_alerts(alerts)
                    logger.warning(f"Generated {len(alerts)} alerts")
            
            # Проверка здоровья сервисов
            if health_checker:
                services = await health_checker.check_all_services()
                if redis_client:
                    await redis_client.setex(
                        f"{settings.redis.prefix}services_status",
                        settings.redis.ttl,
                        str([service.dict() for service in services])
                    )
            
            logger.debug("Metrics collection completed")
            
        except Exception as e:
            logger.error(f"Error in metrics collection task: {e}")
        
        # Ожидание до следующего сбора
        await asyncio.sleep(settings.monitoring.collect_interval)


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request, call_next):
    """Логирование HTTP запросов"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    
    return response


# API эндпоинты

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Корневой эндпоинт"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "timestamp": time.time()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса"""
    start_time = time.time()
    
    # Проверка зависимостей
    services_status = {}
    
    # Redis
    try:
        await redis_client.ping()
        services_status["redis"] = ServiceStatus.HEALTHY
    except Exception:
        services_status["redis"] = ServiceStatus.DOWN
    
    # База данных
    try:
        # TODO: добавить проверку БД
        services_status["database"] = ServiceStatus.HEALTHY
    except Exception:
        services_status["database"] = ServiceStatus.DOWN
    
    # Ollama
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.ollama.url}/api/tags", timeout=5) as response:
                if response.status == 200:
                    services_status["ollama"] = ServiceStatus.HEALTHY
                else:
                    services_status["ollama"] = ServiceStatus.DEGRADED
    except Exception:
        services_status["ollama"] = ServiceStatus.DOWN
    
    # Определение общего статуса
    if all(status == ServiceStatus.HEALTHY for status in services_status.values()):
        overall_status = "healthy"
    elif any(status == ServiceStatus.DOWN for status in services_status.values()):
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return HealthResponse(
        status=overall_status,
        version=settings.version,
        uptime=time.time() - start_time,
        services=services_status
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(query: MetricsQuery = Depends()):
    """Получение метрик"""
    try:
        if not metrics_collector:
            raise HTTPException(status_code=503, detail="Metrics collector not initialized")
        
        # Сбор текущих метрик
        metrics = await metrics_collector.collect_all_metrics()
        
        return MetricsResponse(
            system=metrics.get('system'),
            database=metrics.get('database'),
            cache=metrics.get('cache'),
            ollama=metrics.get('ollama'),
            http=[]  # TODO: добавить HTTP метрики
        )
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to collect metrics")


@app.get("/metrics/history")
async def get_metrics_history(query: MetricsQuery = Depends()):
    """Получение истории метрик"""
    try:
        if not redis_client:
            raise HTTPException(status_code=503, detail="Redis not available")
        
        # TODO: реализовать получение истории метрик
        return {"message": "Metrics history not implemented yet"}
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics history")


@app.get("/alerts", response_model=AlertsResponse)
async def get_alerts(query: AlertsQuery = Depends()):
    """Получение алертов"""
    try:
        if not alert_service:
            raise HTTPException(status_code=503, detail="Alert service not initialized")
        
        alerts = await alert_service.get_alerts(status=query.status)
        
        # Фильтрация по времени
        if query.start_time:
            alerts = [alert for alert in alerts if alert.created_at >= query.start_time]
        if query.end_time:
            alerts = [alert for alert in alerts if alert.created_at <= query.end_time]
        
        # Фильтрация по важности
        if query.severity:
            alerts = [alert for alert in alerts if alert.severity == query.severity]
        
        # Фильтрация по источнику
        if query.source:
            alerts = [alert for alert in alerts if alert.source == query.source]
        
        # Ограничение количества
        alerts = alerts[:query.limit]
        
        # Подсчет статистики
        total = len(alerts)
        active = sum(1 for alert in alerts if alert.status == AlertStatus.ACTIVE)
        resolved = sum(1 for alert in alerts if alert.status == AlertStatus.RESOLVED)
        
        return AlertsResponse(
            alerts=alerts,
            total=total,
            active=active,
            resolved=resolved
        )
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")


@app.post("/alerts", response_model=Alert)
async def create_alert(alert_data: AlertCreate):
    """Создание алерта"""
    try:
        if not alert_service:
            raise HTTPException(status_code=503, detail="Alert service not initialized")
        
        alert = Alert(
            name=alert_data.name,
            description=alert_data.description,
            severity=alert_data.severity,
            source=alert_data.source,
            metric_name=alert_data.metric_name,
            threshold=alert_data.threshold,
            current_value=alert_data.current_value
        )
        
        await alert_service.save_alerts([alert])
        
        return alert
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert")


@app.put("/alerts/{alert_id}")
async def update_alert(alert_id: str, alert_update: AlertUpdate):
    """Обновление алерта"""
    try:
        if not alert_service:
            raise HTTPException(status_code=503, detail="Alert service not initialized")
        
        await alert_service.update_alert_status(
            alert_id,
            alert_update.status,
            alert_update.acknowledged_by
        )
        
        return {"message": "Alert updated successfully"}
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert")


@app.get("/services", response_model=ServicesResponse)
async def get_services():
    """Получение статуса сервисов"""
    try:
        if not health_checker:
            raise HTTPException(status_code=503, detail="Health checker not initialized")
        
        services = await health_checker.check_all_services()
        
        # Подсчет статистики
        total = len(services)
        healthy = sum(1 for service in services if service.status == ServiceStatus.HEALTHY)
        degraded = sum(1 for service in services if service.status == ServiceStatus.DEGRADED)
        down = sum(1 for service in services if service.status == ServiceStatus.DOWN)
        
        return ServicesResponse(
            services=services,
            total=total,
            healthy=healthy,
            degraded=degraded,
            down=down
        )
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        raise HTTPException(status_code=500, detail="Failed to get services")


@app.get("/dashboard")
async def get_dashboard():
    """Получение данных дашборда"""
    try:
        if not dashboard_service:
            raise HTTPException(status_code=503, detail="Dashboard service not initialized")
        
        dashboard_data = await dashboard_service.get_dashboard_data()
        
        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@app.post("/metrics/collect")
async def trigger_metrics_collection(background_tasks: BackgroundTasks):
    """Принудительный сбор метрик"""
    try:
        if not metrics_collector:
            raise HTTPException(status_code=503, detail="Metrics collector not initialized")
        
        # Запуск сбора метрик в фоне
        background_tasks.add_task(metrics_collection_task)
        
        return {"message": "Metrics collection triggered"}
    except Exception as e:
        logger.error(f"Error triggering metrics collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger metrics collection")


@app.get("/prometheus")
async def prometheus_metrics():
    """Эндпоинт для Prometheus метрик"""
    try:
        # TODO: реализовать экспорт метрик в формате Prometheus
        return {"message": "Prometheus metrics not implemented yet"}
    except Exception as e:
        logger.error(f"Error getting Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Prometheus metrics")


# Обработчики ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.debug,
        log_level=settings.logging.level.lower()
    ) 