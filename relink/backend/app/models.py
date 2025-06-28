"""Модели данных для приложения."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid import uuid4
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass, field

class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass

class User(Base):
    """Модель пользователя для аутентификации."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Отношения
    domains: Mapped[List["Domain"]] = relationship("Domain", back_populates="owner")
    analyses: Mapped[List["AnalysisHistory"]] = relationship("AnalysisHistory", back_populates="user")
    diagrams: Mapped[List["Diagram"]] = relationship("Diagram", back_populates="user")
    tests: Mapped[List["Test"]] = relationship("Test", back_populates="user")
    test_executions: Mapped[List["TestExecution"]] = relationship("TestExecution", back_populates="user")
    test_suites: Mapped[List["TestSuite"]] = relationship("TestSuite", back_populates="user")
    
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
    )

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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Владелец домена
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)

    # Статистика
    total_posts: Mapped[int] = mapped_column(Integer, default=0)
    total_analyses: Mapped[int] = mapped_column(Integer, default=0)
    last_analysis_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Отношения
    owner: Mapped["User"] = relationship("User", back_populates="domains")
    posts: Mapped[List["WordPressPost"]] = relationship("WordPressPost", back_populates="domain_ref", cascade="all, delete-orphan")
    analyses: Mapped[List["AnalysisHistory"]] = relationship("AnalysisHistory", back_populates="domain_ref", cascade="all, delete-orphan")
    themes: Mapped[List["ThematicGroup"]] = relationship("ThematicGroup", back_populates="domain_ref", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_domain_name', 'name'),
        Index('idx_domain_owner', 'owner_id'),
    )

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
        Index('idx_thematic_domain', 'domain_id'),
        Index('idx_thematic_name', 'name'),
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
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Отношения
    domain_ref: Mapped["Domain"] = relationship("Domain", back_populates="posts")
    thematic_group: Mapped["ThematicGroup"] = relationship("ThematicGroup", back_populates="posts")
    embeddings: Mapped[List["ArticleEmbedding"]] = relationship("ArticleEmbedding", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_post_domain', 'domain_id'),
        Index('idx_post_thematic', 'thematic_group_id'),
        Index('idx_post_link', 'link'),
        Index('idx_post_published', 'published_at'),
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
        Index('idx_embedding_post', 'post_id'),
        Index('idx_embedding_type', 'embedding_type'),
    )

