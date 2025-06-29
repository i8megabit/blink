"""
🔧 Конфигурация для всех микросервисов reLink
RAG-ориентированная архитектура с ChromaDB
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
    
    # ChromaDB - основная база данных
    CHROMADB_URL: str = Field(
        default="http://chromadb:8000",
        description="URL подключения к ChromaDB"
    )
    CHROMADB_HOST: str = "chromadb"
    CHROMADB_PORT: int = 8000  # Внутренний порт в контейнере
    CHROMADB_COLLECTION: str = Field(
        default="relink_collection",
        description="Коллекция ChromaDB"
    )
    CHROMADB_AUTH_TOKEN: Optional[str] = None
    
    # Redis кеширование
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        description="URL подключения к Redis"
    )
    REDIS_HOST: str = Field(default="redis", description="Хост Redis")
    REDIS_PORT: int = Field(default=6379, description="Порт Redis")
    REDIS_DB: int = Field(default=0, description="База данных Redis")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Пароль Redis")
    
    # Ollama LLM
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_HOST: str = Field(default="ollama", description="Хост Ollama")
    OLLAMA_PORT: int = Field(default=11434, description="Порт Ollama")
    OLLAMA_MODEL: str = Field(
        default="qwen2.5:7b-instruct-turbo",
        description="Модель по умолчанию"
    )
    OLLAMA_TIMEOUT: int = 120  # Увеличенный timeout для больших моделей
    
    # LLM Router
    LLM_ROUTER_URL: str = Field(
        default="http://router:8001",
        description="URL LLM роутера"
    )
    
    # RAG Service
    RAG_SERVICE_URL: str = Field(
        default="http://chromadb:8000",
        description="URL RAG сервиса"
    )
    
    # Мониторинг
    PROMETHEUS_PORT: int = Field(default=9090, description="Порт Prometheus")
    METRICS_ENABLED: bool = Field(default=True, description="Включить метрики")
    
    # Логирование
    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")
    LOG_FORMAT: str = Field(
        default="json",
        description="Формат логов (json/text)"
    )
    
    # Безопасность
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Секретный ключ"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Время жизни токена доступа"
    )
    
    # CORS
    CORS_ORIGINS: list = Field(
        default=["http://localhost:3000", "http://frontend:3000"],
        description="Разрешенные CORS origins"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Глобальный экземпляр настроек
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Получение глобального экземпляра настроек"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 