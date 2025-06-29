"""
🔗 API роуты для сервиса внутренней перелинковки
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models import (
    InternalLink, 
    LinkRecommendation, 
    DomainAnalysisRequest,
    SEOAnalysisResult,
    LinkType
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

router = APIRouter(tags=["reLink Internal Linking"])

# Инициализация сервисов
internal_linking_service = InternalLinkingService()
seo_analyzer_service = SEOAnalyzerService()
content_analyzer_service = ContentAnalyzerService()

@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "reLink Internal Linking",
        "description": "Сервис анализа и оптимизации внутренних ссылок для SEO",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/api/v1/internal-links/analyze")
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

@router.post("/api/v1/internal-links/recommendations")
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

@router.post("/api/v1/seo/analyze", response_model=SEOAnalysisResult)
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

@router.post("/api/v1/content/analyze")
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

@router.get("/api/v1/metrics")
async def get_service_metrics(monitor = Depends(get_service_monitor)):
    """Получение метрик сервиса"""
    return {
        "service": "reLink Internal Linking",
        "metrics": monitor.get_effectiveness_report(),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/api/v1/endpoints")
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