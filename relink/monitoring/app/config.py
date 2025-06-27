"""
Конфигурация микросервиса мониторинга
Настройки для всех компонентов системы мониторинга
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field, validator
from pydantic.types import SecretStr


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    url: str = Field(
        default="postgresql+asyncpg://seo_user:seo_pass@db:5432/seo_db",
        env="DATABASE_URL"
    )
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, env="DB_ECHO")
    
    class Config:
        env_prefix = "DB_"


class RedisSettings(BaseSettings):
    """Настройки Redis"""
    host: str = Field(default="redis", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[SecretStr] = Field(default=None, env="REDIS_PASSWORD")
    ssl: bool = Field(default=False, env="REDIS_SSL")
    
    @property
    def url(self) -> str:
        """Получение URL для подключения к Redis"""
        if self.password:
            return f"redis://:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class OllamaSettings(BaseSettings):
    """Настройки Ollama"""
    url: str = Field(
        default="http://ollama:11434",
        env="OLLAMA_URL"
    )
    timeout: int = Field(default=300, env="OLLAMA_TIMEOUT")
    max_retries: int = Field(default=3, env="OLLAMA_MAX_RETRIES")
    
    class Config:
        env_prefix = "OLLAMA_"


class PrometheusSettings(BaseSettings):
    """Настройки Prometheus"""
    enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    port: int = Field(default=9090, env="PROMETHEUS_PORT")
    path: str = Field(default="/metrics", env="PROMETHEUS_PATH")
    
    class Config:
        env_prefix = "PROMETHEUS_"


class LoggingSettings(BaseSettings):
    """Настройки логирования"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
    file: Optional[str] = Field(default=None, env="LOG_FILE")
    max_size: int = Field(default=100, env="LOG_MAX_SIZE")  # MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    @validator("level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"


class APISettings(BaseSettings):
    """Настройки API"""
    title: str = Field(default="reLink Monitoring API", env="API_TITLE")
    description: str = Field(
        default="High-performance monitoring microservice for reLink platform",
        env="API_DESCRIPTION"
    )
    version: str = Field(default="1.0.0", env="API_VERSION")
    docs_url: str = Field(default="/docs", env="API_DOCS_URL")
    redoc_url: str = Field(default="/redoc", env="API_REDOC_URL")
    
    class Config:
        env_prefix = "API_"


class MonitoringSettings(BaseSettings):
    """Настройки мониторинга"""
    # Интервалы сбора метрик
    system_metrics_interval: int = Field(default=30, env="MONITORING_SYSTEM_INTERVAL")
    database_metrics_interval: int = Field(default=60, env="MONITORING_DB_INTERVAL")
    ollama_metrics_interval: int = Field(default=30, env="MONITORING_OLLAMA_INTERVAL")
    cache_metrics_interval: int = Field(default=15, env="MONITORING_CACHE_INTERVAL")
    
    # Пороги для алертов
    cpu_threshold: float = Field(default=80.0, env="MONITORING_CPU_THRESHOLD")
    memory_threshold: float = Field(default=85.0, env="MONITORING_MEMORY_THRESHOLD")
    disk_threshold: float = Field(default=90.0, env="MONITORING_DISK_THRESHOLD")
    response_time_threshold: float = Field(default=5.0, env="MONITORING_RESPONSE_TIME_THRESHOLD")
    
    # Настройки алертов
    alerts_enabled: bool = Field(default=True, env="MONITORING_ALERTS_ENABLED")
    alert_cooldown: int = Field(default=300, env="MONITORING_ALERT_COOLDOWN")  # 5 минут
    
    # Настройки дашборда
    dashboard_refresh_interval: int = Field(default=10, env="MONITORING_DASHBOARD_REFRESH")
    history_retention_days: int = Field(default=30, env="MONITORING_HISTORY_RETENTION")
    
    class Config:
        env_prefix = "MONITORING_"


class SecuritySettings(BaseSettings):
    """Настройки безопасности"""
    secret_key: SecretStr = Field(
        default=SecretStr("your-secret-key-change-in-production"),
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="SECURITY_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="SECURITY_ACCESS_TOKEN_EXPIRE")
    
    # CORS настройки
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://frontend:80"],
        env="CORS_ORIGINS"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_METHODS"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        env="CORS_HEADERS"
    )
    
    class Config:
        env_prefix = "SECURITY_"


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Окружение
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Порт сервера
    port: int = Field(default=8002, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    
    # Настройки компонентов
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    ollama: OllamaSettings = OllamaSettings()
    prometheus: PrometheusSettings = PrometheusSettings()
    logging: LoggingSettings = LoggingSettings()
    api: APISettings = APISettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    security: SecuritySettings = SecuritySettings()
    
    # Настройки кэширования
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_prefix: str = Field(default="monitoring:", env="CACHE_PREFIX")
    
    # Настройки производительности
    workers: int = Field(default=1, env="WORKERS")
    max_connections: int = Field(default=1000, env="MAX_CONNECTIONS")
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Создание экземпляра настроек
settings = Settings()

# Экспорт для удобства
__all__ = ["settings", "Settings"] 