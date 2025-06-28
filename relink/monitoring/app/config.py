"""
Конфигурация микросервиса мониторинга
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    url: str = Field(default="postgresql+asyncpg://seo_user:seo_pass@db:5432/seo_db", env="DATABASE_URL")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, env="DB_ECHO")


class RedisSettings(BaseSettings):
    """Настройки Redis"""
    host: str = Field(default="redis", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    ttl: int = Field(default=3600, env="CACHE_TTL")
    prefix: str = Field(default="monitoring:", env="CACHE_PREFIX")


class OllamaSettings(BaseSettings):
    """Настройки Ollama"""
    url: str = Field(default="http://ollama:11434", env="OLLAMA_URL")
    timeout: int = Field(default=300, env="OLLAMA_TIMEOUT")
    models: List[str] = Field(default=["qwen2.5:7b-instruct-turbo"], env="OLLAMA_MODELS")


class PrometheusSettings(BaseSettings):
    """Настройки Prometheus"""
    enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    port: int = Field(default=9090, env="PROMETHEUS_PORT")
    path: str = Field(default="/metrics", env="PROMETHEUS_PATH")


class LoggingSettings(BaseSettings):
    """Настройки логирования"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
    file: Optional[str] = Field(default=None, env="LOG_FILE")


class APISettings(BaseSettings):
    """Настройки API"""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8002, env="API_PORT")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://frontend:80"],
        env="CORS_ORIGINS"
    )
    rate_limit: int = Field(default=100, env="RATE_LIMIT")


class MonitoringSettings(BaseSettings):
    """Настройки мониторинга"""
    collect_interval: int = Field(default=30, env="COLLECT_INTERVAL")
    retention_days: int = Field(default=30, env="RETENTION_DAYS")
    alert_thresholds: dict = Field(
        default={
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 2.0,
            "error_rate": 5.0
        },
        env="ALERT_THRESHOLDS"
    )


class SecuritySettings(BaseSettings):
    """Настройки безопасности"""
    secret_key: str = Field(default="your-secret-key", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Основные настройки
    app_name: str = Field(default="reLink Monitoring", env="APP_NAME")
    version: str = Field(default="1.0.0", env="VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Компоненты
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    ollama: OllamaSettings = OllamaSettings()
    prometheus: PrometheusSettings = PrometheusSettings()
    logging: LoggingSettings = LoggingSettings()
    api: APISettings = APISettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    security: SecuritySettings = SecuritySettings()
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Создание экземпляра настроек
settings = Settings() 