"""
Основное FastAPI приложение для микросервиса документации
"""

import logging
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from .config import settings
from .cache import cache
from .services import docs_service
from .models import (
    HealthResponse, VersionInfo, ReadmeInfo, RoadmapInfo,
    FAQEntry, AboutInfo, HowItWorksInfo, CacheStats,
    APIResponse, ErrorResponse
)

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)

# Настройка structlog
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

# Создание FastAPI приложения
app = FastAPI(
    title=settings.app_name,
    description="Микросервис документации и управления версиями",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные переменные
start_time = time.time()


@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    logger.info("Starting documentation service", version=settings.app_version)
    
    # Подключаемся к Redis
    await cache.connect()
    logger.info("Documentation service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    logger.info("Shutting down documentation service")
    
    # Отключаемся от Redis
    await cache.disconnect()
    logger.info("Documentation service shutdown complete")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса"""
    uptime = time.time() - start_time
    
    # Проверяем статус кэша
    cache_stats = await cache.get_stats()
    cache_status = "connected" if cache_stats.get("connected", False) else "disconnected"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        cache_status=cache_status,
        uptime=uptime
    )


@app.get("/api/v1/version", response_model=APIResponse)
async def get_version(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение информации о версии"""
    try:
        version_info = await docs_service.get_version_info(force_refresh=force_refresh)
        
        if not version_info:
            raise HTTPException(status_code=404, detail="Version information not found")
        
        return APIResponse(
            success=True,
            message="Version information retrieved successfully",
            data=version_info.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting version info", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/docs/readme", response_model=APIResponse)
async def get_readme(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение README документации"""
    try:
        readme_info = await docs_service.get_readme_info(force_refresh=force_refresh)
        
        if not readme_info:
            raise HTTPException(status_code=404, detail="README not found")
        
        return APIResponse(
            success=True,
            message="README retrieved successfully",
            data=readme_info.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting README", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/docs/roadmap", response_model=APIResponse)
async def get_roadmap(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение технического roadmap"""
    try:
        roadmap_info = await docs_service.get_roadmap_info(force_refresh=force_refresh)
        
        if not roadmap_info:
            raise HTTPException(status_code=404, detail="Roadmap not found")
        
        return APIResponse(
            success=True,
            message="Roadmap retrieved successfully",
            data=roadmap_info.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting roadmap", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/docs/faq", response_model=APIResponse)
async def get_faq(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение FAQ"""
    try:
        faq_entries = await docs_service.get_faq_entries(force_refresh=force_refresh)
        
        return APIResponse(
            success=True,
            message="FAQ retrieved successfully",
            data=[entry.dict() for entry in faq_entries]
        )
        
    except Exception as e:
        logger.error("Error getting FAQ", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/docs/about", response_model=APIResponse)
async def get_about(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение информации о проекте"""
    try:
        about_info = await docs_service.get_about_info(force_refresh=force_refresh)
        
        if not about_info:
            raise HTTPException(status_code=404, detail="About information not found")
        
        return APIResponse(
            success=True,
            message="About information retrieved successfully",
            data=about_info.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting about info", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/docs/how-it-works", response_model=APIResponse)
async def get_how_it_works(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение информации о том, как работает система"""
    try:
        how_it_works_info = await docs_service.get_how_it_works_info(force_refresh=force_refresh)
        
        if not how_it_works_info:
            raise HTTPException(status_code=404, detail="How it works information not found")
        
        return APIResponse(
            success=True,
            message="How it works information retrieved successfully",
            data=how_it_works_info.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting how it works info", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/cache/stats", response_model=APIResponse)
async def get_cache_stats():
    """Получение статистики кэша"""
    try:
        stats = await cache.get_stats()
        
        return APIResponse(
            success=True,
            message="Cache statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/api/v1/cache/clear", response_model=APIResponse)
async def clear_cache():
    """Очистка кэша"""
    try:
        success = await cache.clear()
        
        if success:
            return APIResponse(
                success=True,
                message="Cache cleared successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error clearing cache", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=str(exc.status_code)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработчик общих исключений"""
    logger.error("Unhandled exception", error=str(exc), exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 