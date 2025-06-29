"""
🔗 Модели данных для сервиса внутренней перелинковки
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class LinkType(str, Enum):
    """Типы внутренних ссылок"""
    NAVIGATION = "navigation"
    CONTENT = "content"
    FOOTER = "footer"
    RELATED = "related"
    CTA = "cta"

class Priority(str, Enum):
    """Приоритеты рекомендаций"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FocusArea(str, Enum):
    """Области фокуса для SEO"""
    INTERNAL_LINKING = "internal_linking"
    CONTENT_OPTIMIZATION = "content_optimization"
    TECHNICAL_SEO = "technical_seo"
    ON_PAGE_SEO = "on_page_seo"
    USER_EXPERIENCE = "user_experience"

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
    """Модель внутренней ссылки"""
    from_url: str = Field(..., description="URL страницы, с которой идет ссылка")
    to_url: str = Field(..., description="URL страницы, на которую ведет ссылка")
    anchor_text: str = Field(..., description="Текст ссылки")
    link_type: LinkType = Field(..., description="Тип ссылки")
    title: Optional[str] = Field(None, description="Title атрибут ссылки")
    nofollow: bool = Field(False, description="Наличие nofollow атрибута")
    position: Optional[str] = Field(None, description="Позиция ссылки на странице")

class Post(BaseModel):
    """Модель поста/страницы"""
    url: str = Field(..., description="URL поста")
    title: str = Field(..., description="Заголовок поста")
    content: str = Field(..., description="Содержимое поста")
    publish_date: Optional[str] = Field(None, description="Дата публикации")
    word_count: int = Field(..., description="Количество слов")
    internal_links: List[InternalLink] = Field(default_factory=list, description="Внутренние ссылки")
    seo_score: Optional[float] = Field(None, description="SEO оценка")
    meta_description: Optional[str] = Field(None, description="Meta description")
    keywords: Optional[List[str]] = Field(None, description="Ключевые слова")

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

class DomainAnalysisRequest(BaseModel):
    """Запрос на анализ домена"""
    domain: str = Field(..., description="Домен для анализа")
    include_posts: bool = Field(True, description="Включить анализ постов")
    include_recommendations: bool = Field(True, description="Включить рекомендации")
    max_posts: int = Field(50, description="Максимальное количество постов для анализа")

class DomainAnalysisResponse(BaseModel):
    """Ответ с анализом домена"""
    domain: str = Field(..., description="Проанализированный домен")
    analysis: Dict[str, Any] = Field(..., description="Результаты анализа")
    timestamp: str = Field(..., description="Время анализа")

class SEORecommendationRequest(BaseModel):
    """Запрос на генерацию SEO рекомендаций"""
    domain: str = Field(..., description="Домен для рекомендаций")
    focus_areas: List[FocusArea] = Field(default_factory=list, description="Области фокуса")
    priority: Priority = Field(Priority.MEDIUM, description="Приоритет рекомендаций")
    include_technical: bool = Field(True, description="Включить технические рекомендации")

class SEORecommendationResponse(BaseModel):
    """Ответ с SEO рекомендациями"""
    domain: str = Field(..., description="Домен")
    recommendations: List[Dict[str, Any]] = Field(..., description="Список рекомендаций")
    generated_at: str = Field(..., description="Время генерации")

class SEOAnalysisResult(BaseModel):
    """Результат SEO анализа"""
    url: str = Field(..., description="URL страницы")
    title_score: float = Field(..., description="Оценка заголовка")
    content_score: float = Field(..., description="Оценка контента")
    meta_description_score: float = Field(..., description="Оценка meta description")
    internal_links_score: float = Field(..., description="Оценка внутренних ссылок")
    overall_score: float = Field(..., description="Общая оценка")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")

class InternalLinkAnalysis(BaseModel):
    """Анализ внутренних ссылок"""
    total_links: int = Field(..., description="Общее количество ссылок")
    unique_targets: int = Field(..., description="Уникальные целевые страницы")
    orphan_pages: List[str] = Field(default_factory=list, description="Страницы без входящих ссылок")
    most_linked_pages: List[Dict[str, Any]] = Field(default_factory=list, description="Самые ссылаемые страницы")
    link_distribution: Dict[str, int] = Field(default_factory=dict, description="Распределение ссылок по типам")

class PostAnalysis(BaseModel):
    """Анализ поста"""
    url: str = Field(..., description="URL поста")
    title: str = Field(..., description="Заголовок")
    word_count: int = Field(..., description="Количество слов")
    internal_links_count: int = Field(..., description="Количество внутренних ссылок")
    seo_score: float = Field(..., description="SEO оценка")
    issues: List[str] = Field(default_factory=list, description="Найденные проблемы")

class IndexingStatus(BaseModel):
    """Статус индексации"""
    status: str = Field(..., description="Статус индексации")
    message: str = Field(..., description="Сообщение")
    domain: str = Field(..., description="Домен")
    timestamp: str = Field(..., description="Время")
    data: Optional[Dict[str, Any]] = Field(None, description="Данные индексации")

class DashboardData(BaseModel):
    """Данные для дашборда"""
    domain: str = Field(..., description="Домен")
    total_posts: int = Field(..., description="Общее количество постов")
    total_internal_links: int = Field(..., description="Общее количество внутренних ссылок")
    average_seo_score: float = Field(..., description="Средняя SEO оценка")
    top_posts: List[PostAnalysis] = Field(default_factory=list, description="Лучшие посты")
    top_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Топ рекомендации")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Недавняя активность")

class ContentAnalysisRequest(BaseModel):
    """Запрос на анализ контента"""
    url: str = Field(..., description="URL страницы")
    title: str = Field(..., description="Заголовок")
    content: str = Field(..., description="Контент")
    meta_description: Optional[str] = Field(None, description="Meta description")

class ContentAnalysisResponse(BaseModel):
    """Ответ с анализом контента"""
    url: str = Field(..., description="URL страницы")
    analysis: Dict[str, Any] = Field(..., description="Результаты анализа")
    score: float = Field(..., description="Общая оценка")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    timestamp: str = Field(..., description="Время анализа")

# Дополнительные модели для расширенной функциональности

class ExportFormat(str, Enum):
    """Форматы экспорта"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"

class MetricsData(BaseModel):
    """Метрики сервиса"""
    total_requests: int = Field(..., description="Общее количество запросов")
    successful_requests: int = Field(..., description="Успешные запросы")
    failed_requests: int = Field(..., description="Неудачные запросы")
    average_response_time: float = Field(..., description="Среднее время ответа")
    domains_analyzed: int = Field(..., description="Количество проанализированных доменов")
    recommendations_generated: int = Field(..., description="Количество сгенерированных рекомендаций")

class ServiceHealth(BaseModel):
    """Здоровье сервиса"""
    status: str = Field(..., description="Статус сервиса")
    version: str = Field(..., description="Версия сервиса")
    uptime: str = Field(..., description="Время работы")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Статус зависимостей")
    last_check: str = Field(..., description="Время последней проверки") 