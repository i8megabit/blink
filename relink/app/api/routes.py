"""
🔗 API роуты для сервиса внутренней перелинковки
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import asyncio

from ..models import (
    InternalLink, 
    LinkRecommendation, 
    DomainAnalysisRequest,
    SEOAnalysisResult,
    LinkType,
    DomainAnalysisResponse,
    SEORecommendationRequest,
    SEORecommendationResponse,
    InternalLinkAnalysis,
    PostAnalysis,
    IndexingStatus
)
from ..services.internal_linking import InternalLinkingService
from ..services.seo_analyzer import SEOAnalyzerService
from ..services.content_analyzer import ContentAnalyzerService
from bootstrap.llm_router import get_llm_router
from bootstrap.rag_service import get_rag_service
from bootstrap.ollama_client import get_ollama_client
from bootstrap.monitoring import get_service_monitor

# Настройка логирования
logger = logging.getLogger(__name__)

router = APIRouter(tags=["reLink Internal Linking"], prefix="/api/v1")

# Инициализация сервисов
internal_linking_service = InternalLinkingService()
seo_analyzer_service = SEOAnalyzerService()
content_analyzer_service = ContentAnalyzerService()

# Глобальный экземпляр сервиса
_linking_service: Optional[InternalLinkingService] = None

def get_linking_service() -> InternalLinkingService:
    """Получение экземпляра сервиса внутренней перелинковки"""
    global _linking_service
    if _linking_service is None:
        _linking_service = InternalLinkingService()
    return _linking_service

@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "reLink Internal Linking",
        "description": "Сервис анализа и оптимизации внутренних ссылок для SEO",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.post("/internal-links/analyze")
async def analyze_internal_links(
    request: DomainAnalysisRequest,
    llm_router = Depends(get_llm_router),
    rag_service = Depends(get_rag_service),
    ollama_client = Depends(get_ollama_client),
    monitor = Depends(get_service_monitor)
):
    """Анализ внутренних ссылок для домена"""
    
    # Отслеживание запроса
    request_data = await monitor.track_request("/internal-links/analyze", f"req_{datetime.now().timestamp()}")
    
    try:
        # Анализ через внутренний сервис
        analysis_result = await internal_linking_service.analyze_domain(
            domain=request.domain,
            llm_router=llm_router,
            rag_service=rag_service,
            ollama_client=ollama_client
        )
        
        # Завершение запроса
        await monitor.complete_request(request_data["request_id"], "success", analysis_result)
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Ошибка при анализе внутренних ссылок: {e}")
        await monitor.complete_request(request_data["request_id"], "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка анализа внутренних ссылок: {str(e)}"
        )

@router.post("/internal-links/recommendations")
async def get_link_recommendations(
    request: DomainAnalysisRequest,
    llm_router = Depends(get_llm_router),
    rag_service = Depends(get_rag_service),
    ollama_client = Depends(get_ollama_client),
    monitor = Depends(get_service_monitor)
):
    """Получение рекомендаций по внутренним ссылкам"""
    
    request_data = await monitor.track_request("/internal-links/recommendations", f"req_{datetime.now().timestamp()}")
    
    try:
        # Генерация рекомендаций
        recommendations = await internal_linking_service.generate_recommendations(
            domain=request.domain,
            llm_router=llm_router,
            rag_service=rag_service,
            ollama_client=ollama_client
        )
        
        await monitor.complete_request(request_data["request_id"], "success", {"recommendations": recommendations})
        
        return {
            "status": "success",
            "domain": request.domain,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка при генерации рекомендаций: {e}")
        await monitor.complete_request(request_data["request_id"], "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации рекомендаций: {str(e)}"
        )

@router.post("/seo/analyze", response_model=SEOAnalysisResult)
async def analyze_seo(
    request: DomainAnalysisRequest,
    llm_router = Depends(get_llm_router),
    rag_service = Depends(get_rag_service),
    ollama_client = Depends(get_ollama_client),
    monitor = Depends(get_service_monitor)
):
    """Комплексный SEO анализ с фокусом на внутренние ссылки"""
    
    request_data = await monitor.track_request("/seo/analyze", f"req_{datetime.now().timestamp()}")
    
    try:
        # SEO анализ
        seo_result = await seo_analyzer_service.analyze_domain(
            domain=request.domain,
            comprehensive=request.comprehensive,
            llm_router=llm_router,
            rag_service=rag_service,
            ollama_client=ollama_client
        )
        
        await monitor.complete_request(request_data["request_id"], "success", seo_result)
        
        return seo_result
        
    except Exception as e:
        logger.error(f"Ошибка при SEO анализе: {e}")
        await monitor.complete_request(request_data["request_id"], "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка SEO анализа: {str(e)}"
        )

@router.post("/content/analyze")
async def analyze_content(
    domain: str,
    llm_router = Depends(get_llm_router),
    rag_service = Depends(get_rag_service),
    ollama_client = Depends(get_ollama_client),
    monitor = Depends(get_service_monitor)
):
    """Анализ контента для оптимизации внутренних ссылок"""
    
    request_data = await monitor.track_request("/content/analyze", f"req_{datetime.now().timestamp()}")
    
    try:
        # Анализ контента
        content_analysis = await content_analyzer_service.analyze_content(
            domain=domain,
            llm_router=llm_router,
            rag_service=rag_service,
            ollama_client=ollama_client
        )
        
        await monitor.complete_request(request_data["request_id"], "success", content_analysis)
        
        return content_analysis
        
    except Exception as e:
        logger.error(f"Ошибка при анализе контента: {e}")
        await monitor.complete_request(request_data["request_id"], "error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка анализа контента: {str(e)}"
        )

@router.get("/metrics")
async def get_service_metrics(monitor = Depends(get_service_monitor)):
    """Получение метрик сервиса"""
    return {
        "service": "reLink Internal Linking",
        "metrics": monitor.get_effectiveness_report(),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/endpoints")
async def get_endpoints():
    """Получение списка доступных эндпоинтов"""
    return {
        "service": "reLink Internal Linking",
        "endpoints": [
            "/health",
            "/api/v1/internal-links/analyze",
            "/api/v1/internal-links/recommendations", 
            "/api/v1/seo/analyze",
            "/api/v1/content/analyze",
            "/api/v1/metrics",
            "/api/v1/endpoints"
        ]
    }

@router.post("/index-domain", response_model=IndexingStatus)
async def index_domain(
    domain: str = "dagorod.ru",
    background_tasks: BackgroundTasks = None
):
    """Индексация домена для анализа"""
    try:
        service = get_linking_service()
        
        # Запускаем индексацию в фоне
        if background_tasks:
            background_tasks.add_task(service.index_domain, domain)
            return IndexingStatus(
                status="started",
                message=f"Индексация домена {domain} запущена в фоне",
                domain=domain,
                timestamp=datetime.now().isoformat()
            )
        else:
            # Синхронная индексация для тестирования
            result = await service.index_domain(domain)
            return IndexingStatus(
                status="completed",
                message=f"Индексация домена {domain} завершена",
                domain=domain,
                timestamp=datetime.now().isoformat(),
                data=result
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка индексации: {str(e)}")

@router.get("/indexing-status/{domain}")
async def get_indexing_status(domain: str):
    """Получение статуса индексации"""
    try:
        service = get_linking_service()
        status = await service.get_indexing_status(domain)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

@router.post("/analyze-domain", response_model=DomainAnalysisResponse)
async def analyze_domain(request: DomainAnalysisRequest):
    """Анализ домена и внутренних ссылок"""
    try:
        service = get_linking_service()
        
        # Анализируем домен
        analysis = await service.analyze_domain(
            domain=request.domain,
            include_posts=request.include_posts,
            include_recommendations=request.include_recommendations
        )
        
        return DomainAnalysisResponse(
            domain=request.domain,
            analysis=analysis,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")

@router.post("/generate-recommendations", response_model=SEORecommendationResponse)
async def generate_seo_recommendations(request: SEORecommendationRequest):
    """Генерация SEO рекомендаций на основе анализа"""
    try:
        service = get_linking_service()
        
        # Генерируем рекомендации
        recommendations = await service.generate_recommendations(
            domain=request.domain,
            focus_areas=request.focus_areas,
            priority=request.priority
        )
        
        return SEORecommendationResponse(
            domain=request.domain,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации рекомендаций: {str(e)}")

@router.get("/internal-links/{domain}")
async def get_internal_links(domain: str, limit: int = 50):
    """Получение анализа внутренних ссылок домена"""
    try:
        service = get_linking_service()
        links = await service.get_internal_links(domain, limit=limit)
        return {
            "domain": domain,
            "internal_links": links,
            "total_count": len(links),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения ссылок: {str(e)}")

@router.get("/posts/{domain}")
async def get_posts(domain: str, limit: int = 20):
    """Получение проиндексированных постов домена"""
    try:
        service = get_linking_service()
        posts = await service.get_posts(domain, limit=limit)
        return {
            "domain": domain,
            "posts": posts,
            "total_count": len(posts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения постов: {str(e)}")

@router.post("/analyze-seo")
async def analyze_seo_content(request: Dict[str, Any]):
    """Анализ SEO контента"""
    try:
        service = get_linking_service()
        
        analysis = await service.analyze_seo_content(
            url=request.get("url"),
            title=request.get("title"),
            content=request.get("content"),
            meta_description=request.get("meta_description")
        )
        
        return {
            "url": request.get("url"),
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка SEO анализа: {str(e)}")

@router.get("/dashboard/{domain}")
async def get_dashboard_data(domain: str):
    """Получение данных для дашборда"""
    try:
        service = get_linking_service()
        
        # Собираем все данные для дашборда
        dashboard_data = await service.get_dashboard_data(domain)
        
        return {
            "domain": domain,
            "dashboard": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных дашборда: {str(e)}")

@router.post("/export-analysis/{domain}")
async def export_analysis(domain: str, format: str = "json"):
    """Экспорт результатов анализа"""
    try:
        service = get_linking_service()
        
        if format.lower() == "json":
            data = await service.export_analysis_json(domain)
            return JSONResponse(
                content=data,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={domain}_analysis.json"
                }
            )
        elif format.lower() == "csv":
            data = await service.export_analysis_csv(domain)
            return JSONResponse(
                content=data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={domain}_analysis.csv"
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Неподдерживаемый формат экспорта")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")

# Специальный эндпоинт для dagorod.ru
@router.post("/analyze-dagorod")
async def analyze_dagorod_special():
    """Специальный анализ для dagorod.ru"""
    try:
        service = get_linking_service()
        
        # Индексируем домен
        await service.index_domain("dagorod.ru")
        
        # Анализируем
        analysis = await service.analyze_domain("dagorod.ru", include_posts=True, include_recommendations=True)
        
        # Генерируем рекомендации
        recommendations = await service.generate_recommendations(
            domain="dagorod.ru",
            focus_areas=["internal_linking", "content_optimization", "technical_seo"],
            priority="high"
        )
        
        return {
            "domain": "dagorod.ru",
            "analysis": analysis,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat(),
            "message": "Специальный анализ dagorod.ru завершен"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа dagorod.ru: {str(e)}") 