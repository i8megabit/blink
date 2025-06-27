"""
Модуль управления конфигурацией приложения
Поддерживает переменные окружения, валидацию и типизацию
"""

import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import validator, Field
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="relink_db", env="DB_NAME")
    username: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, env="DB_ECHO")
    
    @property
    def url(self) -> str:
        """URL подключения к базе данных"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def sync_url(self) -> str:
        """Синхронный URL подключения к базе данных"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    """Настройки Redis"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    
    @property
    def url(self) -> str:
        """URL подключения к Redis"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class OllamaSettings(BaseSettings):
    """Настройки Ollama"""
    url: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    model: str = Field(default="qwen2.5:7b-turbo", env="OLLAMA_MODEL")
    timeout: int = Field(default=300, env="OLLAMA_TIMEOUT")
    max_tokens: int = Field(default=4096, env="OLLAMA_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OLLAMA_TEMPERATURE")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL должен начинаться с http:// или https://')
        return v.rstrip('/')


class SecuritySettings(BaseSettings):
    """Настройки безопасности"""
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY должен быть не менее 32 символов')
        return v


class APISettings(BaseSettings):
    """Настройки API"""
    title: str = Field(default="reLink SEO API", env="API_TITLE")
    description: str = Field(default="AI-powered SEO platform API", env="API_DESCRIPTION")
    version: str = Field(default="1.0.0", env="API_VERSION")
    debug: bool = Field(default=False, env="API_DEBUG")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")


class MonitoringSettings(BaseSettings):
    """Настройки мониторинга"""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")


class CacheSettings(BaseSettings):
    """Настройки кэширования"""
    default_ttl: int = Field(default=3600, env="CACHE_DEFAULT_TTL")
    max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    enable_redis: bool = Field(default=True, env="CACHE_ENABLE_REDIS")
    enable_memory: bool = Field(default=True, env="CACHE_ENABLE_MEMORY")


class Settings(BaseSettings):
    """Основные настройки приложения"""
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Подмодули настроек
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    ollama: OllamaSettings = OllamaSettings()
    security: SecuritySettings = SecuritySettings()
    api: APISettings = APISettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    cache: CacheSettings = CacheSettings()
    
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['development', 'testing', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment должен быть одним из: {allowed}')
        return v
    
    def is_development(self) -> bool:
        """Проверка, что это среда разработки"""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Проверка, что это продакшн среда"""
        return self.environment == "production"
    
    def is_testing(self) -> bool:
        """Проверка, что это тестовая среда"""
        return self.environment == "testing"


@lru_cache()
def get_settings() -> Settings:
    """Получение настроек с кэшированием"""
    try:
        settings = Settings()
        logger.info(f"Настройки загружены для среды: {settings.environment}")
        return settings
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {e}")
        raise


# Глобальный экземпляр настроек
settings = get_settings()


def reload_settings():
    """Перезагрузка настроек (для тестирования)"""
    global settings
    get_settings.cache_clear()
    settings = get_settings()
    return settings


# Экспорт для обратной совместимости
RelinkSettings = Settings 