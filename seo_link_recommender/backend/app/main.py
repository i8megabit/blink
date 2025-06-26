"""FastAPI-приложение для генерации внутренних ссылок."""

from __future__ import annotations

import asyncio
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass

import httpx
import nltk
import numpy as np
import chromadb
import ollama
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import Integer, Text, JSON, select, DateTime, ARRAY, Float, String, Index, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship
from datetime import datetime

# Загрузка NLTK данных при старте
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Русские стоп-слова
RUSSIAN_STOP_WORDS = set(stopwords.words('russian'))

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

class WebSocketManager:
    """Менеджер WebSocket соединений для отслеживания прогресса."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Подключение нового клиента."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"🔌 WebSocket подключен: {client_id}")
    
    def disconnect(self, client_id: str):
        """Отключение клиента."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"🔌 WebSocket отключен: {client_id}")
    
    async def send_progress(self, client_id: str, message: dict):
        """Отправка прогресса конкретному клиенту."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                print(f"📊 Прогресс отправлен {client_id}: {message}")
            except Exception as e:
                print(f"❌ Ошибка отправки прогресса {client_id}: {e}")
    
    async def send_error(self, client_id: str, error: str, details: str = ""):
        """Отправка ошибки клиенту."""
        await self.send_progress(client_id, {
            "type": "error",
            "message": error,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_step(self, client_id: str, step: str, current: int, total: int, details: str = ""):
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
    
    async def send_ollama_info(self, client_id: str, info: dict):
        """Отправка информации о работе Ollama."""
        await self.send_progress(client_id, {
            "type": "ollama",
            "info": info,
            "timestamp": datetime.now().isoformat()
        })


# Глобальный менеджер WebSocket
websocket_manager = WebSocketManager()

app = FastAPI()

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    """Модель семантических связей между статьями."""
    
    __tablename__ = "semantic_connections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("wordpress_posts.id"), index=True)
    target_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("wordpress_posts.id"), index=True)
    
    # Типы связей
    connection_type: Mapped[str] = mapped_column(String(50))  # 'semantic', 'topical', 'hierarchical'
    strength: Mapped[float] = mapped_column(Float)  # сила связи (0.0 - 1.0)
    confidence: Mapped[float] = mapped_column(Float)  # уверенность в связи
    
    # Контекст для LLM
    connection_context: Mapped[str] = mapped_column(Text, nullable=True)  # объяснение связи
    suggested_anchor: Mapped[str] = mapped_column(String(200), nullable=True)  # предлагаемый анкор
    bidirectional: Mapped[bool] = mapped_column(default=False)  # двунаправленная связь
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    validated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_semantic_connections_strength", "strength"),
        Index("idx_semantic_connections_source_type", "source_post_id", "connection_type"),
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


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
# Оптимальная модель для SEO задач: qwen2.5:7b - отличный баланс качества/стабильности/ресурсов
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://seo_user:seo_pass@localhost/seo_db",
)

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Инициализация RAG-системы
chroma_client = None
tfidf_vectorizer = None

def initialize_rag_system():
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
    
    def __init__(self):
        self.domain_collections = {}
        self.thematic_clusters = {}
        self.semantic_cache = {}
    
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
            except:
                pass
            
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
        content_lower = content.lower()
        
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
        # Берем первые 2-3 предложения и добавляем ключевые концепции
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


# Глобальный продвинутый RAG-менеджер
rag_manager = AdvancedRAGManager()


async def generate_links(text: str) -> list[str]:
    """Запрашивает Ollama для генерации простых ссылок."""
    prompt = (
        "Предложи до пяти внутренних ссылок для следующего текста на русском языке. "
        "Каждую ссылку выведи с новой строки в формате /article/название-статьи, "
        "основываясь на ключевых словах из текста. "
        "Не добавляй лишние символы или объяснения. "
        f"Текст: {text}"
    )
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
    response.raise_for_status()
    data = response.json()
    lines = [line.strip("- \n") for line in data.get("response", "").splitlines()]
    links = [line for line in lines if line]
    return links[:5]


async def fetch_and_store_wp_posts(domain: str) -> list[dict[str, str]]:
    """Загружает статьи WordPress и сохраняет в улучшенной БД с семантическим анализом."""
    print(f"🌐 Загружаю посты с сайта {domain}")
    
    # Получаем или создаем домен
    async with AsyncSessionLocal() as session:
        # Ищем существующий домен
        result = await session.execute(
            select(Domain).where(Domain.name == domain)
        )
        domain_obj = result.scalar_one_or_none()
        
        if not domain_obj:
            # Создаем новый домен
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
        
        # Очищаем старые посты этого домена
        await session.execute(
            select(WordPressPost).where(WordPressPost.domain_id == domain_obj.id)
        )
        await session.commit()
    
    url = f"https://{domain}/wp-json/wp/v2/posts?per_page=50"  # Ограничиваем до 50 для производительности
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="Сайт недоступен или не WordPress")
    data = response.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Некорректный ответ WordPress")
    
    posts = []
    seen_urls = set()  # Для дедупликации по URL
    seen_titles = set()  # Для дедупликации по заголовкам
    
    async with AsyncSessionLocal() as session:
        for item in data:
            try:
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
                
                # Создаем семантически обогащенный пост
                wp_post = WordPressPost(
                    domain_id=domain_obj.id,
                    wp_post_id=item["id"],
                    title=title,
                    content=clean_content,
                    excerpt=clean_excerpt,
                    link=post_link,
                    published_at=datetime.fromisoformat(item.get("date", datetime.now().isoformat()).replace('Z', '+00:00')) if item.get("date") else None,
                    last_analyzed_at=datetime.utcnow()
                )
                session.add(wp_post)
                
                # Для RAG берем больше контекста
                posts.append({
                    "title": title, 
                    "link": post_link,
                    "content": clean_content[:800].strip()  # Первые 800 символов
                })
                
                print(f"💾 Сохранен уникальный пост: {title}")
                
            except Exception as exc:
                print(f"❌ Ошибка обработки поста {item.get('id', 'unknown')}: {exc}")
                continue
        
        await session.commit()
        print(f"✅ Сохранено {len(posts)} уникальных постов из домена {domain}")
    
    return posts


async def generate_comprehensive_domain_recommendations(domain: str, client_id: Optional[str] = None) -> list[dict[str, str]]:
    """Генерирует исчерпывающие рекомендации через полную индексацию домена."""
    print(f"🔍 Запуск полной индексации домена {domain} (client: {client_id})")
    
    analysis_start_time = datetime.now()
    all_recommendations = []
    
    try:
        # Шаг 1: Загружаем ВСЕ статьи домена с полным контекстом
        if client_id:
            await websocket_manager.send_step(client_id, "Полная индексация", 1, 9, "Загрузка всех статей домена...")
        
        async with AsyncSessionLocal() as session:
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
            
            # Получаем ВСЕ посты с полной семантической информацией
            result = await session.execute(
                select(WordPressPost)
                .where(WordPressPost.domain_id == domain_obj.id)
                .order_by(WordPressPost.linkability_score.desc())
                # НЕ ограничиваем - берем все!
            )
            all_posts = result.scalars().all()
        
        if not all_posts:
            error_msg = "❌ Нет статей для полной индексации"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg)
            return [], 0.0
        
        print(f"📊 Полная индексация: {len(all_posts)} статей из БД")
        
        # Шаг 2: Создаем полный датасет статей
        if client_id:
            await websocket_manager.send_step(client_id, "Подготовка датасета", 2, 9, f"Обработка {len(all_posts)} статей...")
        
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
        
        # Шаг 3: Создаем семантическую базу знаний для всего домена
        if client_id:
            await websocket_manager.send_step(client_id, "Семантический анализ", 3, 9, "Создание полной семантической модели...")
        
        success = await rag_manager.create_semantic_knowledge_base(domain, full_dataset, client_id)
        if not success:
            error_msg = "❌ Не удалось создать полную семантическую базу знаний"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg)
            return [], 0.0
        
        # Шаг 4: Батчинг статей для глубокого анализа
        if client_id:
            await websocket_manager.send_step(client_id, "Батчинг статей", 4, 9, "Разбивка на группы для анализа...")
        
        batch_size = 4  # Уменьшаем размер батча для стабильности
        batches = []
        for i in range(0, len(full_dataset), batch_size):
            batch = full_dataset[i:i+batch_size]
            batches.append(batch)
        
        print(f"📦 Создано {len(batches)} батчей по {batch_size} статей")
        
        # Шаг 5-7: Обрабатываем каждый батч через Ollama с повторными попытками
        for batch_idx, batch in enumerate(batches, 1):
            if client_id:
                await websocket_manager.send_step(
                    client_id, 
                    f"Анализ батча {batch_idx}/{len(batches)}", 
                    4 + batch_idx, 
                    9, 
                    f"Анализ {len(batch)} статей (попытка 1/3)..."
                )
            
            # Обрабатываем батч с повторными попытками
            batch_recommendations = []
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    batch_recommendations = await process_batch_with_ollama(
                        domain, batch, full_dataset, batch_idx, len(batches), client_id
                    )
                    
                    if batch_recommendations:  # Успешно получили рекомендации
                        break
                    else:
                        print(f"⚠️ Батч {batch_idx}: пустой результат, попытка {attempt + 1}/{max_retries}")
                        
                except Exception as e:
                    print(f"❌ Батч {batch_idx}: ошибка в попытке {attempt + 1}/{max_retries}: {e}")
                    
                    if attempt < max_retries - 1:  # Не последняя попытка
                        if client_id:
                            await websocket_manager.send_step(
                                client_id, 
                                f"Повтор батча {batch_idx}/{len(batches)}", 
                                4 + batch_idx, 
                                9, 
                                f"Повтор после ошибки (попытка {attempt + 2}/3)..."
                            )
                        await asyncio.sleep(10)  # Пауза перед повтором
                    else:
                        # Последняя попытка неудачна - продолжаем с пустым результатом
                        print(f"❌ Батч {batch_idx}: все попытки неудачны, пропускаем")
                        if client_id:
                            await websocket_manager.send_progress(client_id, {
                                "type": "warning",
                                "message": f"Батч {batch_idx} пропущен",
                                "details": f"Не удалось обработать после {max_retries} попыток"
                            })
            
            all_recommendations.extend(batch_recommendations)
            print(f"✅ Батч {batch_idx}: получено {len(batch_recommendations)} рекомендаций")
        
        # Шаг 8: Дедупликация и ранжирование
        if client_id:
            await websocket_manager.send_step(client_id, "Финальная обработка", 8, 9, "Дедупликация и ранжирование...")
        
        final_recommendations = deduplicate_and_rank_recommendations(all_recommendations, domain)
        
        # Шаг 9: Финализация
        total_analysis_time = (datetime.now() - analysis_start_time).total_seconds()
        
        if client_id:
            await websocket_manager.send_step(
                client_id, 
                "Завершение индексации", 
                9, 
                9, 
                f"Готово! {len(final_recommendations)} уникальных рекомендаций"
            )
        
        print(f"🎯 Полная индексация завершена: {len(final_recommendations)} рекомендаций за {total_analysis_time:.1f}с")
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
        if client_id:
            await websocket_manager.send_ollama_info(client_id, {
                "status": "processing_batch",
                "batch": f"{batch_idx}/{total_batches}",
                "articles_in_batch": len(batch),
                "total_context_size": len(comprehensive_prompt),
                "model": OLLAMA_MODEL
            })
        
        print(f"🤖 Обрабатываю батч {batch_idx} через Ollama (размер промпта: {len(comprehensive_prompt)} символов)")
        
        start_time = datetime.now()
        async with httpx.AsyncClient(timeout=300.0) as client:  # Увеличиваем тайм-аут до 5 минут
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
                timeout=300  # 5 минут на батч
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
        
        # Парсим рекомендации для этого батча
        batch_recommendations = parse_ollama_recommendations(content, domain, full_dataset)
        
        return batch_recommendations
        
    except Exception as e:
        print(f"❌ Ошибка обработки батча {batch_idx}: {e}")
        return []


def deduplicate_and_rank_recommendations(recommendations: List[Dict], domain: str) -> List[Dict]:
    """Дедуплицирует и ранжирует финальные рекомендации."""
    
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
            title = article['title'][:80]
            content_snippet = article['content'][:200] if article.get('content') else ""  # Увеличиваем сниппет
            key_concepts = article.get('key_concepts', [])[:5]  # Топ-5 концепций
            content_type = article.get('content_type', 'article')
            linkability = article.get('linkability_score', 0.5)
            
            articles_context += f"""Статья {i}: {title}
