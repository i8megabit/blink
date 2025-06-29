"""
🚀 Бутстрап для всех микросервисов reLink
RAG-ориентированная архитектура с ChromaDB
"""

import os
import sys
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import chromadb
from chromadb.config import Settings as ChromaSettings
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .config import get_settings

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
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Глобальные переменные
chroma_client: Optional[chromadb.Client] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global chroma_client
    
    settings = get_settings()
    
    # Инициализация ChromaDB
    try:
        chroma_client = chromadb.HttpClient(
            host=settings.CHROMADB_HOST,
            port=settings.CHROMADB_PORT
        )
        logger.info("ChromaDB client initialized", 
                   host=settings.CHROMADB_HOST, 
                   port=settings.CHROMADB_PORT)
    except Exception as e:
        logger.error("Failed to initialize ChromaDB", error=str(e))
        chroma_client = None
    
    yield
    
    # Очистка ресурсов
    if chroma_client:
        try:
            chroma_client.close()
            logger.info("ChromaDB client closed")
        except Exception as e:
            logger.error("Error closing ChromaDB client", error=str(e))

def create_app() -> FastAPI:
    """Создание FastAPI приложения"""
    settings = get_settings()
    
    # Определение имени сервиса
    service_name = os.getenv("SERVICE_NAME", settings.SERVICE_NAME)
    
    app = FastAPI(
        title=f"reLink {service_name.title()} Service",
        description=f"Микросервис {service_name} для системы reLink",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Проверка здоровья сервиса"""
        from .rag_service import get_rag_service
        
        # Проверяем RAG сервис
        rag_service = get_rag_service()
        rag_health = await rag_service.health_check()
        
        health_status = {
            "status": "healthy",
            "service": service_name,
            "chromadb": rag_health.get("status", "unknown"),
            "chromadb_connected": rag_health.get("chromadb_connected", False),
            "collections_count": rag_health.get("collections_count", 0)
        }
        
        # Если ChromaDB не подключен, статус degraded
        if not rag_health.get("chromadb_connected", False):
            health_status["status"] = "degraded"
            health_status["warnings"] = ["ChromaDB not connected"]
            if "error" in rag_health:
                health_status["chromadb_error"] = rag_health["error"]
        
        return health_status
    
    # Динамическая загрузка роутеров сервисов
    load_service_routers(app, service_name)
    
    return app

def load_service_routers(app: FastAPI, service_name: str):
    """Динамическая загрузка роутеров в зависимости от сервиса"""
    try:
        if service_name == "router":
            from .routers import router_router
            app.include_router(router_router.router, prefix="/api/v1")
        elif service_name == "benchmark":
            from .routers import benchmark_router
            app.include_router(benchmark_router.router, prefix="/api/v1")
        elif service_name == "relink":
            from .routers import relink_router
            app.include_router(relink_router.router, prefix="/api/v1")
        elif service_name == "backend":
            from .routers import backend_router
            app.include_router(backend_router.router, prefix="/api/v1")
        elif service_name == "monitoring":
            from .routers import monitoring_router
            app.include_router(monitoring_router.router, prefix="/api/v1")
        elif service_name == "testing":
            from .routers import testing_router
            app.include_router(testing_router.router, prefix="/api/v1")
        else:
            logger.warning("Unknown service", service_name=service_name)
    except ImportError as e:
        logger.warning("Failed to load router", service_name=service_name, error=str(e))

def run_service():
    """Запуск сервиса"""
    import uvicorn
    
    settings = get_settings()
    service_name = os.getenv("SERVICE_NAME", settings.SERVICE_NAME)
    service_port = int(os.getenv("SERVICE_PORT", settings.SERVICE_PORT))
    
    logger.info("Starting service", 
               service_name=service_name, 
               port=service_port)
    
    uvicorn.run(
        "bootstrap.main:create_app",
        host="0.0.0.0",
        port=service_port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    run_service() 