"""
Модуль управления конфигурацией приложения
Поддерживает переменные окружения, валидацию и типизацию
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, validator, Field
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="blink_db", env="DB_NAME")
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


class SecuritySettings(BaseSettings):
    """Настройки безопасности"""
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v


class OllamaSettings(BaseSettings):
    """Настройки Ollama"""
    base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    model_name: str = Field(default="qwen2.5:7b", env="OLLAMA_MODEL")
    timeout: int = Field(default=300, env="OLLAMA_TIMEOUT")
    max_tokens: int = Field(default=2048, env="OLLAMA_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OLLAMA_TEMPERATURE")
    keep_alive: str = Field(default="2h", env="OLLAMA_KEEP_ALIVE")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class MonitoringSettings(BaseSettings):
    """Настройки мониторинга"""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    jaeger_host: Optional[str] = Field(default=None, env="JAEGER_HOST")
    jaeger_port: int = Field(default=6831, env="JAEGER_PORT")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()


class CacheSettings(BaseSettings):
    """Настройки кэширования"""
    default_ttl: int = Field(default=300, env="CACHE_DEFAULT_TTL")
    max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    enable_redis: bool = Field(default=True, env="CACHE_ENABLE_REDIS")
    enable_memory: bool = Field(default=True, env="CACHE_ENABLE_MEMORY")
    compression_threshold: int = Field(default=1024, env="CACHE_COMPRESSION_THRESHOLD")


class APISettings(BaseSettings):
    """Настройки API"""
    title: str = Field(default="Blink SEO API", env="API_TITLE")
    version: str = Field(default="1.0.0", env="API_VERSION")
    description: str = Field(default="Advanced SEO Analysis Platform", env="API_DESCRIPTION")
    docs_url: str = Field(default="/docs", env="API_DOCS_URL")
    redoc_url: str = Field(default="/redoc", env="API_REDOC_URL")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")


class Settings(BaseSettings):
    """Основные настройки приложения"""
    # Окружение
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Подмодули
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    ollama: OllamaSettings = OllamaSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    cache: CacheSettings = CacheSettings()
    api: APISettings = APISettings()
    
    # Дополнительные настройки
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: list = Field(default=[".txt", ".html", ".xml", ".json"], env="ALLOWED_FILE_TYPES")
    temp_dir: str = Field(default="/tmp", env="TEMP_DIR")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v
    
    @property
    def is_production(self) -> bool:
        """Проверка, является ли окружение продакшн"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Проверка, является ли окружение разработкой"""
        return self.environment == "development"
    
    def get_database_url(self) -> str:
        """Получение URL базы данных"""
        return self.database.url
    
    def get_redis_url(self) -> str:
        """Получение URL Redis"""
        return self.redis.url
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование настроек в словарь"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "username": self.database.username,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "db": self.redis.db,
                "max_connections": self.redis.max_connections,
            },
            "ollama": {
                "base_url": self.ollama.base_url,
                "model_name": self.ollama.model_name,
                "timeout": self.ollama.timeout,
                "temperature": self.ollama.temperature,
            },
            "monitoring": {
                "log_level": self.monitoring.log_level,
                "enable_metrics": self.monitoring.enable_metrics,
                "enable_tracing": self.monitoring.enable_tracing,
            },
            "cache": {
                "default_ttl": self.cache.default_ttl,
                "max_size": self.cache.max_size,
                "enable_redis": self.cache.enable_redis,
                "enable_memory": self.cache.enable_memory,
            },
        }


@lru_cache()
def get_settings() -> Settings:
    """Получение настроек с кэшированием"""
    try:
        settings = Settings()
        logger.info(f"Loaded settings for environment: {settings.environment}")
        return settings
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise


def reload_settings() -> Settings:
    """Перезагрузка настроек"""
    get_settings.cache_clear()
    return get_settings()


# Экспорт настроек
settings = get_settings() 