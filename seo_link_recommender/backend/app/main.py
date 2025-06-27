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

# Глобальные менеджеры
websocket_manager = WebSocketManager()
thought_generator = IntelligentThoughtGenerator()
rag_manager = AdvancedRAGManager()
cumulative_manager = CumulativeIntelligenceManager()

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


# Глобальные менеджеры
rag_manager = AdvancedRAGManager()
cumulative_intelligence = CumulativeIntelligenceManager()
thought_generator = IntelligentThoughtGenerator()


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
            existing_analysis = await cumulative_intelligence.analyze_existing_connections(domain, session)
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
            clusters = await cumulative_intelligence.discover_thematic_clusters(
                domain_obj.id, full_dataset, session
            )
            print(f"🎯 Обнаружено {len(clusters)} тематических кластеров")

            existing_analysis['clusters'] = clusters
            existing_analysis['total_posts'] = len(all_posts)

        # Шаг 3: Генерация кумулятивных инсайтов
        if client_id:
            await websocket_manager.send_step(client_id, "Генерация инсайтов", 3, 12, "Анализ возможностей улучшения...")

        async with AsyncSessionLocal() as session:
            insights = await cumulative_intelligence.generate_cumulative_insights(
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
            evolved_recommendations = await cumulative_intelligence.deduplicate_and_evolve_recommendations(
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


def deduplicate_and_rank_recommendations(recommendations: List[Dict], domain: str) -> List[Dict]:
    """Дедуплицирует и ранжирует финальные рекомендации (устаревшая функция)."""

    # Дедупликация по паре источник->цель
    seen_pairs = set()
    unique_recommendations = []

    for rec in recommendations:
        pair_key = (rec['from'], rec['to'])
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_recommendations.append(rec)

    # Ранжирование по качеству анкора и обоснования
    def quality_score(rec):
        anchor_score = len(rec['anchor']) * 0.1  # Длина анкора
        comment_score = len(rec['comment']) * 0.05  # Длина обоснования

        # Бонусы за качественные слова в анкоре
        quality_words = ['подробный', 'полный', 'детальный', 'руководство', 'инструкция', 'обзор', 'гайд']
        anchor_quality = sum(1 for word in quality_words if word in rec['anchor'].lower()) * 2

        return anchor_score + comment_score + anchor_quality

    # Сортируем по качеству
    ranked_recommendations = sorted(unique_recommendations, key=quality_score, reverse=True)

    print(f"🎯 Дедупликация: {len(recommendations)} -> {len(unique_recommendations)} уникальных рекомендаций")

    return ranked_recommendations[:50]  # Топ-50 самых качественных


async def generate_rag_recommendations(domain: str, client_id: Optional[str] = None) -> list[dict[str, str]]:
    """Генерирует рекомендации используя RAG-подход с векторной БД."""
    print(f"🚀 Запуск RAG-анализа для домена {domain} (client: {client_id})")

    # Инициализируем время анализа
    analysis_start_time = datetime.now()
    request_time = 0.0

    try:
        # Шаг 1: Загрузка статей из БД
        if client_id:
            await websocket_manager.send_step(client_id, "Загрузка статей", 1, 7, "Получение статей из базы данных...")

        async with AsyncSessionLocal() as session:
            # Получаем домен
            domain_result = await session.execute(
                select(Domain).where(Domain.name == domain)
            )
            domain_obj = domain_result.scalar_one_or_none()

            if not domain_obj:
                error_msg = f"❌ Домен {domain} не найден в БД"
                print(error_msg)
                if client_id:
                    await websocket_manager.send_error(client_id, error_msg)
                return [], 0.0

            # Получаем посты с семантической информацией
            result = await session.execute(
                select(WordPressPost)
                .where(WordPressPost.domain_id == domain_obj.id)
                .order_by(WordPressPost.linkability_score.desc(), WordPressPost.published_at.desc())
                .limit(100)  # Ограничиваем для производительности
            )
            db_posts = result.scalars().all()

        if not db_posts:
            error_msg = "❌ Нет статей для RAG-анализа"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg, f"Не найдено статей для домена {domain}")
            return [], 0.0

        print(f"📊 Загружено {len(db_posts)} статей из БД")

        # Преобразуем в формат для RAG
        posts_data = []
        for post in db_posts:
            posts_data.append({
                "title": post.title,
                "link": post.link,
                "content": post.content[:1000]  # Первые 1000 символов
            })

        # Шаг 2: Создание векторной базы
        if client_id:
            await websocket_manager.send_step(client_id, "Создание векторной базы", 2, 7, "Обработка статей для векторного поиска...")

        success = await rag_manager.create_semantic_knowledge_base(domain, posts_data, client_id)
        if not success:
            error_msg = "❌ Не удалось создать семантическую базу знаний"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg, "Ошибка создания семантических векторов")
            return [], 0.0

        # Шаг 3: Получение обзора статей
        if client_id:
            await websocket_manager.send_step(client_id, "Анализ контента", 3, 7, "Выбор наиболее релевантных статей...")

        articles = await rag_manager.get_semantic_recommendations(domain, limit=12)  # Увеличиваем для более полного анализа
        if not articles:
            error_msg = "❌ Не найдены статьи в базе знаний"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg, "Пустая семантическая база знаний")
            return [], 0.0

        print(f"📋 Выбрано {len(articles)} статей для анализа")

        # Шаг 4: Подготовка улучшенного промпта
        if client_id:
            await websocket_manager.send_step(client_id, "Подготовка ИИ", 4, 7, "Создание контекста для Ollama...")

        # Создаем более качественный и полный промпт с семантическими данными
        articles_context = ""
        for i, article in enumerate(articles, 1):
            title = article['title']
            content_snippet = article['content'][:300] if article.get('content') else ""
            key_concepts = article.get('key_concepts', [])[:8]  # Больше концепций
            content_type = article.get('content_type', 'статья')
            linkability = article.get('linkability_score', 0.5)
            semantic_summary = article.get('semantic_summary', '').strip()
            difficulty_level = article.get('difficulty_level', 'средний')
            target_audience = article.get('target_audience', 'общая аудитория')

            articles_context += f"""📄 СТАТЬЯ {i}: «{title}»
🔗 URL: {article['link']}
📊 МЕТРИКИ: Тип контента: {content_type} | Сложность: {difficulty_level} | Потенциал линковки: {linkability:.2f}
👥 АУДИТОРИЯ: {target_audience}
🧠 КЛЮЧЕВЫЕ КОНЦЕПЦИИ: {', '.join(key_concepts) if key_concepts else 'не определены'}
📝 СЕМАНТИЧЕСКОЕ ОПИСАНИЕ: {semantic_summary if semantic_summary else 'автоматически извлекается из контента'}
💡 СОДЕРЖАНИЕ: {content_snippet}...

"""

        # Интеллектуальный промпт с использованием семантических данных и примерами
        qwen_optimized_prompt = f"""🎯 ЗАДАЧА: Глубокий семантический анализ для создания внутренних ссылок на сайте {domain}

🏗️ КОНТЕКСТ АНАЛИЗА:
Анализируется {len(articles)} статей сайта {domain}. У каждой статьи есть семантические метрики, ключевые концепции, тип контента и целевая аудитория.

📚 СТАТЬИ ДЛЯ АНАЛИЗА:
{articles_context}

🎯 ЦЕЛЬ: Создать МАКСИМАЛЬНОЕ количество осмысленных внутренних ссылок между статьями на основе:
✅ Семантической близости концепций
✅ Логической последовательности для читателя
✅ Дополнения информации между статьями
✅ SEO-ценности для сайта

🧠 ПРИНЦИПЫ КАЧЕСТВЕННОЙ РЕКОМЕНДАЦИИ:

1️⃣ СЕМАНТИЧЕСКАЯ СВЯЗЬ: Статьи должны дополнять друг друга по смыслу
2️⃣ ЕСТЕСТВЕННОСТЬ: Анкор должен органично вписываться в контекст исходной статьи
3️⃣ ЦЕННОСТЬ: Переход должен быть полезным для читателя
4️⃣ СПЕЦИФИЧНОСТЬ: Анкор должен точно описывать содержание целевой страницы

📝 ПРАВИЛА ДЛЯ АНКОРОВ:
❌ ПЛОХО: "подробное руководство", "перейти сюда", "читать далее", "официальный сайт"
✅ ХОРОШО: "особенности климата и стоимости жизни в Волгограде", "полный разбор переезда в Красноярск с ценами на жилье", "детальный гид по достопримечательностям Казани"

🎯 ПРИМЕРЫ КАЧЕСТВЕННЫХ РЕКОМЕНДАЦИЙ:

ИСТОЧНИК: Переезд в Уфу → ЦЕЛЬ: Переезд в Казань
АНКОР: "сравнение переезда в столицу Татарстана с особенностями культурного разнообразия"
ОБОСНОВАНИЕ: Обе статьи про переезд в республиканские столицы, читатель может сравнить варианты

ИСТОЧНИК: Достопримечательности Сочи → ЦЕЛЬ: Переезд в Сочи
АНКОР: "полная информация о переезде в город с учетом климата и стоимости жизни"
ОБОСНОВАНИЕ: Туристическая статья естественно ведет к практической информации о жизни в городе

🔍 ИНСТРУКЦИЯ:
Проанализируй КАЖДУЮ статью и найди ВСЕ логичные связи с другими статьями. Создай минимум 8 - 12 рекомендаций, максимум определи сам исходя из семантических связей.

📋 ФОРМАТ ОТВЕТА:
[НОМЕР] ИСТОЧНИК: [URL источника] → ЦЕЛЬ: [URL цели]
АНКОР: "[специфичный анкор, описывающий содержание целевой страницы]"
ОБОСНОВАНИЕ: [почему эта связь логична и полезна для читателя]

🚀 НАЧИНАЙ АНАЛИЗ:"""

        # Шаг 5: Запрос к Ollama
        if client_id:
            await websocket_manager.send_step(client_id, "Запрос к Ollama", 5, 7, "Отправка улучшенного контекста в ИИ...")
            await websocket_manager.send_ollama_info(client_id, {
                "status": "starting",
                "model": OLLAMA_MODEL,
                "model_info": "qwen2.5:7b-optimized - расширенный контекст 8192 токена",
                "articles_count": len(articles),
                "prompt_length": len(qwen_optimized_prompt),
                "timeout": 300,
                "settings": "temperature=0.4, ctx=8192, predict=1200, threads=6",
                "expected_recommendations": "8 - 15 качественных рекомендаций"
            })

        print("🤖 Отправляю улучшенный семантический запрос...")
        print(f"📝 Размер промпта: {len(qwen_optimized_prompt)} символов")

        # Отправляем "мысли" перед началом анализа
        if client_id:
            await websocket_manager.send_ai_thinking(
                client_id,
                "Изучаю структуру статей и ищу скрытые семантические связи между темами...",
                "preprocessing",
                "🔍"
            )

        # Оптимизированные настройки для качественной генерации
        start_time = datetime.now()
        async with httpx.AsyncClient(timeout=600.0) as client:
            # Добавляем "мысли" во время обработки
            if client_id:
                await websocket_manager.send_ai_thinking(
                    client_id,
                    "Анализирую контекст каждой статьи и определяю её роль в общей структуре сайта...",
                    "analyzing",
                    "🧠"
                )

            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": qwen_optimized_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,      # Баланс между креативностью и точностью
                        "num_ctx": 8192,         # Увеличиваем контекст для полного анализа
                        "num_predict": 1200,     # Больше токенов для детальных рекомендаций
                        "top_p": 0.85,          # Оптимизируем для качества
                        "top_k": 50,            # Расширяем выбор токенов
                        "repeat_penalty": 1.08,  # Снижаем повторения
                        "seed": 42,             # Фиксированное зерно
                        "stop": ["🚀 НАЧИНАЙ", "КОНЕЦ АНАЛИЗА", "```", "---"],
                        "num_thread": 6
                    }
                },
                timeout=600
            )

        request_time = (datetime.now() - start_time).total_seconds()

        if client_id:
            await websocket_manager.send_ollama_info(client_id, {
                "status": "completed",
                "response_code": response.status_code,
                "request_time": f"{request_time:.1f}s",
                "response_length": len(response.text) if response.status_code == 200 else 0
            })

        if response.status_code != 200:
            error_msg = f"❌ Ollama вернула код {response.status_code}"
            print(f"{error_msg}. Ответ: {response.text[:200]}...")

            # Если 499 - клиент отменил запрос (таймаут)
            if response.status_code == 499:
                error_msg = "❌ Таймаут загрузки модели Ollama. Модель загружается впервые и требует времени."
                detailed_msg = f"Попробуйте еще раз через 2 - 3 минуты. Модель {OLLAMA_MODEL} должна остаться в памяти после первой загрузки."
            else:
                detailed_msg = f"HTTP статус: {response.status_code}. Ответ: {response.text[:100]}..."

            if client_id:
                await websocket_manager.send_error(client_id, error_msg, detailed_msg)
            return [], 0.0

        data = response.json()
        content = data.get("response", "")
        print(f"📝 Получен ответ от Ollama: {len(content)} символов за {request_time:.1f}с")

        # Добавляем детальное логирование для отладки
        print("🔍 ОТЛАДКА: Ответ Ollama:")
        print("="*50)
        print(content)
        print("="*50)

        # Отправляем ответ Ollama через WebSocket для отображения в UI
        if client_id:
            # Берем первые 500 символов ответа для preview
            preview_text = content[:500] + "..." if len(content) > 500 else content
            await websocket_manager.send_ollama_info(client_id, {
                "status": "response_preview",
                "preview": preview_text,
                "total_length": len(content),
                "model": OLLAMA_MODEL
            })

            # Отправляем "мысли" о том, что обдумываем ответ
            await websocket_manager.send_ai_thinking(
                client_id,
                f"Получил развернутый ответ в {len(content)} символов. Анализирую и ищу лучшие рекомендации...",
                "processing",
                "💭"
            )

        # Шаг 6: Обработка результатов
        if client_id:
            await websocket_manager.send_step(client_id, "Обработка ответа", 6, 7, "Парсинг рекомендаций от ИИ...")

        recommendations = parse_ollama_recommendations(content, domain, articles)

        print(f"📊 ОТЛАДКА: Парсер нашел {len(recommendations)} рекомендаций из {len(articles)} статей")

        # Шаг 7: Финализация
        if client_id:
            await websocket_manager.send_step(client_id, "Завершение", 7, 7, f"Готово! Получено {len(recommendations)} рекомендаций")

        # Вычисляем общее время анализа
        total_analysis_time = (datetime.now() - analysis_start_time).total_seconds()
        print(f"✅ RAG-анализ завершен: {len(recommendations)} рекомендаций за {total_analysis_time:.1f}с")

        # Возвращаем рекомендации и время для дальнейшего использования
        return recommendations[:25], total_analysis_time  # Увеличиваем до 25 для большего покрытия

    except Exception as e:
        error_msg = f"❌ Ошибка RAG-анализа: {e}"
        print(error_msg)
        if client_id:
            await websocket_manager.send_error(client_id, "Критическая ошибка анализа", str(e))

        # Возвращаем пустой список и время анализа до ошибки
        error_time = (datetime.now() - analysis_start_time).total_seconds()
        return [], error_time


