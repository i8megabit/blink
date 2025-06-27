"""FastAPI-приложение для генерации внутренних ссылок."""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

import chromadb
import httpx
import nltk
import numpy as np
import ollama
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import (
    DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text,
    func, select
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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
        print(f"🔌 WebSocket подключен: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """Отключение клиента."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"🔌 WebSocket отключен: {client_id}")

    async def send_progress(self, client_id: str, message: dict) -> None:
        """Отправка прогресса конкретному клиенту."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                print(f"📊 Прогресс отправлен {client_id}: {message}")
            except Exception as e:
                print(f"❌ Ошибка отправки прогресса {client_id}: {e}")

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
                print(f"🧠 Мысль ИИ отправлена {client_id}: {thought[:50]}...")
            except Exception as e:
                print(f"❌ Ошибка отправки мысли {client_id}: {e}")
    
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
                print(f"🔬 Расширенная мысль ИИ отправлена {client_id}: {ai_thought.stage}")
            except Exception as e:
                print(f"❌ Ошибка отправки расширенной мысли {client_id}: {e}")


# Глобальные переменные
chroma_client: Optional[Any] = None
tfidf_vectorizer: Optional[Any] = None

# Глобальные менеджеры (будут инициализированы после определения классов)
websocket_manager: Optional[WebSocketManager] = None
thought_generator: Optional['IntelligentThoughtGenerator'] = None
rag_manager: Optional['AdvancedRAGManager'] = None
cumulative_manager: Optional['CumulativeIntelligenceManager'] = None

app = FastAPI()

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class IntelligentThoughtGenerator:
    """Генератор интеллектуальных мыслей ИИ с использованием numpy и семантического анализа."""
    
    def __init__(self) -> None:
        self.thought_history: List[AIThought] = []
        self.concept_embeddings: Dict[str, np.ndarray] = {}
        self.reasoning_patterns: Dict[str, List[str]] = defaultdict(list)
        self.semantic_network: Dict[str, Set[str]] = defaultdict(set)
        
    def extract_key_concepts(self, text: str) -> List[str]:
        """Извлечение ключевых концепций с помощью регулярных выражений и NLP."""
        # Паттерны для извлечения SEO-концепций
        seo_patterns = [
            r'\b(?:SEO|сео|оптимизация|ранжирование|поисковик)\b',
            r'\b(?:ключев\w+\s+слов\w+|keywords?)\b',
            r'\b(?:анкор\w*|anchor\w*)\b',
            r'\b(?:ссылк\w+|link\w*)\b',
            r'\b(?:контент|content)\b',
            r'\b(?:семантик\w+|semantic\w*)\b'
        ]
        
        concepts = []
        text_lower = text.lower()
        
        for pattern in seo_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            concepts.extend(matches)
            
        # Дополнительно извлекаем важные существительные
        words = word_tokenize(text_lower)
        filtered_words = [word for word in words if word not in RUSSIAN_STOP_WORDS and len(word) > 3]
        concepts.extend(filtered_words[:5])  # Берем топ-5 слов
        
        return list(set(concepts))[:10]  # Максимум 10 концепций
    
    def calculate_semantic_similarity(self, concepts1: List[str], concepts2: List[str]) -> float:
        """Вычисление семантического сходства между наборами концепций."""
        if not concepts1 or not concepts2:
            return 0.0
            
        # Создаем векторы концепций
        all_concepts = list(set(concepts1 + concepts2))
        
        if len(all_concepts) < 2:
            return 1.0 if concepts1 == concepts2 else 0.0
            
        vector1 = np.array([1 if concept in concepts1 else 0 for concept in all_concepts])
        vector2 = np.array([1 if concept in concepts2 else 0 for concept in all_concepts])
        
        # Избегаем деления на ноль
        if np.linalg.norm(vector1) == 0 or np.linalg.norm(vector2) == 0:
            return 0.0
            
        return float(cosine_similarity([vector1], [vector2])[0][0])
    
    def generate_reasoning_chain(self, stage: str, concepts: List[str], context: str) -> List[str]:
        """Генерация цепочки рассуждений для данного этапа."""
        reasoning_templates = {
            "analyzing": [
                f"Анализирую ключевые концепции: {', '.join(concepts[:3])}",
                f"Определяю семантические связи в контексте: {context[:100]}...",
                "Оцениваю релевантность и потенциал для SEO"
            ],
            "connecting": [
                f"Ищу связи между концепциями: {' ↔ '.join(concepts[:2])}",
                "Анализирую семантическую близость статей",
                "Выявляю возможности для внутренней перелинковки"
            ],
            "evaluating": [
                "Оцениваю качество найденных связей",
                f"Проверяю релевантность для концепций: {', '.join(concepts[:2])}",
                "Рассчитываю потенциальную SEO-ценность"
            ],
            "optimizing": [
                "Оптимизирую анкорный текст для максимальной эффективности",
                "Учитываю семантическую близость и пользовательский опыт",
                "Формирую финальные рекомендации"
            ]
        }
        
        return reasoning_templates.get(stage, ["Выполняю анализ..."])
    
    async def generate_intelligent_thought(
        self, 
        stage: str, 
        context: str, 
        additional_data: Dict = None
    ) -> AIThought:
        """Генерация интеллектуальной мысли с расширенной аналитикой."""
        
        concepts = self.extract_key_concepts(context)
        reasoning_chain = self.generate_reasoning_chain(stage, concepts, context)
        
        # Вычисляем семантический вес на основе истории
        semantic_weight = 0.5  # базовый вес
        if self.thought_history:
            last_thought = self.thought_history[-1]
            similarity = self.calculate_semantic_similarity(
                concepts, last_thought.related_concepts
            )
            semantic_weight = 0.3 + (similarity * 0.7)  # 0.3-1.0 диапазон
        
        # Определяем уверенность на основе количества концепций и их качества
        confidence = min(0.9, 0.4 + (len(concepts) * 0.05) + (len(reasoning_chain) * 0.1))
        
        # Генерируем контент мысли
        thought_content = self._generate_thought_content(stage, concepts, context, additional_data)
        
        thought = AIThought(
            thought_id=f"{stage}_{datetime.now().strftime('%H%M%S_%f')}",
            stage=stage,
            content=thought_content,
            confidence=confidence,
            semantic_weight=semantic_weight,
            related_concepts=concepts,
            reasoning_chain=reasoning_chain,
            timestamp=datetime.now()
        )
        
        self.thought_history.append(thought)
        self._update_semantic_network(concepts)
        
        return thought
    
    def _generate_thought_content(
        self, 
        stage: str, 
        concepts: List[str], 
        context: str, 
        additional_data: Dict = None
    ) -> str:
        """Генерация содержания мысли на основе этапа и концепций."""
        
        stage_templates = {
            "analyzing": f"🔍 Анализирую {len(concepts)} ключевых концепций. " +
                        f"Фокус на: {', '.join(concepts[:2])}. " +
                        f"Глубина анализа: {len(context.split())//10} сегментов.",
            
            "connecting": f"🔗 Устанавливаю семантические связи. " +
                         f"Найдено {len(self.semantic_network)} узлов в сети. " +
                         f"Потенциальных связей: {sum(len(connections) for connections in self.semantic_network.values())}",
            
            "evaluating": f"⚖️ Оцениваю качество связей по {len(concepts)} критериям. " +
                         f"Средний вес связей: {np.mean([0.6, 0.7, 0.8]):.2f}",
            
            "optimizing": f"⚡ Оптимизирую рекомендации. " +
                         f"Применяю {len(self.reasoning_patterns)} паттернов. " +
                         f"Целевые концепции: {', '.join(concepts[:3])}"
        }
        
        base_content = stage_templates.get(stage, "🤔 Выполняю глубокий анализ...")
        
        if additional_data:
            if "articles_count" in additional_data:
                base_content += f" | Статей: {additional_data['articles_count']}"
            if "recommendations_count" in additional_data:
                base_content += f" | Рекомендаций: {additional_data['recommendations_count']}"
                
        return base_content
    
    def _update_semantic_network(self, concepts: List[str]) -> None:
        """Обновление семантической сети концепций."""
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                self.semantic_network[concept1].add(concept2)
                self.semantic_network[concept2].add(concept1)
    
    def get_network_insights(self) -> Dict[str, Any]:
        """Получение инсайтов о семантической сети."""
        if not self.semantic_network:
            return {"status": "empty", "insights": []}
            
        # Находим наиболее связанные концепции
        concept_connections = {
            concept: len(connections) 
            for concept, connections in self.semantic_network.items()
        }
        
        top_concepts = sorted(concept_connections.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "status": "active",
            "total_concepts": len(self.semantic_network),
            "total_connections": sum(len(connections) for connections in self.semantic_network.values()) // 2,
            "top_concepts": top_concepts,
            "network_density": len(self.semantic_network) / max(1, sum(len(connections) for connections in self.semantic_network.values())),
            "insights": [
                f"Доминирующая концепция: {top_concepts[0][0] if top_concepts else 'н/д'}",
                f"Средняя связность: {np.mean(list(concept_connections.values())):.2f}",
                f"Концепций с высокой связностью: {sum(1 for _, count in concept_connections.items() if count > 3)}"
            ]
        }

    async def create_semantic_knowledge_base(
        self,
        domain: str,
        posts: List[Dict],
        client_id: Optional[str] = None
    ) -> bool:
        """Создает семантическую базу знаний с тематической кластеризацией."""
        if not chroma_client:
            print("❌ RAG-система не инициализирована")
            return False

        try:
            if client_id:
                await websocket_manager.send_step(client_id, "Семантический анализ", 1, 5, "Анализ тематик и концепций...")

            print(f"🧠 Создание семантической базы знаний для {domain}...")

            # Очищаем имя коллекции
            collection_name = domain.replace(".", "_").replace("-", "_")

            # Удаляем старую коллекцию
            try:
                chroma_client.delete_collection(name=collection_name)
                print(f"🗑️ Удалена старая коллекция {collection_name}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления коллекции {collection_name}: {e}")

            # Создаем коллекцию с метаданными
            collection = chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "domain": domain,
                    "created_at": datetime.now().isoformat(),
                    "rag_version": "2.0",
                    "semantic_analysis": True
                }
            )

            if client_id:
                await websocket_manager.send_step(client_id, "Обработка контента", 2, 5, "Извлечение ключевых концепций...")

            # Продвинутая обработка статей
            enriched_posts = await self._enrich_posts_with_semantics(posts, domain)

            if client_id:
                await websocket_manager.send_step(client_id, "Векторизация", 3, 5, "Создание семантических векторов...")

            documents = []
            metadatas = []
            ids = []

            for i, post in enumerate(enriched_posts):
                # Создаем богатый семантический контекст для LLM
                semantic_text = self._create_llm_friendly_context(post)

                # Исправляем метаданные - только строки, числа и булевы значения
                key_concepts = post.get('key_concepts', [])
                key_concepts_str = ', '.join(key_concepts[:5]) if key_concepts else ""  # Конвертируем в строку

                documents.append(semantic_text)
                metadatas.append({
                    "title": (post.get('title', '') or '')[:300],  # Обеспечиваем строку
                    "link": post.get('link', '') or '',
                    "content_snippet": (post.get('content', '') or '')[:500],
                    "domain": domain,
                    "post_index": i,
                    "semantic_summary": (post.get('semantic_summary', '') or '')[:500],
                    "key_concepts_str": key_concepts_str,  # Строка вместо списка
                    "key_concepts_count": len(key_concepts),  # Количество как число
                    "content_type": post.get('content_type', 'article'),
                    "difficulty_level": post.get('difficulty_level', 'medium'),
                    "linkability_score": float(post.get('linkability_score', 0.5))  # Убеждаемся что это float
                })
                ids.append(f"{collection_name}_{i}")

            if not documents:
                print(f"❌ Нет статей для семантического анализа {domain}")
                return False

            if client_id:
                await websocket_manager.send_step(client_id, "Кластеризация", 4, 5, "Группировка по тематикам...")

            # Создаем семантические векторы
            vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 3),
                min_df=1,
                max_df=0.8,
                stop_words=list(RUSSIAN_STOP_WORDS),
                analyzer='word'
            )

            tfidf_matrix = vectorizer.fit_transform(documents)
            dense_embeddings = tfidf_matrix.toarray().tolist()

            # Добавляем в коллекцию
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=dense_embeddings
            )

            if client_id:
                await websocket_manager.send_step(client_id, "Финализация", 5, 5, "Сохранение семантической модели...")

            self.domain_collections[domain] = collection_name

            print(f"🧠 Семантическая база знаний создана: {len(documents)} статей для {domain}")
            return True

        except Exception as e:
            print(f"❌ Ошибка создания семантической базы: {e}")
            return False

    async def _enrich_posts_with_semantics(self, posts: List[Dict], domain: str) -> List[Dict]:
        """Обогащает статьи семантической информацией."""
        enriched = []

        for post in posts:
            try:
                title = post.get('title', '')
                content = post.get('content', '')

                # Извлекаем ключевые концепции
                key_concepts = self._extract_key_concepts(title + ' ' + content)

                # Определяем тип контента
                content_type = self._classify_content_type(title, content)

                # Оцениваем уровень сложности
                difficulty = self._assess_difficulty(content)

                # Вычисляем потенциал для внутренних ссылок
                linkability = self._calculate_linkability_score(title, content, key_concepts)

                # Создаем семантическое резюме
                semantic_summary = self._create_semantic_summary(title, content, key_concepts)

                enriched_post = {
                    **post,
                    'key_concepts': key_concepts,
                    'content_type': content_type,
                    'difficulty_level': difficulty,
                    'linkability_score': linkability,
                    'semantic_summary': semantic_summary
                }

                enriched.append(enriched_post)

            except Exception as e:
                print(f"⚠️ Ошибка обогащения статьи {post.get('title', 'unknown')}: {e}")
                enriched.append(post)  # добавляем как есть

        return enriched

    def _extract_key_concepts(self, text: str) -> List[str]:
        """Извлекает ключевые концепции из текста."""
        # Простая реализация на основе частотности
        words = word_tokenize(text.lower())
        words = [w for w in words if w.isalpha() and len(w) > 3 and w not in RUSSIAN_STOP_WORDS]

        # Подсчитываем частоту
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Возвращаем топ-10 концепций
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:10]

    def _classify_content_type(self, title: str, content: str) -> str:
        """Классифицирует тип контента."""
        title_lower = title.lower()

        # Простые правила классификации
        if any(word in title_lower for word in ['как', 'гайд', 'руководство', 'инструкция']):
            return 'guide'
        elif any(word in title_lower for word in ['обзор', 'сравнение', 'тест']):
            return 'review'
        elif any(word in title_lower for word in ['новости', 'анонс', 'релиз']):
            return 'news'
        elif len(content) < 1000:
            return 'short_article'
        else:
            return 'article'

    def _assess_difficulty(self, content: str) -> str:
        """Оценивает уровень сложности контента."""
        words = word_tokenize(content)
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0

        if avg_word_length < 5:
            return 'easy'
        elif avg_word_length < 7:
            return 'medium'
        else:
            return 'advanced'

    def _calculate_linkability_score(self, title: str, content: str, concepts: List[str]) -> float:
        """Вычисляет потенциал для создания внутренних ссылок."""
        score = 0.0

        # Базовый скор на основе длины контента
        score += min(len(content) / 2000, 0.4)  # до 0.4 за длину

        # Скор за количество концепций
        score += min(len(concepts) / 20, 0.3)  # до 0.3 за концепции

        # Скор за ключевые слова в заголовке
        if any(word in title.lower() for word in ['как', 'что', 'где', 'почему']):
            score += 0.2

        # Скор за структурированность (простая проверка)
        if content.count('.') > 5:  # много предложений
            score += 0.1

        return min(score, 1.0)

    def _create_semantic_summary(self, title: str, content: str, concepts: List[str]) -> str:
        """Создает семантическое резюме для LLM."""
        # Берем первые 2 - 3 предложения и добавляем ключевые концепции
        sentences = content.split('.')[:3]
        summary = '. '.join(sentences).strip()

        if concepts:
            summary += f" Ключевые темы: {', '.join(concepts[:5])}."

        return summary[:500]  # ограничиваем длину

    def _create_llm_friendly_context(self, post: Dict) -> str:
        """Создает LLM-дружественный контекст статьи."""
        title = post.get('title', '')
        summary = post.get('semantic_summary', '')
        concepts = post.get('key_concepts', [])
        content_type = post.get('content_type', 'article')
        difficulty = post.get('difficulty_level', 'medium')

        # Формируем структурированный контекст для LLM
        context_parts = [
            f"ЗАГОЛОВОК: {title}",
            f"ТИП: {content_type}",
            f"СЛОЖНОСТЬ: {difficulty}",
            f"ОПИСАНИЕ: {summary}"
        ]

        if concepts:
            context_parts.append(f"КЛЮЧЕВЫЕ_ТЕМЫ: {', '.join(concepts[:7])}")

        return ' | '.join(context_parts)

    async def get_semantic_recommendations(
        self,
        domain: str,
        limit: int = 25,
        min_linkability: float = 0.2  # Снижаем порог для большего покрытия
    ) -> List[Dict]:
        """Получает семантические рекомендации с учетом контекста."""
        if domain not in self.domain_collections:
            return []

        try:
            collection = chroma_client.get_collection(name=self.domain_collections[domain])

            # Получаем все документы с метаданными
            results = collection.get(
                limit=limit * 2,  # берем больше для фильтрации
                include=['metadatas', 'documents']
            )

            # Фильтруем по потенциалу создания ссылок
            filtered_articles = []
            for i, metadata in enumerate(results['metadatas']):
                linkability_score = metadata.get('linkability_score', 0.0)
                if linkability_score >= min_linkability:
                    # Восстанавливаем key_concepts из строки
                    key_concepts_str = metadata.get('key_concepts_str', '')
                    key_concepts = [kc.strip() for kc in key_concepts_str.split(',') if kc.strip()] if key_concepts_str else []

                    filtered_articles.append({
                        'title': metadata['title'],
                        'link': metadata['link'],
                        'content': metadata.get('content_snippet', ''),
                        'semantic_summary': metadata.get('semantic_summary', ''),
                        'key_concepts': key_concepts,
                        'content_type': metadata.get('content_type', 'article'),
                        'difficulty_level': metadata.get('difficulty_level', 'medium'),
                        'linkability_score': linkability_score,
                        'domain': metadata['domain']
                    })

            # Сортируем по потенциалу создания ссылок
            filtered_articles.sort(key=lambda x: x['linkability_score'], reverse=True)

            print(f"🎯 Получено {len(filtered_articles)} семантически релевантных статей")
            return filtered_articles[:limit]

        except Exception as e:
            print(f"❌ Ошибка получения семантических рекомендаций: {e}")
            return []


class CumulativeIntelligenceManager:
    """Менеджер кумулятивного интеллекта для глубокого анализа связей."""

    def __init__(self) -> None:
        self.connection_cache = {}
        self.cluster_cache = {}
        self.insight_cache = {}

    async def analyze_existing_connections(self, domain: str, session: AsyncSession) -> dict:
        """Анализирует существующие связи и рекомендации."""
        domain_result = await session.execute(
            select(Domain).where(Domain.name == domain)
        )
        domain_obj = domain_result.scalar_one_or_none()
        if not domain_obj:
            return {"existing_connections": 0, "existing_recommendations": 0}

        # Получаем существующие семантические связи
        connections_result = await session.execute(
            select(SemanticConnection)
            .join(WordPressPost, SemanticConnection.source_post_id == WordPressPost.id)
            .where(WordPressPost.domain_id == domain_obj.id)
        )
        existing_connections = connections_result.scalars().all()

        # Получаем существующие рекомендации
        recommendations_result = await session.execute(
            select(LinkRecommendation)
            .where(LinkRecommendation.domain_id == domain_obj.id)
            .where(LinkRecommendation.status == 'active')
        )
        existing_recommendations = recommendations_result.scalars().all()

        return {
            "existing_connections": len(existing_connections),
            "existing_recommendations": len(existing_recommendations),
            "connections": existing_connections,
            "recommendations": existing_recommendations,
            "domain_id": domain_obj.id
        }

    async def discover_thematic_clusters(self, domain_id: int, posts: list, session: AsyncSession) -> list:
        """Обнаруживает и анализирует тематические кластеры."""
        from sklearn.cluster import KMeans
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np

        if len(posts) < 3:
            return []

        # Создаем TF-IDF векторы для кластеризации
        texts = [f"{post['title']} {post.get('content', '')[:500]}" for post in posts]
        vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2),
            stop_words=list(RUSSIAN_STOP_WORDS)
        )

        try:
            tfidf_matrix = vectorizer.fit_transform(texts)

            # Определяем оптимальное количество кластеров
            n_clusters = min(max(2, len(posts) // 5), 8)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)

            # Анализируем каждый кластер
            clusters = []
            feature_names = vectorizer.get_feature_names_out()

            for cluster_id in range(n_clusters):
                cluster_posts = [posts[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                if len(cluster_posts) < 2:
                    continue

                # Получаем центроид кластера для ключевых слов
                cluster_center = kmeans.cluster_centers_[cluster_id]
                top_features_idx = cluster_center.argsort()[-10:][::-1]
                cluster_keywords = [feature_names[i] for i in top_features_idx]

                # Вычисляем метрики кластера
                coherence_score = float(np.mean([cluster_center[i] for i in top_features_idx[:5]]))
                diversity_score = float(len(set(cluster_keywords)) / len(cluster_keywords))
                linkability_potential = coherence_score * diversity_score * len(cluster_posts) / len(posts)

                cluster_analysis = ThematicClusterAnalysis(
                    domain_id=domain_id,
                    cluster_name=f"Кластер {cluster_id + 1}: {', '.join(cluster_keywords[:3])}",
                    cluster_keywords=cluster_keywords,
                    cluster_description=f"Тематический кластер из {len(cluster_posts)} статей",
                    article_ids=[post.get('id', 0) for post in cluster_posts],
                    article_count=len(cluster_posts),
                    coherence_score=coherence_score,
                    diversity_score=diversity_score,
                    linkability_potential=linkability_potential,
                    evolution_stage='emerging'
                )

                session.add(cluster_analysis)
                clusters.append({
                    'analysis': cluster_analysis,
                    'posts': cluster_posts,
                    'keywords': cluster_keywords
                })

            await session.commit()
            return clusters

        except Exception as e:
            print(f"❌ Ошибка кластеризации: {e}")
            return []

    async def generate_cumulative_insights(self, domain_id: int, analysis_data: dict, session: AsyncSession):
        """Генерирует накопленные инсайты на основе анализа."""
        insights = []

        # Инсайт о плотности связей
        if analysis_data['existing_connections'] > 0:
            connection_density = analysis_data['existing_connections'] / max(analysis_data.get('total_posts', 1), 1)

            if connection_density < 0.1:
                insight = CumulativeInsight(
                    domain_id=domain_id,
                    insight_type='gap',
                    insight_category='structural',
                    title='Низкая плотность внутренних связей',
                    description=f'Домен имеет только {analysis_data["existing_connections"]} связей между статьями. Рекомендуется увеличить внутреннюю перелинковку.',
                    evidence={'connection_density': connection_density, 'total_connections': analysis_data['existing_connections']},
                    impact_score=0.8,
                    confidence_level=0.9,
                    actionability=0.9
                )
                session.add(insight)
                insights.append(insight)

        # Инсайт о тематическом разнообразии
        clusters = analysis_data.get('clusters', [])
        if len(clusters) > 1:
            avg_linkability = sum(c['analysis'].linkability_potential for c in clusters) / len(clusters)

            if avg_linkability > 0.3:
                insight = CumulativeInsight(
                    domain_id=domain_id,
                    insight_type='opportunity',
                    insight_category='thematic',
                    title='Высокий потенциал межтематических связей',
                    description=f'Обнаружено {len(clusters)} тематических кластеров с высоким потенциалом перелинковки.',
                    evidence={'clusters_count': len(clusters), 'avg_linkability': avg_linkability},
                    impact_score=0.7,
                    confidence_level=0.8,
                    actionability=0.8
                )
                session.add(insight)
                insights.append(insight)

        await session.commit()
        return insights

    async def deduplicate_and_evolve_recommendations(
        self,
        new_recommendations: list,
        domain_id: int,
        session: AsyncSession
    ) -> list:
        """Дедуплицирует и эволюционирует рекомендации."""
        # Получаем существующие рекомендации
        existing_result = await session.execute(
            select(LinkRecommendation)
            .where(LinkRecommendation.domain_id == domain_id)
            .where(LinkRecommendation.status == 'active')
        )
        existing_recommendations = {
            (rec.source_post_id, rec.target_post_id): rec
            for rec in existing_result.scalars().all()
        }

        evolved_recommendations = []

        for new_rec in new_recommendations:
            # Пытаемся найти соответствующие посты в БД
            source_result = await session.execute(
                select(WordPressPost)
                .where(WordPressPost.domain_id == domain_id)
                .where(WordPressPost.link == new_rec['from'])
            )
            source_post = source_result.scalar_one_or_none()

            target_result = await session.execute(
                select(WordPressPost)
                .where(WordPressPost.domain_id == domain_id)
                .where(WordPressPost.link == new_rec['to'])
            )
            target_post = target_result.scalar_one_or_none()

            if not source_post or not target_post:
                continue

            key = (source_post.id, target_post.id)

            if key in existing_recommendations:
                # Эволюционируем существующую рекомендацию
                existing_rec = existing_recommendations[key]

                # Проверяем, улучшилась ли рекомендация
                new_quality = self._calculate_quality_score(new_rec)
                if new_quality > existing_rec.quality_score:
                    # Создаем улучшенную версию
                    improved_rec = LinkRecommendation(
                        domain_id=domain_id,
                        source_post_id=source_post.id,
                        target_post_id=target_post.id,
                        anchor_text=new_rec['anchor'],
                        reasoning=new_rec['comment'],
                        quality_score=new_quality,
                        generation_count=existing_rec.generation_count + 1,
                        improvement_iterations=existing_rec.improvement_iterations + 1,
                        previous_version_id=existing_rec.id,
                        improvement_reason=f"Улучшенное качество: {new_quality:.2f} > {existing_rec.quality_score:.2f}"
                    )

                    # Помечаем старую как улучшенную
                    existing_rec.status = 'improved'

                    session.add(improved_rec)
                    evolved_recommendations.append(new_rec)
                else:
                    # Увеличиваем счетчик генерации
                    existing_rec.generation_count += 1
                    existing_rec.updated_at = datetime.utcnow()
            else:
                # Создаем новую рекомендацию
                quality_score = self._calculate_quality_score(new_rec)
                link_rec = LinkRecommendation(
                    domain_id=domain_id,
                    source_post_id=source_post.id,
                    target_post_id=target_post.id,
                    anchor_text=new_rec['anchor'],
                    reasoning=new_rec['comment'],
                    quality_score=quality_score
                )

                session.add(link_rec)
                evolved_recommendations.append(new_rec)

        await session.commit()
        return evolved_recommendations

    def _calculate_quality_score(self, recommendation: dict) -> float:
        """Вычисляет оценку качества рекомендации."""
        score = 0.0

        # Оценка анкора
        anchor = recommendation.get('anchor', '')
        if len(anchor) > 5:
            score += 0.3
        if any(word in anchor.lower() for word in ['подробный', 'полный', 'детальный', 'руководство']):
            score += 0.2

        # Оценка обоснования
        comment = recommendation.get('comment', '')
        if len(comment) > 20:
            score += 0.3
        if len(comment) > 50:
            score += 0.2

        return min(score, 1.0)


# Инициализация глобальных менеджеров будет ниже


async def generate_links(text: str) -> list[str]:
    """Запрашивает Ollama для генерации простых ссылок."""
    prompt = (
        "Предложи до пяти внутренних ссылок для следующего текста на русском языке. "
        "Каждую ссылку выведи с новой строки в формате /article/название-статьи, "
        "основываясь на ключевых словах из текста. "
        "Не добавляй лишние символы или объяснения. "
        f"Текст: {text}"
    )
    async with httpx.AsyncClient(timeout=720.0) as client:  # Увеличиваем до 12 минут для стабильности
        response = await client.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=720,  # 12 минут на запрос
        )
    response.raise_for_status()
    data = response.json()
    lines = [line.strip("- \n") for line in data.get("response", "").splitlines()]
    links = [line for line in lines if line]
    return links[:5]


async def fetch_and_store_wp_posts(domain: str, client_id: Optional[str] = None) -> tuple[list[dict[str, str]], dict]:
    """Загружает статьи WordPress с умной дельта-индексацией."""
    print(f"🧠 Умная индексация домена {domain}")

    if client_id:
        await websocket_manager.send_step(client_id, "Проверка изменений", 1, 5, "Анализ существующих данных...")

    # Получаем или создаем домен
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Domain).where(Domain.name == domain)
        )
        domain_obj = result.scalar_one_or_none()

        if not domain_obj:
            domain_obj = Domain(
                name=domain,
                display_name=domain,
                description=f"Автоматически созданный домен для {domain}",
                language="ru"
            )
            session.add(domain_obj)
            await session.commit()
            await session.refresh(domain_obj)
            print(f"✅ Создан новый домен: {domain}")

        # Загружаем существующие посты для сравнения
        existing_posts_result = await session.execute(
            select(WordPressPost).where(WordPressPost.domain_id == domain_obj.id)
        )
        existing_posts = {post.wp_post_id: post for post in existing_posts_result.scalars().all()}
        print(f"📊 Найдено {len(existing_posts)} существующих постов в БД")

    if client_id:
        await websocket_manager.send_step(client_id, "Загрузка с WordPress", 2, 5, "Получение актуальных данных...")

    url = f"https://{domain}/wp-json/wp/v2/posts?per_page=50"
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="Сайт недоступен или не WordPress")
    data = response.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Некорректный ответ WordPress")

    if client_id:
        await websocket_manager.send_step(client_id, "Анализ изменений", 3, 5, f"Обработка {len(data)} статей...")

    # Статистика дельта-индексации
    delta_stats = {
        'new_posts': 0,
        'updated_posts': 0,
        'unchanged_posts': 0,
        'removed_posts': 0,
        'total_posts': len(data)
    }

    posts = []
    processed_wp_ids = set()
    seen_urls = set()
    seen_titles = set()

    async with AsyncSessionLocal() as session:
        for item in data:
            try:
                wp_post_id = item["id"]
                processed_wp_ids.add(wp_post_id)

                # Извлекаем содержимое
                content = item.get("content", {}).get("rendered", "")
                excerpt = item.get("excerpt", {}).get("rendered", "")

                # Очищаем HTML
                clean_content = BeautifulSoup(content, 'html.parser').get_text()
                clean_excerpt = BeautifulSoup(excerpt, 'html.parser').get_text() if excerpt else ""

                # Проверяем, что ссылка принадлежит нашему домену
                post_link = item["link"]
                if domain.lower() not in post_link.lower():
                    print(f"⚠️ Пропускаю статью с чужого домена: {post_link}")
                    continue

                # Дедупликация по URL
                if post_link in seen_urls:
                    print(f"⚠️ Дубликат URL пропущен: {post_link}")
                    continue
                seen_urls.add(post_link)

                # Дедупликация по заголовку
                title = item["title"]["rendered"]
                title_normalized = title.lower().strip()
                if title_normalized in seen_titles:
                    print(f"⚠️ Дубликат заголовка пропущен: {title}")
                    continue
                seen_titles.add(title_normalized)

                # Проверяем, нужно ли обновлять пост
                existing_post = existing_posts.get(wp_post_id)
                # Получаем время модификации для потенциального использования
                # modified_str = item.get("modified", datetime.now().isoformat())
                # post_modified = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))

                if existing_post:
                    # Проверяем, изменился ли пост
                    if (existing_post.title == title and existing_post.content == clean_content and existing_post.link == post_link):                        # Пост не изменился
                        delta_stats['unchanged_posts'] += 1
                        print(f"⚡ Пост не изменился: {title}")

                        # Добавляем в результат без пересохранения
                        posts.append({
                            "title": title,
                            "link": post_link,
                            "content": clean_content[:800].strip()
                        })
                        continue
                    else:
                        # Пост изменился - обновляем
                        existing_post.title = title
                        existing_post.content = clean_content
                        existing_post.excerpt = clean_excerpt
                        existing_post.link = post_link
                        existing_post.updated_at = datetime.utcnow()
                        existing_post.last_analyzed_at = None  # type: ignore # Сброс для переиндексации

                        delta_stats['updated_posts'] += 1
                        print(f"🔄 Обновлен пост: {title}")
                else:
                    # Новый пост - создаем
                    wp_post = WordPressPost(
                        domain_id=domain_obj.id,
                        wp_post_id=wp_post_id,
                        title=title,
                        content=clean_content,
                        excerpt=clean_excerpt,
                        link=post_link,
                        published_at=datetime.fromisoformat(
                            item["date"].replace('Z', '+00:00')
                        ) if item.get("date") else None,
                        last_analyzed_at=None  # Новый пост требует анализа
                    )
                    session.add(wp_post)

                    delta_stats['new_posts'] += 1
                    print(f"➕ Добавлен новый пост: {title}")

                # Добавляем в результат
                posts.append({
                    "title": title,
                    "link": post_link,
                    "content": clean_content[:800].strip()
                })

            except Exception as exc:
                print(f"❌ Ошибка обработки поста {item.get('id', 'unknown')}: {exc}")
                continue

        # Удаляем посты, которых больше нет на сайте
        for wp_post_id, existing_post in existing_posts.items():
            if wp_post_id not in processed_wp_ids:
                await session.delete(existing_post)
                delta_stats['removed_posts'] += 1
                print(f"🗑️ Удален пост: {existing_post.title}")

        # Подсчитываем актуальное количество постов в БД
        posts_count_result = await session.execute(
            select(func.count(WordPressPost.id))
            .where(WordPressPost.domain_id == domain_obj.id)
        )
        actual_posts_count = posts_count_result.scalar()

        # Обновляем статистику домена
        domain_obj.total_posts = actual_posts_count if actual_posts_count is not None else 0
        domain_obj.updated_at = datetime.utcnow()

        print(f"📊 Обновлена статистика домена: {actual_posts_count} постов в БД")

        await session.commit()

        if client_id:
            await websocket_manager.send_step(client_id, "Финализация", 4, 5, "Сохранение изменений...")

        print(f"🧠 Умная индексация завершена:")
        print(f"   ➕ Новые посты: {delta_stats['new_posts']}")
        print(f"   🔄 Обновленные: {delta_stats['updated_posts']}")
        print(f"   ⚡ Без изменений: {delta_stats['unchanged_posts']}")
        print(f"   🗑️ Удаленные: {delta_stats['removed_posts']}")
        print(f"   📊 Всего постов: {len(posts)}")

        if client_id:
            await websocket_manager.send_step(client_id, "Индексация завершена", 5, 5,
                f"Новых: {delta_stats['new_posts']}, Обновлено: {delta_stats['updated_posts']}, Удалено: {delta_stats['removed_posts']}")

    return posts, delta_stats


async def generate_comprehensive_domain_recommendations(domain: str, client_id: Optional[str] = None) -> list[dict[str, str]]:
    """Генерирует кумулятивные рекомендации с накоплением знаний."""
    print(f"🧠 Запуск кумулятивного анализа домена {domain} (client: {client_id})")

    analysis_start_time = datetime.now()
    all_recommendations = []

    try:
        # Шаг 1: Анализ существующих связей и накопленных знаний
        if client_id:
            await websocket_manager.send_step(client_id, "Анализ накопленных знаний", 1, 12, "Изучение существующих связей...")

        async with AsyncSessionLocal() as session:
            # Анализируем существующие связи
            existing_analysis = await cumulative_manager.analyze_existing_connections(domain, session)
            print(f"🔗 Найдено {existing_analysis['existing_connections']} существующих связей")
            print(f"📋 Найдено {existing_analysis['existing_recommendations']} активных рекомендаций")

            domain_obj = await session.get(Domain, existing_analysis['domain_id'])
            if not domain_obj:
                error_msg = f"❌ Домен {domain} не найден в БД"
                print(error_msg)
                if client_id:
                    await websocket_manager.send_error(client_id, error_msg)
                return [], 0.0

            # Получаем ВСЕ посты с семантической информацией
            result = await session.execute(
                select(WordPressPost)
                .where(WordPressPost.domain_id == domain_obj.id)
                .order_by(WordPressPost.linkability_score.desc())
            )
            all_posts = result.scalars().all()

        if not all_posts:
            error_msg = "❌ Нет статей для кумулятивного анализа"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg)
            return [], 0.0

        print(f"📊 Кумулятивный анализ: {len(all_posts)} статей из БД")

        # Шаг 2: Тематическая кластеризация
        if client_id:
            await websocket_manager.send_step(client_id, "Тематическая кластеризация", 2, 12, f"Анализ {len(all_posts)} статей по темам...")

        full_dataset = []
        for post in all_posts:
            full_dataset.append({
                "id": post.id,
                "title": post.title,
                "link": post.link,
                "content": post.content,
                "semantic_summary": post.semantic_summary or "",
                "key_concepts": post.key_concepts or [],
                "content_type": post.content_type or "article",
                "difficulty_level": post.difficulty_level or "medium",
                "linkability_score": post.linkability_score or 0.5,
                "semantic_richness": post.semantic_richness or 0.5
            })

        async with AsyncSessionLocal() as session:
            # Обнаруживаем тематические кластеры
            clusters = await cumulative_manager.discover_thematic_clusters(
                domain_obj.id, full_dataset, session
            )
            print(f"🎯 Обнаружено {len(clusters)} тематических кластеров")

            existing_analysis['clusters'] = clusters
            existing_analysis['total_posts'] = len(all_posts)

        # Шаг 3: Генерация кумулятивных инсайтов
        if client_id:
            await websocket_manager.send_step(client_id, "Генерация инсайтов", 3, 12, "Анализ возможностей улучшения...")

        async with AsyncSessionLocal() as session:
            insights = await cumulative_manager.generate_cumulative_insights(
                domain_obj.id, existing_analysis, session
            )
            print(f"💡 Сгенерировано {len(insights)} кумулятивных инсайтов")

        # Шаг 4: Создаем семантическую базу знаний
        if client_id:
            await websocket_manager.send_step(client_id, "Семантический анализ", 4, 12, "Создание семантической модели...")
            await websocket_manager.send_ai_thinking(
                client_id,
                "Создаю векторные представления статей и выстраиваю семантические связи в многомерном пространстве...",
                "vectorizing",
                "🧮"
            )

        success = await rag_manager.create_semantic_knowledge_base(domain, full_dataset, client_id)
        if not success:
            error_msg = "❌ Не удалось создать семантическую базу знаний"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg)
            return [], 0.0

        # Шаг 5: Контекстно-осведомленный батчинг
        if client_id:
            await websocket_manager.send_step(client_id, "Умный батчинг", 5, 12, "Группировка по кластерам...")

        # Группируем статьи по кластерам для более осознанного анализа
        cluster_batches = []
        for cluster in clusters:
            cluster_posts = cluster['posts']
            if len(cluster_posts) >= 2:
                cluster_batches.append({
                    'posts': cluster_posts,
                    'cluster_info': cluster['analysis'],
                    'keywords': cluster['keywords']
                })

        # Добавляем ограниченное количество межкластерных батчей (максимум 5)
        if len(clusters) > 1:
            cross_cluster_count = 0
            max_cross_clusters = 5  # Ограничиваем для стабильности

            for i, cluster1 in enumerate(clusters):
                if cross_cluster_count >= max_cross_clusters:
                    break
                for cluster2 in clusters[i+1:]:
                    if cross_cluster_count >= max_cross_clusters:
                        break
                    # Микс статей из разных кластеров
                    mixed_posts = cluster1['posts'][:2] + cluster2['posts'][:2]
                    cluster_batches.append({
                        'posts': mixed_posts,
                        'cluster_info': None,  # межкластерный анализ
                        'keywords': cluster1['keywords'] + cluster2['keywords'],
                        'cross_cluster': True
                    })
                    cross_cluster_count += 1

        print(f"🧠 Создано {len(cluster_batches)} кластерных батчей")

        # Шаг 6 - 9: Обрабатываем кластерные батчи
        for batch_idx, batch_info in enumerate(cluster_batches, 1):
            if client_id:
                batch_type = "Межкластерный" if batch_info.get('cross_cluster') else "Кластерный"
                await websocket_manager.send_step(
                    client_id,
                    f"{batch_type} анализ {batch_idx}/{len(cluster_batches)}",
                    5 + batch_idx,
                    12,
                    f"Анализ связей в контексте тем..."
                )

            batch_recommendations = await process_cumulative_batch_with_ollama(
                domain, batch_info, existing_analysis, batch_idx, len(cluster_batches), client_id
            )

            all_recommendations.extend(batch_recommendations)
            print(f"✅ Кластерный батч {batch_idx}: получено {len(batch_recommendations)} рекомендаций")

        # Шаг 10: Кумулятивная дедупликация и эволюция
        if client_id:
            await websocket_manager.send_step(client_id, "Кумулятивная обработка", 10, 12, "Эволюция рекомендаций...")

        async with AsyncSessionLocal() as session:
            evolved_recommendations = await cumulative_manager.deduplicate_and_evolve_recommendations(
                all_recommendations, domain_obj.id, session
            )
            print(f"🧬 Эволюционировано {len(evolved_recommendations)} рекомендаций")

        # Шаг 11: Финальное ранжирование с учетом накопленных знаний
        if client_id:
            await websocket_manager.send_step(client_id, "Финальное ранжирование", 11, 12, "Приоритизация по важности...")
            await websocket_manager.send_ai_thinking(
                client_id,
                "Применяю накопленные знания о успешных связях и ранжирую рекомендации по потенциальной ценности...",
                "ranking",
                "🎯"
            )

        final_recommendations = rank_recommendations_with_cumulative_intelligence(
            evolved_recommendations, existing_analysis, insights
        )

        # Шаг 12: Финализация кумулятивного анализа
        total_analysis_time = (datetime.now() - analysis_start_time).total_seconds()

        if client_id:
            await websocket_manager.send_step(
                client_id,
                "Завершение кумулятивного анализа",
                12,
                12,
                f"Готово! {len(final_recommendations)} эволюционированных рекомендаций"
            )

        print(f"🧠 Кумулятивный анализ завершен: {len(final_recommendations)} рекомендаций за {total_analysis_time:.1f}с")
        return final_recommendations, total_analysis_time

    except Exception as e:
        error_msg = f"❌ Ошибка полной индексации: {e}"
        print(error_msg)
        if client_id:
            await websocket_manager.send_error(client_id, "Критическая ошибка индексации", str(e))

        error_time = (datetime.now() - analysis_start_time).total_seconds()
        return [], error_time


async def process_batch_with_ollama(
    domain: str,
    batch: List[Dict],
    full_dataset: List[Dict],
    batch_idx: int,
    total_batches: int,
    client_id: Optional[str] = None
) -> List[Dict]:
    """Обрабатывает батч статей через Ollama с максимальным контекстом."""

    # Создаем оптимизированный контекст для батча
    batch_context = f"""АНАЛИЗ БАТЧА {batch_idx}/{total_batches} ДОМЕНА {domain}

СТАТЬИ ДЛЯ АНАЛИЗА ({len(batch)}):
"""

    for i, article in enumerate(batch, 1):
        key_concepts_str = ', '.join(article['key_concepts'][:4]) if article['key_concepts'] else 'не определены'

        batch_context += f"""
{i}. {article['title']}
   URL: {article['link']}
   Тип: {article['content_type']} | Связность: {article['linkability_score']:.2f}
   Концепции: {key_concepts_str}
   Краткое описание: {article['semantic_summary'][:150]}
   Контент: {article['content'][:200]}...

"""

    # Добавляем сокращенный контекст других статей
    batch_context += f"""ДОСТУПНЫЕ ЦЕЛИ ({len(full_dataset)} статей):
"""

    targets_added = 0
    for article in full_dataset[:15]:  # Топ-15 для экономии токенов
        if article not in batch and targets_added < 10:  # Максимум 10 целей
            batch_context += f"• {article['title'][:50]} | {article['link'][:60]}\n"
            targets_added += 1

    # Создаем компактный но эффективный промпт
    comprehensive_prompt = f"""{batch_context}

ЗАДАЧА: Найди логичные внутренние ссылки между статьями

КРИТЕРИИ:
• Тематическая связь
• Польза для читателя
• SEO-ценность

ПРАВИЛА анкоров:
• Описывать содержание целевой страницы
• НЕ использовать: "сайт", "ресурс", "портал"
• Примеры: "подробное руководство", "полный обзор"

Найди ВСЕ качественные связи для статей этого батча.

ФОРМАТ: ИСТОЧНИК -> ЦЕЛЬ | анкор | обоснование

ОТВЕТ:"""

    try:
        # Генерируем интеллектуальную мысль для этапа анализа
        if client_id:
            analyzing_thought = await thought_generator.generate_intelligent_thought(
                stage="analyzing",
                context=f"Батч {batch_idx} из {len(batch)} статей. Домен: {domain}. " +
                       f"Статьи: {', '.join([article.get('title', '')[:50] for article in batch[:2]])}",
                additional_data={
                    "articles_count": len(batch),
                    "batch_number": batch_idx,
                    "total_batches": total_batches
                }
            )
            await websocket_manager.send_enhanced_ai_thinking(client_id, analyzing_thought)
            
            await websocket_manager.send_ollama_info(client_id, {
                "status": "processing_batch",
                "batch": f"{batch_idx}/{total_batches}",
                "articles_in_batch": len(batch),
                "total_context_size": len(comprehensive_prompt),
                "model": OLLAMA_MODEL
            })

        print(f"🤖 Обрабатываю батч {batch_idx} через Ollama (размер промпта: {len(comprehensive_prompt)} символов)")

        start_time = datetime.now()
        async with httpx.AsyncClient(timeout=600.0) as client:  # Увеличиваем тайм-аут до 10 минут
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": comprehensive_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,    # Немного повышаем для креативности
                        "num_ctx": 4096,       # Уменьшаем контекст для стабильности
                        "num_predict": 800,    # Сбалансированное количество токенов
                        "top_p": 0.8,
                        "top_k": 40,
                        "repeat_penalty": 1.05,
                        "num_thread": 6        # Оптимальное количество потоков
                    }
                },
                timeout=600  # 10 минут на батч
            )

        request_time = (datetime.now() - start_time).total_seconds()

        if client_id:
            await websocket_manager.send_ollama_info(client_id, {
                "status": "batch_completed",
                "batch": f"{batch_idx}/{total_batches}",
                "processing_time": f"{request_time:.1f}s",
                "response_length": len(response.text) if response.status_code == 200 else 0
            })

        if response.status_code != 200:
            print(f"❌ Ollama ошибка для батча {batch_idx}: код {response.status_code}")
            return []

        data = response.json()
        content = data.get("response", "")

        print(f"📝 Батч {batch_idx}: получен ответ {len(content)} символов за {request_time:.1f}с")

        # Генерируем мысль для этапа оптимизации
        if client_id:
            optimizing_thought = await thought_generator.generate_intelligent_thought(
                stage="optimizing",
                context=f"Получен ответ от Ollama для батча {batch_idx}. " +
                       f"Размер ответа: {len(content)} символов. " +
                       f"Время обработки: {request_time:.1f}с",
                additional_data={
                    "response_size": len(content),
                    "processing_time": request_time,
                    "batch_number": batch_idx
                }
            )
            await websocket_manager.send_enhanced_ai_thinking(client_id, optimizing_thought)

        # Парсим рекомендации для этого батча
        batch_recommendations = parse_ollama_recommendations(content, domain, full_dataset)

        # Генерируем мысль для этапа оценки результатов
        if client_id and batch_recommendations:
            evaluating_thought = await thought_generator.generate_intelligent_thought(
                stage="evaluating",
                context=f"Найдено {len(batch_recommendations)} рекомендаций для батча {batch_idx}. " +
                       f"Анализирую качество и релевантность связей.",
                additional_data={
                    "recommendations_count": len(batch_recommendations),
                    "batch_number": batch_idx,
                    "success_rate": min(1.0, len(batch_recommendations) / len(batch))
                }
            )
            await websocket_manager.send_enhanced_ai_thinking(client_id, evaluating_thought)

        return batch_recommendations

    except Exception as e:
        print(f"❌ Ошибка обработки батча {batch_idx}: {e}")
        return []


async def process_cumulative_batch_with_ollama(
    domain: str,
    batch_info: dict,
    existing_analysis: dict,
    batch_idx: int,
    total_batches: int,
    client_id: Optional[str] = None
) -> List[Dict]:
    """Обрабатывает кумулятивный батч с учетом накопленных знаний."""

    posts = batch_info['posts']
    keywords = batch_info.get('keywords', [])
    is_cross_cluster = batch_info.get('cross_cluster', False)

    # Создаем контекст с учетом накопленных знаний
    batch_context = f"""КУМУЛЯТИВНЫЙ АНАЛИЗ ДОМЕНА {domain}

КОНТЕКСТ НАКОПЛЕННЫХ ЗНАНИЙ:
• Существующих связей: {existing_analysis['existing_connections']}
• Активных рекомендаций: {existing_analysis['existing_recommendations']}
• Тематических кластеров: {len(existing_analysis.get('clusters', []))}

СТАТЬИ ДЛЯ АНАЛИЗА ({len(posts)}):
"""

    for i, post in enumerate(posts, 1):
        post_concepts = ', '.join(post.get('key_concepts', [])[:3])
        batch_context += f"""
{i}. {post['title']}
   URL: {post['link']}
   Концепции: {post_concepts}
   Тип: {post.get('content_type', 'article')}
   Связность: {post.get('linkability_score', 0.5):.2f}
   Контент: {post.get('content', '')[:150]}...

"""

    if is_cross_cluster:
        batch_context += f"""
🔗 МЕЖКЛАСТЕРНЫЙ АНАЛИЗ
Ключевые темы пересечения: {', '.join(keywords[:8])}
ЗАДАЧА: Найти глубокие семантические связи между разными тематическими областями
"""
    else:
        batch_context += f"""
🎯 ВНУТРИКЛАСТЕРНЫЙ АНАЛИЗ
Тематические ключевые слова: {', '.join(keywords[:6])}
ЗАДАЧА: Найти логичные связи внутри тематического кластера
"""

    # Умный промпт с учетом кумулятивного контекста
    cumulative_prompt = f"""{batch_context}

ПРИНЦИПЫ КУМУЛЯТИВНОГО АНАЛИЗА:
✅ Избегать дублирования уже существующих {existing_analysis['existing_recommendations']} рекомендаций
✅ Создавать НОВЫЕ связи, дополняющие существующую структуру
✅ Учитывать семантические пересечения между кластерами
✅ Приоритизировать глубокие, осмысленные связи

КРИТЕРИИ КАЧЕСТВА:
• Семантическая логичность
• Дополнительная ценность для читателя
• Уникальность относительно существующих связей
• SEO-эффективность

ФОРМАТ: ИСТОЧНИК -> ЦЕЛЬ | анкор | глубокое_обоснование

ОТВЕТ:"""

    try:
        if client_id:
            await websocket_manager.send_ollama_info(client_id, {
                "status": "processing_cumulative_batch",
                "batch": f"{batch_idx}/{total_batches}",
                "batch_type": "межкластерный" if is_cross_cluster else "внутрикластерный",
                "articles_count": len(posts),
                "context_size": len(cumulative_prompt),
                "existing_connections": existing_analysis['existing_connections']
            })

        print(f"🧠 Кумулятивный анализ батча {batch_idx} ({'межкластерный' if is_cross_cluster else 'внутрикластерный'})")

        start_time = datetime.now()
        async with httpx.AsyncClient(timeout=600.0) as client:  # Увеличиваем до 10 минут
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": cumulative_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,    # Чуть выше для креативности
                        "num_ctx": 4096,
                        "num_predict": 600,
                        "top_p": 0.85,
                        "top_k": 50,
                        "repeat_penalty": 1.1,
                        "num_thread": 6
                    }
                },
                timeout=600  # 10 минут
            )

        request_time = (datetime.now() - start_time).total_seconds()

        if response.status_code != 200:
            print(f"❌ Ollama ошибка для кумулятивного батча {batch_idx}: код {response.status_code}")
            return []

        data = response.json()
        content = data.get("response", "")

        print(f"📝 Кумулятивный батч {batch_idx}: получен ответ {len(content)} символов за {request_time:.1f}с")

        # Парсим рекомендации
        batch_recommendations = parse_ollama_recommendations(content, domain, posts)

        return batch_recommendations

    except Exception as e:
        print(f"❌ Ошибка кумулятивного анализа батча {batch_idx}: {e}")
        return []


def rank_recommendations_with_cumulative_intelligence(
    recommendations: List[Dict],
    existing_analysis: dict,
    insights: List
) -> List[Dict]:
    """Ранжирует рекомендации с учетом кумулятивного интеллекта."""

    def cumulative_quality_score(rec):
        score = 0.0

        # Базовые метрики качества
        anchor = rec.get('anchor', '')
        comment = rec.get('comment', '')

        # Длина и качество анкора
        if len(anchor) > 5:
            score += 0.2
        if len(anchor) > 15:
            score += 0.1

        # Качественные слова в анкоре
        quality_words = ['подробный', 'полный', 'детальный', 'руководство', 'инструкция', 'обзор', 'гайд', 'анализ']
        anchor_quality = sum(1 for word in quality_words if word in anchor.lower()) * 0.15
        score += anchor_quality

        # Глубина обоснования
        if len(comment) > 30:
            score += 0.2
        if len(comment) > 60:
            score += 0.1

        # Бонус за семантические ключевые слова в обосновании
        semantic_words = ['семантически', 'тематически', 'логически', 'дополняет', 'углубляет', 'расширяет']
        semantic_bonus = sum(1 for word in semantic_words if word in comment.lower()) * 0.1
        score += semantic_bonus

        # Бонус за новизну (отсутствие в существующих рекомендациях)
        # Это приблизительная оценка, так как точное сравнение требует доступа к БД
        score += 0.1  # предполагаем, что все рекомендации новые после дедупликации

        return min(score, 1.0)

    # Сортируем по кумулятивному качеству
    ranked_recommendations = sorted(recommendations, key=cumulative_quality_score, reverse=True)

    print(f"🧠 Кумулятивное ранжирование: приоритизировано {len(ranked_recommendations)} рекомендаций")

    return ranked_recommendations[:30]  # Топ-30 самых ценных


def parse_ollama_recommendations(content: str, domain: str, posts: List[Dict]) -> List[Dict]:
    """Парсит рекомендации из ответа Ollama."""

    # Регулярные выражения для разных форматов
    patterns = [
        r"(?P<source>[^->]+) -> (?P<target>[^|]+) \| (?P<anchor>[^|]+) \| (?P<comment>.+)",
        r"(?P<source>[^->]+) -> (?P<target>[^|]+) \| (?P<anchor>[^|]+)",
        r"(?P<source>[^->]+) -> (?P<target>[^|]+)",
        r"(?P<source>[^->]+) -> (?P<target>[^|]+) \| (?P<anchor>[^|]+)",
        r"(?P<source>[^->]+) -> (?P<target>[^|]+) \| (?P<comment>.+)",
        r"(?P<source>[^->]+) -> (?P<target>[^|]+)",
    ]

    recommendations = []
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                source = match.group("source").strip()
                target = match.group("target").strip()
                anchor = match.group("anchor").strip() if match.group("anchor") else ""
                comment = match.group("comment").strip() if match.group("comment") else ""

                # Валидация URL
                if not target.startswith("http"):
                    target = f"https://{domain}/{target}"

                # Валидация анкора
                if not anchor:
                    anchor = target.split("/")[-1].replace("-", " ").replace("_", " ")
                    anchor = anchor.strip()
                    if not anchor:
                        anchor = source.split("/")[-1].replace("-", " ").replace("_", " ")
                        anchor = anchor.strip()

                # Проверка наличия в базе
                source_post = next((post for post in posts if post['link'] == source), None)
                target_post = next((post for post in posts if post['link'] == target), None)
                if not source_post or not target_post:
                    continue

                recommendations.append({
                    "from": source,
                    "to": target,
                    "anchor": anchor,
                    "comment": comment
                })
                break

    return recommendations


@app.on_event("startup")
async def on_startup() -> None:
    """Создает таблицы и инициализирует RAG-систему при запуске."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Инициализируем RAG-систему
    initialize_rag_system()
    
    # Инициализируем глобальные менеджеры
    initialize_global_managers()

    # Прогреваем модель Ollama в фоне (с задержкой для завершения загрузки контейнера)
    async def delayed_warmup():
        await asyncio.sleep(30)  # Ждем 30 секунд для стабилизации Ollama
        print("🚀 Начинаю отложенный прогрев Ollama...")
        success = await warmup_ollama()
        if success:
            print("🔥 Модель успешно прогрета и готова к работе!")
        else:
            print("⚠️ Прогрев не удался, но сервис продолжит работу")

    asyncio.create_task(delayed_warmup())


def initialize_global_managers():
    """Инициализирует глобальные менеджеры."""
    global cumulative_manager, rag_manager, thought_generator, websocket_manager
    
    websocket_manager = WebSocketManager()
    cumulative_manager = CumulativeIntelligenceManager()
    rag_manager = AdvancedRAGManager()
    thought_generator = IntelligentThoughtGenerator()
    
    print("✅ Все глобальные менеджеры инициализированы")


@app.get("/api/v1/ai_insights/semantic_network", response_model=List[dict])
async def get_semantic_network_insights(domain: str, client_id: Optional[str] = None) -> List[dict]:
    """Получает инсайты о семантической сети для домена."""
    print(f"🧠 Запрос инсайтов о семантической сети для домена {domain} (client: {client_id})")

    async with AsyncSessionLocal() as session:
        insights = await cumulative_manager.generate_semantic_network_insights(domain, session)

    print(f"💡 Получено {len(insights)} инсайтов о семантической сети")
    return insights


@app.get("/api/v1/ai_insights/enhanced_analytics", response_model=List[dict])
async def get_enhanced_analytics_insights(domain: str, client_id: Optional[str] = None) -> List[dict]:
    """Получает расширенные аналитические инсайты для домена."""
    print(f"📈 Запрос расширенных аналитических инсайтов для домена {domain} (client: {client_id})")

    async with AsyncSessionLocal() as session:
        insights = await cumulative_manager.generate_enhanced_analytics_insights(domain, session)

    print(f"📊 Получено {len(insights)} расширенных аналитических инсайтов")
    return insights


@app.get("/api/v1/models/available")
async def get_available_models():
    """Получает список доступных моделей Ollama."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Проверяем доступность Ollama
            try:
                response = await client.get("http://ollama:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("models", []):
                        models.append({
                            "name": model["name"],
                            "size": model.get("size", 0),
                            "digest": model.get("digest", ""),
                            "modified_at": model.get("modified_at", "")
                        })
                    
                    return {
                        "status": "success", 
                        "models": models,
                        "ollama_status": "connected",
                        "total_models": len(models)
                    }
                else:
                    return {
                        "status": "error", 
                        "models": [],
                        "ollama_status": "unavailable",
                        "error": f"Ollama returned status {response.status_code}"
                    }
            except httpx.ConnectError:
                # Если Ollama недоступен, возвращаем предполагаемые модели
                return {
                    "status": "partial", 
                    "models": [
                        {"name": "qwen2.5:7b-turbo", "size": 4300000000, "status": "expected"},
                        {"name": "qwen2.5:7b-instruct-turbo", "size": 4300000000, "status": "expected"},
                        {"name": "qwen2.5:7b", "size": 4300000000, "status": "expected"},
                        {"name": "qwen2.5:7b-instruct", "size": 4300000000, "status": "expected"}
                    ],
                    "ollama_status": "connecting",
                    "message": "Ollama подключается..."
                }
    except Exception as e:
        print(f"❌ Ошибка получения моделей: {e}")
        return {
            "status": "error", 
            "models": [],
            "ollama_status": "error",
            "error": str(e)
        }


@app.get("/api/v1/health")
async def health_check():
    """Проверка здоровья API."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/api/v1/domains")
async def get_domains():
    """Получает список доменов."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Domain).order_by(Domain.name))
        domains = result.scalars().all()
        
        domain_data = []
        for domain in domains:
            domain_data.append({
                "id": domain.id,
                "name": domain.name,
                "display_name": domain.display_name,
                "total_posts": domain.total_posts,
                "total_analyses": domain.total_analyses,
                "last_analysis_at": domain.last_analysis_at.isoformat() if domain.last_analysis_at else None,
                "is_indexed": domain.total_posts > 0,
                "created_at": domain.created_at.isoformat(),
                "language": domain.language
            })
        
        return {"domains": domain_data}


@app.get("/api/v1/analysis_history")
async def get_analysis_history(domain: Optional[str] = None, limit: int = 50):
    """Получает историю анализов."""
    async with AsyncSessionLocal() as session:
        query = select(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()).limit(limit)
        
        if domain:
            domain_result = await session.execute(select(Domain).where(Domain.name == domain))
            domain_obj = domain_result.scalar_one_or_none()
            if domain_obj:
                query = query.where(AnalysisHistory.domain_id == domain_obj.id)
        
        result = await session.execute(query)
        analyses = result.scalars().all()
        
        history_data = []
        for analysis in analyses:
            history_data.append({
                "id": analysis.id,
                "domain_id": analysis.domain_id,
                "posts_analyzed": analysis.posts_analyzed,
                "connections_found": analysis.connections_found,
                "recommendations_generated": analysis.recommendations_generated,
                "llm_model_used": analysis.llm_model_used,
                "processing_time_seconds": analysis.processing_time_seconds,
                "created_at": analysis.created_at.isoformat(),
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
            })
        
        return {"history": history_data}


@app.get("/api/v1/benchmark_history")
async def get_benchmark_history(limit: int = 20):
    """Получает историю бенчмарков."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BenchmarkRun)
            .order_by(BenchmarkRun.created_at.desc())
            .limit(limit)
        )
        benchmarks = result.scalars().all()
        
        benchmark_data = []
        for benchmark in benchmarks:
            benchmark_data.append({
                "id": benchmark.id,
                "name": benchmark.name,
                "benchmark_type": benchmark.benchmark_type,
                "status": benchmark.status,
                "overall_score": benchmark.overall_score,
                "quality_score": benchmark.quality_score,
                "performance_score": benchmark.performance_score,
                "duration_seconds": benchmark.duration_seconds,
                "created_at": benchmark.created_at.isoformat(),
                "completed_at": benchmark.completed_at.isoformat() if benchmark.completed_at else None
            })
        
        return {"benchmarks": benchmark_data}


