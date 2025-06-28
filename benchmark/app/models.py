"""
🚀 МОДЕЛИ БЕНЧМАРК МИКРОСЕРВИСА
Pydantic модели для валидации данных и API
"""

from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import UUID4
import uuid


class BenchmarkType(str, Enum):
    """Типы бенчмарков."""
    SEO_BASIC = "seo_basic"
    SEO_ADVANCED = "seo_advanced"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"


class ModelType(str, Enum):
    """Типы моделей."""
    LLAMA2 = "llama2"
    MISTRAL = "mistral"
    CODELLAMA = "codellama"
    NEURAL_CHAT = "neural-chat"
    CUSTOM = "custom"


class BenchmarkStatus(str, Enum):
    """Статусы бенчмарка."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MetricType(str, Enum):
    """Типы метрик."""
    RESPONSE_TIME = "response_time"
    ACCURACY = "accuracy"
    QUALITY = "quality"
    RELIABILITY = "reliability"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


# Базовые модели
class BaseBenchmarkModel(BaseModel):
    """Базовая модель для бенчмарка."""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID4: lambda v: str(v)
        }


# Модели запросов
class BenchmarkRequest(BaseModel):
    """Запрос на запуск бенчмарка."""
    name: str = Field(..., min_length=1, max_length=100, description="Название бенчмарка")
    description: Optional[str] = Field(None, max_length=500, description="Описание бенчмарка")
    benchmark_type: BenchmarkType = Field(..., description="Тип бенчмарка")
    models: List[str] = Field(..., min_items=1, max_items=10, description="Список моделей для тестирования")
    iterations: int = Field(default=3, ge=1, le=20, description="Количество итераций")
    timeout: Optional[int] = Field(None, ge=30, le=1800, description="Таймаут в секундах")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Дополнительные параметры")
    client_id: Optional[str] = Field(None, description="ID клиента для WebSocket")
    
    @validator('models')
    def validate_models(cls, v):
        """Валидация списка моделей."""
        if not v:
            raise ValueError("Список моделей не может быть пустым")
        return [model.lower().strip() for model in v]
    
    @validator('iterations')
    def validate_iterations(cls, v):
        """Валидация количества итераций."""
        if v < 1:
            raise ValueError("Количество итераций должно быть больше 0")
        if v > 20:
            raise ValueError("Количество итераций не может превышать 20")
        return v


class ModelConfigRequest(BaseModel):
    """Запрос на конфигурацию модели."""
    model_name: str = Field(..., description="Название модели")
    display_name: Optional[str] = Field(None, description="Отображаемое имя")
    description: Optional[str] = Field(None, description="Описание модели")
    model_type: ModelType = Field(..., description="Тип модели")
    default_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Параметры по умолчанию")
    benchmark_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Параметры для бенчмарка")
    is_active: bool = Field(default=True, description="Активна ли модель")
    
    @validator('model_name')
    def validate_model_name(cls, v):
        """Валидация названия модели."""
        if not v.strip():
            raise ValueError("Название модели не может быть пустым")
        return v.strip().lower()


class BenchmarkFilterRequest(BaseModel):
    """Запрос для фильтрации бенчмарков."""
    benchmark_type: Optional[BenchmarkType] = Field(None, description="Тип бенчмарка")
    model_name: Optional[str] = Field(None, description="Название модели")
    status: Optional[BenchmarkStatus] = Field(None, description="Статус бенчмарка")
    date_from: Optional[datetime] = Field(None, description="Дата начала")
    date_to: Optional[datetime] = Field(None, description="Дата окончания")
    limit: int = Field(default=50, ge=1, le=1000, description="Лимит результатов")
    offset: int = Field(default=0, ge=0, description="Смещение")


# Модели метрик
class PerformanceMetrics(BaseModel):
    """Метрики производительности."""
    response_time_avg: float = Field(..., ge=0, description="Среднее время ответа (сек)")
    response_time_min: float = Field(..., ge=0, description="Минимальное время ответа (сек)")
    response_time_max: float = Field(..., ge=0, description="Максимальное время ответа (сек)")
    response_time_std: float = Field(..., ge=0, description="Стандартное отклонение времени ответа")
    tokens_per_second: float = Field(..., ge=0, description="Токенов в секунду")
    throughput: float = Field(..., ge=0, description="Пропускная способность (запросов/сек)")
    memory_usage_mb: float = Field(..., ge=0, description="Использование памяти (МБ)")
    cpu_usage_percent: float = Field(..., ge=0, le=100, description="Использование CPU (%)")


class QualityMetrics(BaseModel):
    """Метрики качества."""
    accuracy_score: float = Field(..., ge=0, le=1, description="Оценка точности")
    relevance_score: float = Field(..., ge=0, le=1, description="Оценка релевантности")
    coherence_score: float = Field(..., ge=0, le=1, description="Оценка связности")
    fluency_score: float = Field(..., ge=0, le=1, description="Оценка беглости")
    semantic_similarity: float = Field(..., ge=0, le=1, description="Семантическое сходство")
    hallucination_rate: float = Field(..., ge=0, le=1, description="Частота галлюцинаций")
    factual_accuracy: float = Field(..., ge=0, le=1, description="Фактическая точность")


class SEOMetrics(BaseModel):
    """SEO-специфичные метрики."""
    seo_understanding: float = Field(..., ge=0, le=1, description="Понимание SEO")
    anchor_optimization: float = Field(..., ge=0, le=1, description="Оптимизация анкоров")
    semantic_relevance: float = Field(..., ge=0, le=1, description="Семантическая релевантность")
    internal_linking_strategy: float = Field(..., ge=0, le=1, description="Стратегия внутренних ссылок")
    keyword_density: float = Field(..., ge=0, le=1, description="Плотность ключевых слов")
    content_quality: float = Field(..., ge=0, le=1, description="Качество контента")
    user_intent_alignment: float = Field(..., ge=0, le=1, description="Соответствие намерению пользователя")


class ReliabilityMetrics(BaseModel):
    """Метрики надежности."""
    success_rate: float = Field(..., ge=0, le=1, description="Процент успешных запросов")
    error_rate: float = Field(..., ge=0, le=1, description="Процент ошибок")
    timeout_rate: float = Field(..., ge=0, le=1, description="Процент таймаутов")
    consistency_score: float = Field(..., ge=0, le=1, description="Оценка консистентности")
    stability_score: float = Field(..., ge=0, le=1, description="Оценка стабильности")


class BenchmarkMetrics(BaseModel):
    """Комплексные метрики бенчмарка."""
    performance: PerformanceMetrics = Field(..., description="Метрики производительности")
    quality: QualityMetrics = Field(..., description="Метрики качества")
    seo: Optional[SEOMetrics] = Field(None, description="SEO метрики")
    reliability: ReliabilityMetrics = Field(..., description="Метрики надежности")
    overall_score: float = Field(..., ge=0, le=1, description="Общая оценка")
    
    @root_validator
    def calculate_overall_score(cls, values):
        """Расчет общей оценки."""
        if 'performance' in values and 'quality' in values and 'reliability' in values:
            # Взвешенная оценка
            performance_weight = 0.3
            quality_weight = 0.4
            reliability_weight = 0.3
            
            perf_score = (
                (1 - values['performance'].response_time_avg / 10) * 0.4 +
                values['performance'].tokens_per_second / 100 * 0.3 +
                (1 - values['performance'].cpu_usage_percent / 100) * 0.3
            )
            
            qual_score = (
                values['quality'].accuracy_score * 0.3 +
                values['quality'].relevance_score * 0.3 +
                values['quality'].coherence_score * 0.2 +
                values['quality'].fluency_score * 0.2
            )
            
            rel_score = (
                values['reliability'].success_rate * 0.5 +
                values['reliability'].consistency_score * 0.3 +
                values['reliability'].stability_score * 0.2
            )
            
            overall = (
                perf_score * performance_weight +
                qual_score * quality_weight +
                rel_score * reliability_weight
            )
            
            values['overall_score'] = max(0, min(1, overall))
        
        return values


# Модели результатов
class BenchmarkResult(BaseModel):
    """Результат бенчмарка."""
    benchmark_id: UUID4 = Field(default_factory=uuid.uuid4, description="ID бенчмарка")
    name: str = Field(..., description="Название бенчмарка")
    description: Optional[str] = Field(None, description="Описание")
    benchmark_type: BenchmarkType = Field(..., description="Тип бенчмарка")
    model_name: str = Field(..., description="Название модели")
    status: BenchmarkStatus = Field(..., description="Статус")
    metrics: BenchmarkMetrics = Field(..., description="Метрики")
    iterations: int = Field(..., description="Количество итераций")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Параметры")
    started_at: datetime = Field(..., description="Время начала")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")
    duration: Optional[float] = Field(None, ge=0, description="Длительность (сек)")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Сырые данные")
    
    @validator('duration', always=True)
    def calculate_duration(cls, v, values):
        """Расчет длительности."""
        if 'started_at' in values and 'completed_at' in values and values['completed_at']:
            return (values['completed_at'] - values['started_at']).total_seconds()
        return v


class BenchmarkComparison(BaseModel):
    """Сравнение результатов бенчмарков."""
    comparison_id: UUID4 = Field(default_factory=uuid.uuid4, description="ID сравнения")
    name: str = Field(..., description="Название сравнения")
    benchmark_results: List[BenchmarkResult] = Field(..., min_items=2, description="Результаты бенчмарков")
    comparison_metrics: Dict[str, Any] = Field(default_factory=dict, description="Метрики сравнения")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Время создания")
    
    @validator('benchmark_results')
    def validate_results(cls, v):
        """Валидация результатов."""
        if len(v) < 2:
            raise ValueError("Для сравнения нужно минимум 2 результата")
        return v


# Модели API ответов
class BenchmarkResponse(BaseModel):
    """Ответ API бенчмарка."""
    success: bool = Field(..., description="Успешность операции")
    data: Optional[BenchmarkResult] = Field(None, description="Данные результата")
    message: str = Field(..., description="Сообщение")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Временная метка")


class BenchmarkListResponse(BaseModel):
    """Ответ API со списком бенчмарков."""
    success: bool = Field(..., description="Успешность операции")
    data: List[BenchmarkResult] = Field(..., description="Список результатов")
    total: int = Field(..., description="Общее количество")
    page: int = Field(..., description="Номер страницы")
    limit: int = Field(..., description="Лимит на страницу")
    message: str = Field(..., description="Сообщение")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Временная метка")


class ComparisonResponse(BaseModel):
    """Ответ API сравнения."""
    success: bool = Field(..., description="Успешность операции")
    data: Optional[BenchmarkComparison] = Field(None, description="Данные сравнения")
    message: str = Field(..., description="Сообщение")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Временная метка")


class ErrorResponse(BaseModel):
    """Ответ API с ошибкой."""
    success: bool = Field(default=False, description="Успешность операции")
    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Временная метка")


# Модели мониторинга
class HealthCheck(BaseModel):
    """Проверка здоровья сервиса."""
    status: str = Field(..., description="Статус сервиса")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Временная метка")
    version: str = Field(..., description="Версия сервиса")
    uptime: float = Field(..., description="Время работы (сек)")
    services: Dict[str, str] = Field(default_factory=dict, description="Статус зависимостей")


class CacheStats(BaseModel):
    """Статистика кэша."""
    enabled: bool = Field(..., description="Включен ли кэш")
    total_keys: int = Field(..., description="Общее количество ключей")
    memory_usage: str = Field(..., description="Использование памяти")
    hit_rate: float = Field(..., description="Процент попаданий")
    connected_clients: int = Field(..., description="Подключенные клиенты")
    uptime: int = Field(..., description="Время работы (сек)")


class PerformanceStats(BaseModel):
    """Статистика производительности."""
    active_benchmarks: int = Field(..., description="Активные бенчмарки")
    completed_today: int = Field(..., description="Завершенных сегодня")
    avg_response_time: float = Field(..., description="Среднее время ответа")
    total_requests: int = Field(..., description="Общее количество запросов")
    error_rate: float = Field(..., description="Процент ошибок")
    memory_usage_mb: float = Field(..., description="Использование памяти (МБ)")
    cpu_usage_percent: float = Field(..., description="Использование CPU (%)")


# Модели экспорта
class ExportFormat(str, Enum):
    """Форматы экспорта."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


class ExportRequest(BaseModel):
    """Запрос на экспорт."""
    benchmark_ids: List[UUID4] = Field(..., min_items=1, description="ID бенчмарков")
    format: ExportFormat = Field(..., description="Формат экспорта")
    include_raw_data: bool = Field(default=False, description="Включить сырые данные")
    include_metrics: bool = Field(default=True, description="Включить метрики")
    filename: Optional[str] = Field(None, description="Имя файла")


class ExportResponse(BaseModel):
    """Ответ экспорта."""
    success: bool = Field(..., description="Успешность операции")
    download_url: Optional[str] = Field(None, description="URL для скачивания")
    filename: str = Field(..., description="Имя файла")
    file_size: Optional[int] = Field(None, description="Размер файла (байт)")
    expires_at: Optional[datetime] = Field(None, description="Время истечения")
    message: str = Field(..., description="Сообщение")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Временная метка") 