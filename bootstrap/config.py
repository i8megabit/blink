"""
🔧 Конфигурация для всех микросервисов reLink
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Настройки для всех микросервисов"""
    
    # Основные настройки сервиса
    SERVICE_NAME: str = Field(default="unknown", description="Имя микросервиса")
    SERVICE_PORT: int = Field(default=8000, description="Порт сервиса")
    DEBUG: bool = Field(default=False, description="Режим отладки")
    
    # База данных
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://seo_user:seo_pass@db:5432/seo_db",
        description="URL подключения к БД"
    )
    DB_HOST: str = Field(default="db", description="Хост БД")
    DB_USER: str = Field(default="seo_user", description="Пользователь БД")
    DB_PASSWORD: str = Field(default="seo_pass", description="Пароль БД")
    DB_NAME: str = Field(default="seo_db", description="Имя БД")
    
    # Redis
    REDIS_HOST: str = Field(default="redis", description="Хост Redis")
    REDIS_PORT: int = Field(default=6379, description="Порт Redis")
    REDIS_DB: int = Field(default=0, description="Номер БД Redis")
    REDIS_URL: str = Field(
        default="redis://redis:6379",
        description="URL подключения к Redis"
    )
    CACHE_TTL: int = Field(default=3600, description="TTL кеша в секундах")
    CACHE_PREFIX: str = Field(default="service_", description="Префикс кеша")
    
    # LLM и AI
    OLLAMA_URL: str = Field(
        default="http://ollama:11434",
        description="URL Ollama сервера"
    )
    OLLAMA_MODEL: str = Field(
        default="qwen2.5:7b-instruct-turbo",
        description="Модель Ollama по умолчанию"
    )
    
    # LLM Router
    LLM_ROUTER_URL: str = Field(
        default="http://llm-router:8007",
        description="URL LLM роутера"
    )
    
    # RAG Service
    RAG_SERVICE_URL: str = Field(
        default="http://rag-service:8008",
        description="URL RAG сервиса"
    )
    
    # Безопасность
    SECRET_KEY: str = Field(
        default="your-super-secret-key-for-jwt-tokens-2024",
        description="Секретный ключ для JWT"
    )
    
    # Логирование
    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")
    LOG_FORMAT: str = Field(default="json", description="Формат логов")
    
    # Мониторинг
    METRICS_ENABLED: bool = Field(default=True, description="Включение метрик")
    PROMETHEUS_PORT: int = Field(default=9090, description="Порт Prometheus")
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://frontend:80",
        description="Разрешенные CORS origins"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Глобальный экземпляр настроек
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Получение глобального экземпляра настроек"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 