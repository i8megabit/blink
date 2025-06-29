"""
🚀 Главный модуль бутстрапа - создание FastAPI приложений
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import structlog

from .config import get_settings
from .logging import setup_logging
from .monitoring import get_service_monitor

# Настройка логирования
setup_logging()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск приложения
    logger.info("Starting application", service=app.title)
    
    # Инициализация мониторинга
    monitor = get_service_monitor()
    logger.info("Monitoring initialized")
    
    yield
    
    # Завершение приложения
    logger.info("Shutting down application", service=app.title)

def create_app(
    title: str,
    description: str,
    version: str = "1.0.0",
    debug: Optional[bool] = None,
    **kwargs
) -> FastAPI:
    """
    Создание FastAPI приложения с бутстрапом
    
    Args:
        title: Заголовок приложения
        description: Описание приложения
        version: Версия приложения
        debug: Режим отладки
        **kwargs: Дополнительные параметры
    """
    
    settings = get_settings()
    
    # Определение режима отладки
    if debug is None:
        debug = settings.DEBUG
    
    # Создание приложения
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        debug=debug,
        lifespan=lifespan,
        **kwargs
    )
    
    # Добавление CORS middleware
    cors_origins = settings.CORS_ORIGINS.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Добавление TrustedHost middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # В продакшене нужно ограничить
    )
    
    # Добавление health check endpoint
    @app.get("/health")
    async def health_check():
        """Проверка здоровья сервиса"""
        return {
            "status": "healthy",
            "service": title,
            "version": version,
            "description": description
        }
    
    # Добавление metrics endpoint
    if settings.METRICS_ENABLED:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import Response
        
        @app.get("/metrics")
        async def metrics():
            """Метрики Prometheus"""
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
    
    logger.info(
        "Application created",
        title=title,
        version=version,
        debug=debug
    )
    
    return app

def add_service_routes(app: FastAPI, router, prefix: str = "/api/v1"):
    """
    Добавление роутов сервиса в приложение
    
    Args:
        app: FastAPI приложение
        router: Роутер сервиса
        prefix: Префикс для роутов
    """
    app.include_router(router, prefix=prefix)
    logger.info("Service routes added", prefix=prefix) 