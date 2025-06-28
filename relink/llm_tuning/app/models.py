"""
🧠 Модели данных для LLM Tuning микросервиса
Расширенные модели с поддержкой A/B тестирования, автоматической оптимизации
и детального мониторинга качества
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, 
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

Base = declarative_base()


class ModelStatus(str, Enum):
    """Статусы моделей LLM"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    ERROR = "error"
    OPTIMIZING = "optimizing"


class RouteStrategy(str, Enum):
    """Стратегии маршрутизации"""
    SMART = "smart"
    ROUND_ROBIN = "round_robin"
    LOAD_BASED = "load_based"
    QUALITY_BASED = "quality_based"
    AB_TESTING = "ab_testing"


class TuningStrategy(str, Enum):
    """Стратегии тюнинга"""
    ADAPTIVE = "adaptive"
    AGGREGATE = "aggregate"
    HYBRID = "hybrid"
    MANUAL = "manual"
    CONTINUOUS = "continuous"


class ABTestStatus(str, Enum):
    """Статусы A/B тестов"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationType(str, Enum):
    """Типы оптимизации"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    MEMORY = "memory"
    LATENCY = "latency"
    HYBRID = "hybrid"


class QualityMetric(str, Enum):
    """Метрики качества"""
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COHERENCE = "coherence"
    FLUENCY = "fluency"
    COMPLETENESS = "completeness"
    RESPONSE_TIME = "response_time"


class LLMModel(Base):
    """Модель LLM"""
    __tablename__ = "llm_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    provider = Column(String(50), nullable=False, default="ollama")
    version = Column(String(50), nullable=False, default="latest")
    description = Column(Text)
    
    # Параметры модели
    parameters = Column(JSON, default={})
    context_length = Column(Integer, default=4096)
    max_tokens = Column(Integer, default=2048)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    
    # Статус и доступность
    status = Column(SQLEnum(ModelStatus), default=ModelStatus.ACTIVE)
    is_available = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Производительность
    avg_response_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=1.0)
    quality_score = Column(Float, default=0.0)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    routes = relationship("ModelRoute", back_populates="model", cascade="all, delete-orphan")
    tuning_sessions = relationship("TuningSession", back_populates="model", cascade="all, delete-orphan")
    metrics = relationship("PerformanceMetrics", back_populates="model", cascade="all, delete-orphan")
    ab_tests = relationship("ABTest", back_populates="model", cascade="all, delete-orphan")
    optimizations = relationship("ModelOptimization", back_populates="model", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_model_provider_status', 'provider', 'status'),
        Index('idx_model_quality', 'quality_score'),
        Index('idx_model_response_time', 'avg_response_time'),
    )


class ModelRoute(Base):
    """Маршрут для модели"""
    __tablename__ = "model_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Стратегия маршрутизации
    strategy = Column(SQLEnum(RouteStrategy), default=RouteStrategy.SMART)
    priority = Column(Integer, default=1)
    weight = Column(Float, default=1.0)
    
    # Условия маршрутизации
    request_types = Column(JSON, default=[])  # Список типов запросов
    keywords = Column(JSON, default=[])  # Ключевые слова для маршрутизации
    complexity_threshold = Column(Float, default=0.0)  # Порог сложности
    user_tiers = Column(JSON, default=[])  # Уровни пользователей
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    model = relationship("LLMModel", back_populates="routes")
    
    __table_args__ = (
        Index('idx_route_strategy_active', 'strategy', 'is_active'),
        Index('idx_route_priority', 'priority'),
    )


class TuningSession(Base):
    """Сессия тюнинга модели"""
    __tablename__ = "tuning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Параметры тюнинга
    strategy = Column(SQLEnum(TuningStrategy), default=TuningStrategy.ADAPTIVE)
    training_data = Column(JSON, default=[])  # Данные для обучения
    validation_data = Column(JSON, default=[])  # Данные для валидации
    
    # Гиперпараметры
    learning_rate = Column(Float, default=0.001)
    batch_size = Column(Integer, default=32)
    epochs = Column(Integer, default=3)
    
    # Статус и прогресс
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 0.0 - 1.0
    current_epoch = Column(Integer, default=0)
    
    # Результаты
    final_quality_score = Column(Float, default=0.0)
    improvement_metrics = Column(JSON, default={})
    error_log = Column(Text)
    
    # Метаданные
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    model = relationship("LLMModel", back_populates="tuning_sessions")
    
    __table_args__ = (
        Index('idx_tuning_status', 'status'),
        Index('idx_tuning_model', 'model_id'),
        Index('idx_tuning_created', 'created_at'),
    )


class RAGDocument(Base):
    """Документ для RAG системы"""
    __tablename__ = "rag_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500))
    document_type = Column(String(100), default="general")
    
    # Векторные представления
    embedding = Column(JSON)  # Векторное представление
    keywords = Column(JSON, default=[])  # Извлеченные ключевые слова
    
    # Метаданные
    tags = Column(JSON, default=[])
    metadata = Column(JSON, default={})
    
    # Статистика использования
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_rag_document_type', 'document_type'),
        Index('idx_rag_usage_count', 'usage_count'),
        Index('idx_rag_created', 'created_at'),
    )


