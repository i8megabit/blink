"""
Pydantic схемы для LLM Tuning микросервиса
Обеспечивают валидацию входных и выходных данных API
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
import re


class ModelStatusEnum(str, Enum):
    """Статусы моделей"""
    READY = "ready"
    TUNING = "tuning"
    FAILED = "failed"
    OFFLINE = "offline"


class RouteStrategyEnum(str, Enum):
    """Стратегии маршрутизации"""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    PERFORMANCE_BASED = "performance_based"
    COMPLEXITY_BASED = "complexity_based"
    KEYWORD_BASED = "keyword_based"


class TuningStrategyEnum(str, Enum):
    """Стратегии тюнинга"""
    FINE_TUNING = "fine_tuning"
    PROMPT_TUNING = "prompt_tuning"
    ADAPTER_TUNING = "adapter_tuning"
    LORA = "lora"
    QLORA = "qlora"


# Базовые схемы
class BaseResponse(BaseModel):
    """Базовая схема ответа"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Схема ошибки"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Схемы для моделей
class LLMModelBase(BaseModel):
    """Базовая схема модели LLM"""
    name: str = Field(..., min_length=1, max_length=100, description="Название модели")
    description: Optional[str] = Field(None, max_length=500, description="Описание модели")
    model_type: str = Field(..., description="Тип модели (llama, gpt, etc.)")
    version: str = Field(..., description="Версия модели")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Параметры модели")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Метаданные модели")


class LLMModelCreate(LLMModelBase):
    """Схема для создания модели"""
    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Название модели может содержать только буквы, цифры, дефисы и подчеркивания')
        return v


class LLMModelUpdate(BaseModel):
    """Схема для обновления модели"""
    description: Optional[str] = Field(None, max_length=500)
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_available: Optional[bool] = None


class LLMModelResponse(LLMModelBase):
    """Схема ответа модели"""
    id: int
    is_available: bool
    status: ModelStatusEnum
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Схемы для маршрутов
class ModelRouteBase(BaseModel):
    """Базовая схема маршрута"""
    name: str = Field(..., min_length=1, max_length=100, description="Название маршрута")
    description: Optional[str] = Field(None, max_length=500, description="Описание маршрута")
    strategy: RouteStrategyEnum = Field(..., description="Стратегия маршрутизации")
    request_types: Optional[List[str]] = Field(default_factory=list, description="Типы запросов")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Ключевые слова")
    complexity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Порог сложности")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Параметры маршрута")
    is_active: bool = True
    is_default: bool = False


class ModelRouteCreate(ModelRouteBase):
    """Схема для создания маршрута"""
    model_id: int = Field(..., gt=0, description="ID модели")


class ModelRouteUpdate(BaseModel):
    """Схема для обновления маршрута"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    strategy: Optional[RouteStrategyEnum] = None
    request_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    complexity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ModelRouteResponse(ModelRouteBase):
    """Схема ответа маршрута"""
    id: int
    model_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Схемы для сессий тюнинга
class TuningSessionBase(BaseModel):
    """Базовая схема сессии тюнинга"""
    name: str = Field(..., min_length=1, max_length=100, description="Название сессии")
    description: Optional[str] = Field(None, max_length=500, description="Описание сессии")
    strategy: TuningStrategyEnum = Field(..., description="Стратегия тюнинга")
    training_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Данные для обучения")
    hyperparameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Гиперпараметры")
    target_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Целевые метрики")


class TuningSessionCreate(TuningSessionBase):
    """Схема для создания сессии тюнинга"""
    model_id: int = Field(..., gt=0, description="ID модели")


class TuningSessionUpdate(BaseModel):
    """Схема для обновления сессии тюнинга"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    strategy: Optional[TuningStrategyEnum] = None
    training_data: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    target_metrics: Optional[Dict[str, Any]] = None