def parse_ollama_recommendations(text: str, domain: str, articles: List[Dict]) -> List[Dict]:
    """Парсит рекомендации из ответа Ollama с проверкой домена - улучшенная версия с регулярными выражениями."""
    recommendations = []

    # Создаем множество валидных URL для домена
    valid_urls = set()
    articles_dict = {}  # Для быстрого поиска по URL
    for article in articles:
        url = article['link']
        if domain.lower() in url.lower():
            valid_urls.add(url)
            articles_dict[url] = article

    print(f"🔍 ОТЛАДКА: Валидные URL для домена {domain}: {len(valid_urls)}")

    # Улучшенные регулярные выражения для парсинга
    enhanced_patterns = [
        # Основной формат: ИСТОЧНИК -> ЦЕЛЬ | анкор | обоснование  
        r'(?P<source>.+?)\s*->\s*(?P<target>.+?)\s*\|\s*(?P<anchor>.+?)\s*\|\s*(?P<reasoning>.+?)(?=\n|$)',
        
        # Формат с двойными звездочками: **Источник:** URL **Цель:** URL | анкор | комментарий
        r'\*\*Источник:\*\*\s*(?P<source>.+?)\s*\*\*Цель:\*\*\s*(?P<target>.+?)\s*\|\s*(?P<anchor>.+?)\s*\|\s*(?P<reasoning>.+?)(?=\n|$)',
        
        # Альтернативный формат со стрелкой
        r'(?P<source>.+?)\s*→\s*(?P<target>.+?)\s*[\|\-]\s*(?P<anchor>.+?)\s*[\|\-]\s*(?P<reasoning>.+?)(?=\n|$)',
        
        # Нумерованный формат
        r'\d+\.\s*(?P<source>.+?)\s*->\s*(?P<target>.+?)\s*\|\s*(?P<anchor>.+?)\s*\|\s*(?P<reasoning>.+?)(?=\n|$)',
    ]
    
    # Функция для извлечения URL из скобок или текста
    def extract_url(text: str) -> str:
        """Извлекает URL из текста, удаляя скобки и лишние символы."""
        if not text:
            return ""
        
        # Проверяем наличие URL в скобках
        url_in_brackets = re.search(r'\(([^)]+)\)', text)
        if url_in_brackets:
            url = url_in_brackets.group(1).strip()
            if url.startswith('http'):
                return url
        
        # Ищем URL в тексте
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s.,;:!?<>"{}|\\^`\[\]]'
        url_match = re.search(url_pattern, text)
        if url_match:
            return url_match.group(0)
            
        return text.strip()
    
    # Проверяем качество анкора с помощью регулярных выражений
    def is_quality_anchor(anchor: str) -> bool:
        """Проверяет качество анкора для внутренних ссылок."""
        if not anchor or len(anchor) < 3:
            return False
            
        anchor_lower = anchor.lower()
        
        # Плохие паттерны для внутренних ссылок
        bad_patterns = [
            r'\b(?:сайт|ресурс|портал|веб-сайт|интернет-ресурс)\b',
            r'\b(?:официальный сайт|перейти на сайт|главная страница)\b',
            r'\b(?:домен|ссылка|url)\b'
        ]
        
        for pattern in bad_patterns:
            if re.search(pattern, anchor_lower):
                return False
        
        # Хорошие паттерны
        good_patterns = [
            r'\b(?:подробн\w+|полн\w+|детальн\w+|глубок\w+|расширенн\w+)\b',
            r'\b(?:руководств\w+|гайд\w+|инструкци\w+|мануал\w+)\b',
            r'\b(?:обзор\w+|сравнени\w+|анализ\w+|исследовани\w+)\b',
            r'\b(?:совет\w+|рекомендаци\w+|секрет\w+|лайфхак\w+)\b'
        ]
        
        for pattern in good_patterns:
            if re.search(pattern, anchor_lower):
                return True
                
        # Если нет явных плохих паттернов и длина достаточная, считаем приемлемым
        return len(anchor) >= 10 and not any(word in anchor_lower for word in ['сайт', 'ресурс', 'портал'])

    lines = text.splitlines()
    print(f"🔍 ОТЛАДКА: Обрабатываю {len(lines)} строк ответа с улучшенными регулярными выражениями")

    # Сначала пробуем улучшенные регулярные выражения
    for i, pattern in enumerate(enhanced_patterns, 1):
        matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            print(f"🔍 Найдено совпадение с паттерном {i}: {match.group()[:100]}...")
            
            try:
                source_raw = match.group('source').strip() if 'source' in match.groupdict() else ""
                target_raw = match.group('target').strip() if 'target' in match.groupdict() else ""
                anchor = match.group('anchor').strip().strip('"') if 'anchor' in match.groupdict() else ""
                reasoning = match.group('reasoning').strip() if 'reasoning' in match.groupdict() else ""
                
                # Извлекаем чистые URL
                source = extract_url(source_raw)
                target = extract_url(target_raw)
                
                print(f"   🎯 Источник: {source[:60]}...")
                print(f"   🎯 Цель: {target[:60]}...")
                print(f"   🎯 Анкор: {anchor}")
                print(f"   🎯 Обоснование: {reasoning[:50]}...")
                
                # Проверка качества данных
                if not source or not target or not anchor:
                    print(f"   ❌ Неполные данные")
                    continue
                
                if not is_quality_anchor(anchor):
                    print(f"   ❌ Некачественный анкор: {anchor}")
                    continue
                
                if len(reasoning) < 10:
                    print(f"   ❌ Слишком короткое обоснование: {len(reasoning)} символов")
                    continue
                
                # Проверяем валидность URL
                source_valid = domain.lower() in source.lower() and source != target
                target_valid = domain.lower() in target.lower()
                
                print(f"   ✔️ Источник валиден: {source_valid}")
                print(f"   ✔️ Цель валидна: {target_valid}")
                
                if source_valid and target_valid:
                    # Проверяем, что нет дублей
                    is_duplicate = any(
                        rec["from"] == source and rec["to"] == target 
                        for rec in recommendations
                    )
                    
                    if not is_duplicate:
                        recommendations.append({
                            "from": source,
                            "to": target,
                            "anchor": anchor,
                            "comment": reasoning
                        })
                        print(f"   ✅ ПРИНЯТА рекомендация #{len(recommendations)} (regex)")
                    else:
                        print(f"   ⚠️ Дубликат, пропускаем")
                else:
                    print(f"   ❌ Отклонена: невалидные URL или домен")
                    
            except Exception as e:
                print(f"   ❌ Ошибка обработки regex match: {e}")
                continue

    # Если regex не нашел достаточно результатов, используем старый метод как fallback
    if len(recommendations) < 3:
        print(f"🔄 Regex нашел только {len(recommendations)} рекомендаций, используем fallback парсинг")
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            print(f"   Строка {i}: {line[:100]}...")

            # Поддерживаем разные форматы ответов от Ollama (старый метод)
            if ('**Источник:**' in line and '**Цель:**' in line) or ('->' in line and '|' in line):
                print(f"      ✓ Найден паттерн рекомендации в строке {i}")
                try:
                    source = ""
                    target = ""
                    anchor = ""
                    comment = ""

                    # Формат 1: **Источник:** URL **Цель:** URL | анкор | комментарий
                    if '**Источник:**' in line and '**Цель:**' in line:
                        # Извлекаем источник
                        source_match = line.split('**Источник:**')[1].split('**Цель:**')[0].strip()
                        source = extract_url(source_match)

                        # Извлекаем цель и анкор
                        target_part = line.split('**Цель:**')[1]
                        if '|' in target_part:
                            target_and_anchor = target_part.split('|')
                            target_raw = target_and_anchor[0].strip()
                            target = extract_url(target_raw)

                            # Анкор и комментарий
                            if len(target_and_anchor) >= 2:
                                anchor = target_and_anchor[1].strip().strip('"')
                            if len(target_and_anchor) >= 3:
                                comment = target_and_anchor[2].strip()

                    # Формат 2: URL -> URL | анкор | комментарий (старый формат)
                    elif '->' in line and '|' in line:
                        parts = line.split('|', 2)
                        if len(parts) >= 3:
                            link_part = parts[0].strip()
                            anchor = parts[1].strip().strip('"')
                            comment = parts[2].strip()

                            if '->' in link_part:
                                source_target = link_part.split('->', 1)
                                if len(source_target) == 2:
                                    source = extract_url(source_target[0].strip())
                                    target = extract_url(source_target[1].strip())

                    # Проверки качества
                    if not source or not target or not anchor:
                        print(f"      ❌ Неполные данные")
                        continue

                    if not is_quality_anchor(anchor):
                        print(f"      ❌ Некачественный анкор: {anchor}")
                        continue

                    # Проверяем валидность URL
                    source_valid = domain.lower() in source.lower() and source != target
                    target_valid = domain.lower() in target.lower()

                    if source_valid and target_valid:
                        # Проверяем дубли
                        is_duplicate = any(
                            rec["from"] == source and rec["to"] == target 
                            for rec in recommendations
                        )
                        
                        if not is_duplicate:
                            recommendations.append({
                                "from": source,
                                "to": target,
                                "anchor": anchor,
                                "comment": comment
                            })
                            print(f"      ✅ ПРИНЯТА рекомендация #{len(recommendations)} (fallback)")

                except Exception as e:
                    print(f"      ❌ Ошибка парсинга строки {i}: {e}")
                    continue

    print(f"📊 ФИНАЛ: Найдено {len(recommendations)} валидных рекомендаций (regex + fallback)")
    return recommendations


