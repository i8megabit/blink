"""FastAPI-приложение для генерации внутренних ссылок."""

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

# Импортируем новые модули
from .config import settings, get_settings
from .exceptions import (
    BlinkBaseException, ErrorHandler, ErrorResponse,
    ValidationException, AuthenticationException, AuthorizationException,
    NotFoundException, DatabaseException, OllamaException,
    raise_not_found, raise_validation_error, raise_authentication_error,
    raise_authorization_error, raise_database_error, raise_ollama_error
)
from .middleware import (
    ErrorHandlerMiddleware, RequestLoggingMiddleware, RateLimitMiddleware,
    SecurityMiddleware, PerformanceMiddleware, setup_error_handlers
)
from .monitoring import monitoring, monitoring_middleware, metrics_endpoint, health_check
from .cache import cache_service, cache_middleware, cache_stats, cache_clear
from .validation import (
    ValidationErrorHandler, DomainAnalysisRequest, SEOAnalysisResult,
    UserRegistrationRequest, UserLoginRequest, UserProfileUpdateRequest,
    AnalysisHistoryRequest, ExportRequest, Validators, ValidationUtils
)
from .auth import (
    get_current_user, create_access_token, get_password_hash, verify_password,
    User, UserCreate, UserResponse, Token, TokenData
)
from .database import get_db, engine

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
# Максимум 1 одновременный запрос к Ollama для предотвращения перегрузки системы
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
        monitoring.logger.info(f"WebSocket подключен: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """Отключение клиента."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            monitoring.logger.info(f"WebSocket отключен: {client_id}")

    async def send_progress(self, client_id: str, message: dict) -> None:
        """Отправка прогресса конкретному клиенту."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                monitoring.logger.debug(f"Прогресс отправлен {client_id}: {message}")
            except Exception as e:
                monitoring.log_error(e, {"client_id": client_id, "operation": "send_progress"})

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
                monitoring.logger.debug(f"Мысль ИИ отправлена {client_id}: {thought[:50]}...")
            except Exception as e:
                monitoring.log_error(e, {"client_id": client_id, "operation": "send_ai_thinking"})
    
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
                monitoring.logger.debug(f"Расширенная мысль ИИ отправлена {client_id}: {ai_thought.stage}")
            except Exception as e:
                monitoring.log_error(e, {"client_id": client_id, "operation": "send_enhanced_ai_thinking"})


# Глобальные переменные
chroma_client: Optional[Any] = None
tfidf_vectorizer: Optional[Any] = None

# Глобальные менеджеры (будут инициализированы после определения классов)
websocket_manager: Optional[WebSocketManager] = None
thought_generator: Optional['IntelligentThoughtGenerator'] = None
rag_manager: Optional['AdvancedRAGManager'] = None
cumulative_manager: Optional['CumulativeIntelligenceManager'] = None

# Создаем FastAPI приложение с настройками мониторинга
app = FastAPI(
    title=settings.api.title,
    version=settings.api.version,
    description=settings.api.description,
    docs_url=settings.api.docs_url,
    redoc_url=settings.api.redoc_url,
    debug=settings.debug
)

# Добавляем middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем middleware мониторинга
if settings.monitoring.enable_metrics:
    app.add_middleware(monitoring_middleware)

# Добавляем middleware кэширования
if settings.cache.enable_memory or settings.cache.enable_redis:
    app.add_middleware(cache_middleware)

# Добавляем middleware кастомных
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.api.rate_limit_per_minute)

# Инструментируем приложение для мониторинга
monitoring.instrument_fastapi(app)
monitoring.instrument_sqlalchemy(engine)
monitoring.instrument_requests()

# Добавляем статические файлы
static_dir = Path(__file__).parent.parent.parent / "frontend"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Добавляем статические файлы
static_dir = Path(__file__).parent.parent.parent / "frontend"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class Base(DeclarativeBase):
    """Базовый класс моделей."""


class Domain(Base):
    """Модель доменов для централизованного управления."""

    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="ru")
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Статистика
    total_posts: Mapped[int] = mapped_column(Integer, default=0)
    total_analyses: Mapped[int] = mapped_column(Integer, default=0)
    last_analysis_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Отношения
    posts: Mapped[List["WordPressPost"]] = relationship("WordPressPost", back_populates="domain_ref", cascade="all, delete-orphan")
    analyses: Mapped[List["AnalysisHistory"]] = relationship("AnalysisHistory", back_populates="domain_ref", cascade="all, delete-orphan")
    themes: Mapped[List["ThematicGroup"]] = relationship("ThematicGroup", back_populates="domain_ref", cascade="all, delete-orphan")


class ThematicGroup(Base):
    """Модель тематических групп статей для семантической кластеризации."""

    __tablename__ = "thematic_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str]] = mapped_column(JSON)
    semantic_signature: Mapped[str] = mapped_column(Text)  # TF-IDF подпись темы
    articles_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_semantic_density: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Отношения
    domain_ref: Mapped["Domain"] = relationship("Domain", back_populates="themes")
    posts: Mapped[List["WordPressPost"]] = relationship("WordPressPost", back_populates="thematic_group")

    __table_args__ = (
        Index("idx_thematic_groups_domain_semantic", "domain_id", "avg_semantic_density"),
    )


class WordPressPost(Base):
    """Улучшенная модель статей WordPress с семантическими полями."""

    __tablename__ = "wordpress_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), index=True)
    thematic_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("thematic_groups.id"), nullable=True, index=True)
    wp_post_id: Mapped[int] = mapped_column(Integer)

    # Контентные поля
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(Text, index=True)

    # Семантические поля для LLM
    semantic_summary: Mapped[str] = mapped_column(Text, nullable=True)  # Краткое описание для LLM
    key_concepts: Mapped[list[str]] = mapped_column(JSON, default=list)  # Ключевые концепции
    entity_mentions: Mapped[list[dict]] = mapped_column(JSON, default=list)  # Упоминания сущностей
    content_type: Mapped[str] = mapped_column(String(50), nullable=True)  # тип контента (гайд, обзор, новость)
    difficulty_level: Mapped[str] = mapped_column(String(20), nullable=True)  # уровень сложности
    target_audience: Mapped[str] = mapped_column(String(100), nullable=True)  # целевая аудитория

    # Метрики семантической релевантности
    content_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    semantic_richness: Mapped[float] = mapped_column(Float, default=0.0)  # плотность семантики
    linkability_score: Mapped[float] = mapped_column(Float, default=0.0)  # потенциал для внутренних ссылок

    # Временные метки и статусы
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_analyzed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Отношения
    domain_ref: Mapped["Domain"] = relationship("Domain", back_populates="posts")
    thematic_group: Mapped["ThematicGroup"] = relationship("ThematicGroup", back_populates="posts")
    embeddings: Mapped[List["ArticleEmbedding"]] = relationship("ArticleEmbedding", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_wp_posts_domain_theme", "domain_id", "thematic_group_id"),
        Index("idx_wp_posts_semantic_scores", "semantic_richness", "linkability_score"),
        Index("idx_wp_posts_published", "published_at"),
    )


class ArticleEmbedding(Base):
    """Продвинутая модель эмбеддингов с множественными представлениями."""

    __tablename__ = "article_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("wordpress_posts.id"), index=True)

    # Различные типы эмбеддингов
    embedding_type: Mapped[str] = mapped_column(String(50))  # 'title', 'content', 'summary', 'full'
    vector_model: Mapped[str] = mapped_column(String(100))  # модель векторизации
    embedding_vector: Mapped[str] = mapped_column(Text)  # JSON вектора
    dimension: Mapped[int] = mapped_column(Integer)  # размерность вектора

    # Метаданные для контекста
    context_window: Mapped[int] = mapped_column(Integer, nullable=True)  # размер контекстного окна
    preprocessing_info: Mapped[dict] = mapped_column(JSON, default=dict)  # информация о предобработке
    quality_metrics: Mapped[dict] = mapped_column(JSON, default=dict)  # метрики качества

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Отношения
    post: Mapped["WordPressPost"] = relationship("WordPressPost", back_populates="embeddings")

    __table_args__ = (
        Index("idx_embeddings_post_type", "post_id", "embedding_type"),
    )


class SemanticConnection(Base):
    """Модель семантических связей между статьями с накоплением знаний."""

    __tablename__ = "semantic_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("wordpress_posts.id"), index=True)
    target_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("wordpress_posts.id"), index=True)

    # Типы связей с расширенной классификацией
    connection_type: Mapped[str] = mapped_column(String(50))  # 'semantic', 'topical', 'hierarchical', 'sequential', 'complementary'
    strength: Mapped[float] = mapped_column(Float)  # сила связи (0.0 - 1.0)
    confidence: Mapped[float] = mapped_column(Float)  # уверенность в связи

    # Накопительные метрики
    usage_count: Mapped[int] = mapped_column(Integer, default=0)  # сколько раз связь была рекомендована
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)  # успешность внедрения
    evolution_score: Mapped[float] = mapped_column(Float, default=0.0)  # эволюция связи со временем

    # Контекст для LLM
    connection_context: Mapped[str] = mapped_column(Text, nullable=True)  # объяснение связи
    suggested_anchor: Mapped[str] = mapped_column(String(200), nullable=True)  # предлагаемый анкор
    alternative_anchors: Mapped[list[str]] = mapped_column(JSON, default=list)  # альтернативные анкоры
    bidirectional: Mapped[bool] = mapped_column(default=False)  # двунаправленная связь

    # Семантические теги для группировки
    semantic_tags: Mapped[list[str]] = mapped_column(JSON, default=list)  # семантические теги
    theme_intersection: Mapped[str] = mapped_column(String(200), nullable=True)  # пересечение тем

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    validated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_recommended_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_semantic_connections_strength", "strength"),
        Index("idx_semantic_connections_usage", "usage_count", "success_rate"),
        Index("idx_semantic_connections_evolution", "evolution_score"),
    )


class LinkRecommendation(Base):
    """Модель накопленных рекомендаций с дедупликацией и эволюцией."""

    __tablename__ = "link_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), index=True)
    source_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("wordpress_posts.id"), index=True)
    target_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("wordpress_posts.id"), index=True)

    # Рекомендация
    anchor_text: Mapped[str] = mapped_column(String(300))
    reasoning: Mapped[str] = mapped_column(Text)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)  # качество рекомендации

    # Накопительная аналитика
    generation_count: Mapped[int] = mapped_column(Integer, default=1)  # сколько раз генерировалась
    improvement_iterations: Mapped[int] = mapped_column(Integer, default=0)  # итерации улучшения
    status: Mapped[str] = mapped_column(String(50), default='active')  # active, deprecated, improved

    # Связь с семантической моделью
    semantic_connection_id: Mapped[int] = mapped_column(Integer, ForeignKey("semantic_connections.id"), nullable=True)

    # Эволюция рекомендации
    previous_version_id: Mapped[int] = mapped_column(Integer, ForeignKey("link_recommendations.id"), nullable=True)
    improvement_reason: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    domain_ref: Mapped["Domain"] = relationship("Domain")
    source_post: Mapped["WordPressPost"] = relationship("WordPressPost", foreign_keys=[source_post_id])
    target_post: Mapped["WordPressPost"] = relationship("WordPressPost", foreign_keys=[target_post_id])
    semantic_connection: Mapped["SemanticConnection"] = relationship("SemanticConnection")
    previous_version: Mapped["LinkRecommendation"] = relationship("LinkRecommendation", remote_side=[id])

    __table_args__ = (
        Index("idx_link_recommendations_quality", "quality_score"),
        Index("idx_link_recommendations_status", "status"),
        Index("idx_link_recommendations_generation", "generation_count"),
        # Уникальность по связке источник-цель в рамках домена
        Index("idx_link_recommendations_unique", "domain_id", "source_post_id", "target_post_id"),
    )


class ThematicClusterAnalysis(Base):
    """Модель анализа тематических кластеров и их эволюции."""

    __tablename__ = "thematic_cluster_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), index=True)

    # Кластер
    cluster_name: Mapped[str] = mapped_column(String(200))
    cluster_keywords: Mapped[list[str]] = mapped_column(JSON)
    cluster_description: Mapped[str] = mapped_column(Text)

    # Статьи в кластере
    article_ids: Mapped[list[int]] = mapped_column(JSON)  # ID статей в кластере
    article_count: Mapped[int] = mapped_column(Integer)

    # Семантические метрики
    coherence_score: Mapped[float] = mapped_column(Float)  # связность кластера
    diversity_score: Mapped[float] = mapped_column(Float)  # разнообразие контента
    linkability_potential: Mapped[float] = mapped_column(Float)  # потенциал для линковки

    # Связи с другими кластерами
    related_clusters: Mapped[dict] = mapped_column(JSON, default=dict)  # связанные кластеры и их веса
    cross_cluster_opportunities: Mapped[list[dict]] = mapped_column(JSON, default=list)  # возможности межкластерных связей

    # Эволюция кластера
    evolution_stage: Mapped[str] = mapped_column(String(50), default='emerging')  # emerging, mature, declining
    growth_trend: Mapped[float] = mapped_column(Float, default=0.0)  # тренд роста

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    domain_ref: Mapped["Domain"] = relationship("Domain")

    __table_args__ = (
        Index("idx_thematic_cluster_coherence", "coherence_score"),
        Index("idx_thematic_cluster_linkability", "linkability_potential"),
        Index("idx_thematic_cluster_evolution", "evolution_stage", "growth_trend"),
    )


class CumulativeInsight(Base):
    """Модель накопленных инсайтов для глубокого анализа."""

    __tablename__ = "cumulative_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), index=True)

    # Тип инсайта
    insight_type: Mapped[str] = mapped_column(String(100))  # 'pattern', 'gap', 'opportunity', 'trend'
    insight_category: Mapped[str] = mapped_column(String(100))  # 'semantic', 'structural', 'thematic'

    # Содержание инсайта
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON)  # подтверждающие данные

    # Метрики важности
    impact_score: Mapped[float] = mapped_column(Float)  # важность инсайта
    confidence_level: Mapped[float] = mapped_column(Float)  # уверенность в инсайте
    actionability: Mapped[float] = mapped_column(Float)  # применимость

    # Связанные сущности
    related_posts: Mapped[list[int]] = mapped_column(JSON, default=list)
    related_clusters: Mapped[list[int]] = mapped_column(JSON, default=list)
    related_connections: Mapped[list[int]] = mapped_column(JSON, default=list)

    # Статус и применение
    status: Mapped[str] = mapped_column(String(50), default='discovered')  # discovered, validated, applied
    applied_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    validated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Отношения
    domain_ref: Mapped["Domain"] = relationship("Domain")

    __table_args__ = (
        Index("idx_cumulative_insights_impact", "impact_score"),
        Index("idx_cumulative_insights_type", "insight_type", "insight_category"),
        Index("idx_cumulative_insights_status", "status"),
    )


class AnalysisHistory(Base):
    """Улучшенная модель истории анализов с детальными метриками."""

    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), index=True)

    # Основные метрики
    posts_analyzed: Mapped[int] = mapped_column(Integer)
    connections_found: Mapped[int] = mapped_column(Integer)
    recommendations_generated: Mapped[int] = mapped_column(Integer)

    # Детальные результаты
    recommendations: Mapped[list[dict]] = mapped_column(JSON)
    thematic_analysis: Mapped[dict] = mapped_column(JSON, default=dict)  # анализ тематик
    semantic_metrics: Mapped[dict] = mapped_column(JSON, default=dict)  # семантические метрики
    quality_assessment: Mapped[dict] = mapped_column(JSON, default=dict)  # оценка качества

    # LLM метаданные
    llm_model_used: Mapped[str] = mapped_column(String(100))
    llm_context_size: Mapped[int] = mapped_column(Integer, nullable=True)
    processing_time_seconds: Mapped[float] = mapped_column(Float, nullable=True)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Отношения
    domain_ref: Mapped["Domain"] = relationship("Domain", back_populates="analyses")

    __table_args__ = (
        Index("idx_analysis_history_domain_date", "domain_id", "created_at"),
    )


class ModelConfiguration(Base):
    """Модель конфигураций для различных LLM моделей."""

    __tablename__ = "model_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    model_type: Mapped[str] = mapped_column(String(50))  # ollama, openai, anthropic

    # Параметры модели
    default_parameters: Mapped[dict] = mapped_column(JSON, default=dict)  # temperature, top_p, etc.
    context_size: Mapped[int] = mapped_column(Integer, default=4096)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)

    # Специализированные настройки для разных задач
    seo_optimized_params: Mapped[dict] = mapped_column(JSON, default=dict)
    benchmark_params: Mapped[dict] = mapped_column(JSON, default=dict)
    creative_params: Mapped[dict] = mapped_column(JSON, default=dict)

    # Характеристики производительности
    avg_tokens_per_second: Mapped[float] = mapped_column(Float, nullable=True)
    memory_usage_mb: Mapped[float] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)

    # Метаданные
    is_active: Mapped[bool] = mapped_column(default=True)
    is_available: Mapped[bool] = mapped_column(default=False)  # динамически обновляется
    last_checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    benchmark_runs: Mapped[List["BenchmarkRun"]] = relationship("BenchmarkRun", back_populates="model_config")

    __table_args__ = (
        Index("idx_model_configs_active_available", "is_active", "is_available"),
    )


class BenchmarkRun(Base):
    """Модель для хранения результатов бенчмарков."""

    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    benchmark_type: Mapped[str] = mapped_column(String(100))  # seo_basic, seo_advanced, performance

    # Ссылки на модели
    model_config_id: Mapped[int] = mapped_column(Integer, ForeignKey("model_configurations.id"), index=True)

    # Конфигурация бенчмарка
    test_cases_config: Mapped[dict] = mapped_column(JSON)  # конфигурация тестовых кейсов
    iterations: Mapped[int] = mapped_column(Integer, default=3)

    # Результаты
    results: Mapped[dict] = mapped_column(JSON)  # детальные результаты
    metrics: Mapped[dict] = mapped_column(JSON)  # агрегированные метрики

    # Временные метрики
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)

    # Статус выполнения
    status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, running, completed, failed
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Сравнительные метрики
    overall_score: Mapped[float] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float, nullable=True)
    performance_score: Mapped[float] = mapped_column(Float, nullable=True)
    efficiency_score: Mapped[float] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Отношения
    model_config: Mapped["ModelConfiguration"] = relationship("ModelConfiguration", back_populates="benchmark_runs")
    comparisons: Mapped[List["BenchmarkComparison"]] = relationship("BenchmarkComparison", foreign_keys="BenchmarkComparison.run_id", back_populates="run")

    __table_args__ = (
        Index("idx_benchmark_runs_model_status", "model_config_id", "status"),
        Index("idx_benchmark_runs_type_score", "benchmark_type", "overall_score"),
    )


class BenchmarkComparison(Base):
    """Модель для сравнения результатов бенчмарков между моделями."""

    __tablename__ = "benchmark_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comparison_name: Mapped[str] = mapped_column(String(300))

    # Ссылки на сравниваемые запуски
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark_runs.id"), index=True)
    baseline_run_id: Mapped[int] = mapped_column(Integer, ForeignKey("benchmark_runs.id"), nullable=True)

    # Результаты сравнения
    comparison_results: Mapped[dict] = mapped_column(JSON)  # детальное сравнение
    performance_delta: Mapped[float] = mapped_column(Float, nullable=True)  # изменение производительности
    quality_delta: Mapped[float] = mapped_column(Float, nullable=True)  # изменение качества

    # Выводы и рекомендации
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Отношения
    run: Mapped["BenchmarkRun"] = relationship("BenchmarkRun", foreign_keys=[run_id], back_populates="comparisons")
    baseline_run: Mapped["BenchmarkRun"] = relationship("BenchmarkRun", foreign_keys=[baseline_run_id])

    __table_args__ = (
        Index("idx_benchmark_comparisons_runs", "run_id", "baseline_run_id"),
    )


class Recommendation(Base):
    """Модель рекомендаций (оставляем для совместимости)."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    links: Mapped[list[str]] = mapped_column(JSON)


class RecommendRequest(BaseModel):
    """Запрос с текстом для генерации ссылок."""

    text: str


class WPRequest(BaseModel):
    """Запрос для анализа WordPress-сайта."""

    domain: str
    client_id: Optional[str] = None
    comprehensive: Optional[bool] = False  # Флаг для полной индексации


class BenchmarkRequest(BaseModel):
    """Запрос для запуска бенчмарка."""

    name: str
    description: Optional[str] = None
    benchmark_type: str = "seo_advanced"  # seo_basic, seo_advanced, performance
    models: List[str] = []  # список моделей для тестирования
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


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
# Оптимизированная модель для SEO задач: qwen2.5:7b-instruct-turbo - лучшая для инструкций
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-turbo")

# 🎯 ОПТИМИЗИРОВАННЫЕ НАСТРОЙКИ ТОКЕНОВ для модели qwen2.5:7b
# Модель имеет лимит контекста 8192 токена, оставляем запас для промпта и ответа
OPTIMAL_CONTEXT_SIZE = 3072      # КРИТИЧНО: Снижаем до 3K для экономии памяти (75% от 4096)
OPTIMAL_PREDICTION_SIZE = 800    # Оптимальный размер ответа
OPTIMAL_TEMPERATURE = 0.3        # Баланс точности и креативности
OPTIMAL_TOP_P = 0.85            # Оптимизируем для качества
OPTIMAL_TOP_K = 50              # Расширяем выбор токенов
OPTIMAL_REPEAT_PENALTY = 1.08   # Снижаем повторения

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://seo_user:seo_pass@localhost/seo_db",
)

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

