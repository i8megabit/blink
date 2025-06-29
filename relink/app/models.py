"""
🔗 Модели данных для сервиса внутренней перелинковки
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class LinkType(str, Enum):
    """Типы внутренних ссылок"""
    INTERNAL = "internal"
    EXTERNAL = "external"
    ANCHOR = "anchor"

class Priority(str, Enum):
    """Приоритеты рекомендаций"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DomainRequest(BaseModel):
    """Запрос для анализа домена"""
    domain: str = Field(..., description="Домен для анализа")
    client_id: Optional[str] = Field(None, description="ID клиента")

class PostData(BaseModel):
    """Данные поста"""
    id: Optional[int] = None
    title: str = Field(..., description="Заголовок поста")
    content: str = Field(..., description="Содержимое поста")
    url: str = Field(..., description="URL поста")
    post_type: Optional[str] = Field(None, description="Тип поста")

class InternalLink(BaseModel):
    """Внутренняя ссылка"""
    source_post_id: int = Field(..., description="ID исходного поста")
    target_post_id: int = Field(..., description="ID целевого поста")
    link_text: str = Field(..., description="Текст ссылки")
    link_type: LinkType = Field(LinkType.INTERNAL, description="Тип ссылки")
    strength: float = Field(1.0, description="Сила связи")

class Recommendation(BaseModel):
    """Рекомендация по внутренней перелинковке"""
    type: str = Field(..., description="Тип рекомендации")
    priority: Priority = Field(Priority.MEDIUM, description="Приоритет")
    title: str = Field(..., description="Заголовок рекомендации")
    description: str = Field(..., description="Описание рекомендации")
    details: Optional[Dict[str, Any]] = Field(None, description="Детали")

class AnalysisResult(BaseModel):
    """Результат анализа"""
    domain: str = Field(..., description="Анализируемый домен")
    total_posts: int = Field(..., description="Общее количество постов")
    posts_with_links: int = Field(..., description="Посты с внутренними ссылками")
    posts_without_links: int = Field(..., description="Посты без внутренних ссылок")
    total_internal_links: int = Field(..., description="Общее количество внутренних ссылок")
    recommendations: List[Recommendation] = Field(..., description="Рекомендации")
    analysis_date: datetime = Field(default_factory=datetime.utcnow)

class LinkAnalysisRequest(BaseModel):
    """Запрос для анализа ссылок"""
    posts: List[PostData] = Field(..., description="Список постов для анализа")
    domain: str = Field(..., description="Домен")
    client_id: Optional[str] = Field(None, description="ID клиента")

class OptimizationRequest(BaseModel):
    """Запрос для оптимизации"""
    domain: str = Field(..., description="Домен для оптимизации")
    target_keywords: List[str] = Field(..., description="Целевые ключевые слова")
    client_id: Optional[str] = Field(None, description="ID клиента")

class OptimizationResult(BaseModel):
    """Результат оптимизации"""
    domain: str = Field(..., description="Домен")
    suggested_links: List[InternalLink] = Field(..., description="Предлагаемые ссылки")
    optimization_score: float = Field(..., description="Оценка оптимизации")
    keywords_coverage: Dict[str, float] = Field(..., description="Покрытие ключевых слов")
    created_at: datetime = Field(default_factory=datetime.utcnow) 