async def warmup_ollama() -> bool:
    """Прогрев модели Ollama для предотвращения таймаутов с повторными попытками."""
    print("🔥 Прогрев модели Ollama с повторными попытками...")

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"🔄 Попытка прогрева {attempt}/{max_attempts}")

            # Увеличиваем таймаут с каждой попыткой
            timeout_seconds = 180 + (attempt * 60)  # 180s, 240s, 300s

            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": "Тест",
                        "stream": False,
                        "options": {
                            "num_predict": 5,  # Минимальный ответ
                            "temperature": 0.1,
                            "num_ctx": 1024    # Маленький контекст для быстроты
                        }
                    },
                    timeout=timeout_seconds
                )

                if response.status_code == 200:
                    print(f"✅ Модель {OLLAMA_MODEL} успешно прогрета за попытку {attempt}")
                    return True
                else:
                    print(f"⚠️ Попытка {attempt}: статус {response.status_code}")
                    if attempt < max_attempts:
                        print(f"🔄 Ожидание 10 секунд перед следующей попыткой...")
                        await asyncio.sleep(10)

        except httpx.TimeoutException:
            print(f"⏰ Попытка {attempt}: таймаут {timeout_seconds}s")
            if attempt < max_attempts:
                print(f"🔄 Ожидание 15 секунд перед следующей попыткой...")
                await asyncio.sleep(15)
        except Exception as e:
            print(f"❌ Попытка {attempt}: ошибка {e}")
            if attempt < max_attempts:
                print(f"🔄 Ожидание 10 секунд перед следующей попыткой...")
                await asyncio.sleep(10)

    print(f"❌ Не удалось прогреть модель за {max_attempts} попыток")
    return False


@app.on_event("startup")
async def on_startup() -> None:
    """Создает таблицы и инициализирует RAG-систему при запуске."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Инициализируем RAG-систему
    initialize_rag_system()

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


# Тестовый эндпоинт удален для продакшена


@app.post("/api/v1/recommend")
async def recommend(req: RecommendRequest) -> dict[str, list[str]]:
    """Возвращает простые рекомендации ссылок."""
    links = await generate_links(req.text)

    async with AsyncSessionLocal() as session:
        rec = Recommendation(text=req.text, links=links)
        session.add(rec)
        await session.commit()
    return {"links": links}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket эндпоинт для отслеживания прогресса."""
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            # Ожидаем сообщения от клиента (поддержание соединения)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)


@app.post("/api/v1/wp_index")
async def wp_index_domain(req: WPRequest) -> dict[str, object]:
    """Умная индексация домена с отслеживанием изменений."""
    try:
        if req.client_id:
            await websocket_manager.send_step(
                req.client_id,
                "Начало индексации",
                0,
                5,
                f"Умная индексация домена {req.domain}"
            )

        # Выполняем умную индексацию
        posts, delta_stats = await fetch_and_store_wp_posts(req.domain, req.client_id)

        # Создаем семантическую базу знаний
        success = await rag_manager.create_semantic_knowledge_base(req.domain, posts, req.client_id)

        if req.client_id:
            await websocket_manager.send_progress(req.client_id, {
                "type": "complete",
                "message": "Индексация завершена успешно!",
                "delta_stats": delta_stats,
                "posts_count": len(posts),
                "indexed": success,
                "timestamp": datetime.now().isoformat()
            })

        return {
            "success": True,
            "domain": req.domain,
            "posts_count": len(posts),
            "delta_stats": delta_stats,
            "indexed": success
        }

    except Exception as e:
        error_msg = f"Ошибка индексации: {str(e)}"
        print(f"❌ {error_msg}")

        if req.client_id:
            await websocket_manager.send_error(req.client_id, "Критическая ошибка индексации", error_msg)

        raise HTTPException(status_code=500, detail=error_msg)


# Устаревший эндпоинт wp_generate_recommendations удален


# Устаревший эндпоинт wp_stable удален


# Устаревший эндпоинт wp_comprehensive удален


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Проверка работоспособности."""
    return {"status": "ok"}


@app.get("/api/v1/ollama_status")
async def ollama_status() -> dict[str, object]:
    """Проверка статуса подключения к Ollama и загруженных моделей."""
    try:
        print(f"🔍 Проверка статуса Ollama: {OLLAMA_URL}")

        status_info = {
            "ollama_url": OLLAMA_URL,
            "model_name": OLLAMA_MODEL,
            "server_available": False,
            "model_loaded": False,
            "model_info": None,
            "error": None,
            "ready_for_work": False,
            "last_check": datetime.now().isoformat()
        }

        # Проверяем доступность сервера Ollama
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Проверяем общий статус сервера
                health_response = await client.get(f"{OLLAMA_URL.replace('/api/generate', '')}/api/tags")

                if health_response.status_code == 200:
                    status_info["server_available"] = True
                    models_data = health_response.json()
                    available_models = [model["name"] for model in models_data.get("models", [])]
                    status_info["available_models"] = available_models

                    print(f"✅ Ollama сервер доступен. Доступные модели: {available_models}")

                    # Проверяем, загружена ли нужная модель
                    if OLLAMA_MODEL in available_models:
                        status_info["model_loaded"] = True

                        # Получаем детальную информацию о модели
                        try:
                            model_info_response = await client.post(
                                f"{OLLAMA_URL.replace('/api/generate', '')}/api/show",
                                json={"name": OLLAMA_MODEL}
                            )
                            if model_info_response.status_code == 200:
                                model_details = model_info_response.json()
                                status_info["model_info"] = {
                                    "name": model_details.get("modelfile", "").split("\n")[0] if model_details.get("modelfile") else OLLAMA_MODEL,
                                    "size": model_details.get("size", "неизвестно"),
                                    "modified_at": model_details.get("modified_at", ""),
                                    "parameters": model_details.get("parameters", {}),
                                    "template": model_details.get("template", "")[:100] + "..." if model_details.get("template") else ""
                                }
                        except Exception as model_info_error:
                            print(f"⚠️ Не удалось получить детали модели: {model_info_error}")
                            status_info["model_info"] = {"error": str(model_info_error)}

                        # Проверяем работоспособность модели простым запросом
                        try:
                            test_response = await client.post(
                                OLLAMA_URL,
                                json={
                                    "model": OLLAMA_MODEL,
                                    "prompt": "Тест",
                                    "stream": False,
                                    "options": {"num_predict": 1}
                                },
                                timeout=15.0
                            )

                            if test_response.status_code == 200:
                                status_info["ready_for_work"] = True
                                test_data = test_response.json()
                                status_info["test_response_time"] = test_data.get("total_duration", 0) / 1000000  # наносекунды в миллисекунды
                                print(f"✅ Модель {OLLAMA_MODEL} работает корректно")
                            else:
                                status_info["error"] = f"Тестовый запрос к модели вернул код {test_response.status_code}"
                                print(f"❌ Тестовый запрос неуспешен: {test_response.status_code}")

                        except Exception as test_error:
                            status_info["error"] = f"Ошибка тестирования модели: {str(test_error)}"
                            print(f"❌ Ошибка тестирования модели: {test_error}")
                    else:
                        status_info["error"] = f"Модель {OLLAMA_MODEL} не найдена среди доступных: {available_models}"
                        print(f"❌ Модель {OLLAMA_MODEL} не загружена")

                        # Предлагаем команду для загрузки модели
                        status_info["suggested_command"] = f"ollama pull {OLLAMA_MODEL}"

                else:
                    status_info["error"] = f"Ollama сервер недоступен (код {health_response.status_code})"
                    print(f"❌ Ollama сервер недоступен: {health_response.status_code}")

            except httpx.TimeoutException:
                status_info["error"] = "Таймаут подключения к Ollama серверу"
                print("❌ Таймаут подключения к Ollama")
            except httpx.ConnectError:
                status_info["error"] = "Не удается подключиться к Ollama серверу. Проверьте, что контейнер ollama запущен"
                print("❌ Ошибка подключения к Ollama")
            except Exception as connection_error:
                status_info["error"] = f"Ошибка подключения к Ollama: {str(connection_error)}"
                print(f"❌ Ошибка подключения: {connection_error}")

        # Формируем человекочитаемый статус
        if status_info["ready_for_work"]:
            status_info["status"] = "ready"
            status_info["message"] = f"✅ Ollama готов к работе с моделью {OLLAMA_MODEL}"
        elif status_info["model_loaded"]:
            status_info["status"] = "model_loaded_but_not_ready"
            status_info["message"] = f"⚠️ Модель {OLLAMA_MODEL} загружена, но не отвечает на запросы"
        elif status_info["server_available"]:
            status_info["status"] = "server_available_model_missing"
            status_info["message"] = f"⚠️ Ollama сервер доступен, но модель {OLLAMA_MODEL} не загружена"
        else:
            status_info["status"] = "server_unavailable"
            status_info["message"] = "❌ Ollama сервер недоступен"

        return status_info

    except Exception as e:
        error_msg = f"Критическая ошибка проверки Ollama: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "ollama_url": OLLAMA_URL,
            "model_name": OLLAMA_MODEL,
            "server_available": False,
            "model_loaded": False,
            "ready_for_work": False,
            "status": "error",
            "message": "❌ Критическая ошибка проверки статуса",
            "error": error_msg,
            "last_check": datetime.now().isoformat()
        }


@app.get("/api/v1/recommendations")
async def list_recommendations() -> list[dict[str, object]]:
    """Возвращает все сохраненные рекомендации."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Recommendation).order_by(Recommendation.id.desc())
        )
        items = [
            {"id": rec.id, "text": rec.text, "links": rec.links}
            for rec in result.scalars()
        ]
    return items