# Инициализация RAG-системы
chroma_client = None
tfidf_vectorizer = None

def initialize_rag_system() -> None:
    """Инициализирует продвинутую RAG-систему с семантическим поиском."""
    global chroma_client, tfidf_vectorizer
    try:
        print("🔧 Инициализация продвинутой RAG-системы...")

        # Улучшенная TF-IDF векторизация для русского языка
        tfidf_vectorizer = TfidfVectorizer(
            max_features=2000,  # увеличиваем размерность
            ngram_range=(1, 3),  # добавляем триграммы
            min_df=1,
            max_df=0.85,
            stop_words=list(RUSSIAN_STOP_WORDS),  # русские стоп-слова
            analyzer='word',
            lowercase=True,
            token_pattern=r'\b[а-яё]{2,}\b|\b[a-z]{2,}\b'  # русские и английские слова
        )

        # Инициализируем ChromaDB с улучшенными настройками
        chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        print("✅ Продвинутая RAG-система инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации RAG: {e}")
        chroma_client = None
        tfidf_vectorizer = None


class AdvancedRAGManager:
    """Продвинутый RAG-менеджер с семантическим анализом."""

    def __init__(self) -> None:
        self.domain_collections = {}
        self.thematic_clusters = {}
        self.semantic_cache = {}

    async def create_semantic_knowledge_base(self, domain, posts, client_id=None):
        # Проксируем вызов к глобальному генератору мыслей
        global thought_generator
        return await thought_generator.create_semantic_knowledge_base(domain, posts, client_id)


# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Корневой endpoint."""
    return {"message": "reLink API v4.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/health")
async def api_health():
    """API health check."""
    return {"status": "healthy", "version": "4.0.0", "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/version")
async def get_version():
    """Получение версии приложения."""
    try:
        version_file = Path("VERSION")
        if version_file.exists():
            with open(version_file, 'r', encoding='utf-8') as f:
                version = f.read().strip()
        else:
            version = "4.0.0"  # Версия по умолчанию
        
        return {
            "version": version,
            "buildDate": datetime.now().strftime('%Y-%m-%d'),
            "commitHash": os.getenv("GIT_COMMIT_HASH", ""),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        return {
            "version": "4.0.0",
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
        }
    }


@app.get("/api/v1/ollama_status")
async def get_ollama_status():
    """Проверка статуса Ollama."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://ollama:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "available",
                    "models": [model.get("name", "") for model in models],
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ollama responded with status {response.status_code}",
                    "last_check": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "status": "unavailable",
            "message": str(e),
            "last_check": datetime.now().isoformat()
        }


@app.get("/api/v1/domains")
async def get_domains():
    """Получение списка доменов."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Domain))
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
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()))
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
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(BenchmarkRun).order_by(BenchmarkRun.created_at.desc()))
            benchmarks = result.scalars().all()
            return [
                {
                    "id": benchmark.id,
                    "name": benchmark.name,
                    "description": benchmark.description,
                    "benchmark_type": benchmark.benchmark_type,
                    "status": benchmark.status,
                    "overall_score": benchmark.overall_score,
                    "created_at": benchmark.created_at.isoformat()
                }
                for benchmark in benchmarks
            ]
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# НОВЫЕ API ENDPOINTS ДЛЯ МОНИТОРИНГА, КЭШИРОВАНИЯ И ВАЛИДАЦИИ
# ============================================================================