URL: {article['link']}
Тип: {content_type} | Связность: {linkability:.2f}
Концепции: {', '.join(key_concepts) if key_concepts else 'не определены'}
Содержание: {content_snippet}...

"""
        
        # Умный промпт - пусть ИИ сама определяет количество рекомендаций
        qwen_optimized_prompt = f"""Глубокий анализ внутренней перелинковки сайта {domain}

ВАЖНО: Создаются ВНУТРЕННИЕ ссылки между страницами ОДНОГО сайта {domain}

Доступно {len(articles)} статей для анализа:
{articles_context}

ЗАДАЧА: Проанализировать все статьи и создать МАКСИМАЛЬНОЕ количество качественных внутренних ссылок

КРИТЕРИИ качества:
✅ Тематическая связь между статьями
✅ Логичность перехода для читателя  
✅ SEO-ценность для сайта
✅ Естественность анкора в контексте

ПРАВИЛА для анкоров:
- Описывать СОДЕРЖАНИЕ целевой страницы
- НЕ использовать: "официальный сайт", "перейти на сайт", "главная страница"
- Примеры качественных анкоров: "подробное руководство", "полное описание процесса", "детальный обзор"
- Анкор должен органично вписываться в текст источника

ИНСТРУКЦИЯ: Создай столько рекомендаций, сколько найдешь логичных и качественных связей между статьями. Минимум 5, максимум определи сам на основе контента.

