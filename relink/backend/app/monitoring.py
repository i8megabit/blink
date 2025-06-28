"""
Модуль мониторинга и логирования для reLink
Интеграция с Prometheus, OpenTelemetry и структурированное логирование
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import asynccontextmanager

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import prometheus_client as prometheus
from prometheus_client import Counter, Histogram, Gauge, Summary
import structlog

from .config import settings

# Настройка структурированного логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.monitoring.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Создание логгера
logger = structlog.get_logger()

# Prometheus метрики
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total number of HTTP errors',
    ['method', 'endpoint', 'error_type']
)

DATABASE_OPERATIONS = Counter(
    'database_operations_total',
    'Total number of database operations',
    ['operation', 'table', 'status']
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total number of cache operations',
    ['operation', 'cache_type', 'status']
)

OLLAMA_REQUESTS = Counter(
    'ollama_requests_total',
    'Total number of Ollama requests',
    ['model', 'operation', 'status']
)

OLLAMA_RESPONSE_TIME = Histogram(
    'ollama_response_time_seconds',
    'Ollama response time in seconds',
    ['model', 'operation']
)

SYSTEM_MEMORY = Gauge(
    'system_memory_bytes',
    'System memory usage in bytes',
    ['type']
)

SYSTEM_CPU = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

# RAG-специфичные метрики
RAG_QUERIES = Counter(
    'rag_queries_total',
    'Total number of RAG queries',
    ['service_type', 'status']
)

RAG_EMBEDDING_GENERATION = Counter(
    'rag_embedding_generation_total',
    'Total number of embedding generations',
    ['model', 'status']
)

RAG_SIMILARITY_SEARCH = Counter(
    'rag_similarity_search_total',
    'Total number of similarity searches',
    ['vector_db', 'status']
)

RAG_CONTEXT_LENGTH = Histogram(
    'rag_context_length_chars',
    'RAG context length in characters',
    ['service_type']
)

RAG_RESPONSE_QUALITY = Histogram(
    'rag_response_quality_score',
    'RAG response quality score',
    ['service_type', 'model']
)

RAG_CACHE_HIT_RATIO = Gauge(
    'rag_cache_hit_ratio',
    'RAG cache hit ratio',
    ['cache_type']
)

VECTOR_DB_OPERATIONS = Counter(
    'vector_db_operations_total',
    'Total number of vector database operations',
    ['operation', 'status']
)

EMBEDDING_DIMENSION = Gauge(
    'embedding_dimension',
    'Embedding vector dimension',
    ['model']
)


class MonitoringMiddleware:
    """Middleware для мониторинга HTTP запросов"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        request = Request(scope, receive)
        
        # Увеличение счетчика активных запросов
        ACTIVE_REQUESTS.labels(
            method=request.method,
            endpoint=request.url.path
        ).inc()
        
        # Логирование входящего запроса
        logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        # Обработка запроса
        try:
            await self.app(scope, receive, send)
            
            # Увеличение счетчика успешных запросов
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status="success"
            ).inc()
            
        except Exception as e:
            # Увеличение счетчика ошибок
            ERROR_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                error_type=type(e).__name__
            ).inc()
            
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        finally:
            # Уменьшение счетчика активных запросов
            ACTIVE_REQUESTS.labels(
                method=request.method,
                endpoint=request.url.path
            ).dec()
            
            # Измерение длительности запроса
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                duration=duration,
            )


class MetricsCollector:
    """Сборщик метрик системы"""
    
    def __init__(self, service_name: str = "relink-backend"):
        self.service_name = service_name
        self.start_time = time.time()
    
    def collect_system_metrics(self):
        """Сбор системных метрик"""
        try:
            import psutil
            
            # Метрики памяти
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY.labels(type="total").set(memory.total)
            SYSTEM_MEMORY.labels(type="available").set(memory.available)
            SYSTEM_MEMORY.labels(type="used").set(memory.used)
            SYSTEM_MEMORY.labels(type="free").set(memory.free)
            
            # Метрики CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU.set(cpu_percent)
            
            logger.debug(
                "System metrics collected",
                memory_total=memory.total,
                memory_used=memory.used,
                memory_percent=memory.percent,
                cpu_percent=cpu_percent,
            )
            
        except ImportError:
            logger.warning("psutil not available, system metrics disabled")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")


class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, name: str):
        """Запуск таймера"""
        self.metrics[name] = {"start": time.time()}
    
    def end_timer(self, name: str) -> float:
        """Остановка таймера и возврат длительности"""
        if name in self.metrics:
            duration = time.time() - self.metrics[name]["start"]
            self.metrics[name]["duration"] = duration
            return duration
        return 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        return self.metrics.copy()