class PerformanceMetrics(Base):
    """Метрики производительности"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Временные метрики
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    response_time = Column(Float)  # Время ответа в секундах
    tokens_generated = Column(Integer)  # Количество сгенерированных токенов
    tokens_processed = Column(Integer)  # Количество обработанных токенов
    
    # Качественные метрики
    quality_metrics = Column(JSON, default={})  # Детальные метрики качества
    user_feedback = Column(Float)  # Оценка пользователя (1-5)
    
    # Системные метрики
    memory_usage = Column(Float)  # Использование памяти в MB
    cpu_usage = Column(Float)  # Использование CPU в %
    gpu_usage = Column(Float)  # Использование GPU в %
    
    # Метаданные запроса
    request_type = Column(String(100))
    request_size = Column(Integer)  # Размер запроса в токенах
    route_used = Column(String(255))
    
    # Статус
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Связи
    model = relationship("LLMModel", back_populates="metrics")
    
    __table_args__ = (
        Index('idx_metrics_model_timestamp', 'model_id', 'timestamp'),
        Index('idx_metrics_response_time', 'response_time'),
        Index('idx_metrics_quality', 'quality_metrics'),
    )


class APILog(Base):
    """Лог API запросов"""
    __tablename__ = "api_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Запрос
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    query_params = Column(JSON, default={})
    request_body = Column(Text)
    request_size = Column(Integer)
    
    # Ответ
    status_code = Column(Integer, nullable=False)
    response_body = Column(Text)
    response_size = Column(Integer)
    
    # Временные метрики
    request_time = Column(DateTime(timezone=True), server_default=func.now())
    processing_time = Column(Float)  # Время обработки в секундах
    
    # Пользователь
    user_id = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Метаданные
    headers = Column(JSON, default={})
    error_details = Column(Text)
    
    __table_args__ = (
        Index('idx_api_log_method_path', 'method', 'path'),
        Index('idx_api_log_status_code', 'status_code'),
        Index('idx_api_log_request_time', 'request_time'),
        Index('idx_api_log_user', 'user_id'),
    )


class ABTest(Base):
    """A/B тест для моделей"""
    __tablename__ = "ab_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Конфигурация теста
    control_model = Column(String(255), nullable=False)  # Контрольная модель
    variant_model = Column(String(255), nullable=False)  # Тестовая модель
    traffic_split = Column(Float, default=0.5)  # Доля трафика для варианта (0.0 - 1.0)
    
    # Условия тестирования
    request_types = Column(JSON, default=[])  # Типы запросов для тестирования
    user_segments = Column(JSON, default=[])  # Сегменты пользователей
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True))
    
    # Статус
    status = Column(SQLEnum(ABTestStatus), default=ABTestStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    
    # Результаты
    control_metrics = Column(JSON, default={})
    variant_metrics = Column(JSON, default={})
    statistical_significance = Column(Float, default=0.0)
    winner = Column(String(10))  # "control", "variant", "none"
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    model = relationship("LLMModel", back_populates="ab_tests")
    
    __table_args__ = (
        Index('idx_abtest_status_active', 'status', 'is_active'),
        Index('idx_abtest_dates', 'start_date', 'end_date'),
        Index('idx_abtest_model', 'model_id'),
    )


class ModelOptimization(Base):
    """Запись об оптимизации модели"""
    __tablename__ = "model_optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Тип и параметры оптимизации
    optimization_type = Column(SQLEnum(OptimizationType), nullable=False)
    parameters = Column(JSON, default={})  # Параметры оптимизации
    target_metrics = Column(JSON, default={})  # Целевые метрики
    
    # Результаты
    before_metrics = Column(JSON, default={})  # Метрики до оптимизации
    after_metrics = Column(JSON, default={})  # Метрики после оптимизации
    improvement = Column(JSON, default={})  # Улучшения
    
    # Статус
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    error_message = Column(Text)
    
    # Метаданные
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    model = relationship("LLMModel", back_populates="optimizations")
    
    __table_args__ = (
        Index('idx_optimization_type_status', 'optimization_type', 'status'),
        Index('idx_optimization_model', 'model_id'),
        Index('idx_optimization_created', 'created_at'),
    )


class QualityAssessment(Base):
    """Оценка качества ответов"""
    __tablename__ = "quality_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Запрос и ответ
    request_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    context_documents = Column(JSON, default=[])  # Использованные документы RAG
    
    # Оценки качества
    relevance_score = Column(Float)  # Релевантность ответа
    accuracy_score = Column(Float)  # Точность информации
    coherence_score = Column(Float)  # Связность текста
    fluency_score = Column(Float)  # Беглость языка
    completeness_score = Column(Float)  # Полнота ответа
    
    # Общая оценка
    overall_score = Column(Float, nullable=False)
    
    # Детали оценки
    assessment_details = Column(JSON, default={})
    feedback_notes = Column(Text)
    
    # Метаданные
    assessed_by = Column(String(255))  # Кто оценивал (user, system, expert)
    assessment_method = Column(String(100))  # Метод оценки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_quality_model_score', 'model_id', 'overall_score'),
        Index('idx_quality_assessed_by', 'assessed_by'),
        Index('idx_quality_created', 'created_at'),
    )


class SystemHealth(Base):
    """Состояние системы"""
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Системные метрики
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    cpu_usage = Column(Float)  # Использование CPU в %
    memory_usage = Column(Float)  # Использование памяти в %
    disk_usage = Column(Float)  # Использование диска в %
    network_io = Column(JSON, default={})  # Сетевая активность
    
    # Ollama метрики
    ollama_status = Column(String(50))  # running, stopped, error
    active_models = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    
    # RAG метрики
    rag_status = Column(String(50))  # active, inactive, error
    documents_count = Column(Integer, default=0)
    vector_db_status = Column(String(50))
    
    # Общие метрики
    response_time_avg = Column(Float, default=0.0)
    requests_per_minute = Column(Float, default=0.0)
    active_connections = Column(Integer, default=0)
    
    # Алерты
    alerts = Column(JSON, default=[])
    
    __table_args__ = (
        Index('idx_health_timestamp', 'timestamp'),
        Index('idx_health_ollama_status', 'ollama_status'),
        Index('idx_health_rag_status', 'rag_status'),
    ) 