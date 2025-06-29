"""
🧠 Pydantic схемы для LLM Tuning микросервиса
Расширенные схемы с валидацией и документацией для всех API эндпоинтов
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator, computed_field
import re


# Enums для схем
class ModelStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"
    OPTIMIZING = "optimizing"


class RouteStrategyEnum(str, Enum):
    SMART = "smart"
    ROUND_ROBIN = "round_robin"
    LOAD_BASED = "load_based"
    QUALITY_BASED = "quality_based"
    AB_TESTING = "ab_testing"


class TuningStrategyEnum(str, Enum):
    ADAPTIVE = "adaptive"
    AGGREGATE = "aggregate"
    HYBRID = "hybrid"
    MANUAL = "manual"
    CONTINUOUS = "continuous"


class ABTestStatusEnum(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationTypeEnum(str, Enum):
    PERFORMANCE = "performance"
    QUALITY = "quality"
    MEMORY = "memory"
    LATENCY = "latency"
    HYBRID = "hybrid"


class QualityMetricEnum(str, Enum):
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COHERENCE = "coherence"
    FLUENCY = "fluency"
    COMPLETENESS = "completeness"
    RESPONSE_TIME = "response_time"


# Базовые схемы
class BaseModelSchema(BaseModel):
    """Базовая схема с общими настройками"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Схемы для моделей LLM
class LLMModelCreate(BaseModelSchema):
    """Создание модели LLM"""
    name: str = Field(..., min_length=1, max_length=255, description="Название модели")
    provider: str = Field(default="ollama", description="Провайдер модели")
    version: str = Field(default="latest", description="Версия модели")
    description: Optional[str] = Field(None, max_length=1000, description="Описание модели")
    
    # Параметры модели
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные параметры")
    context_length: int = Field(default=4096, ge=512, le=32768, description="Длина контекста")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Максимальное количество токенов")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Температура генерации")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p параметр")
    
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Название модели может содержать только буквы, цифры, точки, подчеркивания и дефисы')
        return v


class LLMModelUpdate(BaseModelSchema):
    """Обновление модели LLM"""
    description: Optional[str] = Field(None, max_length=1000)
    parameters: Optional[Dict[str, Any]] = None
    context_length: Optional[int] = Field(None, ge=512, le=32768)
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    status: Optional[ModelStatusEnum] = None
    is_available: Optional[bool] = None
    is_default: Optional[bool] = None


class LLMModelResponse(BaseModelSchema):
    """Ответ с моделью LLM"""
    id: int
    name: str
    provider: str
    version: str
    description: Optional[str]
    parameters: Dict[str, Any]
    context_length: int
    max_tokens: int
    temperature: float
    top_p: float
    status: ModelStatusEnum
    is_available: bool
    is_default: bool
    avg_response_time: float
    success_rate: float
    quality_score: float
    created_at: datetime
    updated_at: Optional[datetime]


# Схемы для маршрутизации
class RouteCreate(BaseModelSchema):
    """Создание маршрута"""
    name: str = Field(..., min_length=1, max_length=255, description="Название маршрута")
    model_id: int = Field(..., gt=0, description="ID модели")
    strategy: RouteStrategyEnum = Field(default=RouteStrategyEnum.SMART, description="Стратегия маршрутизации")
    priority: int = Field(default=1, ge=1, le=100, description="Приоритет маршрута")
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="Вес маршрута")
    
    # Условия маршрутизации
    request_types: List[str] = Field(default_factory=list, description="Типы запросов")
    keywords: List[str] = Field(default_factory=list, description="Ключевые слова")
    complexity_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Порог сложности")
    user_tiers: List[str] = Field(default_factory=list, description="Уровни пользователей")
    
    is_active: bool = Field(default=True, description="Активен ли маршрут")
    is_default: bool = Field(default=False, description="Маршрут по умолчанию")


