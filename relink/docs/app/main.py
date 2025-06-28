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
from .services import docs_service, microservice_docs_service
from .models import (
    HealthResponse, VersionInfo, ReadmeInfo, RoadmapInfo,
    FAQEntry, AboutInfo, HowItWorksInfo, CacheStats,
    APIResponse, ErrorResponse,
    MicroserviceInfo, ServiceDocumentation, DocumentationSync,
    DocumentationSearch, DocumentationSearchResult
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
    logger.info("Documentation service starting up")
    
    # Инициализация сервиса микросервисов
    await microservice_docs_service.initialize()
    
    logger.info("Documentation service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    logger.info("Documentation service shutting down")
    
    # Очистка ресурсов
    await microservice_docs_service.cleanup()
    
    logger.info("Documentation service stopped")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        cache_status = "connected" if await cache.ping() else "disconnected"
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            cache_status=cache_status,
            uptime=time.time() - start_time
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


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
            message="Cache stats retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error("Error getting cache stats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/api/v1/cache/clear")
async def clear_cache():
    """Очистка кэша"""
    try:
        await cache.clear()
        
        return APIResponse(
            success=True,
            message="Cache cleared successfully"
        )
        
    except Exception as e:
        logger.error("Error clearing cache", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# 🚀 НОВЫЕ ЭНДПОИНТЫ ДЛЯ АВТОМАТИЧЕСКОЙ ДОКУМЕНТАЦИИ МИКРОСЕРВИСОВ

@app.get("/api/v1/services/discover", response_model=APIResponse)
async def discover_services():
    """Обнаружение доступных микросервисов"""
    try:
        services = await microservice_docs_service.discover_services()
        
        return APIResponse(
            success=True,
            message=f"Discovered {len(services)} services",
            data=[service.dict() for service in services]
        )
        
    except Exception as e:
        logger.error("Error discovering services", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/services", response_model=APIResponse)
async def get_all_services():
    """Получение списка всех известных сервисов"""
    try:
        services = await microservice_docs_service.get_all_services()
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(services)} services",
            data=[service.dict() for service in services]
        )
        
    except Exception as e:
        logger.error("Error getting services", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/services/{service_name}", response_model=APIResponse)
async def get_service_documentation(service_name: str):
    """Получение документации конкретного сервиса"""
    try:
        service_doc = await microservice_docs_service.get_service_documentation(service_name)
        
        if not service_doc:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        
        return APIResponse(
            success=True,
            message=f"Service documentation retrieved successfully",
            data=service_doc.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service documentation for {service_name}", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/services/{service_name}/sync", response_model=APIResponse)
async def sync_service_documentation(service_name: str):
    """Синхронизация документации конкретного сервиса"""
    try:
        sync_result = await microservice_docs_service.sync_service_documentation(service_name)
        
        return APIResponse(
            success=sync_result.status == "completed",
            message=f"Service documentation sync {sync_result.status}",
            data=sync_result.dict()
        )
        
    except Exception as e:
        logger.error(f"Error syncing service documentation for {service_name}", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/services/sync-all", response_model=APIResponse)
async def sync_all_services():
    """Синхронизация документации всех сервисов"""
    try:
        sync_results = []
        
        for service_name in microservice_docs_service.discovered_services.keys():
            sync_result = await microservice_docs_service.sync_service_documentation(service_name)
            sync_results.append(sync_result)
        
        completed = sum(1 for result in sync_results if result.status == "completed")
        failed = len(sync_results) - completed
        
        return APIResponse(
            success=completed > 0,
            message=f"Synced {completed} services, {failed} failed",
            data=[result.dict() for result in sync_results]
        )
        
    except Exception as e:
        logger.error("Error syncing all services", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/docs/search", response_model=APIResponse)
async def search_documentation(search: DocumentationSearch):
    """Поиск по документации всех сервисов"""
    try:
        search_result = await microservice_docs_service.search_documentation(search)
        
        return APIResponse(
            success=True,
            message=f"Found {search_result.total} results",
            data=search_result.dict()
        )
        
    except Exception as e:
        logger.error("Error searching documentation", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/services/{service_name}/health", response_model=APIResponse)
async def get_service_health(service_name: str):
    """Проверка здоровья конкретного сервиса"""
    try:
        discovery = microservice_docs_service.discovered_services.get(service_name)
        
        if not discovery:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        
        health_url = f"{discovery.base_url}{discovery.health_endpoint}"
        
        async with microservice_docs_service.session.get(health_url) as response:
            health_data = await response.json()
            
            return APIResponse(
                success=response.status == 200,
                message=f"Service health check completed",
                data={
                    "service_name": service_name,
                    "status": "healthy" if response.status == 200 else "unhealthy",
                    "response_time_ms": response.headers.get("X-Process-Time", "N/A"),
                    "health_data": health_data
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking service health for {service_name}", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/services/{service_name}/api-docs", response_model=APIResponse)
async def get_service_api_docs(service_name: str):
    """Получение API документации конкретного сервиса"""
    try:
        discovery = microservice_docs_service.discovered_services.get(service_name)
        
        if not discovery:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
        
        if not discovery.openapi_endpoint:
            raise HTTPException(status_code=404, detail=f"OpenAPI endpoint not configured for {service_name}")
        
        openapi_url = f"{discovery.base_url}{discovery.openapi_endpoint}"
        
        async with microservice_docs_service.session.get(openapi_url) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Failed to fetch OpenAPI spec")
            
            openapi_data = await response.json()
            endpoints = microservice_docs_service._parse_openapi_spec(openapi_data)
            
            return APIResponse(
                success=True,
                message=f"API documentation retrieved successfully",
                data={
                    "service_name": service_name,
                    "endpoints": [endpoint.dict() for endpoint in endpoints],
                    "openapi_spec": openapi_data
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API docs for {service_name}", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/sync/history", response_model=APIResponse)
async def get_sync_history(
    limit: int = Query(50, description="Количество записей"),
    offset: int = Query(0, description="Смещение")
):
    """Получение истории синхронизации"""
    try:
        history = microservice_docs_service.sync_history
        total = len(history)
        
        # Пагинация
        paginated_history = history[offset:offset + limit]
        
        return APIResponse(
            success=True,
            message=f"Sync history retrieved successfully",
            data={
                "history": [record.dict() for record in paginated_history],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error("Error getting sync history", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# MIDDLEWARE - ПРОМЕЖУТОЧНОЕ ПО
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Добавление времени обработки в заголовки"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ERROR HANDLERS - ОБРАБОТЧИКИ ОШИБОК
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


# HEALTH CHECK - ПРОВЕРКА ЗДОРОВЬЯ
@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 