@app.get("/api/v1/domains")
async def list_domains() -> list[dict[str, object]]:
    """Возвращает список доменов с кумулятивной информацией."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Domain).order_by(Domain.updated_at.desc())
        )
        items = []
        for domain in result.scalars().all():
            # Принудительно обновляем счетчик постов для актуальности
            actual_posts_count_result = await session.execute(
                select(func.count(WordPressPost.id))
                .where(WordPressPost.domain_id == domain.id)
            )
            actual_posts_count = actual_posts_count_result.scalar()

            # Обновляем если есть расхождение
            if domain.total_posts != actual_posts_count:
                domain.total_posts = actual_posts_count
                await session.commit()
                # Принудительно обновляем объект в сессии
                await session.refresh(domain)

            # Получаем последний анализ рекомендаций
            latest_analysis_result = await session.execute(
                select(AnalysisHistory)
                .where(AnalysisHistory.domain_id == domain.id)
                .order_by(AnalysisHistory.created_at.desc())
                .limit(1)
            )
            latest_analysis = latest_analysis_result.scalar_one_or_none()

            # Получаем кумулятивную статистику
            active_recommendations_result = await session.execute(
                select(LinkRecommendation)
                .where(LinkRecommendation.domain_id == domain.id)
                .where(LinkRecommendation.status == 'active')
            )
            active_recommendations_count = len(active_recommendations_result.scalars().all())

            # Получаем количество инсайтов
            insights_result = await session.execute(
                select(CumulativeInsight)
                .where(CumulativeInsight.domain_id == domain.id)
                .where(CumulativeInsight.status == 'discovered')
            )
            insights_count = len(insights_result.scalars().all())

            # Получаем количество кластеров
            clusters_result = await session.execute(
                select(ThematicClusterAnalysis)
                .where(ThematicClusterAnalysis.domain_id == domain.id)
            )
            clusters_count = len(clusters_result.scalars().all())

            items.append({
                "id": domain.id,
                "name": domain.name,
                "display_name": domain.display_name,
                "description": domain.description,
                "total_posts": domain.total_posts,
                "total_analyses": domain.total_analyses,
                "last_analysis_at": domain.last_analysis_at.isoformat() if domain.last_analysis_at else None,
                "created_at": domain.created_at.isoformat(),
                "updated_at": domain.updated_at.isoformat(),
                "is_indexed": domain.total_posts > 0,
                "latest_recommendations": latest_analysis.recommendations if latest_analysis else [],
                "latest_recommendations_count": len(latest_analysis.recommendations) if latest_analysis else 0,
                "latest_recommendations_date": latest_analysis.created_at.isoformat() if latest_analysis else None,
                # Кумулятивные метрики
                "cumulative_recommendations": active_recommendations_count,
                "cumulative_insights": insights_count,
                "thematic_clusters": clusters_count,
                "intelligence_level": min(1.0, (active_recommendations_count * 0.1 + insights_count * 0.2 + clusters_count * 0.15))
            })
    return items


@app.get("/api/v1/analysis_history")
async def list_analysis_history() -> list[dict[str, object]]:
    """Возвращает историю анализов WordPress сайтов с семантической информацией."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisHistory, Domain)
            .join(Domain, AnalysisHistory.domain_id == Domain.id)
            .order_by(AnalysisHistory.created_at.desc())
        )
        items = []
        for analysis, domain in result:
            items.append({
                "id": analysis.id,
                "domain": domain.name,
                "domain_display_name": domain.display_name,
                "posts_analyzed": analysis.posts_analyzed,
                "connections_found": analysis.connections_found,
                "recommendations_generated": analysis.recommendations_generated,
                "thematic_analysis": analysis.thematic_analysis,
                "semantic_metrics": analysis.semantic_metrics,
                "quality_assessment": analysis.quality_assessment,
                "llm_model_used": analysis.llm_model_used,
                "processing_time_seconds": analysis.processing_time_seconds,
                "created_at": analysis.created_at.isoformat(),
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                "recommendations": analysis.recommendations,
                "summary": f"Семантический анализ {domain.name}: {analysis.posts_analyzed} статей, {analysis.recommendations_generated} качественных рекомендаций"
            })
    return items


@app.get("/api/v1/analysis_history/{analysis_id}")
async def get_analysis_details(analysis_id: int) -> dict[str, object]:
    """Возвращает детали конкретного анализа с семантической информацией."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisHistory, Domain)
            .join(Domain, AnalysisHistory.domain_id == Domain.id)
            .where(AnalysisHistory.id == analysis_id)
        )
        analysis_data = result.first()
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Анализ не найден")

        analysis, domain = analysis_data

        return {
            "id": analysis.id,
            "domain": domain.name,
            "domain_info": {
                "name": domain.name,
                "display_name": domain.display_name,
                "description": domain.description,
                "language": domain.language,
                "category": domain.category,
                "total_posts": domain.total_posts,
                "total_analyses": domain.total_analyses
            },
            "posts_analyzed": analysis.posts_analyzed,
            "connections_found": analysis.connections_found,
            "recommendations_generated": analysis.recommendations_generated,
            "thematic_analysis": analysis.thematic_analysis,
            "semantic_metrics": analysis.semantic_metrics,
            "quality_assessment": analysis.quality_assessment,
            "llm_model_used": analysis.llm_model_used,
            "processing_time_seconds": analysis.processing_time_seconds,
            "created_at": analysis.created_at.isoformat(),
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "recommendations": analysis.recommendations
        }


@app.get("/api/v1/cumulative_insights/{domain_id}")
async def get_cumulative_insights(domain_id: int) -> list[dict[str, object]]:
    """Возвращает кумулятивные инсайты для домена."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CumulativeInsight)
            .where(CumulativeInsight.domain_id == domain_id)
            .order_by(CumulativeInsight.impact_score.desc())
        )
        insights = []
        for insight in result.scalars().all():
            insights.append({
                "id": insight.id,
                "type": insight.insight_type,
                "category": insight.insight_category,
                "title": insight.title,
                "description": insight.description,
                "evidence": insight.evidence,
                "impact_score": insight.impact_score,
                "confidence_level": insight.confidence_level,
                "actionability": insight.actionability,
                "status": insight.status,
                "applied_count": insight.applied_count,
                "created_at": insight.created_at.isoformat()
            })
    return insights


@app.get("/api/v1/thematic_clusters/{domain_id}")
async def get_thematic_clusters(domain_id: int) -> list[dict[str, object]]:
    """Возвращает тематические кластеры для домена."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ThematicClusterAnalysis)
            .where(ThematicClusterAnalysis.domain_id == domain_id)
            .order_by(ThematicClusterAnalysis.linkability_potential.desc())
        )
        clusters = []
        for cluster in result.scalars().all():
            clusters.append({
                "id": cluster.id,
                "name": cluster.cluster_name,
                "description": cluster.cluster_description,
                "keywords": cluster.cluster_keywords,
                "article_count": cluster.article_count,
                "coherence_score": cluster.coherence_score,
                "diversity_score": cluster.diversity_score,
                "linkability_potential": cluster.linkability_potential,
                "evolution_stage": cluster.evolution_stage,
                "growth_trend": cluster.growth_trend,
                "created_at": cluster.created_at.isoformat()
            })
    return clusters


@app.get("/api/v1/cumulative_recommendations/{domain_id}")
async def get_cumulative_recommendations(domain_id: int) -> list[dict[str, object]]:
    """Возвращает накопленные рекомендации для домена."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(LinkRecommendation)
            .where(LinkRecommendation.domain_id == domain_id)
            .where(LinkRecommendation.status == 'active')
            .order_by(LinkRecommendation.quality_score.desc())
        )
        recommendations = []
        for rec in result.scalars().all():
            recommendations.append({
                "id": rec.id,
                "anchor_text": rec.anchor_text,
                "reasoning": rec.reasoning,
                "quality_score": rec.quality_score,
                "generation_count": rec.generation_count,
                "improvement_iterations": rec.improvement_iterations,
                "status": rec.status,
                "created_at": rec.created_at.isoformat(),
                "updated_at": rec.updated_at.isoformat()
            })
    return recommendations


@app.delete("/api/v1/clear_data")
async def clear_all_data() -> dict[str, str]:
    """Очистка всех данных в базе данных (только для разработки)."""
    try:
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            # Очищаем новые кумулятивные таблицы
            await session.execute(text("DELETE FROM cumulative_insights"))
            await session.execute(text("DELETE FROM thematic_cluster_analysis"))
            await session.execute(text("DELETE FROM link_recommendations"))
            await session.execute(text("DELETE FROM semantic_connections"))

            # Очищаем существующие таблицы
            await session.execute(text("DELETE FROM analysis_history"))
            await session.execute(text("DELETE FROM article_embeddings"))
            await session.execute(text("DELETE FROM wordpress_posts"))
            await session.execute(text("DELETE FROM recommendations"))

            # Сброс последовательностей (автоинкремент)
            await session.execute(text("ALTER SEQUENCE cumulative_insights_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE thematic_cluster_analysis_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE link_recommendations_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE semantic_connections_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE analysis_history_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE article_embeddings_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE wordpress_posts_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE recommendations_id_seq RESTART WITH 1"))

            await session.commit()

        # Очищаем ChromaDB
        try:
            if chroma_client:
                # Получаем все коллекции и удаляем их
                collections = chroma_client.list_collections()
                for collection in collections:
                    chroma_client.delete_collection(name=collection.name)
                    print(f"🗑️ Удалена ChromaDB коллекция: {collection.name}")

                # Очищаем кеши менеджеров
                rag_manager.domain_collections.clear()
                cumulative_intelligence.connection_cache.clear()
                cumulative_intelligence.cluster_cache.clear()
                cumulative_intelligence.insight_cache.clear()
                print("🗑️ Очищены кеши менеджеров")
        except Exception as chroma_error:
            print(f"⚠️ Ошибка очистки ChromaDB: {chroma_error}")

        print("🧹 Все данные и кумулятивные знания очищены")
        return {"status": "ok", "message": "Все данные и кумулятивные знания очищены"}

    except Exception as e:
        print(f"❌ Ошибка очистки данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки: {str(e)}")


