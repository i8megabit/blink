"""
🧠 Модели данных для LLM Tuning микросервиса
Поддержка моделей, маршрутизации, RAG и динамического тюнинга
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

Base = declarative_base()


class ModelStatus(str, Enum):
    """Статусы моделей"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOADING = "loading"
    ERROR = "error"
    TUNING = "tuning"


class RouteStrategy(str, Enum):
    """Стратегии маршрутизации"""
    SMART = "smart"
    ROUND_ROBIN = "round_robin"
    LOAD_BASED = "load_based"
    QUALITY_BASED = "quality_based"
    CONTEXT_AWARE = "context_aware"


class TuningStatus(str, Enum):
    """Статусы тюнинга"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# SQLAlchemy модели
class LLMModel(Base):
    """Модель LLM в системе"""
    __tablename__ = "llm_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    provider = Column(String(50), nullable=False)  # ollama, openai, anthropic
    model_id = Column(String(255), nullable=False)  # qwen2.5:7b-turbo
    status = Column(String(20), default=ModelStatus.INACTIVE.value)
    
    # Конфигурация
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    context_length = Column(Integer, default=4096)
    batch_size = Column(Integer, default=512)
    
    # Производительность
    avg_response_time = Column(Float, default=0.0)
    avg_quality_score = Column(Float, default=0.0)
    total_requests = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    
    # Метаданные
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    config = Column(JSON, default=dict)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    routes = relationship("ModelRoute", back_populates="model")
    tuning_sessions = relationship("TuningSession", back_populates="model")
    performance_metrics = relationship("PerformanceMetric", back_populates="model")
    
    __table_args__ = (
        Index('idx_model_provider_status', 'provider', 'status'),
        Index('idx_model_performance', 'avg_response_time', 'avg_quality_score'),
    )


class ModelRoute(Base):
    """Маршруты для моделей"""
    __tablename__ = "model_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    strategy = Column(String(50), default=RouteStrategy.SMART.value)
    
    # Условия маршрутизации
    conditions = Column(JSON, default=dict)  # {"context_type": "seo", "complexity": "high"}
    priority = Column(Integer, default=1)
    weight = Column(Float, default=1.0)
    
    # Статистика
    total_requests = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_response_time = Column(Float, default=0.0)
    
    # Статус
    is_active = Column(Boolean, default=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    model = relationship("LLMModel", back_populates="routes")
    
    __table_args__ = (
        Index('idx_route_strategy_active', 'strategy', 'is_active'),
        Index('idx_route_priority', 'priority', 'weight'),
    )


class TuningSession(Base):
    """Сессии тюнинга моделей"""
    __tablename__ = "tuning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(20), default=TuningStatus.PENDING.value)
    
    # Параметры тюнинга
    strategy = Column(String(50), nullable=False)  # adaptive, aggregate, hybrid
    learning_rate = Column(Float, default=0.001)
    batch_size = Column(Integer, default=32)
    epochs = Column(Integer, default=3)
    
    # Данные для тюнинга
    training_data = Column(JSON, default=list)
    validation_data = Column(JSON, default=list)
    
    # Результаты
    initial_quality = Column(Float, nullable=True)
    final_quality = Column(Float, nullable=True)
    improvement = Column(Float, nullable=True)
    
    # Логи и метрики
    logs = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    
    # Временные метки
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    model = relationship("LLMModel", back_populates="tuning_sessions")
    
    __table_args__ = (
        Index('idx_tuning_status', 'status'),
        Index('idx_tuning_model', 'model_id', 'status'),
    )


class PerformanceMetric(Base):
    """Метрики производительности"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Метрики
    response_time = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    error_occurred = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    # Контекст
    request_type = Column(String(50), nullable=True)  # rag, direct, tuning
    context_length = Column(Integer, nullable=True)
    user_id = Column(String(255), nullable=True)
    
    # Временные метки
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    model = relationship("LLMModel", back_populates="performance_metrics")
    
    __table_args__ = (
        Index('idx_metric_timestamp', 'timestamp'),
        Index('idx_metric_model_time', 'model_id', 'timestamp'),
    )


class RAGDocument(Base):
    """Документы для RAG системы"""
    __tablename__ = "rag_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500), nullable=True)
    
    # Векторные данные
    embedding = Column(JSON, nullable=True)  # Векторное представление
    chunk_id = Column(String(255), nullable=True)
    
    # Метаданные
    document_type = Column(String(50), nullable=True)  # seo, technical, content
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    
    # Статистика использования
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Временные метки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_document_type', 'document_type'),
        Index('idx_document_usage', 'usage_count'),
    )


class APICall(Base):
    """Логи API вызовов"""
    __tablename__ = "api_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Запрос
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    request_data = Column(JSON, nullable=True)
    
    # Ответ
    response_status = Column(Integer, nullable=True)
    response_data = Column(JSON, nullable=True)
    response_time = Column(Float, nullable=False)
    
    # Контекст
    user_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Ошибки
    error_occurred = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    # Временные метки
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_api_timestamp', 'timestamp'),
        Index('idx_api_endpoint', 'endpoint'),
        Index('idx_api_user', 'user_id'),
    )