class RAGMonitor:
    """Мониторинг RAG операций"""
    
    def __init__(self):
        self.embedding_times = []
        self.search_times = []
        self.context_qualities = []
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_embedding_generation(self, model: str, duration: float, success: bool):
        """Запись метрик генерации эмбеддингов"""
        RAG_EMBEDDING_GENERATION.labels(
            model=model,
            status="success" if success else "error"
        ).inc()
        
        if success:
            self.embedding_times.append(duration)
    
    def record_similarity_search(self, vector_db: str, duration: float, success: bool, results_count: int):
        """Запись метрик поиска похожести"""
        RAG_SIMILARITY_SEARCH.labels(
            vector_db=vector_db,
            status="success" if success else "error"
        ).inc()
        
        if success:
            self.search_times.append(duration)
    
    def record_context_generation(self, service_type: str, context_length: int, quality_score: float):
        """Запись метрик генерации контекста"""
        RAG_CONTEXT_LENGTH.labels(service_type=service_type).observe(context_length)
        RAG_RESPONSE_QUALITY.labels(service_type=service_type, model="default").observe(quality_score)
        
        self.context_qualities.append(quality_score)
    
    def record_cache_hit(self, cache_type: str):
        """Запись попадания в кэш"""
        self.cache_hits += 1
        self._update_cache_ratio(cache_type)
    
    def record_cache_miss(self, cache_type: str):
        """Запись промаха кэша"""
        self.cache_misses += 1
        self._update_cache_ratio(cache_type)
    
    def _update_cache_ratio(self, cache_type: str):
        """Обновление соотношения попаданий в кэш"""
        total = self.cache_hits + self.cache_misses
        if total > 0:
            ratio = self.cache_hits / total
            RAG_CACHE_HIT_RATIO.labels(cache_type=cache_type).set(ratio)
    
    def record_vector_db_operation(self, operation: str, success: bool, duration: float = None):
        """Запись операций с векторной БД"""
        VECTOR_DB_OPERATIONS.labels(
            operation=operation,
            status="success" if success else "error"
        ).inc()
    
    def record_embedding_dimension(self, model: str, dimension: int):
        """Запись размерности эмбеддингов"""
        EMBEDDING_DIMENSION.labels(model=model).set(dimension)
    
    def get_rag_metrics(self) -> Dict[str, Any]:
        """Получение RAG метрик"""
        return {
            "embedding_generation": {
                "total_requests": len(self.embedding_times),
                "average_time": sum(self.embedding_times) / len(self.embedding_times) if self.embedding_times else 0,
                "min_time": min(self.embedding_times) if self.embedding_times else 0,
                "max_time": max(self.embedding_times) if self.embedding_times else 0
            },
            "similarity_search": {
                "total_requests": len(self.search_times),
                "average_time": sum(self.search_times) / len(self.search_times) if self.search_times else 0,
                "min_time": min(self.search_times) if self.search_times else 0,
                "max_time": max(self.search_times) if self.search_times else 0
            },
            "context_quality": {
                "total_contexts": len(self.context_qualities),
                "average_quality": sum(self.context_qualities) / len(self.context_qualities) if self.context_qualities else 0,
                "min_quality": min(self.context_qualities) if self.context_qualities else 0,
                "max_quality": max(self.context_qualities) if self.context_qualities else 0
            },
            "cache_performance": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_ratio": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
            }
        }


# Декораторы для мониторинга
def monitor_database_operation(operation: str, table: str = None):
    """Декоратор для мониторинга операций с базой данных"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                DATABASE_OPERATIONS.labels(
                    operation=operation,
                    table=table or "unknown",
                    status="success"
                ).inc()
                return result
            except Exception as e:
                DATABASE_OPERATIONS.labels(
                    operation=operation,
                    table=table or "unknown",
                    status="error"
                ).inc()
                logger.error(
                    "Database operation failed",
                    operation=operation,
                    table=table,
                    error=str(e),
                    duration=time.time() - start_time,
                )
                raise
        return wrapper
    return decorator


def monitor_cache_operation(operation: str, cache_type: str = "memory"):
    """Декоратор для мониторинга операций с кэшем"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                CACHE_OPERATIONS.labels(
                    operation=operation,
                    cache_type=cache_type,
                    status="success"
                ).inc()
                return result
            except Exception as e:
                CACHE_OPERATIONS.labels(
                    operation=operation,
                    cache_type=cache_type,
                    status="error"
                ).inc()
                logger.error(
                    "Cache operation failed",
                    operation=operation,
                    cache_type=cache_type,
                    error=str(e),
                    duration=time.time() - start_time,
                )
                raise
        return wrapper
    return decorator