@app.get("/")
async def root():
    """Редирект на фронтенд."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:3000")


async def generate_stable_recommendations(domain: str, client_id: Optional[str] = None) -> list[dict[str, str]]:
    """Стабильная генерация рекомендаций по одной за раз с ограничением до 5 запросов."""
    print(f"🚀 Запуск стабильной генерации для домена {domain} (client: {client_id})")

    analysis_start_time = datetime.now()
    all_recommendations = []

    try:
        # Шаг 1: Загрузка статей из БД
        if client_id:
            await websocket_manager.send_step(client_id, "Загрузка статей", 1, 7, "Получение статей из базы данных...")

        async with AsyncSessionLocal() as session:
            # Получаем домен
            domain_result = await session.execute(
                select(Domain).where(Domain.name == domain)
            )
            domain_obj = domain_result.scalar_one_or_none()

            if not domain_obj:
                error_msg = f"❌ Домен {domain} не найден в БД"
                print(error_msg)
                if client_id:
                    await websocket_manager.send_error(client_id, error_msg)
                return []

            # Получаем ТОП статей с лучшими метриками
            result = await session.execute(
                select(WordPressPost)
                .where(WordPressPost.domain_id == domain_obj.id)
                .order_by(WordPressPost.linkability_score.desc(), WordPressPost.published_at.desc())
                .limit(10)  # Ограничиваем до 10 лучших статей
            )
            db_posts = result.scalars().all()

        if not db_posts:
            error_msg = "❌ Нет статей для анализа"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg)
            return []

        print(f"📊 Выбрано {len(db_posts)} топовых статей")

        # Шаг 2: Преобразуем в формат для анализа
        if client_id:
            await websocket_manager.send_step(client_id, "Подготовка данных", 2, 7, "Обработка статей...")

        articles_data = []
        for post in db_posts:
            articles_data.append({
                "title": post.title,
                "link": post.link,
                "content": post.content[:800],  # Ограничиваем контент
                "key_concepts": post.key_concepts or [],
                "content_type": post.content_type or "article",
                "linkability_score": post.linkability_score or 0.5
            })

        # Шаг 3: Прогрев модели
        if client_id:
            await websocket_manager.send_step(client_id, "Прогрев модели", 3, 7, "Подготовка Ollama...")

        warmup_success = await warmup_ollama()
        if not warmup_success:
            print("⚠️ Прогрев модели не удался, продолжаем...")

        # Шаг 4 - 6: Генерируем рекомендации по одной
        max_recommendations = 5  # Ограничиваем до 5 рекомендаций

        for i in range(max_recommendations):
            if client_id:
                await websocket_manager.send_step(
                    client_id,
                    f"Генерация рекомендации {i+1}/{max_recommendations}",
                    4 + i,
                    7,
                    f"Поиск связей для рекомендации {i+1}..."
                )

            # Выбираем случайную пару статей для анализа
            import random
            if len(articles_data) >= 2:
                article_pair = random.sample(articles_data, 2)

                # Генерируем одну рекомендацию для этой пары
                single_rec = await generate_single_recommendation(
                    domain, article_pair, articles_data, i+1, client_id
                )

                if single_rec:
                    all_recommendations.extend(single_rec)
                    print(f"✅ Рекомендация {i+1}: получено {len(single_rec)} связей")
                else:
                    print(f"⚠️ Рекомендация {i+1}: пустой результат")

        # Шаг 7: Финализация
        if client_id:
            await websocket_manager.send_step(client_id, "Завершение", 7, 7, f"Готово! Получено {len(all_recommendations)} рекомендаций")

        # Дедуплицируем результаты
        unique_recommendations = deduplicate_and_rank_recommendations(all_recommendations, domain)

        total_analysis_time = (datetime.now() - analysis_start_time).total_seconds()
        print(f"✅ Стабильная генерация завершена: {len(unique_recommendations)} рекомендаций за {total_analysis_time:.1f}с")

        return unique_recommendations

    except Exception as e:
        error_msg = f"❌ Ошибка стабильной генерации: {e}"
        print(error_msg)
        if client_id:
            await websocket_manager.send_error(client_id, "Критическая ошибка генерации", str(e))

        error_time = (datetime.now() - analysis_start_time).total_seconds()
        return []


async def generate_single_recommendation(
    domain: str,
    article_pair: List[Dict],
    all_articles: List[Dict],
    rec_number: int,
    client_id: Optional[str] = None
) -> List[Dict]:
    """Генерирует одну рекомендацию для пары статей."""

    if len(article_pair) != 2:
        return []

    source_article = article_pair[0]
    target_article = article_pair[1]

    # Создаем более качественный и полный промпт с семантическими данными
    articles_context = ""
    for i, article in enumerate(all_articles, 1):
        title = article['title']
        content_snippet = article['content'][:300] if article.get('content') else ""
        key_concepts = article.get('key_concepts', [])[:8]  # Больше концепций
        content_type = article.get('content_type', 'статья')
        linkability = article.get('linkability_score', 0.5)
        semantic_summary = article.get('semantic_summary', '').strip()
        difficulty_level = article.get('difficulty_level', 'средний')
        target_audience = article.get('target_audience', 'общая аудитория')

        articles_context += f"""📄 СТАТЬЯ {i}: «{title}»
🔗 URL: {article['link']}
📊 МЕТРИКИ: Тип контента: {content_type} | Сложность: {difficulty_level} | Потенциал линковки: {linkability:.2f}
👥 АУДИТОРИЯ: {target_audience}
🧠 КЛЮЧЕВЫЕ КОНЦЕПЦИИ: {', '.join(key_concepts) if key_concepts else 'не определены'}
📝 СЕМАНТИЧЕСКОЕ ОПИСАНИЕ: {semantic_summary if semantic_summary else 'автоматически извлекается из контента'}
💡 СОДЕРЖАНИЕ: {content_snippet}...

"""

    # Интеллектуальный промпт с использованием семантических данных и примерами
    qwen_optimized_prompt = f"""🎯 ЗАДАЧА: Глубокий семантический анализ для создания внутренних ссылок на сайте {domain}

🏗️ КОНТЕКСТ АНАЛИЗА:
Анализируется {len(all_articles)} статей сайта {domain}. У каждой статьи есть семантические метрики, ключевые концепции, тип контента и целевая аудитория.

📚 СТАТЬИ ДЛЯ АНАЛИЗА:
{articles_context}

🎯 ЦЕЛЬ: Создать МАКСИМАЛЬНОЕ количество осмысленных внутренних ссылок между статьями на основе:
✅ Семантической близости концепций
✅ Логической последовательности для читателя
✅ Дополнения информации между статьями
✅ SEO-ценности для сайта

🧠 ПРИНЦИПЫ КАЧЕСТВЕННОЙ РЕКОМЕНДАЦИИ:

1️⃣ СЕМАНТИЧЕСКАЯ СВЯЗЬ: Статьи должны дополнять друг друга по смыслу
2️⃣ ЕСТЕСТВЕННОСТЬ: Анкор должен органично вписываться в контекст исходной статьи
3️⃣ ЦЕННОСТЬ: Переход должен быть полезным для читателя
4️⃣ СПЕЦИФИЧНОСТЬ: Анкор должен точно описывать содержание целевой страницы

📝 ПРАВИЛА ДЛЯ АНКОРОВ:
❌ ПЛОХО: "подробное руководство", "перейти сюда", "читать далее", "официальный сайт"
✅ ХОРОШО: "особенности климата и стоимости жизни в Волгограде", "полный разбор переезда в Красноярск с ценами на жилье", "детальный гид по достопримечательностям Казани"

🎯 ПРИМЕРЫ КАЧЕСТВЕННЫХ РЕКОМЕНДАЦИЙ:

ИСТОЧНИК: Переезд в Уфу → ЦЕЛЬ: Переезд в Казань
АНКОР: "сравнение переезда в столицу Татарстана с особенностями культурного разнообразия"
ОБОСНОВАНИЕ: Обе статьи про переезд в республиканские столицы, читатель может сравнить варианты

ИСТОЧНИК: Достопримечательности Сочи → ЦЕЛЬ: Переезд в Сочи
АНКОР: "полная информация о переезде в город с учетом климата и стоимости жизни"
ОБОСНОВАНИЕ: Туристическая статья естественно ведет к практической информации о жизни в городе

🔍 ИНСТРУКЦИЯ:
Проанализируй КАЖДУЮ статью и найди ВСЕ логичные связи с другими статьями. Создай минимум 8 - 12 рекомендаций, максимум определи сам исходя из семантических связей.

📋 ФОРМАТ ОТВЕТА:
[НОМЕР] ИСТОЧНИК: [URL источника] → ЦЕЛЬ: [URL цели]
АНКОР: "[специфичный анкор, описывающий содержание целевой страницы]"
ОБОСНОВАНИЕ: [почему эта связь логична и полезна для читателя]

