"""
Конфигурация микросервиса тестирования reLink
"""

import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    url: str = Field(default="postgresql://user:pass@localhost:5432/testing")
    pool_size: int = Field(default=10, ge=1, le=50)
    max_overflow: int = Field(default=20, ge=0, le=100)
    echo: bool = Field(default=False)
    
    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class RedisSettings(BaseSettings):
    """Настройки Redis"""
    url: str = Field(default="redis://localhost:6379")
    pool_size: int = Field(default=10, ge=1, le=50)
    decode_responses: bool = Field(default=False)
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")


class SecuritySettings(BaseSettings):
    """Настройки безопасности"""
    secret_key: str = Field(default="your-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class TestingSettings(BaseSettings):
    """Настройки тестирования"""
    default_timeout: int = Field(default=30, ge=1, le=300)
    max_concurrent_tests: int = Field(default=10, ge=1, le=100)
    test_data_dir: str = Field(default="./test_data")
    reports_dir: str = Field(default="./reports")
    
    # Настройки для разных типов тестов
    unit_test_timeout: int = Field(default=5, ge=1, le=60)
    integration_test_timeout: int = Field(default=30, ge=1, le=300)
    performance_test_timeout: int = Field(default=300, ge=1, le=3600)
    load_test_timeout: int = Field(default=600, ge=1, le=7200)
    
    # Настройки для бенчмарков
    benchmark_iterations: int = Field(default=100, ge=1, le=10000)
    benchmark_warmup_runs: int = Field(default=10, ge=0, le=1000)
    
    model_config = SettingsConfigDict(env_prefix="TESTING_")


class MonitoringSettings(BaseSettings):
    """Настройки мониторинга"""
    enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090, ge=1024, le=65535)
    log_level: str = Field(default="INFO")
    prometheus_enabled: bool = Field(default=True)
    
    model_config = SettingsConfigDict(env_prefix="MONITORING_")


class APISettings(BaseSettings):
    """Настройки API"""
    title: str = Field(default="reLink Testing Service")
    description: str = Field(default="Мощный сервис тестирования для reLink")
    version: str = Field(default="1.0.0")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    
    # CORS настройки
    cors_origins: List[str] = Field(default=["*"])
    cors_methods: List[str] = Field(default=["*"])
    cors_headers: List[str] = Field(default=["*"])
    
    model_config = SettingsConfigDict(env_prefix="API_")


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Основные настройки
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8003, ge=1024, le=65535)
    workers: int = Field(default=4, ge=1, le=16)
    
    # CORS и безопасность
    allowed_origins: List[str] = Field(default=["*"])
    allowed_hosts: List[str] = Field(default=["*"])
    auth_required: bool = Field(default=False)
    
    # Поднастройки
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    testing: TestingSettings = TestingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
"""
Конфигурация микросервиса тестирования reLink
"""

import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    url: str = Field(default="postgresql://user:pass@localhost:5432/testing")
    pool_size: int = Field(default=10, ge=1, le=50)
    max_overflow: int = Field(default=20, ge=0, le=100)
    echo: bool = Field(default=False)
    
    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class RedisSettings(BaseSettings):
    """Настройки Redis"""
    url: str = Field(default="redis://localhost:6379")
    pool_size: int = Field(default=10, ge=1, le=50)
    decode_responses: bool = Field(default=False)
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")


class SecuritySettings(BaseSettings):
    """Настройки безопасности"""
    secret_key: str = Field(default="your-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    
    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class TestingSettings(BaseSettings):
    """Настройки тестирования"""
    default_timeout: int = Field(default=30, ge=1, le=300)
    max_concurrent_tests: int = Field(default=10, ge=1, le=100)
    test_data_dir: str = Field(default="./test_data")
    reports_dir: str = Field(default="./reports")
    
    # Настройки для разных типов тестов
    unit_test_timeout: int = Field(default=5, ge=1, le=60)
    integration_test_timeout: int = Field(default=30, ge=1, le=300)
    performance_test_timeout: int = Field(default=300, ge=1, le=3600)
    load_test_timeout: int = Field(default=600, ge=1, le=7200)
    
    # Настройки для бенчмарков
    benchmark_iterations: int = Field(default=100, ge=1, le=10000)
    benchmark_warmup_runs: int = Field(default=10, ge=0, le=1000)
    
    model_config = SettingsConfigDict(env_prefix="TESTING_")


class MonitoringSettings(BaseSettings):
    """Настройки мониторинга"""
    enabled: bool = Field(default=True)
    metrics_port: int = Field(default=9090, ge=1024, le=65535)
    log_level: str = Field(default="INFO")
    prometheus_enabled: bool = Field(default=True)
    
    model_config = SettingsConfigDict(env_prefix="MONITORING_")


class APISettings(BaseSettings):
    """Настройки API"""
    title: str = Field(default="reLink Testing Service")
    description: str = Field(default="Мощный сервис тестирования для reLink")
    version: str = Field(default="1.0.0")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    
    # CORS настройки
    cors_origins: List[str] = Field(default=["*"])
    cors_methods: List[str] = Field(default=["*"])
    cors_headers: List[str] = Field(default=["*"])
    
    model_config = SettingsConfigDict(env_prefix="API_")


class Settings(BaseSettings):
    """Основные настройки приложения"""
    
    # Основные настройки
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8003, ge=1024, le=65535)
    workers: int = Field(default=4, ge=1, le=16)
    
    # Поднастройки
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    testing: TestingSettings = TestingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    api: APISettings = APISettings()
    
    # Валидация
    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production", "testing"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("debug")
    def validate_debug(cls, v, values):
        if values.get("environment") == "production" and v:
            raise ValueError("Debug mode cannot be enabled in production")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Создание экземпляра настроек
settings = Settings()


def get_settings() -> Settings:
    """Получение настроек приложения"""
    return settings


def is_development() -> bool:
    """Проверка, что приложение запущено в режиме разработки"""
    return settings.environment == "development"


def is_production() -> bool:
    """Проверка, что приложение запущено в production режиме"""
    return settings.environment == "production"


def is_testing() -> bool:
    """Проверка, что приложение запущено в режиме тестирования"""
    return settings.environment == "testing" 