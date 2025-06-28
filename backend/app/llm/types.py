"""
Типы для LLM модулей
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RequestPriority(Enum):
    """Приоритеты запросов"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class RequestStatus(Enum):
    """Статусы запросов"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LLMRequest:
    """Запрос к LLM"""
    id: str
    prompt: str
    model: str
    priority: RequestPriority = RequestPriority.NORMAL
    timeout: int = 300
    max_tokens: int = 4096
    temperature: float = 0.7
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    rag_context: Optional[List[str]] = None


@dataclass
class LLMResponse:
    """Ответ от LLM"""
    id: str
    request_id: str
    content: str
    model: str
    tokens_used: int
    processing_time: float
    status: RequestStatus
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class CacheEntry:
    """Запись в кэше"""
    key: str
    value: Any
    ttl: int
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    active_connections: int = 0
    queue_size: int = 0
    last_updated: Optional[datetime] = None 