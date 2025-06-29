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
    CHROMADB_HOST: str = Field(default="chromadb", description="Хост ChromaDB")
    CHROMADB_PORT: int = Field(default=8000, description="Порт ChromaDB")
    CHROMADB_PERSIST_DIR: str = Field(
        default="./chromadb_persist",
        description="Директория для персистентности ChromaDB"
    )
    
    # Redis
    REDIS_HOST: str = Field(default="redis", description="Хост Redis")
    REDIS_PORT: int = Field(default=6379, description="Порт Redis")
    REDIS_DB: int = Field(default=0, description="Номер БД Redis")
    REDIS_PASSWORD: str = Field(default="relink_redis_pass", description="Пароль Redis")
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
        default="http://router:8001",
        description="URL LLM роутера"
    )
    
    # RAG Service
    RAG_SERVICE_URL: str = Field(
        default="http://chromadb:8000",
        description="URL RAG сервиса (ChromaDB)"
    )
    
    # Векторные настройки
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Модель для эмбеддингов"
    )
    VECTOR_CHUNK_SIZE: int = Field(default=1000, description="Размер чанков для векторизации")
    VECTOR_CHUNK_OVERLAP: int = Field(default=200, description="Перекрытие чанков")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, description="Порог схожести для поиска")
    
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