# Pydantic модели для API
class LLMModelCreate(BaseModel):
    """Создание модели LLM"""
    name: str = Field(..., description="Название модели")
    provider: str = Field(..., description="Провайдер (ollama, openai, anthropic)")
    model_id: str = Field(..., description="ID модели у провайдера")
    temperature: float = Field(default=0.7, description="Температура генерации")
    max_tokens: int = Field(default=4096, description="Максимальное количество токенов")
    context_length: int = Field(default=4096, description="Длина контекста")
    description: Optional[str] = Field(None, description="Описание модели")
    tags: List[str] = Field(default=list, description="Теги модели")
    config: Dict[str, Any] = Field(default=dict, description="Дополнительная конфигурация")


class LLMModelUpdate(BaseModel):
    """Обновление модели LLM"""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    context_length: Optional[int] = None
    status: Optional[ModelStatus] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class LLMModelResponse(BaseModel):
    """Ответ с моделью LLM"""
    id: int
    name: str
    provider: str
    model_id: str
    status: str
    temperature: float
    max_tokens: int
    context_length: int
    avg_response_time: float
    avg_quality_score: float
    total_requests: int
    error_rate: float
    description: Optional[str]
    tags: List[str]
    config: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    last_used: Optional[datetime]
    
    class Config:
        from_attributes = True


class RouteCreate(BaseModel):
    """Создание маршрута"""
    name: str = Field(..., description="Название маршрута")
    model_id: int = Field(..., description="ID модели")
    strategy: RouteStrategy = Field(default=RouteStrategy.SMART, description="Стратегия маршрутизации")
    conditions: Dict[str, Any] = Field(default=dict, description="Условия маршрутизации")
    priority: int = Field(default=1, description="Приоритет")
    weight: float = Field(default=1.0, description="Вес маршрута")


class RouteResponse(BaseModel):
    """Ответ с маршрутом"""
    id: int
    name: str
    model_id: int
    strategy: str
    conditions: Dict[str, Any]
    priority: int
    weight: float
    total_requests: int
    success_rate: float
    avg_response_time: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TuningSessionCreate(BaseModel):
    """Создание сессии тюнинга"""
    model_id: int = Field(..., description="ID модели")
    name: str = Field(..., description="Название сессии")
    strategy: str = Field(..., description="Стратегия тюнинга")
    learning_rate: float = Field(default=0.001, description="Скорость обучения")
    batch_size: int = Field(default=32, description="Размер батча")
    epochs: int = Field(default=3, description="Количество эпох")
    training_data: List[Dict[str, Any]] = Field(default=list, description="Данные для обучения")
    validation_data: List[Dict[str, Any]] = Field(default=list, description="Данные для валидации")


class TuningSessionResponse(BaseModel):
    """Ответ с сессией тюнинга"""
    id: int
    model_id: int
    name: str
    status: str
    strategy: str
    learning_rate: float
    batch_size: int
    epochs: int
    initial_quality: Optional[float]
    final_quality: Optional[float]
    improvement: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RAGQuery(BaseModel):
    """RAG запрос"""
    query: str = Field(..., description="Запрос пользователя")
    context_type: Optional[str] = Field(None, description="Тип контекста")
    top_k: int = Field(default=5, description="Количество результатов")
    similarity_threshold: float = Field(default=0.7, description="Порог схожести")
    use_hybrid_search: bool = Field(default=True, description="Использовать гибридный поиск")


class RAGResponse(BaseModel):
    """RAG ответ"""
    answer: str = Field(..., description="Ответ на запрос")
    sources: List[Dict[str, Any]] = Field(default=list, description="Источники")
    confidence: float = Field(..., description="Уверенность в ответе")
    response_time: float = Field(..., description="Время ответа")
    tokens_used: int = Field(..., description="Использовано токенов")


class RouteRequest(BaseModel):
    """Запрос на маршрутизацию"""
    query: str = Field(..., description="Запрос пользователя")
    context: Optional[Dict[str, Any]] = Field(None, description="Контекст запроса")
    user_id: Optional[str] = Field(None, description="ID пользователя")
    priority: Optional[str] = Field(None, description="Приоритет (high, normal, low)")
    model_preference: Optional[str] = Field(None, description="Предпочтительная модель")


class RouteResponse(BaseModel):
    """Ответ маршрутизатора"""
    model_id: int = Field(..., description="ID выбранной модели")
    model_name: str = Field(..., description="Название модели")
    route_id: int = Field(..., description="ID маршрута")
    strategy: str = Field(..., description="Использованная стратегия")
    confidence: float = Field(..., description="Уверенность в выборе")
    reasoning: str = Field(..., description="Объяснение выбора")


class PerformanceMetrics(BaseModel):
    """Метрики производительности"""
    model_id: int
    response_time: float
    quality_score: Optional[float] = None
    token_count: Optional[int] = None
    error_occurred: bool = False
    error_message: Optional[str] = None
    request_type: Optional[str] = None
    context_length: Optional[int] = None
    user_id: Optional[str] = None 