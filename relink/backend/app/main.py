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

# Импортируем новые модули
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
from .models import Base, User, Domain, WordPressPost, AnalysisHistory

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

# ... existing code ...