class RouteUpdate(BaseModelSchema):
    """Обновление маршрута"""
    strategy: Optional[RouteStrategyEnum] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    weight: Optional[float] = Field(None, ge=0.0, le=10.0)
    request_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    complexity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    user_tiers: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class RouteResponse(BaseModelSchema):
    """Ответ с маршрутом"""
    id: int
    name: str
    model_id: int
    strategy: RouteStrategyEnum
    priority: int
    weight: float
    request_types: List[str]
    keywords: List[str]
    complexity_threshold: float
    user_tiers: List[str]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime]


# Схемы для тюнинга
class TuningSessionCreate(BaseModelSchema):
    """Создание сессии тюнинга"""
    name: str = Field(..., min_length=1, max_length=255, description="Название сессии")
    model_id: int = Field(..., gt=0, description="ID модели")
    strategy: TuningStrategyEnum = Field(default=TuningStrategyEnum.ADAPTIVE, description="Стратегия тюнинга")
    
    # Данные для обучения
    training_data: List[Dict[str, str]] = Field(..., min_items=1, description="Данные для обучения")
    validation_data: List[Dict[str, str]] = Field(default_factory=list, description="Данные для валидации")
    
    # Гиперпараметры
    learning_rate: float = Field(default=0.001, ge=0.0001, le=0.1, description="Скорость обучения")
    batch_size: int = Field(default=32, ge=1, le=128, description="Размер батча")
    epochs: int = Field(default=3, ge=1, le=50, description="Количество эпох")
    
    @validator('training_data')
    def validate_training_data(cls, v):
        for item in v:
            if not isinstance(item, dict) or 'prompt' not in item or 'response' not in item:
                raise ValueError('Каждый элемент training_data должен содержать поля "prompt" и "response"')
        return v


class TuningSessionUpdate(BaseModelSchema):
    """Обновление сессии тюнинга"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    strategy: Optional[TuningStrategyEnum] = None
    training_data: Optional[List[Dict[str, str]]] = None
    validation_data: Optional[List[Dict[str, str]]] = None
    learning_rate: Optional[float] = Field(None, ge=0.0001, le=0.1)
    batch_size: Optional[int] = Field(None, ge=1, le=128)
    epochs: Optional[int] = Field(None, ge=1, le=50)


class TuningSessionResponse(BaseModelSchema):
    """Ответ с сессией тюнинга"""
    id: int
    name: str
    model_id: int
    strategy: TuningStrategyEnum
    training_data: List[Dict[str, str]]
    validation_data: List[Dict[str, str]]
    learning_rate: float
    batch_size: int
    epochs: int
    status: str
    progress: float
    current_epoch: int
    final_quality_score: float
    improvement_metrics: Dict[str, Any]
    error_log: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


# Схемы для RAG
class RAGQuery(BaseModelSchema):
    """RAG запрос"""
    query: str = Field(..., min_length=1, max_length=5000, description="Запрос пользователя")
    context_type: Optional[str] = Field(None, description="Тип контекста")
    top_k: int = Field(default=5, ge=1, le=20, description="Количество результатов")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Порог схожести")
    use_hybrid_search: bool = Field(default=True, description="Использовать гибридный поиск")
    max_context_length: Optional[int] = Field(None, ge=100, le=8000, description="Максимальная длина контекста")


class RAGDocumentCreate(BaseModelSchema):
    """Создание документа RAG"""
    title: str = Field(..., min_length=1, max_length=500, description="Заголовок документа")
    content: str = Field(..., min_length=1, max_length=50000, description="Содержание документа")
    source: Optional[str] = Field(None, max_length=500, description="Источник документа")
    document_type: str = Field(default="general", max_length=100, description="Тип документа")
    tags: List[str] = Field(default_factory=list, description="Теги документа")
    doc_metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")


class RAGDocumentUpdate(BaseModelSchema):
    """Обновление документа RAG"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1, max_length=50000)
    source: Optional[str] = Field(None, max_length=500)
    document_type: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    doc_metadata: Optional[Dict[str, Any]] = None


class RAGDocumentResponse(BaseModelSchema):
    """Ответ с документом RAG"""
    id: int
    title: str
    content: str
    source: Optional[str]
    document_type: str
    tags: List[str]
    doc_metadata: Dict[str, Any]
    usage_count: int
    last_used: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


