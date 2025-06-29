"""🚀 Расширенная система мониторинга и профилирования для reLink Backend"""

import asyncio
import json
import logging
import os
import time
import traceback
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import wraps

import psutil
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# Настройка базового логирования
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    """Метрики для профилирования запросов."""
    request_id: str
    method: str
    url: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status_code: Optional[int] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    request_size: Optional[int] = None
    response_size: Optional[int] = None
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    cpu_before: Optional[float] = None
    cpu_after: Optional[float] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Общие метрики производительности."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_requests: int
    total_requests: int
    error_rate: float
    avg_response_time: float
    slow_requests: int

class AdvancedMetricsCollector:
    """Расширенный сборщик метрик с профилированием."""
    
    def __init__(self):
        self.request_metrics: Dict[str, RequestMetrics] = {}
        self.performance_history: deque = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.slow_requests: List[RequestMetrics] = []
        self.active_requests = 0
        self.total_requests = 0
        self.start_time = time.time()
        
        # Настройки из переменных окружения
        self.enable_profiling = os.getenv("ENABLE_PROFILING", "false").lower() == "true"
        self.enable_detailed_logging = os.getenv("ENABLE_DETAILED_LOGGING", "false").lower() == "true"
        self.enable_request_profiling = os.getenv("ENABLE_REQUEST_PROFILING", "false").lower() == "true"
        self.enable_performance_monitoring = os.getenv("ENABLE_PERFORMANCE_MONITORING", "false").lower() == "true"
        
        # Пороги для медленных запросов (в секундах)
        self.slow_request_threshold = float(os.getenv("SLOW_REQUEST_THRESHOLD", "2.0"))
        
        logger.info("🚀 AdvancedMetricsCollector инициализирован", extra={
            "enable_profiling": self.enable_profiling,
            "enable_detailed_logging": self.enable_detailed_logging,
            "enable_request_profiling": self.enable_request_profiling,
            "enable_performance_monitoring": self.enable_performance_monitoring,
            "slow_request_threshold": self.slow_request_threshold
        })

    def start_request_profiling(self, request: Request) -> str:
        """Начинает профилирование запроса."""
        if not self.enable_request_profiling:
            return ""

        request_id = f"req_{int(time.time() * 1000)}_{id(request)}"
        
        # Получаем информацию о системе
        memory_before = psutil.virtual_memory().percent if psutil else None
        cpu_before = psutil.cpu_percent() if psutil else None
        
        metrics = RequestMetrics(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            start_time=time.time(),
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            request_size=len(request.body) if hasattr(request, 'body') else None,
            memory_before=memory_before,
            cpu_before=cpu_before
        )
        
        self.request_metrics[request_id] = metrics
        self.active_requests += 1
        self.total_requests += 1
        
        if self.enable_detailed_logging:
            logger.debug("🚀 Начало профилирования запроса", extra={
                "request_id": request_id,
                "method": metrics.method,
                "url": metrics.url,
                "user_agent": metrics.user_agent,
                "ip_address": metrics.ip_address,
                "memory_before": memory_before,
                "cpu_before": cpu_before
            })
        
        return request_id

    def end_request_profiling(self, request_id: str, response: Response, error: Optional[Exception] = None):
        """Завершает профилирование запроса."""
        if not self.enable_request_profiling or not request_id:
            return

        metrics = self.request_metrics.get(request_id)
        if not metrics:
            return

        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time
        metrics.status_code = response.status_code
        metrics.response_size = len(response.body) if hasattr(response, 'body') else None
        
        # Получаем финальные метрики системы
        if psutil:
            metrics.memory_after = psutil.virtual_memory().percent
            metrics.cpu_after = psutil.cpu_percent()

        # Обрабатываем ошибки
        if error:
            metrics.error = str(error)
            metrics.stack_trace = traceback.format_exc()
            self.error_counts[type(error).__name__] += 1

        # Проверяем медленные запросы
        if metrics.duration and metrics.duration > self.slow_request_threshold:
            self.slow_requests.append(metrics)
            if len(self.slow_requests) > 100:  # Ограничиваем количество
                self.slow_requests.pop(0)

        self.active_requests -= 1

        if self.enable_detailed_logging:
            logger.debug("✅ Завершение профилирования запроса", extra={
                "request_id": request_id,
                "method": metrics.method,
                "url": metrics.url,
                "status_code": metrics.status_code,
                "duration": f"{metrics.duration:.3f}s",
                "memory_delta": f"{metrics.memory_after - metrics.memory_before:.2f}%" if metrics.memory_after and metrics.memory_before else None,
                "cpu_delta": f"{metrics.cpu_after - metrics.cpu_before:.2f}%" if metrics.cpu_after and metrics.cpu_before else None,
                "error": metrics.error
            })

        # Удаляем метрики из памяти для экономии места
        del self.request_metrics[request_id]

    def collect_performance_metrics(self) -> PerformanceMetrics:
        """Собирает текущие метрики производительности."""
        if not psutil:
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                active_requests=self.active_requests,
                total_requests=self.total_requests,
                error_rate=self._calculate_error_rate(),
                avg_response_time=self._calculate_avg_response_time(),
                slow_requests=len(self.slow_requests)
            )

        # Системные метрики
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            disk_usage_percent=disk.percent,
            active_requests=self.active_requests,
            total_requests=self.total_requests,
            error_rate=self._calculate_error_rate(),
            avg_response_time=self._calculate_avg_response_time(),
            slow_requests=len(self.slow_requests)
        )

        self.performance_history.append(metrics)
        return metrics

    def _calculate_error_rate(self) -> float:
        """Вычисляет процент ошибок."""
        if self.total_requests == 0:
            return 0.0
        total_errors = sum(self.error_counts.values())
        return (total_errors / self.total_requests) * 100

    def _calculate_avg_response_time(self) -> float:
        """Вычисляет среднее время ответа."""
        if not self.performance_history:
            return 0.0
        
        recent_metrics = list(self.performance_history)[-100:]  # Последние 100 метрик
        total_time = sum(m.avg_response_time for m in recent_metrics)
        return total_time / len(recent_metrics) if recent_metrics else 0.0

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Возвращает детальную статистику."""
        current_metrics = self.collect_performance_metrics()
        
        return {
            "system": {
                "cpu_percent": current_metrics.cpu_percent,
                "memory_percent": current_metrics.memory_percent,
                "memory_used_mb": current_metrics.memory_used_mb,
                "disk_usage_percent": current_metrics.disk_usage_percent,
                "uptime_seconds": time.time() - self.start_time
            },
            "requests": {
                "active": current_metrics.active_requests,
                "total": current_metrics.total_requests,
                "error_rate": current_metrics.error_rate,
                "avg_response_time": current_metrics.avg_response_time,
                "slow_requests": current_metrics.slow_requests
            },
            "errors": dict(self.error_counts),
            "recent_slow_requests": [
                {
                    "request_id": req.request_id,
                    "method": req.method,
                    "url": req.url,
                    "duration": req.duration,
                    "status_code": req.status_code,
                    "error": req.error
                }
                for req in self.slow_requests[-10:]  # Последние 10 медленных запросов
            ],
            "settings": {
                "enable_profiling": self.enable_profiling,
                "enable_detailed_logging": self.enable_detailed_logging,
                "enable_request_profiling": self.enable_request_profiling,
                "enable_performance_monitoring": self.enable_performance_monitoring,
                "slow_request_threshold": self.slow_request_threshold
            }
        }

# Глобальный экземпляр сборщика метрик
metrics_collector = AdvancedMetricsCollector()

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware для мониторинга производительности запросов."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Начинаем профилирование
        request_id = metrics_collector.start_request_profiling(request)
        
        try:
            # Выполняем запрос
            response = await call_next(request)
            return response
        except Exception as e:
            # Логируем ошибку
            logger.error("❌ Ошибка в запросе", extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            # Создаем ответ с ошибкой
            error_response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "details": str(e)}
            )
            
            # Завершаем профилирование с ошибкой
            metrics_collector.end_request_profiling(request_id, error_response, e)
            return error_response
        finally:
            # Завершаем профилирование
            if request_id:
                metrics_collector.end_request_profiling(request_id, response)

@asynccontextmanager
async def monitor_operation(operation_name: str, context: Dict[str, Any] = None):
    """Контекстный менеджер для мониторинга операций."""
    start_time = time.time()
    operation_id = f"op_{int(time.time() * 1000)}_{id(operation_name)}"
    
    if metrics_collector.enable_detailed_logging:
        logger.debug("🚀 Начало операции", extra={
            "operation_id": operation_id,
            "operation_name": operation_name,
            "context": context or {},
            "start_time": start_time
        })
    
    try:
        yield operation_id
    except Exception as e:
        if metrics_collector.enable_detailed_logging:
            logger.error("❌ Ошибка в операции", extra={
                "operation_id": operation_id,
                "operation_name": operation_name,
                "error": str(e),
                "duration": time.time() - start_time,
                "traceback": traceback.format_exc()
            })
        raise
    finally:
        duration = time.time() - start_time
        if metrics_collector.enable_detailed_logging:
            logger.debug("✅ Завершение операции", extra={
                "operation_id": operation_id,
                "operation_name": operation_name,
                "duration": f"{duration:.3f}s"
            })

def profile_function(func_name: str = None):
    """Декоратор для профилирования функций."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or func.__name__
            async with monitor_operation(name, {"function": func.__name__}):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            
            if metrics_collector.enable_detailed_logging:
                logger.debug("🚀 Вызов функции", extra={
                    "function_name": name,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                    "start_time": start_time
                })
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if metrics_collector.enable_detailed_logging:
                    logger.debug("✅ Завершение функции", extra={
                        "function_name": name,
                        "duration": f"{duration:.3f}s"
                    })
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error("❌ Ошибка в функции", extra={
                    "function_name": name,
                    "error": str(e),
                    "duration": f"{duration:.3f}s",
                    "traceback": traceback.format_exc()
                })
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Функции для получения метрик
async def get_metrics() -> Dict[str, Any]:
    """Возвращает текущие метрики."""
    return metrics_collector.get_detailed_stats()