🚀 НАЧИНАЙ АНАЛИЗ:"""

    # Шаг 5: Запрос к Ollama
    if client_id:
        await websocket_manager.send_step(client_id, "Запрос к Ollama", 5, 7, "Отправка улучшенного контекста в ИИ...")
        await websocket_manager.send_ollama_info(client_id, {
            "status": "starting",
            "model": OLLAMA_MODEL,
            "model_info": "qwen2.5:7b - улучшенный семантический анализ",
            "articles_count": len(all_articles),
            "prompt_length": len(qwen_optimized_prompt),
            "timeout": 300,
            "settings": "temperature=0.4, ctx=8192, predict=1200, threads=6",
            "expected_recommendations": "8 - 15 качественных рекомендаций"
        })

    print("🤖 Отправляю улучшенный семантический запрос...")
    print(f"📝 Размер промпта: {len(qwen_optimized_prompt)} символов")

    # Оптимизированные настройки для качественной генерации
    start_time = datetime.now()
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": qwen_optimized_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,      # Баланс между креативностью и точностью
                        "num_ctx": 8192,         # Увеличиваем контекст для полного анализа
                        "num_predict": 1200,     # Больше токенов для детальных рекомендаций
                        "top_p": 0.85,          # Оптимизируем для качества
                        "top_k": 50,            # Расширяем выбор токенов
                        "repeat_penalty": 1.08,  # Снижаем повторения
                        "seed": 42,             # Фиксированное зерно
                        "stop": ["🚀 НАЧИНАЙ", "КОНЕЦ АНАЛИЗА", "```", "---"],
                        "num_thread": 6
                    }
                }
            )

            request_time = (datetime.now() - start_time).total_seconds()

            if response.status_code != 200:
                print(f"❌ Ошибка Ollama для рекомендации {rec_number}: код {response.status_code}")
                return []

            data = response.json()
            content = data.get("response", "")

            print(f"📝 Рекомендация {rec_number}: ответ {len(content)} символов за {request_time:.1f}с")

            # Парсим одну рекомендацию
            single_recommendations = parse_ollama_recommendations(content, domain, all_articles)

            return single_recommendations

    except Exception as e:
        print(f"❌ Ошибка генерации рекомендации {rec_number}: {e}")
        return []


async def generate_intelligent_semantic_recommendations(domain: str, client_id: Optional[str] = None) -> list[dict[str, str]]:
    """Улучшенная генерация рекомендаций с использованием глубокого семантического анализа."""

    analysis_start_time = datetime.now()

    try:
        if client_id:
            await websocket_manager.send_step(client_id, "Начало умного анализа", 1, 8, "Инициализация семантического движка...")

        print(f"🧠 Запуск интеллектуального анализа для {domain}...")

        # Шаг 1: Получаем семантически обогащенные данные из БД
        async with AsyncSessionLocal() as session:
            try:
                domain_obj = await session.execute(
                    select(Domain).where(Domain.name == domain)
                )
                domain_record = domain_obj.scalar_one_or_none()

                if not domain_record:
                    error_msg = f"❌ Домен {domain} не найден в БД"
                    if client_id:
                        await websocket_manager.send_error(client_id, error_msg)
                    return []

                # Получаем все посты с полными семантическими данными
                result = await session.execute(
                    select(WordPressPost)
                    .where(WordPressPost.domain_id == domain_record.id)
                    .where(WordPressPost.content.isnot(None))
                    .order_by(WordPressPost.linkability_score.desc())
                    .limit(50)  # Увеличиваем до 50 статей для лучшего покрытия
                )

                all_posts = result.scalars().all()

                if not all_posts:
                    error_msg = f"❌ Не найдено статей для домена {domain}"
                    if client_id:
                        await websocket_manager.send_error(client_id, error_msg)
                    return []

                # Диагностическое логирование
                print(f"🔍 ДИАГНОСТИКА СТАТЕЙ:")
                print(f"   📊 Всего статей в БД для домена: {len(all_posts)}")
                print(f"   📈 Статьи с linkability_score > 0: {len([p for p in all_posts if p.linkability_score and p.linkability_score > 0])}")
                print(f"   📝 Статьи с семантическим резюме: {len([p for p in all_posts if p.semantic_summary])}")
                print(f"   🔑 Статьи с ключевыми концепциями: {len([p for p in all_posts if p.key_concepts])}")

                if client_id:
                    await websocket_manager.send_step(client_id, "Анализ семантики", 2, 8, f"Обработка {len(all_posts)} статей...")

                print(f"📊 Загружено {len(all_posts)} семантически обогащенных статей")

                # Шаг 2: Создаем улучшенный контекст для LLM
                articles_context = ""
                posts_data = []

                for i, post in enumerate(all_posts, 1):
                    post_data = {
                        'title': post.title,
                        'link': post.link,
                        'content': post.content[:400],  # Больше контента
                        'key_concepts': post.key_concepts or [],
                        'semantic_summary': post.semantic_summary or '',
                        'content_type': post.content_type or 'статья',
                        'difficulty_level': post.difficulty_level or 'средний',
                        'target_audience': post.target_audience or 'общая аудитория',
                        'linkability_score': post.linkability_score or 0.5,
                        'semantic_richness': post.semantic_richness or 0.5
                    }
                    posts_data.append(post_data)

                    # Создаем богатый контекст для каждой статьи
                    concepts_str = ', '.join(post_data['key_concepts'][:10]) if post_data['key_concepts'] else 'не определены'

                    articles_context += f"""📄 СТАТЬЯ {i}: «{post_data['title']}»
🔗 URL: {post_data['link']}
📊 АНАЛИТИКА: Тип: {post_data['content_type']} | Сложность: {post_data['difficulty_level']} | Потенциал связей: {post_data['linkability_score']:.2f} | Семантическая насыщенность: {post_data['semantic_richness']:.2f}
👥 ЦЕЛЕВАЯ АУДИТОРИЯ: {post_data['target_audience']}
🧠 КЛЮЧЕВЫЕ КОНЦЕПЦИИ: {concepts_str}
📝 СЕМАНТИЧЕСКОЕ РЕЗЮМЕ: {post_data['semantic_summary'] or 'Автоматически извлечено из контента'}
💡 ФРАГМЕНТ КОНТЕНТА: {post_data['content']}...

"""

                if client_id:
                    await websocket_manager.send_step(client_id, "Создание промпта", 3, 8, "Подготовка контекста для ИИ...")

                # Шаг 3: Создаем интеллектуальный промпт
                intelligent_prompt = f"""🎯 ЗАДАЧА: Создание внутренних ссылок для сайта {domain}

Анализируешь {len(all_posts)} статей сайта {domain}:

{articles_context}

ЦЕЛЬ: Создать качественные внутренние ссылки между статьями.

ПРИНЦИПЫ:
1. Семантическая связь между статьями
2. Логичные переходы для читателя
3. Анкоры описывают содержание целевой страницы
4. Избегай общих фраз: "читать далее", "подробнее"

ПРИМЕРЫ ХОРОШИХ АНКОРОВ:
❌ "подробное руководство по Волгограду"
✅ "климат, цены на жилье и работу в Волгограде"

❌ "информация о достопримечательностях"
✅ "музеи и памятники Казани с режимом работы"

ИНСТРУКЦИЯ:
1. Найди семантические связи между статьями
2. Создай 10 - 15 рекомендаций
3. Для каждой дай обоснование

ФОРМАТ:
[№] ИСТОЧНИК: [URL] → ЦЕЛЬ: [URL]
АНКОР: "[описательный анкор]"
ОБОСНОВАНИЕ: [почему связь логична]

