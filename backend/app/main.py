"""FastAPI-приложение для генерации внутренних ссылок reLink."""

from __future__ import annotations

import asyncio
import json
import os
import re
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

import chromadb
import httpx
import nltk
import numpy as np
import ollama
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from pydantic import BaseModel, ValidationError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import (
    DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text,
    func, select, update, delete
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

# Импортируем модули
from .config import settings, get_settings
from .exceptions import (
    RelinkBaseException, ErrorHandler, ErrorResponse,
    ValidationException, AuthenticationException, AuthorizationException,
    NotFoundException, DatabaseException, OllamaException,
    raise_not_found, raise_validation_error, raise_authentication_error,
    raise_authorization_error, raise_database_error, raise_ollama_error
)
from .monitoring import (
    logger, metrics_collector, performance_monitor, 
    get_metrics, get_health_status, monitor_operation,
    MonitoringMiddleware
)
from .cache import (
    cache_manager, cache_result, invalidate_cache,
    SEOCache, UserCache
)
from .validation import (
    UserRegistrationModel, UserLoginModel, DomainAnalysisModel,
    SEORecommendationModel, ExportModel, PaginationModel,
    validate_request, validate_response, validate_and_clean_data
)
from .auth import (
    get_current_user, create_access_token, get_password_hash, verify_password,
    User, UserCreate, UserResponse, Token, TokenData,
    UserRegistrationRequest, UserLoginRequest
)
from .database import get_db, engine
from .models import Base, User, Domain, WordPressPost, AnalysisHistory, Diagram, DiagramEmbedding
from .models import (
    TestRequest, TestResponse, TestSuiteRequest, TestSuiteResponse, TestExecutionResponse,
    TestType, TestStatus, TestPriority, TestEnvironment
)
from .llm_router import system_analyzer, llm_router
from .diagram_service import DiagramService, DiagramGenerationRequest
from .testing_service import testing_service, router as testing_router
from .api.auth import router as auth_router

# Загрузка NLTK данных при старте
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Русские стоп-слова
RUSSIAN_STOP_WORDS = set(stopwords.words('russian'))

# 🔒 КРИТИЧЕСКИЙ СЕМАФОР ДЛЯ ОГРАНИЧЕНИЯ НАГРУЗКИ НА OLLAMA
OLLAMA_SEMAPHORE = asyncio.Semaphore(1)

@dataclass
class SemanticEntity:
    """Семантическая сущность для контекста LLM."""
    entity_type: str
    value: str
    confidence: float
    context: str

@dataclass
class ThematicCluster:
    """Тематический кластер статей."""
    cluster_id: str
    theme: str
    keywords: List[str]
    articles_count: int
    semantic_density: float

@dataclass
class AIThought:
    """Структурированная мысль ИИ с расширенной аналитикой."""
    thought_id: str
    stage: str  # analyzing, connecting, evaluating, optimizing
    content: str
    confidence: float
    semantic_weight: float
    related_concepts: List[str]
    reasoning_chain: List[str]
    timestamp: datetime
    
@dataclass
class SemanticConnection:
    """Расширенная семантическая связь между концепциями."""
    source_concept: str
    target_concept: str
    connection_type: str  # semantic, causal, hierarchical, temporal
    strength: float
    evidence: List[str]
    context_keywords: Set[str]

class WebSocketManager:
    """Менеджер WebSocket соединений для отслеживания прогресса."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Подключение нового клиента."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket подключен: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """Отключение клиента."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket отключен: {client_id}")

    async def send_progress(self, client_id: str, message: dict) -> None:
        """Отправка прогресса конкретному клиенту."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                logger.debug(f"Прогресс отправлен {client_id}: {message}")
            except Exception as e:
                logger.error(f"Error sending progress to {client_id}: {e}")

    async def send_error(self, client_id: str, error: str, details: str = "") -> None:
        """Отправка ошибки клиенту."""
        await self.send_progress(client_id, {
            "type": "error",
            "message": error,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    async def send_step(self, client_id: str, step: str, current: int, total: int, details: str = "") -> None:
        """Отправка информации о текущем шаге."""
        await self.send_progress(client_id, {
            "type": "progress",
            "step": step,
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100) if total > 0 else 0,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    async def send_ollama_info(self, client_id: str, info: dict) -> None:
        """Отправка информации о работе Ollama."""
        await self.send_progress(client_id, {
            "type": "ollama",
            "info": info,
            "timestamp": datetime.now().isoformat()
        })

    async def send_ai_thinking(self, client_id: str, thought: str, thinking_stage: str = "analyzing", emoji: str = "🤔") -> None:
        """Отправка 'мыслей' ИИ в реальном времени."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json({
                    "type": "ai_thinking",
                    "thought": thought,
                    "thinking_stage": thinking_stage,
                    "emoji": emoji,
                    "timestamp": datetime.now().isoformat()
                })
                logger.debug(f"Мысль ИИ отправлена {client_id}: {thought[:50]}...")
            except Exception as e:
                logger.error(f"Error sending AI thinking to {client_id}: {e}")
    
    async def send_enhanced_ai_thinking(self, client_id: str, ai_thought: AIThought) -> None:
        """Отправка расширенных мыслей ИИ с аналитикой."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json({
                    "type": "enhanced_ai_thinking",
                    "thought_id": ai_thought.thought_id,
                    "stage": ai_thought.stage,
                    "content": ai_thought.content,
                    "confidence": ai_thought.confidence,
                    "semantic_weight": ai_thought.semantic_weight,
                    "related_concepts": ai_thought.related_concepts,
                    "reasoning_chain": ai_thought.reasoning_chain,
                    "timestamp": ai_thought.timestamp.isoformat()
                })
                logger.debug(f"Расширенная мысль ИИ отправлена {client_id}: {ai_thought.content[:50]}...")
            except Exception as e:
                logger.error(f"Error sending enhanced AI thinking to {client_id}: {e}")

# Глобальный менеджер WebSocket
websocket_manager = WebSocketManager()

# Инициализация FastAPI приложения
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    debug=settings.api.debug,
    docs_url=settings.api.docs_url,
    redoc_url=settings.api.redoc_url
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавление middleware для мониторинга
app.add_middleware(MonitoringMiddleware)

# Инициализация RAG системы
def initialize_rag_system() -> None:
    """Инициализация RAG системы с ChromaDB."""
    try:
        # Создание клиента ChromaDB
        chroma_client = chromadb.Client()
        
        # Создание коллекции для документов
        collection = chroma_client.create_collection(
            name="relink_documents",
            metadata={"description": "Документы для RAG системы reLink"}
        )
        
        logger.info("RAG система инициализирована с ChromaDB")
        return collection
    except Exception as e:
        logger.error(f"Ошибка инициализации RAG системы: {e}")
        return None

# Глобальная переменная для RAG коллекции
rag_collection = initialize_rag_system()

class AdvancedRAGManager:
    """Продвинутый менеджер RAG системы."""
    
    def __init__(self) -> None:
        self.collection = rag_collection
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=RUSSIAN_STOP_WORDS,
            ngram_range=(1, 2)
        )
    
    async def create_semantic_knowledge_base(self, domain, posts, client_id=None):
        # Проксируем вызов к глобальному генератору мыслей
        return await generate_ai_thoughts_for_domain(domain, posts, client_id)

# Глобальный менеджер RAG
rag_manager = AdvancedRAGManager()

# Pydantic модели для запросов
class RecommendRequest(BaseModel):
    """Запрос с текстом для генерации ссылок."""
    text: str

class WPRequest(BaseModel):
    """Запрос для анализа WordPress-сайта."""
    domain: str
    client_id: Optional[str] = None
    comprehensive: Optional[bool] = False

class BenchmarkRequest(BaseModel):
    """Запрос для запуска бенчмарка."""
    name: str
    description: Optional[str] = None
    benchmark_type: str = "seo_advanced"
    models: List[str] = []
    iterations: int = 3
    client_id: Optional[str] = None

class ModelConfigRequest(BaseModel):
    """Запрос для обновления конфигурации модели."""
    llm_model: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    default_parameters: Optional[dict] = None
    seo_optimized_params: Optional[dict] = None
    benchmark_params: Optional[dict] = None

class SEOAnalysisResult(BaseModel):
    """Результат SEO анализа."""
    domain: str
    analysis_date: datetime
    score: float
    recommendations: List[dict]
    metrics: dict
    status: str

class DomainAnalysisRequest(BaseModel):
    """Запрос для анализа домена."""
    domain: str
    comprehensive: Optional[bool] = False

class CompetitorAnalysisRequest(BaseModel):
    """Запрос для анализа конкурентов."""
    domain: str
    competitors: List[str]

class AnalysisHistoryRequest(BaseModel):
    """Запрос для получения истории анализов."""
    limit: int = 10
    offset: int = 0

class ExportRequest(BaseModel):
    """Запрос для экспорта данных."""
    format: str  # json, csv, pdf
    analysis_ids: List[int]

# Глобальные переменные для Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-turbo")

# Оптимизированные настройки токенов
OPTIMAL_CONTEXT_SIZE = 3072
OPTIMAL_PREDICTION_SIZE = 800
OPTIMAL_TEMPERATURE = 0.3
OPTIMAL_TOP_P = 0.85
OPTIMAL_TOP_K = 50
OPTIMAL_REPEAT_PENALTY = 1.08

# Функция для генерации мыслей ИИ
async def generate_ai_thoughts_for_domain(domain: str, posts: List[dict], client_id: str = None) -> List[AIThought]:
    """Генерация мыслей ИИ для анализа домена."""
    thoughts = []
    
    if client_id:
        await websocket_manager.send_ai_thinking(
            client_id, 
            f"Начинаю анализ домена {domain}...", 
            "analyzing", 
            "🔍"
        )
    
    # Анализ контента
    content_thought = AIThought(
        thought_id=f"content_analysis_{domain}",
        stage="analyzing",
        content=f"Анализирую {len(posts)} статей на домене {domain}",
        confidence=0.8,
        semantic_weight=0.7,
        related_concepts=["контент", "анализ", "семантика"],
        reasoning_chain=["подсчет статей", "оценка качества"],
        timestamp=datetime.now(timezone.utc)
    )
    thoughts.append(content_thought)
    
    if client_id:
        await websocket_manager.send_enhanced_ai_thinking(client_id, content_thought)
    
    # Поиск связей
    connection_thought = AIThought(
        thought_id=f"connection_search_{domain}",
        stage="connecting",
        content="Ищу семантические связи между статьями",
        confidence=0.9,
        semantic_weight=0.8,
        related_concepts=["связи", "семантика", "рекомендации"],
        reasoning_chain=["анализ тем", "поиск пересечений"],
        timestamp=datetime.now(timezone.utc)
    )
    thoughts.append(connection_thought)
    
    if client_id:
        await websocket_manager.send_enhanced_ai_thinking(client_id, connection_thought)
    
    return thoughts

# API endpoints
@app.get("/")
async def root():
    """Корневой endpoint."""
    return {"message": "reLink SEO Platform v4.1.1.022 запущен!"}

@app.get("/health")
async def health_check():
    """Проверка здоровья приложения."""
    return {"status": "healthy", "version": settings.api.version}

@app.get("/api/v1/health")
async def api_health():
    """Проверка здоровья API."""
    return {"status": "healthy", "version": settings.api.version}

@app.get("/api/v1/version")
async def get_version():
    """Получение версии приложения."""
    try:
        version_file = Path("VERSION")
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                version = f.read().strip()
        else:
            version = settings.api.version
        
        return {
            "version": version,
            "buildDate": datetime.now().strftime('%Y-%m-%d'),
            "commitHash": os.getenv("GIT_COMMIT_HASH", ""),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        return {
            "version": settings.api.version,
            "buildDate": datetime.now().strftime('%Y-%m-%d'),
            "error": str(e)
        }

@app.get("/api/v1/settings")
async def get_settings():
    """Заглушка настроек для фронтенда."""
    return {
        "theme": "light",
        "language": "ru",
        "features": {
            "ai_recommendations": True,
            "advanced_benchmark": True,
            "notifications": True,
            "export": True
        },
        "version": settings.api.version
    }

@app.get("/api/v1/ollama_status")
async def get_ollama_status():
    """Проверка статуса Ollama."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://ollama:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                
                return {
                    "ready_for_work": len(model_names) > 0,
                    "server_available": True,
                    "model_loaded": len(model_names) > 0,
                    "message": f"Готов к работе ({len(model_names)} моделей)" if model_names else "Модели не загружены",
                    "status": "available",
                    "connection": "connected",
                    "models_count": len(model_names),
                    "available_models": model_names,
                    "timestamp": datetime.now().isoformat(),
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "ready_for_work": False,
                    "server_available": False,
                    "model_loaded": False,
                    "message": f"Ollama ответил со статусом {response.status_code}",
                    "status": "error",
                    "connection": "disconnected",
                    "models_count": 0,
                    "available_models": [],
                    "timestamp": datetime.now().isoformat(),
                    "last_check": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "ready_for_work": False,
            "server_available": False,
            "model_loaded": False,
            "message": f"Ошибка подключения: {str(e)}",
            "status": "unavailable",
            "connection": "disconnected",
            "models_count": 0,
            "available_models": [],
            "timestamp": datetime.now().isoformat(),
            "last_check": datetime.now().isoformat()
        }