# Endpoints для мониторинга
@app.get("/metrics")
async def get_metrics():
    """Endpoint для получения метрик Prometheus"""
    return await metrics_endpoint()

@app.get("/api/v1/monitoring/health")
async def get_monitoring_health():
    """Endpoint для проверки здоровья с мониторингом"""
    return await health_check()

@app.get("/api/v1/monitoring/stats")
async def get_monitoring_stats():
    """Получение статистики мониторинга"""
    try:
        stats = await cache_service.get_stats()
        return {
            "cache_stats": stats,
            "active_connections": len(websocket_manager.active_connections) if websocket_manager else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        monitoring.log_error(e, {"operation": "get_monitoring_stats"})
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")

# Endpoints для кэширования
@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Получение статистики кэша"""
    return await cache_stats()

@app.post("/api/v1/cache/clear")
async def clear_cache():
    """Очистка кэша"""
    return await cache_clear()

@app.delete("/api/v1/cache/{pattern}")
async def clear_cache_pattern(pattern: str):
    """Очистка кэша по паттерну"""
    try:
        deleted_count = await cache_service.clear_pattern(pattern)
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        monitoring.log_error(e, {"operation": "clear_cache_pattern", "pattern": pattern})
        raise HTTPException(status_code=500, detail="Ошибка очистки кэша")

# Endpoints для аутентификации
@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegistrationRequest, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    try:
        # Проверяем, существует ли пользователь с таким email
        existing_user = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
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
        
        monitoring.logger.info(f"Зарегистрирован новый пользователь: {user_data.email}")
        
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
        monitoring.log_error(e, {"operation": "register_user", "email": user_data.email})
        raise HTTPException(status_code=500, detail="Ошибка регистрации пользователя")

@app.post("/api/v1/auth/login", response_model=Token)
async def login_user(user_data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """Вход пользователя"""
    try:
        # Ищем пользователя
        user = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        user = user.scalar_one_or_none()
        
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
        
        monitoring.logger.info(f"Пользователь вошел в систему: {user.email}")
        
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        monitoring.log_error(e, {"operation": "login_user", "email": user_data.email})
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
        monitoring.log_error(e, {"operation": "refresh_token", "user_id": current_user.id})
        raise HTTPException(status_code=500, detail="Ошибка обновления токена")

@app.post("/api/v1/auth/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """Выход пользователя"""
    try:
        monitoring.logger.info(f"Пользователь вышел из системы: {current_user.email}")
        return {"message": "Успешный выход из системы"}
    except Exception as e:
        monitoring.log_error(e, {"operation": "logout_user", "user_id": current_user.id})
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
        # Логируем начало анализа
        monitoring.logger.info(f"Начат анализ домена: {request_data.domain}")
        
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
        
        # Логируем завершение анализа
        monitoring.log_seo_analysis(
            domain=request_data.domain,
            status="completed",
            duration=2.5
        )
        
        return analysis_result
        
    except Exception as e:
        monitoring.log_error(e, {
            "operation": "analyze_domain",
            "domain": request_data.domain,
            "user_id": current_user.id
        })
        raise HTTPException(status_code=500, detail="Ошибка анализа домена")

@app.post("/api/v1/seo/competitors")
async def analyze_competitors(
    request_data: CompetitorAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Анализ конкурентов"""
    try:
        monitoring.logger.info(f"Начат анализ конкурентов для домена: {request_data.domain}")
        
        # Здесь будет логика анализа конкурентов
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
        monitoring.log_error(e, {
            "operation": "analyze_competitors",
            "domain": request_data.domain,
            "user_id": current_user.id
        })
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
        # Здесь будет логика получения истории
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
        monitoring.log_error(e, {
            "operation": "get_analysis_history",
            "user_id": current_user.id
        })
        raise HTTPException(status_code=500, detail="Ошибка получения истории")

@app.post("/api/v1/export")
async def export_data(
    request_data: ExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Экспорт данных"""
    try:
        monitoring.logger.info(f"Запрошен экспорт данных: {request_data.format}")
        
        # Здесь будет логика экспорта
        export_result = {
            "format": request_data.format,
            "analysis_count": len(request_data.analysis_ids),
            "download_url": f"/api/v1/downloads/export_{datetime.utcnow().timestamp()}.{request_data.format}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        return export_result
        
    except Exception as e:
        monitoring.log_error(e, {
            "operation": "export_data",
            "user_id": current_user.id,
            "format": request_data.format
        })
        raise HTTPException(status_code=500, detail="Ошибка экспорта данных")

# Endpoints для валидации
@app.post("/api/v1/validate/domain")
async def validate_domain(domain: str):
    """Валидация домена"""
    try:
        # Используем валидатор из модуля валидации
        validated_domain = Validators.validate_url(f"https://{domain}")
        return {
            "valid": True,
            "domain": domain,
            "sanitized": ValidationUtils.sanitize_input(domain)
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
        # Простая валидация email
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return {
                "valid": True,
                "email": email,
                "sanitized": ValidationUtils.sanitize_input(email)
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
    return ValidationErrorHandler.handle_validation_error(exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP ошибок"""
    return ValidationErrorHandler.handle_http_error(exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Общий обработчик исключений"""
    monitoring.log_error(exc, {
        "request_method": request.method,
        "request_path": request.url.path,
        "operation": "general_exception"
    })
    
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
    global websocket_manager
    websocket_manager = WebSocketManager()
    initialize_rag_system()
    
    # Создаем директорию для логов
    os.makedirs("logs", exist_ok=True)
    
    monitoring.logger.info("🚀 Blink SEO Platform запущен!")
    print("🚀 Blink SEO Platform v1.0.0 запущен!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

