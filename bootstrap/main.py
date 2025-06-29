"""
🚀 Главный модуль бутстрапа - создание FastAPI приложений
"""

import os
import importlib
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
    title: Optional[str] = None,
    description: Optional[str] = None,
    version: str = "1.0.0",
    debug: Optional[bool] = None,
    **kwargs
) -> FastAPI:
    """
    Создание FastAPI приложения с бутстрапом
    
    Args:
        title: Заголовок приложения (автоматически определяется из SERVICE_NAME)
        description: Описание приложения
        version: Версия приложения
        debug: Режим отладки
        **kwargs: Дополнительные параметры
    """
    
    settings = get_settings()
    
    # Автоматическое определение названия сервиса
    if title is None:
        title = settings.SERVICE_NAME or "reLink Service"
    
    if description is None:
        description = f"{title} - Микросервис reLink"
    
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
            "description": description,
            "port": settings.SERVICE_PORT
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
    
    # Автоматическая загрузка роутов сервиса
    try:
        service_name = settings.SERVICE_NAME.lower()
        if service_name and service_name != "unknown":
            # Попытка импорта роутера сервиса
            try:
                service_module = importlib.import_module(f"{service_name}.api")
                if hasattr(service_module, 'router'):
                    app.include_router(service_module.router, prefix="/api/v1")
                    logger.info("Service routes loaded", service=service_name)
            except ImportError:
                logger.warning("Service routes not found", service=service_name)
    except Exception as e:
        logger.warning("Failed to load service routes", error=str(e))
    
    logger.info(
        "Application created",
        title=title,
        version=version,
        debug=debug,
        service=settings.SERVICE_NAME
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

def run_service():
    """Запуск сервиса с автоматической конфигурацией"""
    import uvicorn
    
    settings = get_settings()
    
    # Создание приложения
    app = create_app()
    
    # Запуск сервера
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )

if __name__ == "__main__":
    run_service() 