class AnalysisHistory(Base):
    """Улучшенная модель истории анализов с детальными метриками."""

    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain_id: Mapped[int] = mapped_column(Integer, ForeignKey("domains.id"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)

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
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Отношения
    domain_ref: Mapped["Domain"] = relationship("Domain", back_populates="analyses")
    user: Mapped["User"] = relationship("User", back_populates="analyses")
    diagrams: Mapped[List["Diagram"]] = relationship("Diagram", back_populates="analysis", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_analysis_domain', 'domain_id'),
        Index('idx_analysis_user', 'user_id'),
        Index('idx_analysis_created', 'created_at'),
    )

class Diagram(Base):
    """Модель для хранения SVG диаграмм."""

    __tablename__ = "diagrams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("analysis_history.id"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    
    # Основные характеристики диаграммы
    diagram_type: Mapped[str] = mapped_column(String(50))  # system_architecture, data_flow, microservices, etc.
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # SVG контент и метаданные
    svg_content: Mapped[str] = mapped_column(Text)  # сам SVG код
    svg_metadata: Mapped[dict] = mapped_column(JSON, default=dict)  # метаданные SVG
    
    # Качество и валидация
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    accessibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    performance_score: Mapped[float] = mapped_column(Float, default=0.0)
    validation_errors: Mapped[list[str]] = mapped_column(JSON, default=list)
    optimization_suggestions: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # LLM метаданные
    llm_model_used: Mapped[str] = mapped_column(String(100))
    generation_time_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Компоненты и связи (для RAG)
    components: Mapped[list[dict]] = mapped_column(JSON, default=list)
    relationships: Mapped[list[dict]] = mapped_column(JSON, default=list)
    style_config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Статус и версионирование
    status: Mapped[str] = mapped_column(String(20), default="generated")  # generated, validated, optimized, archived
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Временные метки
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    analysis: Mapped["AnalysisHistory"] = relationship("AnalysisHistory", back_populates="diagrams")
    user: Mapped["User"] = relationship("User", back_populates="diagrams")
    embeddings: Mapped[List["DiagramEmbedding"]] = relationship("DiagramEmbedding", back_populates="diagram", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_diagram_analysis', 'analysis_id'),
        Index('idx_diagram_user', 'user_id'),
        Index('idx_diagram_type', 'diagram_type'),
        Index('idx_diagram_status', 'status'),
        Index('idx_diagram_created', 'created_at'),
    )

class DiagramEmbedding(Base):
    """Модель эмбеддингов для диаграмм (для RAG поиска)."""

    __tablename__ = "diagram_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    diagram_id: Mapped[int] = mapped_column(Integer, ForeignKey("diagrams.id"), index=True)
    
    # Типы эмбеддингов
    embedding_type: Mapped[str] = mapped_column(String(50))  # 'title', 'description', 'components', 'full'
    vector_model: Mapped[str] = mapped_column(String(100))
    embedding_vector: Mapped[str] = mapped_column(Text)  # JSON вектора
    dimension: Mapped[int] = mapped_column(Integer)
    
    # Контекст для RAG
    context_text: Mapped[str] = mapped_column(Text)  # текст, из которого создан эмбеддинг
    semantic_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Отношения
    diagram: Mapped["Diagram"] = relationship("Diagram", back_populates="embeddings")

    __table_args__ = (
        Index('idx_diagram_embedding_diagram', 'diagram_id'),
        Index('idx_diagram_embedding_type', 'embedding_type'),
    )

class DiagramTemplate(Base):
    """Модель шаблонов для диаграмм."""

    __tablename__ = "diagram_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Основные характеристики шаблона
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    diagram_type: Mapped[str] = mapped_column(String(50))
    
    # Шаблон и конфигурация
    prompt_template: Mapped[str] = mapped_column(Text)
    default_style: Mapped[dict] = mapped_column(JSON, default=dict)
    example_svg: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Метаданные
    author: Mapped[str] = mapped_column(String(100), nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Статистика использования
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_template_name', 'name'),
        Index('idx_template_type', 'diagram_type'),
        Index('idx_template_active', 'is_active'),
    )

# ============================================================================
# МОДЕЛИ ДЛЯ СИСТЕМЫ ТЕСТИРОВАНИЯ
# ============================================================================

class TestType(str, Enum):
    """Типы тестов"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    LOAD = "load"
    SECURITY = "security"
    API = "api"
    UI = "ui"
    E2E = "e2e"
    BENCHMARK = "benchmark"
    SEO = "seo"
    LLM = "llm"


class TestStatus(str, Enum):
    """Статусы тестов"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TestPriority(str, Enum):
    """Приоритеты тестов"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestEnvironment(str, Enum):
    """Окружения для тестирования"""
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TestRequest(BaseModel):
    """Запрос на создание теста"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    test_type: TestType
    priority: TestPriority = TestPriority.MEDIUM
    environment: TestEnvironment = TestEnvironment.LOCAL
    timeout: Optional[int] = Field(None, ge=1, le=3600)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    retry_count: int = Field(default=0, ge=0, le=5)
    parallel: bool = Field(default=False)
    dependencies: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)


class TestResult(BaseModel):
    """Результат выполнения теста"""
    test_id: str
    status: TestStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration: Optional[float] = Field(None, ge=0)
    passed: Optional[int] = Field(None, ge=0)
    failed: Optional[int] = Field(None, ge=0)
    skipped: Optional[int] = Field(None, ge=0)
    total: Optional[int] = Field(None, ge=0)
    message: Optional[str] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    memory_usage: Optional[float] = Field(None, ge=0)
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    test_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TestExecution(BaseModel):
    """Выполнение теста"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    test_request: Optional[TestRequest] = None
    status: TestStatus = TestStatus.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    results: List[TestResult] = Field(default_factory=list)
    user_id: Optional[int] = None
    test_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TestSuite(BaseModel):
    """Набор тестов"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tests: List[TestRequest] = Field(..., min_items=1)
    parallel: bool = Field(default=False)
    stop_on_failure: bool = Field(default=False)
    timeout: Optional[int] = Field(None, ge=1, le=7200)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TestReport(BaseModel):
    """Отчет о тестировании"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    execution_id: str
    total_tests: int = Field(..., ge=0)
    passed_tests: int = Field(..., ge=0)
    failed_tests: int = Field(..., ge=0)
    skipped_tests: int = Field(..., ge=0)
    total_duration: float = Field(..., ge=0)
    average_duration: float = Field(..., ge=0)
    success_rate: float = Field(..., ge=0, le=100)
    results: List[TestResult]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    test_metadata: Dict[str, Any] = Field(default_factory=dict)


class TestMetrics(BaseModel):
    """Метрики тестирования"""
    execution_id: str
    response_time_avg: float = Field(..., ge=0)
    response_time_min: float = Field(..., ge=0)
    response_time_max: float = Field(..., ge=0)
    response_time_std: float = Field(..., ge=0)
    memory_usage_avg: float = Field(..., ge=0)
    cpu_usage_avg: float = Field(..., ge=0, le=100)
    throughput: float = Field(..., ge=0)
    error_rate: float = Field(..., ge=0, le=100)
    collected_at: datetime = Field(default_factory=datetime.utcnow)


class TestFilter(BaseModel):
    """Фильтр для поиска тестов"""
    test_type: Optional[TestType] = None
    status: Optional[TestStatus] = None
    priority: Optional[TestPriority] = None
    environment: Optional[TestEnvironment] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    name_contains: Optional[str] = None
    description_contains: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")


class TestResponse(BaseModel):
    """Ответ с информацией о тесте"""
    id: str
    name: str
    description: Optional[str]
    test_type: TestType
    priority: TestPriority
    environment: TestEnvironment
    status: TestStatus
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    test_metadata: Dict[str, Any]


class TestExecutionResponse(BaseModel):
    """Ответ с информацией о выполнении теста"""
    id: str
    test_request: Optional[TestRequest]
    status: TestStatus
    progress: float
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    results: List[TestResult]
    user_id: Optional[int]
    test_metadata: Dict[str, Any]


class TestSuiteRequest(BaseModel):
    """Запрос на создание набора тестов"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tests: List[TestRequest] = Field(..., min_items=1)
    parallel: bool = Field(default=False)
    stop_on_failure: bool = Field(default=False)
    timeout: Optional[int] = Field(None, ge=1, le=7200)
    tags: List[str] = Field(default_factory=list)