async def get_health_status() -> Dict[str, Any]:
    """Возвращает статус здоровья системы."""
    metrics = metrics_collector.collect_performance_metrics()
    
    # Определяем статус здоровья
    health_status = "healthy"
    issues = []
    
    if metrics.cpu_percent > 80:
        health_status = "warning"
        issues.append(f"Высокое использование CPU: {metrics.cpu_percent:.1f}%")
    
    if metrics.memory_percent > 85:
        health_status = "warning"
        issues.append(f"Высокое использование памяти: {metrics.memory_percent:.1f}%")
    
    if metrics.error_rate > 5:
        health_status = "error"
        issues.append(f"Высокий процент ошибок: {metrics.error_rate:.1f}%")
    
    if metrics.avg_response_time > 5:
        health_status = "warning"
        issues.append(f"Медленные ответы: {metrics.avg_response_time:.2f}s")
    
    return {
        "status": health_status,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - metrics_collector.start_time,
        "metrics": {
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "active_requests": metrics.active_requests,
            "error_rate": metrics.error_rate,
            "avg_response_time": metrics.avg_response_time
        },
        "issues": issues
    }

# Инициализация периодического сбора метрик
async def start_performance_monitoring():
    """Запускает периодический мониторинг производительности."""
    if not metrics_collector.enable_performance_monitoring:
        return
    
    logger.info("🚀 Запуск периодического мониторинга производительности")
    
    while True:
        try:
            metrics = metrics_collector.collect_performance_metrics()
            
            # Логируем метрики каждые 30 секунд
            logger.info("📊 Метрики производительности", extra={
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "active_requests": metrics.active_requests,
                "error_rate": metrics.error_rate,
                "avg_response_time": metrics.avg_response_time
            })
            
            await asyncio.sleep(30)
        except Exception as e:
            logger.error("❌ Ошибка в мониторинге производительности", extra={
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            await asyncio.sleep(60)  # Ждем дольше при ошибке 