class RAGResponse(BaseModelSchema):
    """RAG ответ"""
    answer: str = Field(..., description="Ответ на запрос")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Источники")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность в ответе")
    response_time: float = Field(..., ge=0.0, description="Время ответа в секундах")
    tokens_used: int = Field(..., ge=0, description="Использовано токенов")
    context_documents: List[RAGDocumentResponse] = Field(default_factory=list, description="Использованные документы")


# Схемы для A/B тестирования
class ABTestCreate(BaseModelSchema):
    """Создание A/B теста"""
    name: str = Field(..., min_length=1, max_length=255, description="Название теста")
    model_id: int = Field(..., gt=0, description="ID модели")
    control_model: str = Field(..., min_length=1, max_length=255, description="Контрольная модель")
    variant_model: str = Field(..., min_length=1, max_length=255, description="Тестовая модель")
    traffic_split: float = Field(default=0.5, ge=0.1, le=0.9, description="Доля трафика для варианта")
    
    # Условия тестирования
    request_types: List[str] = Field(default_factory=list, description="Типы запросов для тестирования")
    user_segments: List[str] = Field(default_factory=list, description="Сегменты пользователей")
    start_date: datetime = Field(..., description="Дата начала теста")
    end_date: Optional[datetime] = Field(None, description="Дата окончания теста")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError('Дата окончания должна быть позже даты начала')
        return v