НАЧНИ:"""

                if client_id:
                    await websocket_manager.send_step(client_id, "Запрос к ИИ", 4, 8, "Отправка семантического контекста...")
                    await websocket_manager.send_ollama_info(client_id, {
                        "status": "starting",
                        "model": OLLAMA_MODEL,
                        "model_info": "qwen2.5:7b - экспертный семантический анализ",
                        "articles_count": len(all_posts),
                        "prompt_length": len(intelligent_prompt),
                        "timeout": 300,
                        "settings": "temperature=0.3, ctx=10240, predict=1500",
                        "expected_recommendations": "12 - 18 экспертных рекомендаций"
                    })

                print("🤖 Отправляю экспертный семантический запрос...")
                print(f"📝 Размер промпта: {len(intelligent_prompt)} символов")

                # Шаг 4: Запрос к Ollama с оптимальными настройками
                start_time = datetime.now()
                async with httpx.AsyncClient(timeout=600.0) as client:
                    response = await client.post(
                        OLLAMA_URL,
                        json={
                            "model": OLLAMA_MODEL,
                            "prompt": intelligent_prompt,
                            "stream": False,
                            "options": {
                                "temperature": OPTIMAL_TEMPERATURE,
                                "num_ctx": OPTIMAL_CONTEXT_SIZE,
                                "num_predict": OPTIMAL_PREDICTION_SIZE,
                                "top_p": OPTIMAL_TOP_P,
                                "top_k": OPTIMAL_TOP_K,
                                "repeat_penalty": OPTIMAL_REPEAT_PENALTY,
                                "seed": 123,
                                "stop": ["🚀 НАЧНИ", "КОНЕЦ АНАЛИЗА", "```"],
                                "num_thread": 6
                            }
                        },
                        timeout=600
                    )

                request_time = (datetime.now() - start_time).total_seconds()

                if client_id:
                    await websocket_manager.send_ollama_info(client_id, {
                        "status": "completed",
                        "response_code": response.status_code,
                        "request_time": f"{request_time:.1f}s",
                        "response_length": len(response.text) if response.status_code == 200 else 0
                    })

                if response.status_code != 200:
                    error_msg = f"❌ Ollama error: {response.status_code}"
                    if client_id:
                        await websocket_manager.send_error(client_id, error_msg)
                    return []

                data = response.json()
                content = data.get("response", "")

                if client_id:
                    await websocket_manager.send_step(client_id, "Обработка результата", 5, 8, "Парсинг семантических рекомендаций...")

                print(f"📝 Получен ответ от Ollama: {len(content)} символов за {request_time:.1f}с")
                print("🔍 ЭКСПЕРТНЫЙ ОТВЕТ:")
                print("="*70)
                print(content[:1500] + "..." if len(content) > 1500 else content)
                print("="*70)

                # Шаг 5: Улучшенный парсинг рекомендаций
                recommendations = parse_intelligent_recommendations(content, domain, posts_data)

                if client_id:
                    await websocket_manager.send_step(client_id, "Финализация", 6, 8, f"Обработано {len(recommendations)} рекомендаций")

                total_time = (datetime.now() - analysis_start_time).total_seconds()
                print(f"✅ Интеллектуальный анализ завершен: {len(recommendations)} рекомендаций за {total_time:.1f}с")

                return recommendations[:25]  # Возвращаем топ-25

            except Exception as db_error:
                error_msg = f"❌ Ошибка БД: {db_error}"
                print(error_msg)
                if client_id:
                    await websocket_manager.send_error(client_id, "Ошибка базы данных", str(db_error))
                return []

    except Exception as e:
        error_msg = f"❌ Критическая ошибка интеллектуального анализа: {e}"
        print(error_msg)
        if client_id:
            await websocket_manager.send_error(client_id, "Критическая ошибка", str(e))
        return []


def parse_intelligent_recommendations(text: str, domain: str, posts_data: List[Dict]) -> List[Dict]:
    """Улучшенный парсер для экспертных рекомендаций."""
    recommendations = []

    # Создаем множество валидных URL
    valid_urls = {post['link'] for post in posts_data}
    url_to_title = {post['link']: post['title'] for post in posts_data}

    print(f"🔍 Парсинг рекомендаций: {len(valid_urls)} валидных URL")

    lines = text.split('\n')
    current_rec = {}

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Ищем начальные маркеры рекомендаций
        if line.startswith('[') and 'ИСТОЧНИК:' in line and '→' in line and 'ЦЕЛЬ:' in line:
            # Парсим основную строку: [1] ИСТОЧНИК: URL → ЦЕЛЬ: URL
            try:
                parts = line.split('→')
                if len(parts) >= 2:
                    source_part = parts[0].strip()
                    target_part = parts[1].strip()

                    # Извлекаем URL источника
                    source_url = source_part.split('ИСТОЧНИК:')[-1].strip()

                    # Извлекаем URL цели
                    target_url = target_part.split('ЦЕЛЬ:')[-1].strip()

                    # Проверяем валидность URL
                    if source_url in valid_urls and target_url in valid_urls and source_url != target_url:
                        current_rec = {
                            'from': source_url,
                            'to': target_url,
                            'from_title': url_to_title.get(source_url, ''),
                            'to_title': url_to_title.get(target_url, ''),
                            'anchor': '',
                            'comment': ''
                        }
                        print(f"✓ Найдена рекомендация {len(recommendations)+1}: {source_url} → {target_url}")

            except Exception as e:
                print(f"⚠️ Ошибка парсинга строки {line_num}: {e}")
                continue

        # Ищем анкор
        elif line.startswith('АНКОР:') and current_rec:
            anchor = line.replace('АНКОР:', '').strip().strip('"').strip("'")
            current_rec['anchor'] = anchor

        # Ищем обоснование
        elif ('СЕМАНТИЧЕСКОЕ ОБОСНОВАНИЕ:' in line or 'ЦЕННОСТЬ ДЛЯ ЧИТАТЕЛЯ:' in line) and current_rec:
            if 'СЕМАНТИЧЕСКОЕ ОБОСНОВАНИЕ:' in line:
                reasoning = line.split('СЕМАНТИЧЕСКОЕ ОБОСНОВАНИЕ:')[-1].strip()
            else:
                reasoning = line.split('ЦЕННОСТЬ ДЛЯ ЧИТАТЕЛЯ:')[-1].strip()

            if current_rec.get('comment'):
                current_rec['comment'] += ' ' + reasoning
            else:
                current_rec['comment'] = reasoning

            # Если у нас есть все данные, добавляем рекомендацию
            if current_rec.get('anchor'):
                recommendations.append(current_rec.copy())
                current_rec = {}

    print(f"📊 Успешно распарсено {len(recommendations)} рекомендаций")

    # Ранжируем по качеству
    for rec in recommendations:
        quality_score = 0.5

        # Бонус за длинный содержательный анкор
        if len(rec['anchor']) > 30:
            quality_score += 0.2

        # Бонус за подробное обоснование
        if len(rec['comment']) > 50:
            quality_score += 0.2

        # Штраф за общие фразы
        generic_phrases = ['подробное руководство', 'читать далее', 'узнать больше', 'перейти']
        if any(phrase in rec['anchor'].lower() for phrase in generic_phrases):
            quality_score -= 0.3

        rec['quality_score'] = min(quality_score, 1.0)

    # Сортируем по качеству
    recommendations.sort(key=lambda x: x['quality_score'], reverse=True)

    return recommendations


@app.post("/api/v1/wp_intelligent")
async def wp_intelligent_recommendations(req: WPRequest) -> dict[str, list[dict[str, str]]]:
    """🧠 Интеллектуальная генерация семантических рекомендаций."""
    try:
        if not req.domain:
            raise HTTPException(status_code=400, detail="Домен обязателен")

        print(f"🧠 Запуск интеллектуального анализа для {req.domain}")

        # Используем нашу новую улучшенную функцию
        recommendations = await generate_intelligent_semantic_recommendations(req.domain, req.client_id)

        if not recommendations:
            return {
                "message": "Рекомендации не найдены или произошла ошибка",
                "recommendations": [],
                "domain": req.domain,
                "analysis_type": "intelligent_semantic",
                "count": 0
            }

        # Форматируем рекомендации для возврата
        formatted_recommendations = []
        for rec in recommendations:
            formatted_recommendations.append({
                "from": rec.get('from', ''),
                "to": rec.get('to', ''),
                "anchor": rec.get('anchor', ''),
                "comment": rec.get('comment', ''),
                "quality_score": rec.get('quality_score', 0.5)
            })

        print(f"✅ Интеллектуальный анализ завершен: {len(formatted_recommendations)} рекомендаций")

        return {
            "message": f"Интеллектуальный анализ завершен успешно!",
            "recommendations": formatted_recommendations,
            "domain": req.domain,
            "analysis_type": "intelligent_semantic",
            "count": len(formatted_recommendations)
        }

    except Exception as e:
        error_msg = f"❌ Ошибка интеллектуального анализа: {e}"
        print(error_msg)

        if req.client_id:
            await websocket_manager.send_error(req.client_id, "Ошибка интеллектуального анализа", str(e))

        raise HTTPException(status_code=500, detail=error_msg)


async def ensure_ollama_model_context(model_name: str, context_size: int = OPTIMAL_CONTEXT_SIZE) -> bool:
    """Обеспечивает правильную настройку контекста модели Ollama."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Проверяем текущие настройки модели
            response = await client.post(
                f"{OLLAMA_URL.replace('/api/generate', '/api/show')}",
                json={"name": model_name}
            )

            if response.status_code == 200:
                model_info = response.json()
                current_ctx = model_info.get("model_info", {}).get("num_ctx", 2048)

                print(f"🔧 Текущий контекст модели {model_name}: {current_ctx}")

                if current_ctx < context_size:
                    print(f"⚙️  Настраиваю контекст модели на {context_size}...")

                    # Выполняем пустой запрос с нужными настройками для "прогрева"
                    warmup_response = await client.post(
                        OLLAMA_URL,
                        json={
                            "model": model_name,
                            "prompt": "Тест настройки контекста",
                            "stream": False,
                            "options": {
                                "num_ctx": context_size,
                                "num_predict": 1,
                                "temperature": 0.1
                            }
                        },
                        timeout=60
                    )

                    if warmup_response.status_code == 200:
                        print(f"✅ Контекст модели настроен на {context_size}")
                        return True
                    else:
                        print(f"❌ Ошибка настройки контекста: {warmup_response.status_code}")
                        return False
                else:
                    print(f"✅ Контекст модели уже настроен правильно: {current_ctx}")
                    return True
            else:
                print(f"❌ Не удалось получить информацию о модели: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Ошибка настройки контекста модели: {e}")
        return False


@app.post("/api/v1/benchmark_model")
async def benchmark_model_endpoint(request: dict) -> dict[str, str]:
    """Переключает активную модель для бенчмарка."""
    global OLLAMA_MODEL

    model_name = request.get("model_name")
    if not model_name:
        return {
            "status": "error",
            "message": "model_name обязательный параметр"
        }

    try:
        # Проверяем доступность модели
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{OLLAMA_URL.replace('/api/generate', '/api/tags')}")

            if response.status_code == 200:
                models_data = response.json()
                available_models = [model["name"] for model in models_data.get("models", [])]

                if model_name in available_models:
                    OLLAMA_MODEL = model_name

                    # Тестируем новую модель
                    test_response = await client.post(
                        OLLAMA_URL,
                        json={
                            "model": model_name,
                            "prompt": "Тест переключения модели",
                            "stream": False,
                            "options": {"num_predict": 5}
                        },
                        timeout=30
                    )

                    if test_response.status_code == 200:
                        return {
                            "status": "success",
                            "message": f"Модель переключена на {model_name}",
                            "current_model": OLLAMA_MODEL,
                            "available_models": str(available_models)
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Модель {model_name} недоступна для использования"
                        }
                else:
                    return {
                        "status": "error",
                        "message": f"Модель {model_name} не найдена. Доступные: {available_models}"
                    }
            else:
                return {
                    "status": "error",
                    "message": "Ollama сервер недоступен"
                }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка переключения модели: {str(e)}"
        }


# ========================================
# 🎯 BENCHMARK API ENDPOINTS
# ========================================

@app.get("/api/v1/models/available")
async def get_available_models() -> dict[str, list]:
    """Получает список доступных моделей из Ollama."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{OLLAMA_URL.replace('/api/generate', '/api/tags')}")

            if response.status_code == 200:
                models_data = response.json()
                available_models = []

                for model in models_data.get("models", []):
                    model_name = model["name"]
                    model_size = model.get("size", 0)
                    modified_at = model.get("modified_at", "")

                    available_models.append({
                        "name": model_name,
                        "size_bytes": model_size,
                        "size_gb": round(model_size / (1024**3), 2),
                        "modified_at": modified_at,
                        "family": model.get("details", {}).get("family", "unknown"),
                        "format": model.get("details", {}).get("format", "unknown")
                    })

                return {
                    "status": "success",
                    "models": available_models,
                    "count": len(available_models)
                }
            else:
                return {
                    "status": "error",
                    "models": [],
                    "error": "Ollama server недоступен"
                }

    except Exception as e:
        return {
            "status": "error",
            "models": [],
            "error": str(e)
        }


@app.get("/api/v1/models/configurations")
async def get_model_configurations() -> list[dict]:
    """Получает конфигурации моделей из БД."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ModelConfiguration).order_by(ModelConfiguration.model_name)
            )
            configs = result.scalars().all()

            return [
                {
                    "id": config.id,
                    "model_name": config.model_name,
                    "display_name": config.display_name,
                    "description": config.description,
                    "model_type": config.model_type,
                    "is_active": config.is_active,
                    "is_available": config.is_available,
                    "context_size": config.context_size,
                    "max_tokens": config.max_tokens,
                    "avg_tokens_per_second": config.avg_tokens_per_second,
                    "quality_score": config.quality_score,
                    "last_checked_at": config.last_checked_at.isoformat() if config.last_checked_at else None,
                    "benchmark_runs_count": len(config.benchmark_runs)
                }
                for config in configs
            ]

    except Exception as e:
        print(f"❌ Ошибка получения конфигураций моделей: {e}")
        return []


@app.post("/api/v1/models/configurations")
async def create_or_update_model_configuration(req: ModelConfigRequest) -> dict[str, str]:
    """Создает или обновляет конфигурацию модели."""
    try:
        async with AsyncSessionLocal() as session:
            # Проверяем, существует ли конфигурация
            result = await session.execute(
                select(ModelConfiguration).where(ModelConfiguration.model_name == req.model_name)
            )
            config = result.scalar_one_or_none()

            if config:
                # Обновляем существующую
                if req.display_name:
                    config.display_name = req.display_name
                if req.description:
                    config.description = req.description
                if req.default_parameters:
                    config.default_parameters = req.default_parameters
                if req.seo_optimized_params:
                    config.seo_optimized_params = req.seo_optimized_params
                if req.benchmark_params:
                    config.benchmark_params = req.benchmark_params

                config.updated_at = datetime.utcnow()
                action = "updated"
            else:
                # Создаем новую
                config = ModelConfiguration(
                    model_name=req.model_name,
                    display_name=req.display_name or req.model_name,
                    description=req.description,
                    model_type="ollama",  # по умолчанию
                    default_parameters=req.default_parameters or {},
                    seo_optimized_params=req.seo_optimized_params or {},
                    benchmark_params=req.benchmark_params or {}
                )
                session.add(config)
                action = "created"

            await session.commit()

            return {
                "status": "success",
                "message": f"Конфигурация модели {req.model_name} {action}",
                "model_name": req.model_name
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка работы с конфигурацией: {str(e)}"
        }