async def warmup_ollama():
    """Прогревает модель Ollama в фоне."""
    try:
        async with OLLAMA_SEMAPHORE:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Простой запрос для прогрева
                response = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": "Система готова?",
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_ctx": 1024,
                            "num_predict": 50
                        }
                    },
                    timeout=60
                )
                if response.status_code == 200:
                    print(f"🔥 Ollama модель {OLLAMA_MODEL} успешно прогрета")
                    return True
                else:
                    print(f"⚠️ Ошибка прогрева: статус {response.status_code}")
                    return False
    except Exception as e:
        print(f"⚠️ Ошибка прогрева Ollama: {e}")
        return False


# Эндпоинты для WordPress анализа
@app.post("/api/v1/wp_index")
async def wp_index_endpoint(request: WPRequest) -> dict:
    """Индексация и генерация рекомендаций для WordPress сайта."""
    try:
        # Fetch and store WordPress posts
        posts, delta_stats = await fetch_and_store_wp_posts(request.domain, request.client_id)
        
        # Генерируем рекомендации
        if request.comprehensive:
            recommendations, analysis_time = await generate_comprehensive_domain_recommendations(
                request.domain, request.client_id
            )
        else:
            # Простая генерация рекомендаций
            recommendations = []
            analysis_time = 0.0

        return {
            "status": "success",
            "domain": request.domain,
            "posts_found": len(posts),
            "recommendations": recommendations,
            "delta_stats": delta_stats,
            "analysis_time": analysis_time
        }

    except Exception as e:
        error_msg = f"❌ Ошибка индексации {request.domain}: {e}"
        print(error_msg)
        return {
            "status": "error",
            "error": str(e),
            "domain": request.domain
        }


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket для отслеживания прогресса анализа."""
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            # Ждем сообщения от клиента или поддерживаем соединение
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Отправляем ping для поддержания соединения
                await websocket.send_json({"type": "ping", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
    except Exception as e:
        print(f"❌ WebSocket ошибка {client_id}: {e}")
        websocket_manager.disconnect(client_id)


# Эндпоинты данных
@app.get("/api/v1/domains/{domain}/posts")
async def get_domain_posts(domain: str, limit: int = 50):
    """Получает посты для домена."""
    async with AsyncSessionLocal() as session:
        domain_result = await session.execute(select(Domain).where(Domain.name == domain))
        domain_obj = domain_result.scalar_one_or_none()
        
        if not domain_obj:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        result = await session.execute(
            select(WordPressPost)
            .where(WordPressPost.domain_id == domain_obj.id)
            .order_by(WordPressPost.created_at.desc())
            .limit(limit)
        )
        posts = result.scalars().all()
        
        posts_data = []
        for post in posts:
            posts_data.append({
                "id": post.id,
                "title": post.title,
                "link": post.link,
                "content_type": post.content_type,
                "difficulty_level": post.difficulty_level,
                "linkability_score": post.linkability_score,
                "semantic_richness": post.semantic_richness,
                "created_at": post.created_at.isoformat(),
                "key_concepts": post.key_concepts[:5] if post.key_concepts else []
            })
        
        return {"posts": posts_data, "total": len(posts_data)}


@app.get("/api/v1/ollama_status")
async def get_ollama_status():
    """Проверяет статус подключения к Ollama."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://ollama:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "status": "ready",
                    "connection": "connected",
                    "models_count": len(models),
                    "available_models": [model["name"] for model in models[:5]],  # Первые 5 моделей
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "connection": "failed",
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
    except httpx.ConnectError:
        return {
            "status": "connecting",
            "connection": "connecting",
            "message": "Ollama подключается...",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "connection": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