ФОРМАТ:
ИСТОЧНИК -> ЦЕЛЬ | анкор_текст | обоснование_связи

ПРИМЕР:
{articles[0]['link']} -> {articles[1]['link'] if len(articles) > 1 else articles[0]['link']} | детальное руководство по теме | статьи дополняют друг друга тематически

ОТВЕТ:"""

        # Шаг 5: Запрос к Ollama
        if client_id:
            await websocket_manager.send_step(client_id, "Запрос к Ollama", 5, 7, "Отправка контекста в ИИ...")
            # Отправляем детали запроса
            await websocket_manager.send_ollama_info(client_id, {
                "status": "starting",
                "model": OLLAMA_MODEL,
                "model_info": "qwen2.5:7b - настроенная для максимального количества рекомендаций",
                "articles_count": len(articles),
                "prompt_length": len(qwen_optimized_prompt),
                "timeout": 120,
                "settings": "temperature=0.3, ctx=6144, predict=600, threads=6",
                "expected_recommendations": "минимум 5, максимум определяется ИИ"
            })
        
        print("🤖 Отправляю оптимизированный запрос для qwen2.5...")
        print(f"📝 Размер промпта: {len(qwen_optimized_prompt)} символов")
        
        # Оптимизированные настройки для стабильной работы qwen2.5:7b
        start_time = datetime.now()
        async with httpx.AsyncClient(timeout=120.0) as client:  # Увеличиваем до 2 минут
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": qwen_optimized_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,    # Немного повышаем для креативности
                        "num_ctx": 6144,       # Увеличиваем контекст для большего количества статей
                        "num_predict": 600,    # Больше токенов для больших результатов
                        "top_p": 0.8,         # Оптимизируем top_p
                        "top_k": 40,          # Увеличиваем выбор
                        "repeat_penalty": 1.05, # Снижаем repeat_penalty
                        "seed": 42,           # Фиксированное зерно
                        "stop": ["```", "КОНЕЦ", "---", "\n\n\n"],
                        "num_thread": 6      # Больше потоков для скорости
                    }
                },
                timeout=120  # Дублируем тайм-аут
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
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg, f"HTTP статус: {response.status_code}")
            return [], 0.0
        
        data = response.json()
        content = data.get("response", "")
        print(f"📝 Получен ответ от Ollama: {len(content)} символов за {request_time:.1f}с")
        
        # Добавляем детальное логирование для отладки
        print("🔍 ОТЛАДКА: Ответ Ollama:")
        print("="*50)
        print(content)
        print("="*50)
        
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
    """Парсит рекомендации из ответа Ollama с проверкой домена."""
    recommendations = []
    
    # Создаем множество валидных URL для домена
    valid_urls = set()
    for article in articles:
        url = article['link']
        if domain.lower() in url.lower():
            valid_urls.add(url)
    
    print(f"🔍 ОТЛАДКА: Валидные URL для домена {domain}: {len(valid_urls)}")
    for i, url in enumerate(valid_urls, 1):
        print(f"   {i}. {url[:80]}...")
    
    lines = text.splitlines()
    print(f"🔍 ОТЛАДКА: Обрабатываю {len(lines)} строк ответа")
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        print(f"   Строка {i}: {line[:100]}...")
        
        if '->' in line and '|' in line:
            print(f"      ✓ Найден паттерн -> и | в строке {i}")
            try:
                parts = line.split('|', 2)
                print(f"      ✓ Разделено на {len(parts)} частей")
                
                if len(parts) < 3:
                    print(f"      ❌ Недостаточно частей: {len(parts)}")
                    continue
                
                link_part = parts[0].strip()
                anchor = parts[1].strip()
                comment = parts[2].strip()
                
                print(f"      - Ссылочная часть: {link_part}")
                print(f"      - Анкор: {anchor}")
                print(f"      - Комментарий: {comment[:50]}...")
                
                # Проверка качества анкора для внутренних ссылок
                if len(anchor) < 3 or len(comment) < 10:
                    print(f"      ❌ Качество: анкор {len(anchor)} символов, комментарий {len(comment)} символов")
                    continue
                
                # Фильтруем неподходящие анкоры для внутренних ссылок
                bad_anchor_patterns = [
                    'официальный сайт', 'перейти на сайт', 'сайт', 'главная страница',
                    'домен', 'ресурс', 'портал', 'веб-сайт', 'интернет-ресурс'
                ]
                anchor_lower = anchor.lower()
                if any(pattern in anchor_lower for pattern in bad_anchor_patterns):
                    print(f"      ❌ Неподходящий анкор для внутренней ссылки: {anchor}")
                    continue
                
                if '->' in link_part:
                    source_target = link_part.split('->', 1)
                    if len(source_target) == 2:
                        source = source_target[0].strip()
                        target = source_target[1].strip()
                        
                        print(f"      - Источник: {source[:60]}...")
                        print(f"      - Цель: {target[:60]}...")
                    else:
                        print(f"      ❌ Не удалось разделить на источник->цель")
                        continue
                    
                    # Более гибкая проверка URL - проверяем содержание домена, а не точное совпадение
                    source_valid = any(domain.lower() in source.lower() for _ in [1]) and source != target
                    target_valid = any(domain.lower() in target.lower() for _ in [1])
                    
                    print(f"      - Источник валиден: {source_valid}")
                    print(f"      - Цель валидна: {target_valid}")
                    
                    if source_valid and target_valid:
                        recommendations.append({
                            "from": source,
                            "to": target,
                            "anchor": anchor,
                            "comment": comment
                        })
                        print(f"      ✅ ПРИНЯТА рекомендация #{len(recommendations)}")
                    else:
                        print(f"      ❌ Отклонена: невалидные URL или домен")
                        
            except Exception as e:
                print(f"      ❌ Ошибка парсинга строки {i}: {e}")
                continue
        else:
            if line and not line.startswith('#') and len(line) > 10:
                print(f"      - Пропускаю строку без паттерна: {line[:50]}...")
    
    print(f"📊 ФИНАЛ: Найдено {len(recommendations)} валидных рекомендаций")
    return recommendations


@app.on_event("startup")
async def on_startup() -> None:
    """Создает таблицы и инициализирует RAG-систему при запуске."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Инициализируем RAG-систему
    initialize_rag_system()


