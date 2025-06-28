"""
🚀 КОНФИГУРАЦИЯ БЕНЧМАРК МИКРОСЕРВИСА
Настройки для максимальной производительности и масштабируемости
"""

import os
from typing import List, Dict, Optional
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings


class BenchmarkSettings(BaseSettings):
    """Настройки бенчмарк микросервиса."""
    
    # Основные настройки сервиса
    service_name: str = "benchmark-service"
    version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Настройки сервера
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8002, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # Настройки производительности
    max_concurrent_benchmarks: int = Field(default=10, env="MAX_CONCURRENT_BENCHMARKS")
    benchmark_timeout: int = Field(default=300, env="BENCHMARK_TIMEOUT")  # секунды
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # секунды
    
    # Настройки базы данных
    database_url: str = Field(
        default="postgresql+asyncpg://benchmark:benchmark@localhost:5432/benchmark_db",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
    # Настройки Redis
    redis_url: str = Field(default="redis://localhost:6379/1", env="REDIS_URL")
    redis_pool_size: int = Field(default=50, env="REDIS_POOL_SIZE")
    
    # Настройки Ollama
    ollama_url: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    ollama_timeout: int = Field(default=120, env="OLLAMA_TIMEOUT")
    ollama_models: List[str] = Field(
        default=["qwen2.5:7b-instruct-turbo", "llama2", "mistral", "codellama", "neural-chat"],
        env="OLLAMA_MODELS"
    )
    
    # Настройки бенчмарка
    default_iterations: int = Field(default=3, env="DEFAULT_ITERATIONS")
    max_iterations: int = Field(default=10, env="MAX_ITERATIONS")
    min_response_time: float = Field(default=0.1, env="MIN_RESPONSE_TIME")
    max_response_time: float = Field(default=30.0, env="MAX_RESPONSE_TIME")
    
    # Настройки метрик
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Настройки логирования
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Настройки безопасности
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Настройки тестовых данных
    test_data_path: str = Field(default="/app/test_data", env="TEST_DATA_PATH")
    benchmark_results_path: str = Field(default="/app/results", env="BENCHMARK_RESULTS_PATH")
    
    # Настройки уведомлений
    notifications_enabled: bool = Field(default=True, env="NOTIFICATIONS_ENABLED")
    webhook_url: Optional[str] = Field(default=None, env="WEBHOOK_URL")
    
    # Настройки экспорта
    export_formats: List[str] = Field(
        default=["json", "csv", "html", "pdf"],
        env="EXPORT_FORMATS"
    )
    
    # Настройки кэширования
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_prefix: str = Field(default="benchmark:", env="CACHE_PREFIX")
    
    # Настройки мониторинга
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    performance_monitoring: bool = Field(default=True, env="PERFORMANCE_MONITORING")
    
    # Настройки масштабирования
    auto_scaling: bool = Field(default=False, env="AUTO_SCALING")
    max_instances: int = Field(default=10, env="MAX_INSTANCES")
    min_instances: int = Field(default=1, env="MIN_INSTANCES")
    
    @validator("ollama_models", pre=True)
    def parse_ollama_models(cls, v):
        """Парсинг списка моделей Ollama."""
        if isinstance(v, str):
            return [model.strip() for model in v.split(",")]
        return v
    
    @validator("export_formats", pre=True)
    def parse_export_formats(cls, v):
        """Парсинг форматов экспорта."""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = BenchmarkSettings()


def get_settings() -> BenchmarkSettings:
    """Получение настроек."""
    return settings


# Константы для бенчмарка
BENCHMARK_TYPES = {
    "seo_basic": {
        "name": "SEO Basic Benchmark",
        "description": "Базовый тест SEO-функциональности",
        "iterations": 3,
        "timeout": 60
    },
    "seo_advanced": {
        "name": "SEO Advanced Benchmark", 
        "description": "Продвинутый тест SEO с RAG",
        "iterations": 5,
        "timeout": 120
    },
    "performance": {
        "name": "Performance Benchmark",
        "description": "Тест производительности и скорости",
        "iterations": 10,
        "timeout": 180
    },
    "quality": {
        "name": "Quality Benchmark",
        "description": "Тест качества ответов",
        "iterations": 3,
        "timeout": 90
    },
    "comprehensive": {
        "name": "Comprehensive Benchmark",
        "description": "Комплексный тест всех аспектов",
        "iterations": 7,
        "timeout": 300
    }
}

METRICS_WEIGHTS = {
    "response_time": 0.25,
    "accuracy": 0.30,
    "quality": 0.25,
    "reliability": 0.20
}

# Настройки для разных типов моделей
MODEL_CONFIGS = {
    "llama2": {
        "default_params": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048
        },
        "benchmark_params": {
            "temperature": 0.5,
            "top_p": 0.8,
            "max_tokens": 1024
        }
    },
    "mistral": {
        "default_params": {
            "temperature": 0.6,
            "top_p": 0.9,
            "max_tokens": 2048
        },
        "benchmark_params": {
            "temperature": 0.4,
            "top_p": 0.8,
            "max_tokens": 1024
        }
    },
    "codellama": {
        "default_params": {
            "temperature": 0.3,
            "top_p": 0.95,
            "max_tokens": 2048
        },
        "benchmark_params": {
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 1024
        }
    }
} 