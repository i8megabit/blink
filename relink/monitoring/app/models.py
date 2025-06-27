"""
Pydantic модели для микросервиса мониторинга
Модели для метрик, алертов, дашборда и API
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class MetricType(str, Enum):
    """Типы метрик"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(str, Enum):
    """Уровни важности алертов"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Статусы алертов"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


class ServiceStatus(str, Enum):
    """Статусы сервисов"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class SystemMetrics(BaseModel):
    """Системные метрики"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # CPU метрики
    cpu_percent: float = Field(..., ge=0, le=100)
    cpu_count: int = Field(..., ge=1)
    cpu_freq: Optional[float] = None
    
    # Память
    memory_total: int = Field(..., ge=0)
    memory_available: int = Field(..., ge=0)
    memory_used: int = Field(..., ge=0)
    memory_percent: float = Field(..., ge=0, le=100)
    
    # Диск
    disk_total: int = Field(..., ge=0)
    disk_used: int = Field(..., ge=0)
    disk_free: int = Field(..., ge=0)
    disk_percent: float = Field(..., ge=0, le=100)
    
    # Сеть
    network_bytes_sent: Optional[int] = None
    network_bytes_recv: Optional[int] = None
    network_packets_sent: Optional[int] = None
    network_packets_recv: Optional[int] = None
    
    # Загрузка системы
    load_average_1m: Optional[float] = None
    load_average_5m: Optional[float] = None
    load_average_15m: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DatabaseMetrics(BaseModel):
    """Метрики базы данных"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Подключения
    active_connections: int = Field(..., ge=0)
    max_connections: int = Field(..., ge=0)
    connection_usage_percent: float = Field(..., ge=0, le=100)
    
    # Производительность
    queries_per_second: float = Field(..., ge=0)
    slow_queries: int = Field(..., ge=0)
    avg_query_time: float = Field(..., ge=0)
    
    # Размер БД
    database_size: int = Field(..., ge=0)
    table_sizes: Dict[str, int] = Field(default_factory=dict)
    
    # Кэш
    cache_hit_ratio: float = Field(..., ge=0, le=100)
    cache_size: int = Field(..., ge=0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OllamaMetrics(BaseModel):
    """Метрики Ollama"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Статус
    status: ServiceStatus = Field(...)
    models_loaded: List[str] = Field(default_factory=list)
    
    # Производительность
    requests_per_second: float = Field(..., ge=0)
    avg_response_time: float = Field(..., ge=0)
    total_requests: int = Field(..., ge=0)
    failed_requests: int = Field(..., ge=0)
    
    # Ресурсы
    memory_usage: int = Field(..., ge=0)
    cpu_usage: float = Field(..., ge=0, le=100)
    
    # Модели
    model_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CacheMetrics(BaseModel):
    """Метрики кэша"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Redis метрики
    redis_connected: bool = Field(...)
    redis_memory_used: int = Field(..., ge=0)
    redis_memory_peak: int = Field(..., ge=0)
    redis_keys_total: int = Field(..., ge=0)
    redis_evicted_keys: int = Field(..., ge=0)
    
    # Hit/Miss статистика
    cache_hits: int = Field(..., ge=0)
    cache_misses: int = Field(..., ge=0)
    cache_hit_ratio: float = Field(..., ge=0, le=100)
    
    # Операции
    operations_per_second: float = Field(..., ge=0)
    avg_operation_time: float = Field(..., ge=0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HTTPMetrics(BaseModel):
    """HTTP метрики"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Запросы
    total_requests: int = Field(..., ge=0)
    requests_per_second: float = Field(..., ge=0)
    active_requests: int = Field(..., ge=0)
    
    # Статус коды
    status_codes: Dict[str, int] = Field(default_factory=dict)
    error_rate: float = Field(..., ge=0, le=100)
    
    # Время ответа
    avg_response_time: float = Field(..., ge=0)
    p95_response_time: float = Field(..., ge=0)
    p99_response_time: float = Field(..., ge=0)
    
    # Размеры
    avg_request_size: float = Field(..., ge=0)
    avg_response_size: float = Field(..., ge=0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Alert(BaseModel):
    """Модель алерта"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Основная информация
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    severity: AlertSeverity = Field(...)
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)
    
    # Источник
    source: str = Field(..., min_length=1, max_length=100)
    service: str = Field(..., min_length=1, max_length=100)
    
    # Метрики
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    
    # Дополнительные данные
    labels: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Время жизни
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ServiceHealth(BaseModel):
    """Здоровье сервиса"""
    service: str = Field(...)
    status: ServiceStatus = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Метрики здоровья
    response_time: Optional[float] = None
    uptime: Optional[float] = None
    error_rate: Optional[float] = None
    
    # Дополнительная информация
    version: Optional[str] = None
    endpoint: Optional[str] = None
    last_check: Optional[datetime] = None
    
    # Детали
    details: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardData(BaseModel):
    """Данные для дашборда"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Общий статус
    overall_status: ServiceStatus = Field(...)
    services_healthy: int = Field(..., ge=0)
    services_total: int = Field(..., ge=0)
    
    # Метрики
    system: Optional[SystemMetrics] = None
    database: Optional[DatabaseMetrics] = None
    ollama: Optional[OllamaMetrics] = None
    cache: Optional[CacheMetrics] = None
    http: Optional[HTTPMetrics] = None
    
    # Алерты
    active_alerts: List[Alert] = Field(default_factory=list)
    alerts_count: Dict[AlertSeverity, int] = Field(default_factory=dict)
    
    # Здоровье сервисов
    services: List[ServiceHealth] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricData(BaseModel):
    """Данные метрики"""
    name: str = Field(...)
    type: MetricType = Field(...)
    value: Union[int, float] = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Метки
    labels: Dict[str, str] = Field(default_factory=dict)
    
    # Дополнительные данные для гистограмм и summary
    buckets: Optional[Dict[str, int]] = None
    quantiles: Optional[Dict[str, float]] = None
    count: Optional[int] = None
    sum: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricsResponse(BaseModel):
    """Ответ с метриками"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: List[MetricData] = Field(...)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertRule(BaseModel):
    """Правило алерта"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    
    # Условия
    metric_name: str = Field(...)
    condition: str = Field(...)  # ">", "<", "==", ">=", "<="
    threshold: float = Field(...)
    duration: int = Field(default=60)  # секунды
    
    # Настройки алерта
    severity: AlertSeverity = Field(...)
    enabled: bool = Field(default=True)
    
    # Уведомления
    notification_channels: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """Ответ проверки здоровья"""
    status: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(...)
    environment: str = Field(...)
    
    # Детали
    services: Dict[str, ServiceHealth] = Field(default_factory=dict)
    uptime: float = Field(...)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Экспорт моделей
__all__ = [
    "SystemMetrics",
    "DatabaseMetrics", 
    "OllamaMetrics",
    "CacheMetrics",
    "HTTPMetrics",
    "Alert",
    "ServiceHealth",
    "DashboardData",
    "MetricData",
    "MetricsResponse",
    "AlertRule",
    "HealthCheckResponse",
    "MetricType",
    "AlertSeverity",
    "AlertStatus",
    "ServiceStatus"
] 