"""
Конфигурация микросервиса документации
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    app_name: str = "SEO Link Recommender Documentation Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Сервер
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    
    # Redis настройки
    redis_url: str = Field(default="redis://redis:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    
    # Кэширование
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 час
    cache_prefix: str = Field(default="docs:", env="CACHE_PREFIX")
    
    # Документация
    docs_path: str = Field(default="/app", env="DOCS_PATH")
    version_file: str = Field(default="/app/VERSION", env="VERSION_FILE")
    readme_file: str = Field(default="/app/README.md", env="README_FILE")
    roadmap_file: str = Field(default="/app/TECHNICAL_ROADMAP.md", env="ROADMAP_FILE")
    cicd_file: str = Field(default="/app/CI_CD_SETUP.md", env="CICD_FILE")
    
    # API настройки
    api_prefix: str = "/api/v1"
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    # Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Безопасность
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()


def get_redis_url() -> str:
    """Получение URL для подключения к Redis"""
    if settings.redis_password:
        return f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def get_cache_key(prefix: str, key: str) -> str:
    """Формирование ключа кэша"""
    return f"{settings.cache_prefix}{prefix}:{key}" 