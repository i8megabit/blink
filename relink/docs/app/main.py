"""
Основной файл FastAPI приложения для микросервиса документации
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import structlog

from .config import settings
from .cache import cache
from .services import docs_service
from .models import (
    DocumentType, DocumentationResponse, VersionResponse, 
    FAQResponse, AboutResponse, HowItWorksResponse,
    HealthResponse, CacheStatsResponse
)

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

# Время запуска для расчета uptime
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("Запуск микросервиса документации")
    
    # Подключение к Redis
    try:
        await cache.connect()
        logger.info("Redis подключен успешно")
    except Exception as e:
        logger.error("Ошибка подключения к Redis", error=str(e))
    
    yield
    
    # Остановка
    logger.info("Остановка микросервиса документации")
    await cache.disconnect()


# Создание FastAPI приложения
app = FastAPI(
    title=settings.app_name,
    description="Микросервис документации и управления версиями для SEO Link Recommender",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Корневой эндпоинт с информацией о сервисе"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SEO Link Recommender - Документация</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .endpoints { margin-top: 30px; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .method { font-weight: bold; color: #007bff; }
            .url { font-family: monospace; color: #666; }
            .description { margin-top: 5px; color: #555; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 SEO Link Recommender - Документация</h1>
            <p>Микросервис документации и управления версиями</p>
            
            <div class="endpoints">
                <h2>Доступные эндпоинты:</h2>
                
                <div class="endpoint">
                    <div class="method">GET</div>
                    <div class="url">/api/v1/health</div>
                    <div class="description">Проверка состояния сервиса</div>
                </div>
                
                <div class="endpoint">
                    <div class="method">GET</div>
                    <div class="url">/api/v1/version</div>
                    <div class="description">Информация о версии</div>
                </div>
                
                <div class="endpoint">
                    <div class="method">GET</div>
                    <div class="url">/api/v1/docs/{type}</div>
                    <div class="description">Получение документации (readme, roadmap, cicd, faq, about, how_it_works)</div>
                </div>
                
                <div class="endpoint">
                    <div class="method">GET</div>
                    <div class="url">/api/v1/cache/stats</div>
                    <div class="description">Статистика кэша Redis</div>
                </div>
                
                <div class="endpoint">
                    <div class="method">DELETE</div>
                    <div class="url">/api/v1/cache/clear</div>
                    <div class="description">Очистка кэша</div>
                </div>
            </div>
            
            <p style="text-align: center; margin-top: 30px; color: #666;">
                <a href="/docs">📖 Swagger документация</a> | 
                <a href="/redoc">📋 ReDoc документация</a>
            </p>
        </div>
    </body>
    </html>
    """


@app.get(f"{settings.api_prefix}/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервиса"""
    try:
        # Проверяем Redis
        redis_status = "connected" if cache.redis else "disconnected"
        
        # Рассчитываем uptime
        uptime = time.time() - start_time
        
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            redis_status=redis_status,
            uptime=uptime
        )
    except Exception as e:
        logger.error("Ошибка проверки здоровья", error=str(e))
        raise HTTPException(status_code=500, detail="Service unhealthy")


@app.get(f"{settings.api_prefix}/version", response_model=VersionResponse)
async def get_version(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение информации о версии"""
    try:
        version_info = await docs_service.get_version_info(force_refresh=force_refresh)
        
        # Проверяем, был ли кэш-хит
        cache_hit = await cache.exists("version_info") and not force_refresh
        
        return VersionResponse(
            success=True,
            data=version_info,
            cache_hit=cache_hit
        )
    except Exception as e:
        logger.error("Ошибка получения версии", error=str(e))
        return VersionResponse(
            success=False,
            error=str(e)
        )


@app.get(f"{settings.api_prefix}/docs/{{doc_type}}", response_model=DocumentationResponse)
async def get_document(
    doc_type: DocumentType,
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение документации по типу"""
    try:
        document = await docs_service.get_document(doc_type, force_refresh=force_refresh)
        
        # Проверяем, был ли кэш-хит
        cache_hit = await cache.exists(f"document_{doc_type.value}") and not force_refresh
        
        return DocumentationResponse(
            success=True,
            data=document,
            cache_hit=cache_hit
        )
    except Exception as e:
        logger.error("Ошибка получения документа", doc_type=doc_type, error=str(e))
        return DocumentationResponse(
            success=False,
            error=str(e)
        )


@app.get(f"{settings.api_prefix}/docs", response_model=DocumentationResponse)
async def get_document_by_type(
    type: str = Query(..., description="Тип документа"),
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение документации по строковому типу"""
    try:
        doc_type = DocumentType(type.lower())
        return await get_document(doc_type, force_refresh)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Неизвестный тип документа: {type}. Доступные типы: {[t.value for t in DocumentType]}"
        )


@app.get(f"{settings.api_prefix}/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Получение статистики кэша"""
    try:
        stats = await cache.get_stats()
        return CacheStatsResponse(
            success=True,
            data=stats
        )
    except Exception as e:
        logger.error("Ошибка получения статистики кэша", error=str(e))
        return CacheStatsResponse(
            success=False,
            error=str(e)
        )


@app.delete(f"{settings.api_prefix}/cache/clear")
async def clear_cache():
    """Очистка кэша"""
    try:
        # Очищаем все ключи с префиксом docs:
        cleared = await cache.clear_pattern("*")
        logger.info("Кэш очищен", cleared_keys=cleared)
        return {"success": True, "cleared_keys": cleared}
    except Exception as e:
        logger.error("Ошибка очистки кэша", error=str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка очистки кэша: {str(e)}")


@app.get(f"{settings.api_prefix}/docs/readme", response_model=DocumentationResponse)
async def get_readme(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение README документации"""
    return await get_document(DocumentType.README, force_refresh)


@app.get(f"{settings.api_prefix}/docs/roadmap", response_model=DocumentationResponse)
async def get_roadmap(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение технической дорожной карты"""
    return await get_document(DocumentType.ROADMAP, force_refresh)


@app.get(f"{settings.api_prefix}/docs/cicd", response_model=DocumentationResponse)
async def get_cicd(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение CI/CD документации"""
    return await get_document(DocumentType.CICD, force_refresh)


@app.get(f"{settings.api_prefix}/docs/faq", response_model=DocumentationResponse)
async def get_faq(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение FAQ"""
    return await get_document(DocumentType.FAQ, force_refresh)


@app.get(f"{settings.api_prefix}/docs/about", response_model=DocumentationResponse)
async def get_about(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение информации о программе"""
    return await get_document(DocumentType.ABOUT, force_refresh)


@app.get(f"{settings.api_prefix}/docs/how-it-works", response_model=DocumentationResponse)
async def get_how_it_works(
    force_refresh: bool = Query(False, description="Принудительное обновление кэша")
):
    """Получение описания работы системы"""
    return await get_document(DocumentType.HOW_IT_WORKS, force_refresh)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 