@app.post("/api/v1/benchmark/run")
async def run_benchmark(req: BenchmarkRequest) -> dict[str, object]:
    """Запускает бенчмарк для указанных моделей."""
    try:
        if not req.models:
            raise HTTPException(status_code=400, detail="Список моделей не может быть пустым")

        # Импортируем класс бенчмарка
        from advanced_seo_benchmark import AdvancedSEOBenchmark

        benchmark = AdvancedSEOBenchmark()

        # Создаем записи в БД для каждой модели
        benchmark_runs = []

        async with AsyncSessionLocal() as session:
            for model_name in req.models:
                # Получаем или создаем конфигурацию модели
                result = await session.execute(
                    select(ModelConfiguration).where(ModelConfiguration.model_name == model_name)
                )
                model_config = result.scalar_one_or_none()

                if not model_config:
                    # Создаем базовую конфигурацию
                    model_config = ModelConfiguration(
                        model_name=model_name,
                        display_name=model_name,
                        model_type="ollama"
                    )
                    session.add(model_config)
                    await session.flush()  # Получаем ID

                # Создаем запуск бенчмарка
                benchmark_run = BenchmarkRun(
                    name=req.name,
                    description=req.description,
                    benchmark_type=req.benchmark_type,
                    model_config_id=model_config.id,
                    iterations=req.iterations,
                    status="pending",
                    test_cases_config={
                        "benchmark_type": req.benchmark_type,
                        "iterations": req.iterations
                    }
                )
                session.add(benchmark_run)
                benchmark_runs.append(benchmark_run)

            await session.commit()

        # Запускаем бенчмарк асинхронно
        results = {}

        # Отправляем WebSocket уведомление о начале
        if req.client_id:
            await websocket_manager.send_progress(req.client_id, {
                "type": "benchmark_started",
                "models": req.models,
                "benchmark_type": req.benchmark_type
            })

        for idx, model_name in enumerate(req.models):
            if req.client_id:
                await websocket_manager.send_step(
                    req.client_id,
                    f"Тестирование модели {model_name}",
                    idx + 1,
                    len(req.models),
                    f"Запуск {req.iterations} итераций..."
                )

            # Запускаем бенчмарк для модели
            try:
                metrics = await benchmark.benchmark_model_advanced(model_name, req.iterations)
                results[model_name] = metrics

                # Обновляем результаты в БД
                async with AsyncSessionLocal() as session:
                    run = next((r for r in benchmark_runs if r.model_config.model_name == model_name), None)
                    if run:
                        result = await session.execute(
                            select(BenchmarkRun).where(BenchmarkRun.id == run.id)
                        )
                        db_run = result.scalar_one_or_none()
                        if db_run:
                            db_run.status = "completed"
                            db_run.completed_at = datetime.utcnow()
                            db_run.overall_score = metrics.overall_score
                            db_run.quality_score = metrics.language_quality_score
                            db_run.performance_score = metrics.tokens_per_second
                            db_run.results = {
                                "metrics": metrics.__dict__,
                                "model_name": model_name
                            }
                            db_run.duration_seconds = (db_run.completed_at - db_run.started_at).total_seconds()
                            await session.commit()

            except Exception as e:
                print(f"❌ Ошибка бенчмарка модели {model_name}: {e}")
                results[model_name] = {"error": str(e)}

                # Помечаем как failed в БД
                async with AsyncSessionLocal() as session:
                    run = next((r for r in benchmark_runs if r.model_config.model_name == model_name), None)
                    if run:
                        result = await session.execute(
                            select(BenchmarkRun).where(BenchmarkRun.id == run.id)
                        )
                        db_run = result.scalar_one_or_none()
                        if db_run:
                            db_run.status = "failed"
                            db_run.error_message = str(e)
                            await session.commit()

        # Отправляем финальное уведомление
        if req.client_id:
            await websocket_manager.send_progress(req.client_id, {
                "type": "benchmark_completed",
                "results": {k: v.__dict__ if hasattr(v, '__dict__') else v for k, v in results.items()}
            })

        return {
            "status": "success",
            "message": f"Бенчмарк завершен для {len(req.models)} моделей",
            "results": results,
            "benchmark_runs": [run.id for run in benchmark_runs]
        }

    except Exception as e:
        error_msg = f"❌ Ошибка запуска бенчмарка: {e}"
        print(error_msg)

        if req.client_id:
            await websocket_manager.send_error(req.client_id, "Ошибка бенчмарка", str(e))

        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/api/v1/benchmark/history")
async def get_benchmark_history() -> list[dict]:
    """Получает историю запусков бенчмарков."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BenchmarkRun, ModelConfiguration)
                .join(ModelConfiguration)
                .order_by(BenchmarkRun.created_at.desc())
                .limit(50)  # Последние 50 запусков
            )
            runs = result.all()

            history = []
            for run, model_config in runs:
                history.append({
                    "id": run.id,
                    "name": run.name,
                    "description": run.description,
                    "benchmark_type": run.benchmark_type,
                    "model_name": model_config.model_name,
                    "model_display_name": model_config.display_name,
                    "status": run.status,
                    "iterations": run.iterations,
                    "overall_score": run.overall_score,
                    "quality_score": run.quality_score,
                    "performance_score": run.performance_score,
                    "duration_seconds": run.duration_seconds,
                    "started_at": run.started_at.isoformat(),
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                    "error_message": run.error_message
                })

            return history

    except Exception as e:
        print(f"❌ Ошибка получения истории бенчмарков: {e}")
        return []


@app.get("/api/v1/benchmark/{run_id}")
async def get_benchmark_details(run_id: int) -> dict[str, object]:
    """Получает детальную информацию о запуске бенчмарка."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BenchmarkRun, ModelConfiguration)
                .join(ModelConfiguration)
                .where(BenchmarkRun.id == run_id)
            )
            run_data = result.first()

            if not run_data:
                raise HTTPException(status_code=404, detail="Запуск бенчмарка не найден")

            run, model_config = run_data

            return {
                "id": run.id,
                "name": run.name,
                "description": run.description,
                "benchmark_type": run.benchmark_type,
                "model_config": {
                    "id": model_config.id,
                    "name": model_config.model_name,
                    "display_name": model_config.display_name,
                    "model_type": model_config.model_type,
                    "context_size": model_config.context_size,
                    "max_tokens": model_config.max_tokens
                },
                "test_cases_config": run.test_cases_config,
                "results": run.results,
                "metrics": run.metrics,
                "status": run.status,
                "iterations": run.iterations,
                "overall_score": run.overall_score,
                "quality_score": run.quality_score,
                "performance_score": run.performance_score,
                "efficiency_score": run.efficiency_score,
                "duration_seconds": run.duration_seconds,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error_message": run.error_message
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка получения деталей бенчмарка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/benchmark/compare")
async def compare_benchmark_runs(run_ids: List[int]) -> dict[str, object]:
    """Сравнивает результаты нескольких запусков бенчмарков."""
    try:
        if len(run_ids) < 2:
            raise HTTPException(status_code=400, detail="Нужно минимум 2 запуска для сравнения")

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BenchmarkRun, ModelConfiguration)
                .join(ModelConfiguration)
                .where(BenchmarkRun.id.in_(run_ids))
            )
            runs_data = result.all()

            if len(runs_data) != len(run_ids):
                raise HTTPException(status_code=404, detail="Некоторые запуски не найдены")

            comparison_data = []
            for run, model_config in runs_data:
                comparison_data.append({
                    "run_id": run.id,
                    "model_name": model_config.model_name,
                    "overall_score": run.overall_score or 0,
                    "quality_score": run.quality_score or 0,
                    "performance_score": run.performance_score or 0,
                    "duration_seconds": run.duration_seconds or 0,
                    "results": run.results
                })

            # Находим лучший результат по каждой метрике
            best_overall = max(comparison_data, key=lambda x: x["overall_score"])
            best_quality = max(comparison_data, key=lambda x: x["quality_score"])
            best_performance = max(comparison_data, key=lambda x: x["performance_score"])
            fastest = min(comparison_data, key=lambda x: x["duration_seconds"])

            return {
                "comparison_data": comparison_data,
                "winners": {
                    "best_overall": {
                        "model": best_overall["model_name"],
                        "score": best_overall["overall_score"]
                    },
                    "best_quality": {
                        "model": best_quality["model_name"],
                        "score": best_quality["quality_score"]
                    },
                    "best_performance": {
                        "model": best_performance["model_name"],
                        "score": best_performance["performance_score"]
                    },
                    "fastest": {
                        "model": fastest["model_name"],
                        "duration": fastest["duration_seconds"]
                    }
                },
                "analysis": {
                    "total_runs": len(comparison_data),
                    "avg_overall_score": sum(x["overall_score"] for x in comparison_data) / len(comparison_data),
                    "avg_quality_score": sum(x["quality_score"] for x in comparison_data) / len(comparison_data),
                    "avg_performance_score": sum(x["performance_score"] for x in comparison_data) / len(comparison_data)
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сравнения бенчмарков: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/ai_insights/semantic_network")
async def get_semantic_network_insights() -> dict[str, object]:
    """Получение инсайтов о семантической сети ИИ."""
    try:
        network_insights = thought_generator.get_network_insights()
        thought_history = []
        
        # Получаем последние 10 мыслей
        for thought in thought_generator.thought_history[-10:]:
            thought_history.append({
                "thought_id": thought.thought_id,
                "stage": thought.stage,
                "content": thought.content,
                "confidence": thought.confidence,
                "semantic_weight": thought.semantic_weight,
                "related_concepts": thought.related_concepts,
                "reasoning_chain": thought.reasoning_chain,
                "timestamp": thought.timestamp.isoformat()
            })
        
        return {
            "semantic_network": network_insights,
            "recent_thoughts": thought_history,
            "thought_statistics": {
                "total_thoughts": len(thought_generator.thought_history),
                "avg_confidence": np.mean([t.confidence for t in thought_generator.thought_history]) if thought_generator.thought_history else 0.0,
                "avg_semantic_weight": np.mean([t.semantic_weight for t in thought_generator.thought_history]) if thought_generator.thought_history else 0.0,
                "stage_distribution": {
                    stage: len([t for t in thought_generator.thought_history if t.stage == stage])
                    for stage in ["analyzing", "connecting", "evaluating", "optimizing"]
                }
            },
            "ai_performance": {
                "concepts_processed": len(thought_generator.concept_embeddings),
                "reasoning_patterns": len(thought_generator.reasoning_patterns),
                "network_complexity": len(thought_generator.semantic_network)
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения инсайтов семантической сети: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.post("/api/v1/ai_insights/reset_network")
async def reset_semantic_network() -> dict[str, str]:
    """Сброс семантической сети ИИ для нового анализа."""
    try:
        thought_generator.thought_history.clear()
        thought_generator.concept_embeddings.clear()
        thought_generator.reasoning_patterns.clear()
        thought_generator.semantic_network.clear()
        
        return {
            "status": "success",
            "analytics": {
                "correlation_analysis": {
                    "confidence_weight_correlation": float(correlation),
                    "interpretation": "высокая" if abs(correlation) > 0.7 else "средняя" if abs(correlation) > 0.3 else "низкая"
                },
                "stage_performance": stage_analysis,
                "overall_metrics": {
                    "total_thoughts": len(thought_generator.thought_history),
                    "avg_confidence": float(np.mean(confidences)),
                    "confidence_stability": float(1.0 - np.std(confidences)),
                    "semantic_richness": float(np.mean(semantic_weights)),
                    "cognitive_diversity": len(set(t.stage for t in thought_generator.thought_history))
                }
            }
        }
        
    except Exception as e:
        print(f"❌ Ошибка получения расширенной аналитики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
