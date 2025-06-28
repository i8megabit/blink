"""
Модуль мониторинга и метрик для микросервиса тестирования reLink.
Предоставляет инструменты для отслеживания производительности, ошибок и состояния системы.
"""

import asyncio
import logging
import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import uuid

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, generate_latest,
    CONTENT_TYPE_LATEST, CollectorRegistry, multiprocess
)
from prometheus_client.exposition import start_http_server
import structlog

from .config import settings

logger = logging.getLogger(__name__)

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Prometheus метрики
class Metrics:
    """Класс для управления Prometheus метриками"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Счетчики
        self.test_executions_total = Counter(
            'test_executions_total',
            'Total number of test executions',
            ['test_type', 'status', 'environment'],
            registry=self.registry
        )
        
        self.test_requests_total = Counter(
            'test_requests_total',
            'Total number of test requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'service'],
            registry=self.registry
        )
        
        # Гистограммы
        self.test_execution_duration = Histogram(
            'test_execution_duration_seconds',
            'Test execution duration in seconds',
            ['test_type', 'environment'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )
        
        # Gauge метрики
        self.active_executions = Gauge(
            'active_executions',
            'Number of currently active test executions',
            ['test_type'],
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'queue_size',
            'Number of tests in queue',
            ['priority'],
            registry=self.registry
        )
        
        # Системные метрики
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'disk_usage_percent',
            'Disk usage percentage',
            registry=self.registry
        )
    
    def record_test_execution(self, test_type: str, status: str, environment: str, duration: float):
        """Запись метрики выполнения теста"""
        self.test_executions_total.labels(test_type=test_type, status=status, environment=environment).inc()
        self.test_execution_duration.labels(test_type=test_type, environment=environment).observe(duration)
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Запись метрики HTTP запроса"""
        self.test_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_error(self, error_type: str, service: str = "testing"):
        """Запись метрики ошибки"""
        self.errors_total.labels(error_type=error_type, service=service).inc()
    
    def set_active_executions(self, test_type: str, count: int):
        """Установка количества активных выполнений"""
        self.active_executions.labels(test_type=test_type).set(count)
    
    def set_queue_size(self, priority: str, size: int):
        """Установка размера очереди"""
        self.queue_size.labels(priority=priority).set(size)
    
    def update_system_metrics(self):
        """Обновление системных метрик"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage.set(cpu_percent)
            
            # Memory
            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            
            # Disk
            disk = psutil.disk_usage('/')
            self.disk_usage.set((disk.used / disk.total) * 100)
            
        except Exception as e:
            logger.error(f"Ошибка обновления системных метрик: {e}")

# Глобальный экземпляр метрик
metrics = Metrics()

@dataclass
class PerformanceMetric:
    """Класс для хранения метрики производительности"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorMetric:
    """Класс для хранения метрики ошибки"""
    error_type: str
    message: str
    timestamp: datetime
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.error_history: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Запись метрики производительности"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {},
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics_history.append(metric)
    
    def record_error(self, error_type: str, message: str, stack_trace: str = None, context: Dict[str, Any] = None):
        """Запись метрики ошибки"""
        error = ErrorMetric(
            error_type=error_type,
            message=message,
            timestamp=datetime.now(),
            stack_trace=stack_trace,
            context=context or {}
        )
        
        with self._lock:
            self.error_history.append(error)
    
    def get_metrics_summary(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Получение сводки метрик за временное окно"""
        cutoff_time = datetime.now() - time_window
        
        with self._lock:
            recent_metrics = [
                m for m in self.metrics_history 
                if m.timestamp >= cutoff_time
            ]
        
        if not recent_metrics:
            return {}
        
        # Группировка по имени метрики
        grouped_metrics = defaultdict(list)
        for metric in recent_metrics:
            grouped_metrics[metric.name].append(metric.value)
        
        summary = {}
        for name, values in grouped_metrics.items():
            summary[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 0 else 0,
                "p99": sorted(values)[int(len(values) * 0.99)] if len(values) > 0 else 0
            }
        
        return summary
    
    def get_error_summary(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Получение сводки ошибок за временное окно"""
        cutoff_time = datetime.now() - time_window
        
        with self._lock:
            recent_errors = [
                e for e in self.error_history 
                if e.timestamp >= cutoff_time
            ]
        
        if not recent_errors:
            return {}
        
        # Группировка по типу ошибки
        error_counts = defaultdict(int)
        for error in recent_errors:
            error_counts[error.error_type] += 1
        
        return {
            "total_errors": len(recent_errors),
            "error_types": dict(error_counts),
            "recent_errors": [
                {
                    "type": e.error_type,
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat(),
                    "context": e.context
                }
                for e in recent_errors[-10:]  # Последние 10 ошибок
            ]
        }

# Глобальный монитор производительности
performance_monitor = PerformanceMonitor()

class HealthChecker:
    """Проверка здоровья системы"""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.last_check_results: Dict[str, Dict[str, Any]] = {}
    
    def register_health_check(self, name: str, check_func: Callable):
        """Регистрация проверки здоровья"""
        self.health_checks[name] = check_func
    
    async def run_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """Запуск всех проверок здоровья"""
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                duration = time.time() - start_time
                
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                    "details": result
                }
                
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat(),
                    "details": str(e)
                }
        
        self.last_check_results = results
        return results
    
    def get_health_status(self) -> str:
        """Получение общего статуса здоровья"""
        if not self.last_check_results:
            return "unknown"
        
        all_healthy = all(
            result["status"] == "healthy" 
            for result in self.last_check_results.values()
        )
        
        return "healthy" if all_healthy else "unhealthy"