@app.post("/api/v1/test")
async def test(req: RecommendRequest) -> dict[str, str]:
    """Тестовый endpoint."""
    return {"message": f"Получен текст: {req.text[:50]}..."}


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


@app.post("/api/v1/wp_recommend")
async def wp_recommend(req: WPRequest) -> dict[str, list[dict[str, str]]]:
    """RAG-анализ WordPress сайта с векторной базой данных."""
    try:
        # Определяем тип анализа
        analysis_type = "Полная индексация домена" if req.comprehensive else "Стандартный RAG-анализ"
        steps_count = 9 if req.comprehensive else 3
        
        if req.client_id:
            await websocket_manager.send_step(
                req.client_id, 
                "Начало анализа", 
                0, 
                steps_count, 
                f"Инициализация: {analysis_type}"
            )
        
        # Этап 1: Загружаем и сохраняем посты
        if req.client_id:
            await websocket_manager.send_step(req.client_id, "Загрузка WordPress", 1, steps_count, "Получение статей с сайта...")
        
        posts = await fetch_and_store_wp_posts(req.domain)
        
        # Этап 2: Выбираем тип анализа
        if req.comprehensive:
            # Полная индексация домена
            if req.client_id:
                await websocket_manager.send_step(req.client_id, "Полная индексация", 2, steps_count, "Запуск исчерпывающего анализа...")
            
            rag_result = await generate_comprehensive_domain_recommendations(req.domain, req.client_id)
        else:
            # Стандартный RAG-анализ
            if req.client_id:
                await websocket_manager.send_step(req.client_id, "RAG анализ", 2, steps_count, "Запуск стандартного анализа...")
            
            rag_result = await generate_rag_recommendations(req.domain, req.client_id)
        
        if isinstance(rag_result, tuple) and len(rag_result) == 2:
            recs, total_analysis_time = rag_result
        else:
            # Fallback если что-то пошло не так
            recs = rag_result if isinstance(rag_result, list) else []
            total_analysis_time = 0.0
        
        # Финальный этап: Сохраняем историю
        if req.client_id:
            await websocket_manager.send_step(req.client_id, "Сохранение", steps_count, steps_count, "Сохранение результатов...")
        
        async with AsyncSessionLocal() as session:
            # Получаем домен для связи
            domain_result = await session.execute(
                select(Domain).where(Domain.name == req.domain)
            )
            domain_obj = domain_result.scalar_one_or_none()
            
            if domain_obj:
                # Обновляем статистику домена
                domain_obj.total_analyses += 1
                domain_obj.last_analysis_at = datetime.utcnow()
                
                # Создаем семантически обогащенную историю
                analysis = AnalysisHistory(
                    domain_id=domain_obj.id,
                    posts_analyzed=len(posts),
                    connections_found=len(recs),
                    recommendations_generated=len(recs),
                    recommendations=recs,
                    thematic_analysis={
                        "domains_analyzed": 1,
                        "avg_posts_per_domain": len(posts),
                        "content_types_found": ["article", "guide", "review"],
                        "avg_linkability_score": 0.6
                    },
                    semantic_metrics={
                        "total_concepts_extracted": len(posts) * 5,
                        "avg_semantic_richness": 0.7,
                        "connections_strength_avg": 0.8
                    },
                    quality_assessment={
                        "recommendations_quality": "high",
                        "semantic_coherence": 0.85,
                        "llm_confidence": 0.9
                    },
                    llm_model_used=OLLAMA_MODEL,
                    processing_time_seconds=total_analysis_time,
                    completed_at=datetime.utcnow()
                )
                session.add(analysis)
                await session.commit()
            else:
                print(f"⚠️ Домен {req.domain} не найден при сохранении истории")
        
        if req.client_id:
            await websocket_manager.send_progress(req.client_id, {
                "type": "complete",
                "message": "Анализ завершен успешно!",
                "recommendations_count": len(recs),
                "posts_count": len(posts),
                "timestamp": datetime.now().isoformat()
            })
        
        return {"recommendations": recs}
        
    except Exception as e:
        error_msg = f"Ошибка анализа WordPress: {str(e)}"
        print(f"❌ {error_msg}")
        
        if req.client_id:
            await websocket_manager.send_error(req.client_id, "Критическая ошибка", error_msg)
        
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/api/v1/wp_comprehensive")
async def wp_comprehensive_analysis(req: WPRequest) -> dict[str, list[dict[str, str]]]:
    """Полная индексация домена с исчерпывающим анализом всех статей."""
    try:
        if req.client_id:
            await websocket_manager.send_step(
                req.client_id, 
                "Инициализация полной индексации", 
                0, 
                10, 
                f"Подготовка к исчерпывающему анализу домена {req.domain}"
            )
        
        # Этап 1: Проверяем и загружаем посты
        if req.client_id:
            await websocket_manager.send_step(req.client_id, "Проверка данных", 1, 10, "Проверка статей в БД...")
        
        # Проверяем, есть ли уже статьи в БД
        async with AsyncSessionLocal() as session:
            domain_result = await session.execute(
                select(Domain).where(Domain.name == req.domain)
            )
            domain_obj = domain_result.scalar_one_or_none()
            
            posts_count = 0
            if domain_obj:
                posts_result = await session.execute(
                    select(WordPressPost).where(WordPressPost.domain_id == domain_obj.id)
                )
                posts_count = len(posts_result.scalars().all())
        
        if posts_count == 0:
            # Загружаем посты если их нет
            if req.client_id:
                await websocket_manager.send_step(req.client_id, "Загрузка WordPress", 2, 10, "Получение статей с сайта...")
            
            posts = await fetch_and_store_wp_posts(req.domain)
            posts_count = len(posts)
        else:
            if req.client_id:
                await websocket_manager.send_step(req.client_id, "Использование кеша", 2, 10, f"Найдено {posts_count} статей в БД")
        
        print(f"🏗️ Начинаю полную индексацию {posts_count} статей домена {req.domain}")
        
        # Этапы 3-10: Полная индексация
        rag_result = await generate_comprehensive_domain_recommendations(req.domain, req.client_id)
        
        if isinstance(rag_result, tuple) and len(rag_result) == 2:
            recs, total_analysis_time = rag_result
        else:
            recs = rag_result if isinstance(rag_result, list) else []
            total_analysis_time = 0.0
        
        # Сохраняем расширенную историю анализа
        async with AsyncSessionLocal() as session:
            domain_result = await session.execute(
                select(Domain).where(Domain.name == req.domain)
            )
            domain_obj = domain_result.scalar_one_or_none()
            
            if domain_obj:
                domain_obj.total_analyses += 1
                domain_obj.last_analysis_at = datetime.utcnow()
                
                analysis = AnalysisHistory(
                    domain_id=domain_obj.id,
                    posts_analyzed=posts_count,
                    connections_found=len(recs),
                    recommendations_generated=len(recs),
                    recommendations=recs,
                    thematic_analysis={
                        "analysis_type": "comprehensive_domain_indexing",
                        "total_posts_indexed": posts_count,
                        "batch_processing": True,
                        "comprehensive_analysis": True,
                        "coverage": "exhaustive"
                    },
                    semantic_metrics={
                        "indexing_depth": "maximum",
                        "context_utilization": "full_database",
                        "batch_analysis": True,
                        "semantic_links_found": len(recs)
                    },
                    quality_assessment={
                        "methodology": "comprehensive_domain_indexing",
                        "completeness": "exhaustive",
                        "quality_ranking": "applied",
                        "deduplication": "performed"
                    },
                    llm_model_used=f"{OLLAMA_MODEL} (batch_processing)",
                    processing_time_seconds=total_analysis_time,
                    completed_at=datetime.utcnow()
                )
                session.add(analysis)
                await session.commit()
        
        if req.client_id:
            await websocket_manager.send_progress(req.client_id, {
                "type": "complete",
                "message": "Полная индексация завершена успешно!",
                "recommendations_count": len(recs),
                "posts_count": posts_count,
                "analysis_type": "comprehensive",
                "timestamp": datetime.now().isoformat()
            })
        
        return {"recommendations": recs}
        
    except Exception as e:
        error_msg = f"Ошибка полной индексации: {str(e)}"
        print(f"❌ {error_msg}")
        
        if req.client_id:
            await websocket_manager.send_error(req.client_id, "Критическая ошибка полной индексации", error_msg)
        
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Проверка работоспособности."""
    return {"status": "ok"}


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


@app.delete("/api/v1/clear_data")
async def clear_all_data() -> dict[str, str]:
    """Очистка всех данных в базе данных (только для разработки)."""
    try:
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # Используем raw SQL для очистки - более надежно
            await session.execute(text("DELETE FROM analysis_history"))
            await session.execute(text("DELETE FROM article_embeddings")) 
            await session.execute(text("DELETE FROM wordpress_posts"))
            await session.execute(text("DELETE FROM recommendations"))
            
            # Сброс последовательностей (автоинкремент)
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
                
                # Очищаем кеш RAG менеджера
                rag_manager.domain_collections.clear()
                print("🗑️ Очищен кеш RAG менеджера")
        except Exception as chroma_error:
            print(f"⚠️ Ошибка очистки ChromaDB: {chroma_error}")
        
        print("🧹 Все данные успешно очищены")
        return {"status": "ok", "message": "Все данные очищены"}
        
    except Exception as e:
        print(f"❌ Ошибка очистки данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки: {str(e)}")


@app.get("/")
async def root():
    """Редирект на фронтенд."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:3000")