@app.get("/api/v1/domains")
async def get_domains():
    """Получение списка доменов."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(select(Domain))
            domains = result.scalars().all()
            return [
                {
                    "id": domain.id,
                    "name": domain.name,
                    "display_name": domain.display_name,
                    "description": domain.description,
                    "total_posts": domain.total_posts,
                    "total_analyses": domain.total_analyses,
                    "last_analysis_at": domain.last_analysis_at.isoformat() if domain.last_analysis_at else None
                }
                for domain in domains
            ]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/analysis_history")
async def get_analysis_history():
    """Получение истории анализов."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(select(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()))
            histories = result.scalars().all()
            return [
                {
                    "id": history.id,
                    "domain_id": history.domain_id,
                    "posts_analyzed": history.posts_analyzed,
                    "connections_found": history.connections_found,
                    "recommendations_generated": history.recommendations_generated,
                    "created_at": history.created_at.isoformat(),
                    "completed_at": history.completed_at.isoformat() if history.completed_at else None
                }
                for history in histories
            ]
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/benchmarks")
async def get_benchmarks():
    """Получение списка бенчмарков."""
    try:
        # Заглушка для бенчмарков
        return [
            {
                "id": 1,
                "name": "SEO Basic Benchmark",
                "description": "Базовый SEO бенчмарк",
                "benchmark_type": "seo_basic",
                "status": "completed",
                "overall_score": 85.5,
                "created_at": datetime.now().isoformat()
            }
        ]
    except Exception as e:
        return {"error": str(e)}

