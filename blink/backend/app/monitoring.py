"""
Модуль мониторинга и логирования для Blink
Интеграция Prometheus, OpenTelemetry и структурированного логирования
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

# Настройка логирования
class StructuredFormatter(logging.Formatter):
    """Структурированный форматтер для логов"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем дополнительные поля
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        
        # Добавляем исключения
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

class MonitoringService:
    """Сервис мониторинга и логирования"""
    
    def __init__(self, service_name: str = "blink-backend"):
        self.service_name = service_name
        self.logger = self._setup_logger()
        self.tracer = self._setup_tracing()
        self.meter = self._setup_metrics()
        self._setup_prometheus_metrics()
    
    def _setup_logger(self) -> logging.Logger:
        """Настройка структурированного логирования"""
        logger = logging.getLogger(self.service_name)
        logger.setLevel(logging.INFO)
        
        # Удаляем существующие обработчики
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        logger.addHandler(console_handler)
        
        # Файловый обработчик
        file_handler = logging.FileHandler(f"logs/{self.service_name}.log")
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
        
        return logger
    
    def _setup_tracing(self) -> trace.Tracer:
        """Настройка распределенной трассировки"""
        # Создаем провайдер трассировки
        trace_provider = TracerProvider()
        
        # Настраиваем экспорт в Jaeger
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
        
        # Добавляем процессор для экспорта
        trace_provider.add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        
        # Устанавливаем провайдер
        trace.set_tracer_provider(trace_provider)
        
        return trace.get_tracer(self.service_name)
    
    def _setup_metrics(self) -> metrics.Meter:
        """Настройка метрик OpenTelemetry"""
        # Создаем провайдер метрик
        metric_reader = PrometheusMetricReader()
        meter_provider = MeterProvider(metric_reader=metric_reader)
        metrics.set_meter_provider(meter_provider)
        
        return metrics.get_meter(self.service_name)
    
    def _setup_prometheus_metrics(self):
        """Настройка Prometheus метрик"""
        # HTTP метрики
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        # Бизнес метрики
        self.seo_analyses_total = Counter(
            'seo_analyses_total',
            'Total SEO analyses performed',
            ['domain', 'status']
        )
        
        self.active_users = Gauge(
            'active_users',
            'Number of active users'
        )
        
        self.database_connections = Gauge(
            'database_connections',
            'Number of active database connections'
        )
    
    def log_request(self, request: Request, response: Response, duration: float):
        """Логирование HTTP запроса"""
        # Создаем запись лога
        log_record = logging.LogRecord(
            name=self.service_name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"{request.method} {request.url.path}",
            args=(),
            exc_info=None
        )
        
        # Добавляем дополнительные поля
        log_record.status_code = response.status_code
        log_record.duration = duration
        log_record.request_id = request.headers.get('X-Request-ID', 'unknown')
        
        # Логируем запрос
        self.logger.handle(log_record)
        
        # Обновляем метрики
        self.http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        self.http_request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
    
    def log_seo_analysis(self, domain: str, status: str, duration: float = None):
        """Логирование SEO анализа"""
        self.seo_analyses_total.labels(domain=domain, status=status).inc()
        
        log_record = logging.LogRecord(
            name=self.service_name,
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=f"SEO analysis completed for {domain}",
            args=(),
            exc_info=None
        )
        
        log_record.duration = duration
        self.logger.handle(log_record)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Логирование ошибок"""
        log_record = logging.LogRecord(
            name=self.service_name,
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg=str(error),
            args=(),
            exc_info=(type(error), error, error.__traceback__)
        )
        
        if context:
            for key, value in context.items():
                setattr(log_record, key, value)
        
        self.logger.handle(log_record)
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str, attributes: Dict[str, Any] = None):
        """Контекстный менеджер для трассировки операций"""
        with self.tracer.start_as_current_span(operation_name, attributes=attributes) as span:
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    
    def instrument_fastapi(self, app):
        """Инструментирование FastAPI приложения"""
        FastAPIInstrumentor.instrument_app(app)
    
    def instrument_sqlalchemy(self, engine):
        """Инструментирование SQLAlchemy"""
        SQLAlchemyInstrumentor().instrument(engine=engine)
    
    def instrument_requests(self):
        """Инструментирование HTTP клиентов"""
        RequestsInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
    
    def get_metrics(self) -> str:
        """Получение метрик в формате Prometheus"""
        return generate_latest()
    
    def update_active_users(self, count: int):
        """Обновление количества активных пользователей"""
        self.active_users.set(count)
    
    def update_database_connections(self, count: int):
        """Обновление количества подключений к БД"""
        self.database_connections.set(count)

# Глобальный экземпляр сервиса мониторинга
monitoring = MonitoringService()

# Декораторы для мониторинга
def monitor_function(operation_name: str):
    """Декоратор для мониторинга функций"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            with monitoring.trace_operation(operation_name) as span:
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Логируем успешное выполнение
                    log_record = logging.LogRecord(
                        name=monitoring.service_name,
                        level=logging.INFO,
                        pathname="",
                        lineno=0,
                        msg=f"Function {operation_name} completed successfully",
                        args=(),
                        exc_info=None
                    )
                    log_record.duration = duration
                    monitoring.logger.handle(log_record)
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    monitoring.log_error(e, {
                        'operation': operation_name,
                        'duration': duration
                    })
                    raise
        
        return wrapper
    return decorator

def monitor_database_operation(operation_type: str):
    """Декоратор для мониторинга операций с БД"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            with monitoring.trace_operation(f"db.{operation_type}") as span:
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Обновляем метрики БД
                    span.set_attribute("db.operation", operation_type)
                    span.set_attribute("db.duration", duration)
                    
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
        
        return wrapper
    return decorator

# Middleware для FastAPI
async def monitoring_middleware(request: Request, call_next):
    """Middleware для мониторинга HTTP запросов"""
    start_time = time.time()
    
    # Добавляем request ID если его нет
    if 'X-Request-ID' not in request.headers:
        request.headers.__dict__['_list'].append(
            (b'x-request-id', str(time.time()).encode())
        )
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Логируем запрос
        monitoring.log_request(request, response, duration)
        
        # Добавляем заголовки мониторинга
        response.headers['X-Request-ID'] = request.headers.get('X-Request-ID', 'unknown')
        response.headers['X-Response-Time'] = str(duration)
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        monitoring.log_error(e, {
            'request_method': request.method,
            'request_path': request.url.path,
            'duration': duration
        })
        raise

# Endpoint для метрик Prometheus
async def metrics_endpoint():
    """Endpoint для получения метрик Prometheus"""
    return PlainTextResponse(
        monitoring.get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )

# Endpoint для проверки здоровья
async def health_check():
    """Endpoint для проверки здоровья приложения"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": monitoring.service_name,
        "version": "1.0.0"
    } 