class TuningSessionResponse(TuningSessionBase):
    """Схема ответа сессии тюнинга"""
    id: int
    model_id: int
    status: ModelStatusEnum
    progress: float = Field(0.0, ge=0.0, le=100.0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Схемы для метрик производительности
class PerformanceMetricsBase(BaseModel):
    """Базовая схема метрик производительности"""
    request_type: str = Field(..., description="Тип запроса")
    response_time: float = Field(..., ge=0.0, description="Время ответа в секундах")
    tokens_generated: Optional[int] = Field(None, ge=0, description="Количество сгенерированных токенов")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Процент успешных запросов")
    memory_usage: Optional[float] = Field(None, ge=0.0, description="Использование памяти в MB")
    cpu_usage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Использование CPU в %")


class PerformanceMetricsCreate(PerformanceMetricsBase):
    """Схема для создания метрик"""
    model_id: int = Field(..., gt=0, description="ID модели")
    route_id: Optional[int] = Field(None, gt=0, description="ID маршрута")


class PerformanceMetricsResponse(PerformanceMetricsBase):
    """Схема ответа метрик"""
    id: int
    model_id: int
    route_id: Optional[int] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Схемы для RAG документов
class RAGDocumentBase(BaseModel):
    """Базовая схема RAG документа"""
    title: str = Field(..., min_length=1, max_length=200, description="Заголовок документа")
    content: str = Field(..., min_length=1, description="Содержимое документа")
    source: Optional[str] = Field(None, max_length=500, description="Источник документа")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Метаданные документа")
    tags: Optional[List[str]] = Field(default_factory=list, description="Теги документа")


class RAGDocumentCreate(RAGDocumentBase):
    """Схема для создания RAG документа"""
    pass


class RAGDocumentUpdate(BaseModel):
    """Схема для обновления RAG документа"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    source: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class RAGDocumentResponse(RAGDocumentBase):
    """Схема ответа RAG документа"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Схемы для API запросов
class GenerateRequest(BaseModel):
    """Схема запроса генерации"""
    content: str = Field(..., min_length=1, description="Текст запроса")
    request_type: str = Field("general", description="Тип запроса")
    use_rag: bool = Field(False, description="Использовать RAG")
    optimization_level: str = Field("balanced", description="Уровень оптимизации")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Дополнительные параметры")
    
    @validator('content')
    def validate_content(cls, v):
        if len(v) > 10000:
            raise ValueError('Содержимое запроса не может превышать 10000 символов')
        return v


class GenerateResponse(BaseModel):
    """Схема ответа генерации"""
    response: str = Field(..., description="Сгенерированный ответ")
    model_used: str = Field(..., description="Использованная модель")
    route_used: Optional[str] = Field(None, description="Использованный маршрут")
    tokens_generated: int = Field(..., ge=0, description="Количество сгенерированных токенов")
    response_time: float = Field(..., ge=0.0, description="Время ответа в секундах")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные")


# Схемы для оптимизации
class OptimizationRequest(BaseModel):
    """Схема запроса оптимизации"""
    model_id: int = Field(..., gt=0, description="ID модели")
    target_response_time: Optional[float] = Field(None, ge=0.1, description="Целевое время ответа")
    target_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Целевое качество")
    optimization_type: str = Field("automatic", description="Тип оптимизации")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Параметры оптимизации")


class OptimizationResponse(BaseModel):
    """Схема ответа оптимизации"""
    model_id: int
    optimization_applied: bool
    new_params: Dict[str, Any]
    performance_improvement: float
    message: Optional[str] = None


# Схемы для мониторинга
class SystemStatusResponse(BaseModel):
    """Схема статуса системы"""
    status: str = Field(..., description="Статус системы")
    models_count: int = Field(..., ge=0, description="Количество моделей")
    active_routes: int = Field(..., ge=0, description="Активные маршруты")
    total_requests_24h: int = Field(..., ge=0, description="Общее количество запросов за 24 часа")
    avg_response_time: float = Field(..., ge=0.0, description="Среднее время ответа")
    timestamp: datetime = Field(..., description="Временная метка")


class HealthCheckResponse(BaseModel):
    """Схема проверки здоровья"""
    status: str = Field(..., description="Статус сервиса")
    database: str = Field(..., description="Статус базы данных")
    ollama: str = Field(..., description="Статус Ollama")
    timestamp: datetime = Field(..., description="Временная метка")
    version: str = Field(..., description="Версия сервиса")


# Схемы для пагинации
class PaginationParams(BaseModel):
    """Параметры пагинации"""
    page: int = Field(1, ge=1, description="Номер страницы")
    size: int = Field(20, ge=1, le=100, description="Размер страницы")


class PaginatedResponse(BaseModel):
    """Схема пагинированного ответа"""
    items: List[Any] = Field(..., description="Элементы")
    total: int = Field(..., ge=0, description="Общее количество")
    page: int = Field(..., ge=1, description="Текущая страница")
    size: int = Field(..., ge=1, description="Размер страницы")
    pages: int = Field(..., ge=0, description="Общее количество страниц")


# Схемы для фильтрации
class ModelFilterParams(BaseModel):
    """Параметры фильтрации моделей"""
    status: Optional[ModelStatusEnum] = None
    model_type: Optional[str] = None
    is_available: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class RouteFilterParams(BaseModel):
    """Параметры фильтрации маршрутов"""
    strategy: Optional[RouteStrategyEnum] = None
    is_active: Optional[bool] = None
    model_id: Optional[int] = None
    request_type: Optional[str] = None


class MetricsFilterParams(BaseModel):
    """Параметры фильтрации метрик"""
    model_id: Optional[int] = None
    route_id: Optional[int] = None
    request_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_response_time: Optional[float] = None
    max_response_time: Optional[float] = None


# Схемы для статистики
class ModelStatistics(BaseModel):
    """Статистика модели"""
    model_id: int
    model_name: str
    total_requests: int
    avg_response_time: float
    avg_tokens_generated: float
    success_rate: float
    last_used: Optional[datetime] = None


class SystemStatistics(BaseModel):
    """Статистика системы"""
    total_models: int
    active_models: int
    total_routes: int
    active_routes: int
    total_requests_24h: int
    avg_response_time_24h: float
    total_tuning_sessions: int
    active_tuning_sessions: int
    system_load: float
    memory_usage: float
    cpu_usage: float 