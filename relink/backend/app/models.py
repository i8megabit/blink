"""Модели данных для приложения."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

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

    __table_args__ = (
        Index('idx_analysis_domain', 'domain_id'),
        Index('idx_analysis_user', 'user_id'),
        Index('idx_analysis_created', 'created_at'),
    ) 