class TestSuiteResponse(BaseModel):
    """Ответ с информацией о наборе тестов"""
    id: str
    name: str
    description: Optional[str]
    tests: List[TestRequest]
    parallel: bool
    stop_on_failure: bool
    timeout: Optional[int]
    tags: List[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# МОДЕЛИ БАЗЫ ДАННЫХ ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================================

class Test(Base):
    """Модель теста в базе данных"""
    __tablename__ = "tests"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="local")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    timeout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parallel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dependencies: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Связи
    user: Mapped[Optional["User"]] = relationship("User", back_populates="tests")
    executions: Mapped[List["TestExecution"]] = relationship("TestExecution", back_populates="test", cascade="all, delete-orphan")


class TestExecution(Base):
    """Модель выполнения теста в базе данных"""
    __tablename__ = "test_executions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    test_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tests.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    test_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Связи
    test: Mapped[Optional["Test"]] = relationship("Test", back_populates="executions")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="test_executions")
    results: Mapped[List["TestResult"]] = relationship("TestResult", back_populates="execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_execution_test', 'test_id'),
        Index('idx_execution_user', 'user_id'),
        Index('idx_execution_status', 'status'),
        Index('idx_execution_created', 'created_at'),
    )


class TestResult(Base):
    """Модель результата теста в базе данных"""
    __tablename__ = "test_results"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_executions.id"), nullable=False)
    test_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    passed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    failed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    skipped: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    memory_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Связи
    execution: Mapped["TestExecution"] = relationship("TestExecution", back_populates="results")


class TestSuite(Base):
    """Модель набора тестов в базе данных"""
    __tablename__ = "test_suites"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tests: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    parallel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stop_on_failure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    timeout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Связи
    user: Mapped[Optional["User"]] = relationship("User", back_populates="test_suites")


class TestReport(Base):
    """Модель отчета о тестировании в базе данных"""
    __tablename__ = "test_reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_executions.id"), nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False)
    passed_tests: Mapped[int] = mapped_column(Integer, nullable=False)
    failed_tests: Mapped[int] = mapped_column(Integer, nullable=False)
    skipped_tests: Mapped[int] = mapped_column(Integer, nullable=False)
    total_duration: Mapped[float] = mapped_column(Float, nullable=False)
    average_duration: Mapped[float] = mapped_column(Float, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    results: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    test_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Связи
    execution: Mapped["TestExecution"] = relationship("TestExecution")


# Обновляем модель User для связи с тестами
User.tests = relationship("Test", back_populates="user")
User.test_executions = relationship("TestExecution", back_populates="user")
User.test_suites = relationship("TestSuite", back_populates="user")

class LLMServiceType(Enum):
    SEO_RECOMMENDATIONS = "seo_recommendations"
    DIAGRAM_GENERATION = "diagram_generation"
    CONTENT_ANALYSIS = "content_analysis"
    BENCHMARK_SERVICE = "benchmark_service"
    LLM_TUNING = "llm_tuning"

@dataclass
class LLMRequest:
    service_type: LLMServiceType
    prompt: str
    context: Optional[Dict[str, Any]] = None
    model: str = "qwen2.5:7b-instruct-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048
    use_rag: bool = True
    cache_ttl: int = 3600
    priority: int = 1

@dataclass
class LLMResponse:
    content: str
    service_type: LLMServiceType
    model_used: str
    tokens_used: int
    response_time: float
    cached: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LLMEmbedding:
    embedding: List[float]
    model: str
    created_at: Optional[str] = None 