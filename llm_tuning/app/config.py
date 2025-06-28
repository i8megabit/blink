"""
🧠 Стероидная конфигурация для LLM Tuning микросервиса
Расширенная система настроек с поддержкой динамического тюнинга,
RAG-нативности и ZooKeeper-подобного управления
"""

import os
import subprocess
from typing import Optional, Dict, Any, List, Union
from pydantic_settings import BaseSettings
from pydantic import validator, Field, computed_field
from functools import lru_cache
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Провайдеры LLM моделей"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class VectorDBType(str, Enum):
    """Типы векторных баз данных"""
    CHROMA = "chroma"
    WEAVIATE = "weaviate"
    PINECONE = "pinecone"
    QDRANT = "qdrant"


class TuningStrategy(str, Enum):
    """Стратегии тюнинга"""
    ADAPTIVE = "adaptive"
    AGGREGATE = "aggregate"
    HYBRID = "hybrid"
    MANUAL = "manual"


def get_version_from_readme() -> str:
    """Извлекает версию из README.md"""
    try:
        result = subprocess.run(
            ["python", "scripts/extract_version.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            logger.info(f"Версия извлечена из README: {version}")
            return version
    except Exception as e:
        logger.warning(f"Не удалось извлечь версию из README: {e}")
    
    return os.getenv("LLM_TUNING_VERSION", "1.0.0")


class DatabaseSettings(BaseSettings):
    """Настройки базы данных"""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="relink_db", env="DB_NAME")
    username: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")
    pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=40, env="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, env="DB_ECHO")
    
    @computed_field
    @property
    def url(self) -> str:
        """URL подключения к базе данных"""
        if self.password:
            return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql+asyncpg://{self.username}@{self.host}:{self.port}/{self.database}"
    
    @computed_field
    @property
    def sync_url(self) -> str:
        """Синхронный URL подключения к базе данных"""
        if self.password:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    """Настройки Redis для кэширования и очередей"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    cache_ttl: int = Field(default=3600, env="REDIS_CACHE_TTL")
    
    @computed_field
    @property
    def url(self) -> str:
        """URL подключения к Redis"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class OllamaSettings(BaseSettings):
    """Расширенные настройки Ollama"""
    url: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    default_model: str = Field(default="qwen2.5:7b-instruct-turbo", env="OLLAMA_DEFAULT_MODEL")
    timeout: int = Field(default=300, env="OLLAMA_TIMEOUT")
    max_tokens: int = Field(default=4096, env="OLLAMA_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OLLAMA_TEMPERATURE")
    
    # Apple Silicon оптимизации
    metal_enabled: bool = Field(default=True, env="OLLAMA_METAL")
    flash_attention: bool = Field(default=True, env="OLLAMA_FLASH_ATTENTION")
    kv_cache_type: str = Field(default="q8_0", env="OLLAMA_KV_CACHE_TYPE")
    context_length: int = Field(default=4096, env="OLLAMA_CONTEXT_LENGTH")
    batch_size: int = Field(default=512, env="OLLAMA_BATCH_SIZE")
    num_parallel: int = Field(default=2, env="OLLAMA_NUM_PARALLEL")
    mem_fraction: float = Field(default=0.9, env="OLLAMA_MEM_FRACTION")
    
    # Динамические настройки
    auto_scale: bool = Field(default=True, env="OLLAMA_AUTO_SCALE")
    max_instances: int = Field(default=5, env="OLLAMA_MAX_INSTANCES")
    load_threshold: float = Field(default=0.8, env="OLLAMA_LOAD_THRESHOLD")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL должен начинаться с http:// или https://')
        return v.rstrip('/')


class VectorDBSettings(BaseSettings):
    """Настройки векторных баз данных"""
    type: VectorDBType = Field(default=VectorDBType.CHROMA, env="VECTOR_DB_TYPE")
    
    # ChromaDB настройки
    chroma_host: str = Field(default="localhost", env="CHROMA_HOST")
    chroma_port: int = Field(default=8000, env="CHROMA_PORT")
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIR")
    
    # Weaviate настройки
    weaviate_url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    # Общие настройки
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    chunk_size: int = Field(default=1000, env="VECTOR_CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="VECTOR_CHUNK_OVERLAP")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")


class RAGSettings(BaseSettings):
    """Настройки RAG системы"""
    enabled: bool = Field(default=True, env="RAG_ENABLED")
    max_context_length: int = Field(default=4000, env="RAG_MAX_CONTEXT")
    top_k_results: int = Field(default=5, env="RAG_TOP_K")
    rerank_enabled: bool = Field(default=True, env="RAG_RERANK")
    hybrid_search: bool = Field(default=True, env="RAG_HYBRID_SEARCH")
    
    # Промпты
    system_prompt: str = Field(
        default="Ты эксперт по SEO и веб-аналитике. Отвечай на основе предоставленного контекста.",
        env="RAG_SYSTEM_PROMPT"
    )
    query_template: str = Field(
        default="Контекст: {context}\n\nВопрос: {question}\n\nОтвет:",
        env="RAG_QUERY_TEMPLATE"
    )


class TuningSettings(BaseSettings):
    """Настройки динамического тюнинга"""
    enabled: bool = Field(default=True, env="TUNING_ENABLED")
    strategy: TuningStrategy = Field(default=TuningStrategy.ADAPTIVE, env="TUNING_STRATEGY")
    
    # Параметры адаптации
    learning_rate: float = Field(default=0.001, env="TUNING_LEARNING_RATE")
    batch_size: int = Field(default=32, env="TUNING_BATCH_SIZE")
    epochs: int = Field(default=3, env="TUNING_EPOCHS")
    
    # Метрики качества
    quality_threshold: float = Field(default=0.8, env="QUALITY_THRESHOLD")
    response_time_threshold: float = Field(default=2.0, env="RESPONSE_TIME_THRESHOLD")
    
    # A/B тестирование
    ab_testing_enabled: bool = Field(default=True, env="AB_TESTING_ENABLED")
    ab_test_ratio: float = Field(default=0.1, env="AB_TEST_RATIO")
    
    # Автоматическая оптимизация
    auto_optimize: bool = Field(default=True, env="AUTO_OPTIMIZE")
    optimization_interval: int = Field(default=3600, env="OPTIMIZATION_INTERVAL")  # секунды


class RouterSettings(BaseSettings):
    """Настройки маршрутизатора"""
    enabled: bool = Field(default=True, env="ROUTER_ENABLED")
    routing_strategy: str = Field(default="smart", env="ROUTING_STRATEGY")
    
    # Стратегии маршрутизации
    strategies: Dict[str, Dict[str, Any]] = Field(default={
        "smart": {
            "description": "Умная маршрутизация на основе контекста и нагрузки",
            "weight": 1.0
        },
        "round_robin": {
            "description": "Круговая маршрутизация",
            "weight": 0.3
        },
        "load_based": {
            "description": "Маршрутизация по нагрузке",
            "weight": 0.7
        },
        "quality_based": {
            "description": "Маршрутизация по качеству ответов",
            "weight": 0.8
        }
    })
    
    # Кэширование маршрутов
    route_cache_ttl: int = Field(default=300, env="ROUTE_CACHE_TTL")
    route_cache_size: int = Field(default=10000, env="ROUTE_CACHE_SIZE")


class MonitoringSettings(BaseSettings):
    """Расширенные настройки мониторинга"""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # Детальный мониторинг
    track_response_times: bool = Field(default=True, env="TRACK_RESPONSE_TIMES")
    track_quality_metrics: bool = Field(default=True, env="TRACK_QUALITY_METRICS")
    track_model_performance: bool = Field(default=True, env="TRACK_MODEL_PERFORMANCE")
    
    # Алерты
    alert_threshold_response_time: float = Field(default=5.0, env="ALERT_THRESHOLD_RESPONSE_TIME")
    alert_threshold_error_rate: float = Field(default=0.05, env="ALERT_THRESHOLD_ERROR_RATE")


class SecuritySettings(BaseSettings):
    """Настройки безопасности"""
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # API ключи
    enable_api_keys: bool = Field(default=True, env="ENABLE_API_KEYS")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY должен быть не менее 32 символов')
        return v


class APISettings(BaseSettings):
    """Настройки API"""
    title: str = Field(default="reLink LLM Tuning API", env="API_TITLE")
    description: str = Field(default="AI-powered LLM tuning and routing platform", env="API_DESCRIPTION")
    version: str = Field(default_factory=get_version_from_readme, env="API_VERSION")
    debug: bool = Field(default=False, env="API_DEBUG")
    docs_url: str = Field(default="/docs", env="API_DOCS_URL")
    redoc_url: str = Field(default="/redoc", env="API_REDOC_URL")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Performance
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")
    keep_alive_timeout: int = Field(default=2, env="KEEP_ALIVE_TIMEOUT")


class Settings(BaseSettings):
    """Основные настройки LLM Tuning микросервиса"""
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Подмодули настроек
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    ollama: OllamaSettings = OllamaSettings()
    vector_db: VectorDBSettings = VectorDBSettings()
    rag: RAGSettings = RAGSettings()
    tuning: TuningSettings = TuningSettings()
    router: RouterSettings = RouterSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    security: SecuritySettings = SecuritySettings()
    api: APISettings = APISettings()
    
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
    
    def get_ollama_env_vars(self) -> Dict[str, str]:
        """Получение переменных окружения для Ollama"""
        return {
            "OLLAMA_METAL": "1" if self.ollama.metal_enabled else "0",
            "OLLAMA_FLASH_ATTENTION": "1" if self.ollama.flash_attention else "0",
            "OLLAMA_KV_CACHE_TYPE": self.ollama.kv_cache_type,
            "OLLAMA_CONTEXT_LENGTH": str(self.ollama.context_length),
            "OLLAMA_BATCH_SIZE": str(self.ollama.batch_size),
            "OLLAMA_NUM_PARALLEL": str(self.ollama.num_parallel),
            "OLLAMA_MEM_FRACTION": str(self.ollama.mem_fraction),
        }


@lru_cache()
def get_settings() -> Settings:
    """Получение настроек с кэшированием"""
    try:
        settings = Settings()
        logger.info(f"LLM Tuning настройки загружены для среды: {settings.environment}")
        logger.info(f"Версия API: {settings.api.version}")
        logger.info(f"RAG включен: {settings.rag.enabled}")
        logger.info(f"Тюнинг включен: {settings.tuning.enabled}")
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
LLMTuningSettings = Settings 