def monitor_ollama_request(model: str, operation: str):
    """Декоратор для мониторинга запросов к Ollama"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                OLLAMA_REQUESTS.labels(
                    model=model,
                    operation=operation,
                    status="success"
                ).inc()
                OLLAMA_RESPONSE_TIME.labels(
                    model=model,
                    operation=operation
                ).observe(time.time() - start_time)
                return result
            except Exception as e:
                OLLAMA_REQUESTS.labels(
                    model=model,
                    operation=operation,
                    status="error"
                ).inc()
                logger.error(
                    "Ollama request failed",
                    model=model,
                    operation=operation,
                    error=str(e),
                    duration=time.time() - start_time,
                )
                raise
        return wrapper
    return decorator


@asynccontextmanager
async def monitor_operation(operation_name: str, **context):
    """Контекстный менеджер для мониторинга операций"""
    start_time = time.time()
    logger.info(f"Starting operation: {operation_name}", **context)
    
    try:
        yield
        duration = time.time() - start_time
        logger.info(
            f"Operation completed: {operation_name}",
            duration=duration,
            **context
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Operation failed: {operation_name}",
            duration=duration,
            error=str(e),
            **context
        )
        raise


# Функции для экспорта метрик
def get_metrics():
    """Получение всех метрик Prometheus"""
    return prometheus.generate_latest()


def get_health_status() -> Dict[str, Any]:
    """Получение статуса здоровья системы"""
    uptime = time.time() - time.time()  # Время работы приложения
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": uptime,
        "version": settings.api.version,
        "environment": settings.environment,
    }


# Инициализация мониторинга
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor()

# Глобальный экземпляр RAG монитора
rag_monitor = RAGMonitor()

# Экспорт для обратной совместимости
RelinkMonitoring = {
    "logger": logger,
    "metrics_collector": metrics_collector,
    "performance_monitor": performance_monitor,
    "get_metrics": get_metrics,
    "get_health_status": get_health_status,
}

def monitor_rag_operation(operation_type: str, service_type: str = "default"):
    """Декоратор для мониторинга RAG операций"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                
                # Запись метрик в зависимости от типа операции
                duration = time.time() - start_time
                
                if operation_type == "embedding_generation":
                    rag_monitor.record_embedding_generation(
                        model=kwargs.get("model", "default"),
                        duration=duration,
                        success=success
                    )
                elif operation_type == "similarity_search":
                    rag_monitor.record_similarity_search(
                        vector_db=kwargs.get("vector_db", "default"),
                        duration=duration,
                        success=success,
                        results_count=len(result) if isinstance(result, list) else 0
                    )
                elif operation_type == "context_generation":
                    rag_monitor.record_context_generation(
                        service_type=service_type,
                        context_length=len(result) if isinstance(result, str) else 0,
                        quality_score=kwargs.get("quality_score", 0.8)
                    )
                
                # Общая метрика RAG запросов
                RAG_QUERIES.labels(
                    service_type=service_type,
                    status="success"
                ).inc()
                
                return result
                
            except Exception as e:
                # Запись ошибки
                RAG_QUERIES.labels(
                    service_type=service_type,
                    status="error"
                ).inc()
                
                logger.error(f"RAG operation failed: {operation_type} - {e}")
                raise
                
        return wrapper
    return decorator

def get_rag_health_status() -> Dict[str, Any]:
    """Получение статуса здоровья RAG системы"""
    try:
        rag_metrics = rag_monitor.get_rag_metrics()
        
        # Определение статуса на основе метрик
        health_status = "healthy"
        issues = []
        
        # Проверка времени ответа эмбеддингов
        if rag_metrics["embedding_generation"]["average_time"] > 5.0:
            health_status = "degraded"
            issues.append("Slow embedding generation")
        
        # Проверка времени поиска
        if rag_metrics["similarity_search"]["average_time"] > 2.0:
            health_status = "degraded"
            issues.append("Slow similarity search")
        
        # Проверка качества контекста
        if rag_metrics["context_quality"]["average_quality"] < 0.6:
            health_status = "degraded"
            issues.append("Low context quality")
        
        # Проверка кэша
        if rag_metrics["cache_performance"]["hit_ratio"] < 0.3:
            health_status = "degraded"
            issues.append("Low cache hit ratio")
        
        return {
            "status": health_status,
            "issues": issues,
            "metrics": rag_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting RAG health status: {e}")
        return {
            "status": "error",
            "issues": [f"Health check failed: {e}"],
            "metrics": {},
            "timestamp": datetime.utcnow().isoformat()
        } 