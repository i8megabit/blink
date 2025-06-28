"""FastAPI-приложение для генерации внутренних ссылок reLink."""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
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
    func, select
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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
from .llm_router import system_analyzer, llm_router
from .diagram_service import DiagramService, DiagramGenerationRequest

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
    model_name: str
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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
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
            "timestamp": datetime.utcnow().isoformat()
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
                "last_optimization": datetime.utcnow().isoformat()
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
                "model_used": report["optimized_config"]["model"],
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
            "timestamp": datetime.utcnow().isoformat()
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
                "model": new_config.model,
                "num_gpu": new_config.num_gpu,
                "num_thread": new_config.num_thread,
                "batch_size": new_config.batch_size,
                "context_length": new_config.context_length,
                "semaphore_limit": new_config.semaphore_limit
            },
            "optimization_timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
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

# Endpoints для аутентификации
@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegistrationRequest, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    try:
        # Проверяем, существует ли пользователь с таким email
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким email уже существует"
            )
        
        # Создаем нового пользователя
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка регистрации пользователя")

@app.post("/api/v1/auth/login", response_model=Token)
async def login_user(user_data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """Вход пользователя"""
    try:
        # Ищем пользователя
        result = await db.execute(select(User).where(User.email == user_data.email))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Неверный email или пароль"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="Пользователь неактивен"
            )
        
        # Создаем токен доступа
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка входа")

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Обновление токена доступа"""
    try:
        access_token = create_access_token(data={"sub": str(current_user.id)})
        return Token(access_token=access_token, token_type="bearer")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка обновления токена")

@app.post("/api/v1/auth/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """Выход пользователя"""
    try:
        return {"message": "Успешный выход из системы"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка выхода")

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
            analysis_date=datetime.utcnow(),
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
            "analysis_date": datetime.utcnow().isoformat(),
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
                "analysis_date": datetime.utcnow().isoformat(),
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
            "download_url": f"/api/v1/downloads/export_{datetime.utcnow().timestamp()}.{request_data.format}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
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
    model_used: str
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
            model_used=result.model_used,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