# Глобальный проверщик здоровья
health_checker = HealthChecker()

class MonitoringMiddleware:
    """Middleware для мониторинга HTTP запросов"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Создание кастомного send для перехвата ответа
        async def custom_send(message):
            if message["type"] == "http.response.start":
                # Запись метрик
                duration = time.time() - start_time
                method = scope.get("method", "UNKNOWN")
                path = scope.get("path", "/")
                status_code = message.get("status", 500)
                
                metrics.record_request(method, path, status_code, duration)
                performance_monitor.record_metric(
                    "request_duration",
                    duration,
                    {"method": method, "path": path, "status_code": str(status_code)}
                )
            
            await send(message)
        
        try:
            await self.app(scope, receive, custom_send)
        except Exception as e:
            # Запись ошибки
            duration = time.time() - start_time
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/")
            
            metrics.record_error("http_error", str(e))
            performance_monitor.record_error(
                "http_error",
                str(e),
                context={"method": method, "path": path, "duration": duration}
            )
            raise

class MetricsExporter:
    """Экспортер метрик для Prometheus"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.server = None
    
    async def start(self):
        """Запуск HTTP сервера для экспорта метрик"""
        try:
            # Запуск сервера в отдельном потоке
            def run_server():
                start_http_server(self.port, registry=metrics.registry)
            
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            
            logger.info(f"📊 Prometheus метрики доступны на порту {self.port}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска экспортера метрик: {e}")
    
    def get_metrics(self) -> str:
        """Получение метрик в формате Prometheus"""
        return generate_latest(metrics.registry)

# Глобальный экспортер метрик
metrics_exporter = MetricsExporter(port=settings.METRICS_PORT)

class SystemMonitor:
    """Монитор системных ресурсов"""
    
    def __init__(self, update_interval: int = 30):
        self.update_interval = update_interval
        self.running = False
        self._task = None
    
    async def start(self):
        """Запуск мониторинга системных ресурсов"""
        self.running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("🔍 Запущен мониторинг системных ресурсов")
    
    async def stop(self):
        """Остановка мониторинга"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Мониторинг системных ресурсов остановлен")
    
    async def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self.running:
            try:
                # Обновление системных метрик
                metrics.update_system_metrics()
                
                # Запись метрик производительности
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                performance_monitor.record_metric("cpu_usage", cpu_percent)
                performance_monitor.record_metric("memory_usage", memory.percent)
                performance_monitor.record_metric("disk_usage", (disk.used / disk.total) * 100)
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга системных ресурсов: {e}")
                await asyncio.sleep(self.update_interval)

# Глобальный системный монитор
system_monitor = SystemMonitor()

# Регистрация стандартных проверок здоровья
def check_database_health():
    """Проверка здоровья базы данных"""
    # TODO: Реализовать реальную проверку
    return {"status": "connected", "tables": ["tests", "executions", "reports"]}

def check_redis_health():
    """Проверка здоровья Redis"""
    # TODO: Реализовать реальную проверку
    return {"status": "connected", "keys": 0}

def check_disk_space():
    """Проверка свободного места на диске"""
    try:
        disk = psutil.disk_usage('/')
        free_percent = (disk.free / disk.total) * 100
        return {
            "free_percent": free_percent,
            "free_bytes": disk.free,
            "total_bytes": disk.total
        }
    except Exception as e:
        return {"error": str(e)}

# Регистрация проверок здоровья
health_checker.register_health_check("database", check_database_health)
health_checker.register_health_check("redis", check_redis_health)
health_checker.register_health_check("disk_space", check_disk_space)

# Декораторы для мониторинга
def monitor_performance(name: str):
    """Декоратор для мониторинга производительности функций"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_metric(name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_metric(name, duration)
                performance_monitor.record_error("function_error", str(e), context={"function": name})
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_metric(name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_metric(name, duration)
                performance_monitor.record_error("function_error", str(e), context={"function": name})
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

@asynccontextmanager
async def monitor_operation(name: str, labels: Dict[str, str] = None):
    """Контекстный менеджер для мониторинга операций"""
    start_time = time.time()
    try:
        yield
        duration = time.time() - start_time
        performance_monitor.record_metric(name, duration, labels or {})
    except Exception as e:
        duration = time.time() - start_time
        performance_monitor.record_metric(name, duration, labels or {})
        performance_monitor.record_error("operation_error", str(e), context={"operation": name})
        raise

# Инициализация мониторинга
async def initialize_monitoring():
    """Инициализация системы мониторинга"""
    try:
        # Запуск экспортера метрик
        await metrics_exporter.start()
        
        # Запуск системного монитора
        await system_monitor.start()
        
        logger.info("✅ Система мониторинга инициализирована")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации мониторинга: {e}")
        raise

async def cleanup_monitoring():
    """Очистка ресурсов мониторинга"""
    try:
        await system_monitor.stop()
        logger.info("🛑 Система мониторинга остановлена")
        
    except Exception as e:
        logger.error(f"❌ Ошибка остановки мониторинга: {e}") 