class ABTestUpdate(BaseModelSchema):
    """Обновление A/B теста"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    control_model: Optional[str] = Field(None, min_length=1, max_length=255)
    variant_model: Optional[str] = Field(None, min_length=1, max_length=255)
    traffic_split: Optional[float] = Field(None, ge=0.1, le=0.9)
    request_types: Optional[List[str]] = None
    user_segments: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[ABTestStatusEnum] = None
    is_active: Optional[bool] = None


class ABTestResponse(BaseModelSchema):
    """Ответ с A/B тестом"""
    id: int
    name: str
    model_id: int
    control_model: str
    variant_model: str
    traffic_split: float
    request_types: List[str]
    user_segments: List[str]
    start_date: datetime
    end_date: Optional[datetime]
    status: ABTestStatusEnum
    is_active: bool
    control_metrics: Dict[str, Any]
    variant_metrics: Dict[str, Any]
    statistical_significance: float
    winner: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


# Схемы для оптимизации
class ModelOptimizationCreate(BaseModelSchema):
    """Создание оптимизации модели"""
    model_id: int = Field(..., gt=0, description="ID модели")
    optimization_type: OptimizationTypeEnum = Field(..., description="Тип оптимизации")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Параметры оптимизации")
    target_metrics: Dict[str, Any] = Field(default_factory=dict, description="Целевые метрики")


class ModelOptimizationResponse(BaseModelSchema):
    """Ответ с оптимизацией модели"""
    id: int
    model_id: int
    optimization_type: OptimizationTypeEnum
    parameters: Dict[str, Any]
    target_metrics: Dict[str, Any]
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    improvement: Dict[str, Any]
    status: str
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime


# Схемы для оценки качества
class QualityAssessmentCreate(BaseModelSchema):
    """Создание оценки качества"""
    model_id: int = Field(..., gt=0, description="ID модели")
    request_text: str = Field(..., min_length=1, max_length=10000, description="Текст запроса")
    response_text: str = Field(..., min_length=1, max_length=50000, description="Текст ответа")
    context_documents: List[Dict[str, Any]] = Field(default_factory=list, description="Использованные документы")
    
    # Оценки качества
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Релевантность ответа")
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Точность информации")
    coherence_score: float = Field(..., ge=0.0, le=1.0, description="Связность текста")
    fluency_score: float = Field(..., ge=0.0, le=1.0, description="Беглость языка")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Полнота ответа")
    
    # Дополнительная информация
    assessment_details: Dict[str, Any] = Field(default_factory=dict, description="Детали оценки")
    feedback_notes: Optional[str] = Field(None, max_length=2000, description="Заметки по оценке")
    assessed_by: str = Field(default="system", max_length=255, description="Кто оценивал")
    assessment_method: str = Field(default="automatic", max_length=100, description="Метод оценки")
    
    @computed_field
    @property
    def overall_score(self) -> float:
        """Общая оценка качества"""
        scores = [
            self.relevance_score,
            self.accuracy_score,
            self.coherence_score,
            self.fluency_score,
            self.completeness_score
        ]
        return sum(scores) / len(scores)


class QualityAssessmentResponse(BaseModelSchema):
    """Ответ с оценкой качества"""
    id: int
    model_id: int
    request_text: str
    response_text: str
    context_documents: List[Dict[str, Any]]
    relevance_score: float
    accuracy_score: float
    coherence_score: float
    fluency_score: float
    completeness_score: float
    overall_score: float
    assessment_details: Dict[str, Any]
    feedback_notes: Optional[str]
    assessed_by: str
    assessment_method: str
    created_at: datetime


# Схемы для мониторинга
class PerformanceMetricsCreate(BaseModelSchema):
    """Создание метрик производительности"""
    model_id: int = Field(..., gt=0, description="ID модели")
    response_time: float = Field(..., ge=0.0, description="Время ответа в секундах")
    tokens_generated: Optional[int] = Field(None, ge=0, description="Количество сгенерированных токенов")
    tokens_processed: Optional[int] = Field(None, ge=0, description="Количество обработанных токенов")
    
    # Качественные метрики
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="Детальные метрики качества")
    user_feedback: Optional[float] = Field(None, ge=1.0, le=5.0, description="Оценка пользователя")
    
    # Системные метрики
    memory_usage: Optional[float] = Field(None, ge=0.0, description="Использование памяти в MB")
    cpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Использование CPU в %")
    gpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Использование GPU в %")
    
    # Метаданные запроса
    request_type: Optional[str] = Field(None, max_length=100, description="Тип запроса")
    request_size: Optional[int] = Field(None, ge=0, description="Размер запроса в токенах")
    route_used: Optional[str] = Field(None, max_length=255, description="Использованный маршрут")
    
    # Статус
    success: bool = Field(default=True, description="Успешность запроса")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")


class PerformanceMetricsResponse(BaseModelSchema):
    """Ответ с метриками производительности"""
    id: int
    model_id: int
    timestamp: datetime
    response_time: float
    tokens_generated: Optional[int]
    tokens_processed: Optional[int]
    quality_metrics: Dict[str, float]
    user_feedback: Optional[float]
    memory_usage: Optional[float]
    cpu_usage: Optional[float]
    gpu_usage: Optional[float]
    request_type: Optional[str]
    request_size: Optional[int]
    route_used: Optional[str]
    success: bool
    error_message: Optional[str]


class SystemHealthResponse(BaseModelSchema):
    """Ответ с состоянием системы"""
    id: int
    timestamp: datetime
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    disk_usage: Optional[float]
    network_io: Dict[str, Any]
    ollama_status: Optional[str]
    active_models: int
    total_requests: int
    error_rate: float
    rag_status: Optional[str]
    documents_count: int
    vector_db_status: Optional[str]
    response_time_avg: float
    requests_per_minute: float
    active_connections: int
    alerts: List[Dict[str, Any]]


# Схемы для маршрутизации запросов
class RouteRequest(BaseModelSchema):
    """Запрос на маршрутизацию"""
    query: str = Field(..., min_length=1, max_length=10000, description="Запрос пользователя")
    context: Optional[Dict[str, Any]] = Field(None, description="Контекст запроса")
    user_id: Optional[str] = Field(None, max_length=255, description="ID пользователя")
    priority: Optional[str] = Field(None, regex="^(high|normal|low)$", description="Приоритет запроса")
    model_preference: Optional[str] = Field(None, max_length=255, description="Предпочтительная модель")
    use_rag: bool = Field(default=True, description="Использовать RAG")
    optimization_level: str = Field(default="balanced", regex="^(speed|balanced|quality)$", description="Уровень оптимизации")


class RouteResponse(BaseModelSchema):
    """Ответ маршрутизатора"""
    model_id: int = Field(..., description="ID выбранной модели")
    model_name: str = Field(..., description="Название модели")
    route_id: int = Field(..., description="ID маршрута")
    strategy: str = Field(..., description="Использованная стратегия")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность в выборе")
    reasoning: str = Field(..., description="Объяснение выбора")
    estimated_response_time: float = Field(..., ge=0.0, description="Ожидаемое время ответа")
    use_rag: bool = Field(..., description="Будет ли использоваться RAG")


# Схемы для статистики
class ModelStatsResponse(BaseModelSchema):
    """Статистика модели"""
    model_id: int
    model_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    avg_quality_score: float
    total_tokens_generated: int
    total_tokens_processed: int
    error_rate: float
    last_used: Optional[datetime]
    performance_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Тренд производительности")


class SystemStatsResponse(BaseModelSchema):
    """Статистика системы"""
    total_models: int
    active_models: int
    total_routes: int
    active_routes: int
    total_documents: int
    total_requests_today: int
    avg_response_time: float
    error_rate: float
    system_health: SystemHealthResponse
    top_models: List[ModelStatsResponse] = Field(default_factory=list, description="Топ моделей по использованию")


# Схемы для пагинации
class PaginationParams(BaseModelSchema):
    """Параметры пагинации"""
    skip: int = Field(default=0, ge=0, description="Количество записей для пропуска")
    limit: int = Field(default=100, ge=1, le=1000, description="Количество записей на страницу")


class PaginatedResponse(BaseModelSchema):
    """Ответ с пагинацией"""
    items: List[Any] = Field(..., description="Список элементов")
    total: int = Field(..., ge=0, description="Общее количество элементов")
    skip: int = Field(..., ge=0, description="Количество пропущенных элементов")
    limit: int = Field(..., ge=1, description="Количество элементов на страницу")
    has_more: bool = Field(..., description="Есть ли еще элементы")


# Схемы для фильтров
class ModelFilterParams(BaseModelSchema):
    """Параметры фильтрации моделей"""
    provider: Optional[str] = Field(None, description="Фильтр по провайдеру")
    status: Optional[ModelStatusEnum] = Field(None, description="Фильтр по статусу")
    is_available: Optional[bool] = Field(None, description="Фильтр по доступности")
    min_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Минимальный балл качества")
    max_response_time: Optional[float] = Field(None, ge=0.0, description="Максимальное время ответа")


class RouteFilterParams(BaseModelSchema):
    """Параметры фильтрации маршрутов"""
    strategy: Optional[RouteStrategyEnum] = Field(None, description="Фильтр по стратегии")
    is_active: Optional[bool] = Field(None, description="Фильтр по активности")
    model_id: Optional[int] = Field(None, gt=0, description="Фильтр по модели")


class TuningSessionFilterParams(BaseModelSchema):
    """Параметры фильтрации сессий тюнинга"""
    status: Optional[str] = Field(None, description="Фильтр по статусу")
    model_id: Optional[int] = Field(None, gt=0, description="Фильтр по модели")
    strategy: Optional[TuningStrategyEnum] = Field(None, description="Фильтр по стратегии")
    created_after: Optional[datetime] = Field(None, description="Создано после")
    created_before: Optional[datetime] = Field(None, description="Создано до")


# Схемы для ошибок
class ErrorResponse(BaseModelSchema):
    """Ответ с ошибкой"""
    error: str = Field(..., description="Сообщение об ошибке")
    code: str = Field(..., description="Код ошибки")
    details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время ошибки")


class ValidationErrorResponse(BaseModelSchema):
    """Ответ с ошибкой валидации"""
    error: str = Field(default="Validation error", description="Сообщение об ошибке")
    field_errors: List[Dict[str, Any]] = Field(..., description="Ошибки полей")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время ошибки") 