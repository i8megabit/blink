"""
Конфигурация микросервиса документации
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    app_name: str = "SEO Documentation Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Настройки сервера
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    
    # Redis настройки
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Настройки кэширования
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 час
    cache_prefix: str = Field(default="docs:", env="CACHE_PREFIX")
    
    # Настройки документации
    docs_path: str = Field(default="/app/static", env="DOCS_PATH")
    version_file: str = Field(default="/app/VERSION", env="VERSION_FILE")
    readme_file: str = Field(default="/app/README.md", env="README_FILE")
    
    # CORS настройки
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://frontend:80"],
        env="CORS_ORIGINS"
    )
    
    # Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Создаем экземпляр настроек
settings = Settings()


def get_redis_url() -> str:
    """Получение URL для подключения к Redis"""
    if settings.redis_password:
        return f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def get_cache_key(prefix: str, key: str) -> str:
    """Формирование ключа кэша"""
    return f"{settings.cache_prefix}{prefix}:{key}" 