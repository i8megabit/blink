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
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Глобальные переменные
settings = get_settings()
chroma_client: Optional[chromadb.Client] = None

def initialize_chromadb() -> chromadb.Client:
    """Инициализация ChromaDB клиента"""
    global chroma_client
    
    try:
        chroma_settings = ChromaSettings(
            chroma_api_impl="rest",
            chroma_server_host=settings.CHROMADB_HOST,
            chroma_server_http_port=settings.CHROMADB_PORT,
            chroma_server_ssl_enabled=False,
            anonymized_telemetry=False
        )
        
        chroma_client = chromadb.Client(chroma_settings)
        
        # Проверка подключения
        collections = chroma_client.list_collections()
        logger.info(
            "ChromaDB initialized successfully",
            host=settings.CHROMADB_HOST,
            port=settings.CHROMADB_PORT,
            collections_count=len(collections)
        )
        
        return chroma_client
        
    except Exception as e:
        logger.error(
            "Failed to initialize ChromaDB",
            error=str(e),
            host=settings.CHROMADB_HOST,
            port=settings.CHROMADB_PORT
        )
        raise

def get_chroma_client() -> chromadb.Client:
    """Получение глобального ChromaDB клиента"""
    global chroma_client
    if chroma_client is None:
        chroma_client = initialize_chromadb()
    return chroma_client

def create_app(
    title: str = "reLink Microservice",
    description: str = "Микросервис reLink с RAG интеграцией",
    version: str = "1.0.0"
) -> FastAPI:
    """Создание FastAPI приложения с бутстрапом"""
    
    # Инициализация ChromaDB
    try:
        initialize_chromadb()
    except Exception as e:
        logger.error("Failed to initialize ChromaDB during app creation", error=str(e))
    
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Проверка здоровья сервиса"""
        try:
            # Проверка ChromaDB
            chroma_status = "healthy"
            try:
                client = get_chroma_client()
                collections = client.list_collections()
                chroma_collections = len(collections)
            except Exception as e:
                chroma_status = "unhealthy"
                chroma_collections = 0
                logger.error("ChromaDB health check failed", error=str(e))
            
            return {
                "status": "healthy",
                "service": settings.SERVICE_NAME,
                "version": version,
                "chromadb": {
                    "status": chroma_status,
                    "collections_count": chroma_collections
                },
                "timestamp": asyncio.get_event_loop().time()
            }
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            raise HTTPException(status_code=500, detail="Service unhealthy")
    
    # ChromaDB endpoints
    @app.get("/api/v1/chromadb/collections")
    async def list_collections():
        """Получение списка коллекций ChromaDB"""
        try:
            client = get_chroma_client()
            collections = client.list_collections()
            return {
                "collections": [
                    {
                        "name": col.name,
                        "count": col.count(),
                        "metadata": col.metadata
                    }
                    for col in collections
                ]
            }
        except Exception as e:
            logger.error("Failed to list collections", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/chromadb/collections/{collection_name}")
    async def get_collection_info(collection_name: str):
        """Получение информации о коллекции"""
        try:
            client = get_chroma_client()
            collection = client.get_collection(collection_name)
            
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
        except Exception as e:
            logger.error(f"Failed to get collection {collection_name}", error=str(e))
            raise HTTPException(status_code=404, detail="Collection not found")
    
    @app.post("/api/v1/chromadb/collections/{collection_name}")
    async def create_collection(collection_name: str, metadata: Dict[str, Any] = None):
        """Создание новой коллекции"""
        try:
            client = get_chroma_client()
            collection = client.create_collection(
                name=collection_name,
                metadata=metadata or {}
            )
            
            logger.info(f"Collection {collection_name} created successfully")
            return {
                "name": collection.name,
                "metadata": collection.metadata,
                "status": "created"
            }
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

def run_service():
    """Запуск сервиса"""
    import uvicorn
    
    logger.info(
        "Starting reLink microservice",
        service_name=settings.SERVICE_NAME,
        port=settings.SERVICE_PORT,
        debug=settings.DEBUG
    )
    
    # Создание приложения
    app = create_app(
        title=f"reLink {settings.SERVICE_NAME.title()}",
        description=f"Микросервис {settings.SERVICE_NAME} с RAG интеграцией",
        version="1.0.0"
    )
    
    # Запуск сервера
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    run_service() 