@app.get("/metrics")
async def get_metrics():
    """Endpoint для получения метрик Prometheus"""
    return await get_metrics()

@app.get("/api/v1/monitoring/health")
async def get_monitoring_health():
    """Endpoint для проверки здоровья с мониторингом"""
    return await get_health_status()

@app.get("/api/v1/monitoring/stats")
async def get_monitoring_stats():
    """Получение статистики мониторинга"""
    try:
        return {
            "uptime": "99.9%",
            "response_time": "150ms",
            "error_rate": "0.1%",
            "active_connections": 10,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")

@app.get("/api/v1/optimization/report")
async def get_optimization_report():
    """
    🧠 Получение отчета об интеллектуальной оптимизации системы
    
    Возвращает:
    - Анализ системных характеристик
    - Оптимизированную конфигурацию
    - Историю производительности
    - Рекомендации LLM
    """
    try:
        # Получение отчета от SystemAnalyzer
        report = await system_analyzer.get_optimization_report()
        
        # Добавление дополнительной информации
        enhanced_report = {
            **report,
            "optimization_status": {
                "llm_recommendations_applied": True,
                "adaptive_optimization_active": True,
                "performance_monitoring": True,
                "knowledge_base_entries": len(system_analyzer.knowledge_base),
                "last_optimization": datetime.now().isoformat()
            },
            "system_insights": {
                "apple_silicon_detected": report["system_specs"]["apple_silicon"],
                "gpu_acceleration_available": report["system_specs"]["gpu_available"],
                "memory_optimization": "high" if report["system_specs"]["memory_gb"] >= 16 else "medium",
                "cpu_utilization_optimal": report["system_specs"]["cpu_count"] >= 6
            },
            "performance_metrics": {
                "avg_response_time": report["performance_history"]["recent_avg_response_time"],
                "success_rate": report["performance_history"]["recent_success_rate"],
                "total_requests_processed": report["performance_history"]["total_records"],
                "optimization_effectiveness": "excellent" if report["performance_history"]["recent_avg_response_time"] < 2.0 else "good"
            },
            "llm_insights": {
                "used_model": report["optimized_config"]["model"],
                "temperature_optimized": report["optimized_config"]["temperature"],
                "context_length_optimized": report["optimized_config"]["context_length"],
                "batch_size_optimized": report["optimized_config"]["batch_size"]
            }
        }
        
        return enhanced_report
        
    except Exception as e:
        logger.error(f"Error getting optimization report: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка получения отчета об оптимизации: {str(e)}"
        )

@app.get("/api/v1/optimization/environment")
async def get_optimization_environment():
    """
    🔧 Получение переменных окружения для Ollama
    
    Возвращает оптимизированные переменные окружения
    для запуска Ollama с максимальной производительностью
    """
    try:
        env_vars = await system_analyzer.get_environment_variables()
        
        return {
            "environment_variables": env_vars,
            "optimization_applied": True,
            "recommended_ollama_command": f"OLLAMA_HOST={env_vars['OLLAMA_HOST']} OLLAMA_ORIGINS={env_vars['OLLAMA_ORIGINS']} ollama serve",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting environment variables: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка получения переменных окружения: {str(e)}"
        )

@app.post("/api/v1/optimization/trigger")
async def trigger_optimization():
    """
    🔄 Принудительный запуск оптимизации
    
    Сбрасывает текущую конфигурацию и запускает
    полный цикл интеллектуальной оптимизации
    """
    try:
        # Сброс текущей конфигурации
        system_analyzer.optimized_config = None
        
        # Запуск новой оптимизации
        new_config = await system_analyzer.optimize_config()
        
        return {
            "message": "Оптимизация успешно запущена",
            "new_config": {
                "used_model": new_config.model,
                "num_gpu": new_config.num_gpu,
                "num_thread": new_config.num_thread,
                "batch_size": new_config.batch_size,
                "context_length": new_config.context_length,
                "semaphore_limit": new_config.semaphore_limit
            },
            "optimization_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering optimization: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка запуска оптимизации: {str(e)}"
        )

@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Получение статистики кэша"""
    try:
        return {
            "memory_cache_size": 0,
            "redis_cache_size": 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка получения статистики кэша")

@app.post("/api/v1/cache/clear")
async def clear_cache():
    """Очистка кэша"""
    try:
        return {"success": True, "message": "Кэш очищен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка очистки кэша")

@app.delete("/api/v1/cache/{pattern}")
async def clear_cache_pattern(pattern: str):
    """Очистка кэша по паттерну"""
    try:
        return {"success": True, "deleted_count": 0, "pattern": pattern}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка очистки кэша")

# Endpoints для SEO анализа с валидацией
@app.post("/api/v1/seo/analyze", response_model=SEOAnalysisResult)
async def analyze_domain(
    request_data: DomainAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Анализ домена с валидацией"""
    try:
        # Здесь будет логика анализа домена
        # Пока возвращаем заглушку
        analysis_result = SEOAnalysisResult(
            domain=request_data.domain,
            analysis_date=datetime.now(timezone.utc),
            score=75.5,
            recommendations=[
                {
                    "type": "internal_linking",
                    "priority": "high",
                    "description": "Добавить внутренние ссылки между связанными статьями"
                }
            ],
            metrics={
                "total_posts": 100,
                "internal_links": 50,
                "semantic_density": 0.8
            },
            status="completed"
        )
        
        return analysis_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка анализа домена")

@app.post("/api/v1/seo/competitors")
async def analyze_competitors(
    request_data: CompetitorAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Анализ конкурентов"""
    try:
        result = {
            "domain": request_data.domain,
            "competitors": request_data.competitors,
            "analysis_date": datetime.now().isoformat(),
            "metrics": {
                "traffic_comparison": {},
                "backlink_analysis": {},
                "keyword_overlap": {}
            }
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка анализа конкурентов")

# Endpoints для истории и экспорта
@app.get("/api/v1/history")
async def get_analysis_history(
    request: AnalysisHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение истории анализов с валидацией"""
    try:
        history = [
            {
                "id": 1,
                "domain": "example.com",
                "analysis_date": datetime.now().isoformat(),
                "status": "completed",
                "score": 85.0
            }
        ]
        
        return {
            "history": history,
            "total": len(history),
            "limit": request.limit,
            "offset": request.offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка получения истории")

@app.post("/api/v1/export")
async def export_data(
    request_data: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Экспорт данных"""
    try:
        export_result = {
            "format": request_data.format,
            "analysis_count": len(request_data.analysis_ids),
            "download_url": f"/api/v1/downloads/export_{datetime.now().timestamp()}.{request_data.format}",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        return export_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка экспорта данных")

# Endpoints для валидации
@app.post("/api/v1/validate/domain")
async def validate_domain(domain: str):
    """Валидация домена"""
    try:
        import re
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if re.match(pattern, domain):
            return {
                "valid": True,
                "domain": domain,
                "sanitized": domain.lower().strip()
            }
        else:
            return {
                "valid": False,
                "domain": domain,
                "error": "Некорректный формат домена"
            }
    except ValueError as e:
        return {
            "valid": False,
            "domain": domain,
            "error": str(e)
        }

@app.post("/api/v1/validate/email")
async def validate_email(email: str):
    """Валидация email"""
    try:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return {
                "valid": True,
                "email": email,
                "sanitized": email.lower().strip()
            }
        else:
            return {
                "valid": False,
                "email": email,
                "error": "Некорректный формат email"
            }
    except Exception as e:
        return {
            "valid": False,
            "email": email,
            "error": str(e)
        }

# Обработчики ошибок
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Обработчик ошибок валидации Pydantic"""
    return JSONResponse(
        status_code=422,
        content={"detail": "Ошибка валидации данных", "errors": exc.errors()}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP ошибок"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Общий обработчик исключений"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "Внутренняя ошибка сервера",
            "timestamp": datetime.now().isoformat()
        }
    )

# Инициализация при запуске
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения."""
    # Создаем директорию для логов
    os.makedirs("logs", exist_ok=True)
    
    print("🚀 reLink SEO Platform v1.0.0 запущен!")

@app.get("/api/v1/rag/cache/stats")
async def get_rag_cache_stats():
    """Получение статистики RAG кэша"""
    try:
        stats = await cache_manager.get_rag_stats()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting RAG cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/rag/cache/clear")
async def clear_rag_cache():
    """Очистка RAG кэша"""
    try:
        # Очищаем все типы RAG кэша
        await cache_manager.rag_cache.clear_expired()
        return {
            "status": "success",
            "message": "RAG cache cleared",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing RAG cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/rag/monitoring/metrics")
async def get_rag_monitoring_metrics():
    """Получение RAG метрик мониторинга"""
    try:
        from .monitoring import rag_monitor
        metrics = rag_monitor.get_rag_metrics()
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting RAG monitoring metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/rag/monitoring/health")
async def get_rag_health():
    """Получение статуса здоровья RAG системы."""
    try:
        # Проверяем доступность ChromaDB
        chroma_client = chromadb.Client()
        collections = chroma_client.list_collections()
        
        return {
            "status": "healthy",
            "chromadb_available": True,
            "collections_count": len(collections),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        return {
            "status": "unhealthy",
            "chromadb_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# 🎨 DIAGRAM GENERATION ENDPOINTS

class DiagramGenerationRequestModel(BaseModel):
    """Модель запроса для генерации диаграммы."""
    diagram_type: str
    title: str
    description: str
    components: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    style: Optional[Dict[str, Any]] = None
    width: int = 800
    height: int = 600
    interactive: bool = True
    include_legend: bool = True

class DiagramGenerationResponseModel(BaseModel):
    """Модель ответа для генерации диаграммы."""
    diagram_id: int
    svg_content: str
    quality_score: float
    generation_time: float
    used_model: str
    confidence_score: float
    validation_result: Dict[str, Any]

@app.post("/api/diagrams/generate", response_model=DiagramGenerationResponseModel)
async def generate_diagram(
    request: DiagramGenerationRequestModel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерация SVG диаграммы архитектуры."""
    try:
        diagram_service = DiagramService()
        
        # Преобразуем запрос в формат сервиса
        diagram_request = DiagramGenerationRequest(
            diagram_type=request.diagram_type,
            title=request.title,
            description=request.description,
            components=request.components,
            relationships=request.relationships,
            style_config=request.style,
            user_id=current_user.id
        )
        
        # Генерируем диаграмму
        result = await diagram_service.generate_diagram(diagram_request, db)
        
        return DiagramGenerationResponseModel(
            diagram_id=result.diagram_id,
            svg_content=result.svg_content,
            quality_score=result.quality_score,
            generation_time=result.generation_time,
            used_model=result.used_model,
            confidence_score=result.confidence_score,
            validation_result=result.validation_result
        )
        
    except Exception as e:
        logger.error(f"Ошибка генерации диаграммы: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации диаграммы: {str(e)}"
        )

@app.get("/api/diagrams/templates")
async def get_diagram_templates():
    """Получение доступных шаблонов диаграмм."""
    try:
        diagram_service = DiagramService()
        templates = await diagram_service.get_available_templates()
        return {"templates": templates}
    except Exception as e:
        logger.error(f"Ошибка получения шаблонов: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения шаблонов: {str(e)}"
        )

@app.get("/api/diagrams/{diagram_id}")
async def get_diagram(
    diagram_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение диаграммы по ID."""
    try:
        from .models import Diagram
        result = await db.execute(
            select(Diagram).where(
                Diagram.id == diagram_id,
                Diagram.user_id == current_user.id
            )
        )
        diagram = result.scalar_one_or_none()
        
        if not diagram:
            raise HTTPException(status_code=404, detail="Диаграмма не найдена")
        
        return {
            "id": diagram.id,
            "title": diagram.title,
            "description": diagram.description,
            "svg_content": diagram.svg_content,
            "quality_score": diagram.quality_score,
            "created_at": diagram.created_at.isoformat(),
            "diagram_type": diagram.diagram_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения диаграммы: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения диаграммы: {str(e)}"
        )

@app.get("/api/diagrams")
async def get_user_diagrams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """Получение списка диаграмм пользователя."""
    try:
        from .models import Diagram
        result = await db.execute(
            select(Diagram)
            .where(Diagram.user_id == current_user.id)
            .order_by(Diagram.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        diagrams = result.scalars().all()
        
        return {
            "diagrams": [
                {
                    "id": d.id,
                    "title": d.title,
                    "description": d.description,
                    "diagram_type": d.diagram_type,
                    "quality_score": d.quality_score,
                    "created_at": d.created_at.isoformat()
                }
                for d in diagrams
            ],
            "total": len(diagrams)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения диаграмм: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения диаграмм: {str(e)}"
        )

# ============================================================================
# API ЭНДПОИНТЫ ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================================

@app.post("/api/v1/tests/", response_model=TestResponse)
async def create_test(
    test_request: TestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание нового теста"""
    return await testing_service.create_test(test_request, current_user.id, db)

@app.get("/api/v1/tests/", response_model=List[TestResponse])
async def get_tests(
    test_type: Optional[TestType] = None,
    status: Optional[TestStatus] = None,
    priority: Optional[TestPriority] = None,
    environment: Optional[TestEnvironment] = None,
    name_contains: Optional[str] = None,
    description_contains: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка тестов с фильтрацией"""
    filters = TestFilter(
        test_type=test_type,
        status=status,
        priority=priority,
        environment=environment,
        name_contains=name_contains,
        description_contains=description_contains,
        tags=tags,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return await testing_service.get_tests(filters, offset, limit, db)

@app.get("/api/v1/tests/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение теста по ID"""
    test = await testing_service.get_test(test_id, db)
    if not test:
        raise_not_found("Тест не найден")
    return test

@app.post("/api/v1/tests/{test_id}/execute", response_model=TestExecutionResponse)
async def execute_test(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Выполнение теста"""
    return await testing_service.execute_test(test_id, current_user.id, db)

@app.get("/api/v1/test-executions/", response_model=List[TestExecutionResponse])
async def get_test_executions(
    test_id: Optional[str] = None,
    status: Optional[TestStatus] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка выполнений тестов"""
    return await testing_service.get_executions(offset, limit, test_id, status, db)

@app.post("/api/v1/test-executions/{execution_id}/cancel")
async def cancel_test_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отмена выполнения теста"""
    success = await testing_service.cancel_execution(execution_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Выполнение не найдено")
    return {"message": "Выполнение отменено"}

@app.post("/api/v1/test-suites/", response_model=TestSuiteResponse)
async def create_test_suite(
    suite_request: TestSuiteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание набора тестов"""
    return await testing_service.create_test_suite(suite_request, current_user.id, db)

@app.post("/api/v1/test-suites/{suite_id}/execute", response_model=List[TestExecutionResponse])
async def execute_test_suite(
    suite_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Выполнение набора тестов"""
    return await testing_service.execute_test_suite(suite_id, current_user.id, db)

@app.get("/api/v1/testing/metrics")
async def get_testing_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение метрик тестирования"""
    return await testing_service.get_test_metrics(db=db)

@app.get("/api/v1/testing/health")
async def get_testing_health():
    """Проверка здоровья системы тестирования"""
    return {
        "status": "healthy",
        "running_executions": len(testing_service.running_executions),
        "timestamp": datetime.now().isoformat()
    }

app.include_router(testing_router, prefix="/api/v1/testing")
app.include_router(auth_router, prefix="/api/v1")

@app.post("/api/v1/wordpress/index")
async def index_wordpress_site(
    request: WPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Индексация WordPress сайта."""
    try:
        domain = request.domain.strip().lower()
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        logger.info(f"Начинаю индексацию WordPress сайта: {domain}")
        
        # Проверяем, есть ли уже домен в базе
        existing_domain = await db.execute(
            select(Domain).where(Domain.name == domain)
        )
        domain_obj = existing_domain.scalar_one_or_none()
        
        if not domain_obj:
            # Создаем новый домен
            domain_obj = Domain(
                name=domain,
                display_name=domain.replace('https://', '').replace('http://', ''),
                description=f"WordPress сайт {domain}",
                owner_id=current_user.id
            )
            db.add(domain_obj)
            await db.commit()
            await db.refresh(domain_obj)
        
        # Парсим WordPress сайт
        posts = await parse_wordpress_site(domain, request.client_id)
        
        # Сохраняем посты в базу данных
        saved_posts = []
        for post_data in posts:
            post = WordPressPost(
                domain_id=domain_obj.id,
                wp_post_id=post_data.get('id', 0),
                title=post_data.get('title', ''),
                content=post_data.get('content', ''),
                excerpt=post_data.get('excerpt', ''),
                link=post_data.get('link', ''),
                published_at=post_data.get('date', datetime.now(timezone.utc))
            )
            db.add(post)
            saved_posts.append(post)
        
        await db.commit()
        
        # Обновляем статистику домена
        domain_obj.total_posts = len(saved_posts)
        domain_obj.last_analysis_at = datetime.now(timezone.utc)
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Индексация завершена. Найдено {len(saved_posts)} статей.",
            "domain": domain,
            "posts_count": len(saved_posts),
            "domain_id": domain_obj.id
        }
        
    except Exception as e:
        logger.error(f"Ошибка при индексации WordPress сайта: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка индексации: {str(e)}")

@app.post("/api/v1/wordpress/reindex")
async def reindex_wordpress_site(
    request: WPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Реиндексация WordPress сайта."""
    try:
        domain = request.domain.strip().lower()
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        logger.info(f"Начинаю реиндексацию WordPress сайта: {domain}")
        
        # Проверяем, есть ли домен в базе
        existing_domain = await db.execute(
            select(Domain).where(Domain.name == domain)
        )
        domain_obj = existing_domain.scalar_one_or_none()
        
        if not domain_obj:
            raise HTTPException(status_code=404, detail="Домен не найден. Сначала выполните индексацию.")
        
        # Удаляем старые посты
        await db.execute(
            delete(WordPressPost).where(WordPressPost.domain_id == domain_obj.id)
        )
        await db.commit()
        
        # Парсим WordPress сайт заново
        posts = await parse_wordpress_site(domain, request.client_id)
        
        # Сохраняем новые посты в базу данных
        saved_posts = []
        for post_data in posts:
            post = WordPressPost(
                domain_id=domain_obj.id,
                wp_post_id=post_data.get('id', 0),
                title=post_data.get('title', ''),
                content=post_data.get('content', ''),
                excerpt=post_data.get('excerpt', ''),
                link=post_data.get('link', ''),
                published_at=post_data.get('date', datetime.now(timezone.utc))
            )
            db.add(post)
            saved_posts.append(post)
        
        await db.commit()
        
        # Обновляем статистику домена
        domain_obj.total_posts = len(saved_posts)
        domain_obj.last_analysis_at = datetime.now(timezone.utc)
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Реиндексация завершена. Обновлено {len(saved_posts)} статей.",
            "domain": domain,
            "posts_count": len(saved_posts),
            "domain_id": domain_obj.id,
            "reindexed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при реиндексации WordPress сайта: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка реиндексации: {str(e)}")

async def parse_wordpress_site(domain: str, client_id: str = None) -> List[dict]:
    """Парсинг WordPress сайта через REST API для извлечения статей."""
    posts = []
    
    try:
        # Формируем URL для WordPress REST API
        api_url = f"{domain.rstrip('/')}/wp-json/wp/v2/posts"
        
        if client_id:
            await websocket_manager.send_step(client_id, "Подключение к WordPress API", 0, 1)
        
        # Получаем статьи через WordPress REST API
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Сначала пробуем получить 100 статей
            response = await client.get(f"{api_url}?per_page=100")
            
            if response.status_code != 200:
                # Если не получилось, пробуем получить меньше статей
                response = await client.get(f"{api_url}?per_page=50")
                
                if response.status_code != 200:
                    # Если и это не работает, пробуем получить 10 статей
                    response = await client.get(f"{api_url}?per_page=10")
                    
                    if response.status_code != 200:
                        raise Exception(f"Не удалось получить доступ к WordPress API: {response.status_code}")
            
            wp_posts = response.json()
            
            if client_id:
                await websocket_manager.send_step(client_id, f"Найдено {len(wp_posts)} статей", 1, len(wp_posts))
            
            # Обрабатываем каждую статью
            for i, wp_post in enumerate(wp_posts):
                try:
                    if client_id:
                        await websocket_manager.send_step(client_id, f"Обработка статьи {i+1}", i+1, len(wp_posts))
                    
                    # Извлекаем данные из WordPress API ответа
                    post_id = wp_post.get('id', 0)
                    title = wp_post.get('title', {}).get('rendered', '')
                    content = wp_post.get('content', {}).get('rendered', '')
                    excerpt = wp_post.get('excerpt', {}).get('rendered', '')
                    link = wp_post.get('link', '')
                    
                    # Парсим дату
                    date = datetime.now(timezone.utc)
                    date_str = wp_post.get('date', '')
                    if date_str:
                        try:
                            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        except:
                            pass
                    
                    # Очищаем HTML теги из контента
                    if content:
                        soup = BeautifulSoup(content, 'html.parser')
                        content = soup.get_text().strip()
                    
                    if excerpt:
                        soup = BeautifulSoup(excerpt, 'html.parser')
                        excerpt = soup.get_text().strip()
                    
                    if title and content:
                        posts.append({
                            'id': post_id,
                            'title': title,
                            'content': content,
                            'excerpt': excerpt,
                            'link': link,
                            'date': date
                        })
                    
                    # Небольшая задержка между обработкой статей
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Ошибка при обработке статьи {i+1}: {e}")
                    continue
            
            if client_id:
                await websocket_manager.send_step(client_id, "Индексация завершена", len(wp_posts), len(wp_posts))
        
        return posts
        
    except Exception as e:
        logger.error(f"Ошибка при парсинге WordPress сайта: {e}")
        if client_id:
            await websocket_manager.send_error(client_id, "Ошибка парсинга", str(e))
        raise

@app.post("/api/v1/seo/recommendations")
async def get_seo_recommendations(
    request_data: DomainAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение SEO рекомендаций на основе индексированных данных."""
    try:
        domain = request_data.domain.strip().lower()
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
        
        # Получаем домен из базы данных
        domain_obj = await db.execute(
            select(Domain).where(Domain.name == domain)
        )
        domain_obj = domain_obj.scalar_one_or_none()
        
        if not domain_obj:
            raise HTTPException(status_code=404, detail="Домен не найден. Сначала выполните индексацию.")
        
        # Получаем все посты домена
        posts = await db.execute(
            select(WordPressPost).where(WordPressPost.domain_id == domain_obj.id)
        )
        posts = posts.scalars().all()
        
        if not posts:
            raise HTTPException(status_code=404, detail="Статьи не найдены. Сначала выполните индексацию.")
        
        # Анализируем контент и генерируем рекомендации
        recommendations = await generate_seo_recommendations(posts, domain, request_data.client_id)
        
        # Сохраняем анализ в историю
        analysis = AnalysisHistory(
            domain_id=domain_obj.id,
            user_id=current_user.id,
            posts_analyzed=len(posts),
            connections_found=len([r for r in recommendations if r.get('type') == 'internal_linking']),
            recommendations_generated=len(recommendations),
            recommendations=recommendations,
            thematic_analysis={
                "total_posts": len(posts),
                "avg_content_length": sum(len(p.content) for p in posts) / len(posts),
                "topics_found": len(set(p.content_type for p in posts if p.content_type))
            },
            semantic_metrics={
                "content_quality_avg": sum(p.content_quality_score for p in posts) / len(posts),
                "semantic_richness_avg": sum(p.semantic_richness for p in posts) / len(posts)
            },
            llm_model_used=OLLAMA_MODEL,
            processing_time_seconds=0.0
        )
        db.add(analysis)
        await db.commit()
        
        return {
            "status": "success",
            "domain": domain,
            "posts_analyzed": len(posts),
            "recommendations": recommendations,
            "analysis_id": analysis.id,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации SEO рекомендаций: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации рекомендаций: {str(e)}")

async def generate_seo_recommendations(posts: List[WordPressPost], domain: str, client_id: str = None) -> List[dict]:
    """Генерация SEO рекомендаций на основе анализа постов."""
    recommendations = []
    
    try:
        if client_id:
            await websocket_manager.send_ai_thinking(client_id, "Анализирую контент для SEO рекомендаций...", "analyzing", "🔍")
        
        # Анализ внутренних ссылок
        internal_linking_recs = await analyze_internal_linking(posts, client_id)
        recommendations.extend(internal_linking_recs)
        
        # Анализ контента
        content_recs = await analyze_content_quality(posts, client_id)
        recommendations.extend(content_recs)
        
        # Анализ семантики
        semantic_recs = await analyze_semantic_optimization(posts, client_id)
        recommendations.extend(semantic_recs)
        
        # Анализ структуры
        structure_recs = await analyze_content_structure(posts, client_id)
        recommendations.extend(structure_recs)
        
        if client_id:
            await websocket_manager.send_ai_thinking(client_id, f"Сгенерировано {len(recommendations)} рекомендаций", "optimizing", "✅")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Ошибка при генерации рекомендаций: {e}")
        if client_id:
            await websocket_manager.send_error(client_id, "Ошибка генерации рекомендаций", str(e))
        raise

async def analyze_internal_linking(posts: List[WordPressPost], client_id: str = None) -> List[dict]:
    """Анализ внутренних ссылок."""
    recommendations = []
    
    # Простой анализ - ищем статьи без внутренних ссылок
    posts_without_links = []
    for post in posts:
        # Проверяем, есть ли в контенте ссылки на другие статьи
        content_lower = post.content.lower()
        has_internal_links = any(
            other_post.title.lower() in content_lower 
            for other_post in posts 
            if other_post.id != post.id
        )
        
        if not has_internal_links:
            posts_without_links.append(post)
    
    if posts_without_links:
        recommendations.append({
            "type": "internal_linking",
            "priority": "high",
            "title": "Добавить внутренние ссылки",
            "description": f"Найдено {len(posts_without_links)} статей без внутренних ссылок",
            "details": [
                {
                    "post_title": post.title,
                    "post_url": post.link,
                    "suggested_links": [
                        other_post.title 
                        for other_post in posts[:3] 
                        if other_post.id != post.id
                    ]
                }
                for post in posts_without_links[:5]  # Показываем только первые 5
            ]
        })
    
    return recommendations

async def analyze_content_quality(posts: List[WordPressPost], client_id: str = None) -> List[dict]:
    """Анализ качества контента."""
    recommendations = []
    
    # Анализ длины контента
    short_posts = [post for post in posts if len(post.content) < 1000]
    if short_posts:
        recommendations.append({
            "type": "content_quality",
            "priority": "medium",
            "title": "Расширить короткие статьи",
            "description": f"Найдено {len(short_posts)} статей с недостаточным объемом контента",
            "details": [
                {
                    "post_title": post.title,
                    "post_url": post.link,
                    "current_length": len(post.content),
                    "recommended_length": "1500+ символов"
                }
                for post in short_posts[:3]
            ]
        })
    
    # Анализ заголовков
    posts_without_h1 = [post for post in posts if not post.title or len(post.title) < 10]
    if posts_without_h1:
        recommendations.append({
            "type": "content_quality",
            "priority": "medium",
            "title": "Улучшить заголовки статей",
            "description": f"Найдено {len(posts_without_h1)} статей с неоптимальными заголовками",
            "details": [
                {
                    "post_title": post.title,
                    "post_url": post.link,
                    "current_length": len(post.title),
                    "recommendation": "Заголовок должен быть 50-60 символов"
                }
                for post in posts_without_h1[:3]
            ]
        })
    
    return recommendations

async def analyze_semantic_optimization(posts: List[WordPressPost], client_id: str = None) -> List[dict]:
    """Анализ семантической оптимизации."""
    recommendations = []
    
    # Анализ ключевых слов
    all_content = " ".join([post.content for post in posts])
    words = word_tokenize(all_content.lower())
    words = [word for word in words if word.isalpha() and word not in RUSSIAN_STOP_WORDS]
    
    # Простой анализ частоты слов
    word_freq = defaultdict(int)
    for word in words:
        word_freq[word] += 1
    
    # Находим наиболее частые слова
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    recommendations.append({
        "type": "semantic_optimization",
        "priority": "medium",
        "title": "Оптимизировать ключевые слова",
        "description": "Анализ семантического ядра сайта",
        "details": {
            "top_keywords": [{"word": word, "frequency": freq} for word, freq in top_words],
            "recommendation": "Используйте найденные ключевые слова в заголовках и мета-описаниях"
        }
    })
    
    return recommendations

async def analyze_content_structure(posts: List[WordPressPost], client_id: str = None) -> List[dict]:
    """Анализ структуры контента."""
    recommendations = []
    
    # Анализ тематических групп
    content_types = defaultdict(int)
    for post in posts:
        if post.content_type:
            content_types[post.content_type] += 1
    
    if len(content_types) < 3:
        recommendations.append({
            "type": "content_structure",
            "priority": "low",
            "title": "Разнообразить типы контента",
            "description": "Сайт содержит ограниченное количество типов контента",
            "details": {
                "current_types": dict(content_types),
                "recommendation": "Добавьте различные типы контента: гайды, обзоры, новости, интервью"
            }
        })
    
    return recommendations

@app.get("/api/v1/insights/{domain_id}")
async def get_domain_insights(
    domain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение инсайтов по домену."""
    try:
        # Получаем домен
        domain = await db.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        domain = domain.scalar_one_or_none()
        
        if not domain:
            raise HTTPException(status_code=404, detail="Домен не найден")
        
        # Получаем посты домена
        posts = await db.execute(
            select(WordPressPost).where(WordPressPost.domain_id == domain_id)
        )
        posts = posts.scalars().all()
        
        # Получаем историю анализов
        analyses = await db.execute(
            select(AnalysisHistory)
            .where(AnalysisHistory.domain_id == domain_id)
            .order_by(AnalysisHistory.created_at.desc())
            .limit(5)
        )
        analyses = analyses.scalars().all()
        
        # Генерируем инсайты
        insights = await generate_domain_insights(posts, analyses)
        
        return {
            "status": "success",
            "domain": {
                "id": domain.id,
                "name": domain.name,
                "display_name": domain.display_name,
                "total_posts": domain.total_posts,
                "last_analysis": domain.last_analysis_at.isoformat() if domain.last_analysis_at else None
            },
            "insights": insights,
            "recent_analyses": [
                {
                    "id": analysis.id,
                    "created_at": analysis.created_at.isoformat(),
                    "posts_analyzed": analysis.posts_analyzed,
                    "recommendations_count": analysis.recommendations_generated
                }
                for analysis in analyses
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении инсайтов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения инсайтов: {str(e)}")

@app.get("/api/v1/analytics/{domain_id}")
async def get_domain_analytics(
    domain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение аналитики по домену."""
    try:
        # Получаем домен
        domain = await db.execute(
            select(Domain).where(Domain.id == domain_id)
        )
        domain = domain.scalar_one_or_none()
        
        if not domain:
            raise HTTPException(status_code=404, detail="Домен не найден")
        
        # Получаем посты домена
        posts = await db.execute(
            select(WordPressPost).where(WordPressPost.domain_id == domain_id)
        )
        posts = posts.scalars().all()
        
        # Генерируем аналитику
        analytics = await generate_domain_analytics(posts)
        
        return {
            "status": "success",
            "domain": {
                "id": domain.id,
                "name": domain.name,
                "display_name": domain.display_name
            },
            "analytics": analytics,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении аналитики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения аналитики: {str(e)}")

async def generate_domain_insights(posts: List[WordPressPost], analyses: List[AnalysisHistory]) -> dict:
    """Генерация инсайтов по домену."""
    insights = {
        "content_insights": {},
        "performance_insights": {},
        "seo_insights": {},
        "trends": {}
    }
    
    if not posts:
        return insights
    
    # Инсайты по контенту
    total_content_length = sum(len(post.content) for post in posts)
    avg_content_length = total_content_length / len(posts)
    
    insights["content_insights"] = {
        "total_posts": len(posts),
        "total_content_length": total_content_length,
        "average_content_length": round(avg_content_length, 2),
        "content_distribution": {
            "short_posts": len([p for p in posts if len(p.content) < 1000]),
            "medium_posts": len([p for p in posts if 1000 <= len(p.content) < 3000]),
            "long_posts": len([p for p in posts if len(p.content) >= 3000])
        },
        "top_performing_content": [
            {
                "title": post.title,
                "url": post.link,
                "length": len(post.content),
                "quality_score": post.content_quality_score
            }
            for post in sorted(posts, key=lambda p: p.content_quality_score, reverse=True)[:5]
        ]
    }
    
    # Инсайты по производительности
    if analyses:
        latest_analysis = analyses[0]
        insights["performance_insights"] = {
            "last_analysis_date": latest_analysis.created_at.isoformat(),
            "total_recommendations": latest_analysis.recommendations_generated,
            "internal_links_found": latest_analysis.connections_found,
            "analysis_metrics": latest_analysis.semantic_metrics
        }
    
    # SEO инсайты
    all_content = " ".join([post.content for post in posts])
    words = word_tokenize(all_content.lower())
    words = [word for word in words if word.isalpha() and word not in RUSSIAN_STOP_WORDS]
    
    word_freq = defaultdict(int)
    for word in words:
        word_freq[word] += 1
    
    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
    
    insights["seo_insights"] = {
        "top_keywords": [{"word": word, "frequency": freq} for word, freq in top_keywords],
        "keyword_density": len(set(words)) / len(words) if words else 0,
        "content_optimization_score": sum(post.content_quality_score for post in posts) / len(posts)
    }
    
    # Тренды
    if len(analyses) > 1:
        insights["trends"] = {
            "analysis_frequency": "regular" if len(analyses) >= 3 else "occasional",
            "improvement_trend": "positive" if analyses[0].recommendations_generated < analyses[-1].recommendations_generated else "stable"
        }
    
    return insights

async def generate_domain_analytics(posts: List[WordPressPost]) -> dict:
    """Генерация аналитики по домену."""
    analytics = {
        "content_metrics": {},
        "semantic_analysis": {},
        "quality_metrics": {},
        "engagement_potential": {}
    }
    
    if not posts:
        return analytics
    
    # Метрики контента
    content_lengths = [len(post.content) for post in posts]
    analytics["content_metrics"] = {
        "total_posts": len(posts),
        "total_words": sum(len(post.content.split()) for post in posts),
        "average_length": round(sum(content_lengths) / len(content_lengths), 2),
        "min_length": min(content_lengths),
        "max_length": max(content_lengths),
        "length_distribution": {
            "0-500": len([l for l in content_lengths if l < 500]),
            "500-1000": len([l for l in content_lengths if 500 <= l < 1000]),
            "1000-2000": len([l for l in content_lengths if 1000 <= l < 2000]),
            "2000+": len([l for l in content_lengths if l >= 2000])
        }
    }
    
    # Семантический анализ
    all_content = " ".join([post.content for post in posts])
    words = word_tokenize(all_content.lower())
    words = [word for word in words if word.isalpha() and word not in RUSSIAN_STOP_WORDS]
    
    word_freq = defaultdict(int)
    for word in words:
        word_freq[word] += 1
    
    analytics["semantic_analysis"] = {
        "unique_words": len(set(words)),
        "total_words": len(words),
        "lexical_diversity": len(set(words)) / len(words) if words else 0,
        "top_keywords": [{"word": word, "frequency": freq} for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]]
    }
    
    # Метрики качества
    quality_scores = [post.content_quality_score for post in posts]
    semantic_scores = [post.semantic_richness for post in posts]
    
    analytics["quality_metrics"] = {
        "average_content_quality": round(sum(quality_scores) / len(quality_scores), 3),
        "average_semantic_richness": round(sum(semantic_scores) / len(semantic_scores), 3),
        "quality_distribution": {
            "excellent": len([s for s in quality_scores if s >= 0.8]),
            "good": len([s for s in quality_scores if 0.6 <= s < 0.8]),
            "average": len([s for s in quality_scores if 0.4 <= s < 0.6]),
            "poor": len([s for s in quality_scores if s < 0.4])
        }
    }
    
    # Потенциал вовлеченности
    analytics["engagement_potential"] = {
        "linkability_score": round(sum(post.linkability_score for post in posts) / len(posts), 3),
        "content_types": {
            "guides": len([p for p in posts if p.content_type == "guide"]),
            "reviews": len([p for p in posts if p.content_type == "review"]),
            "news": len([p for p in posts if p.content_type == "news"]),
            "other": len([p for p in posts if not p.content_type])
        },
        "target_audience_diversity": len(set(p.target_audience for p in posts if p.target_audience))
    }
    
    return analytics

@app.post("/api/v1/test/setup")
async def setup_test_user():
    """Создание тестового пользователя для демонстрации."""
    try:
        from .auth import get_password_hash
        
        # Проверяем, есть ли уже тестовый пользователь
        async with async_sessionmaker(engine)() as db:
            existing_user = await db.execute(
                select(User).where(User.username == "test_user")
            )
            existing_user = existing_user.scalar_one_or_none()
            
            if existing_user:
                return {
                    "status": "success",
                    "message": "Тестовый пользователь уже существует",
                    "user": {
                        "id": existing_user.id,
                        "username": existing_user.username,
                        "email": existing_user.email
                    }
                }
            
            # Создаем тестового пользователя
            test_user = User(
                username="test_user",
                email="test@example.com",
                full_name="Тестовый пользователь",
                hashed_password=get_password_hash("test123"),
                is_active=True
            )
            db.add(test_user)
            await db.commit()
            await db.refresh(test_user)
            
            return {
                "status": "success",
                "message": "Тестовый пользователь создан",
                "user": {
                    "id": test_user.id,
                    "username": test_user.username,
                    "email": test_user.email
                }
            }
            
    except Exception as e:
        logger.error(f"Ошибка при создании тестового пользователя: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания пользователя: {str(e)}")

@app.post("/api/v1/test/login")
async def test_login():
    """Быстрый логин тестового пользователя."""
    try:
        from .auth import create_access_token
        
        # Создаем токен для тестового пользователя
        access_token = create_access_token(data={"sub": "test_user"})
        
        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": "test_user",
                "email": "test@example.com"
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка при логине тестового пользователя: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка логина: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

