"""
Middleware для LLM Tuning микросервиса
Обеспечивает обработку запросов, логирование, аутентификацию и мониторинг
"""

import time
import json
import logging
import hashlib
import hmac
from typing import Callable, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp

from .config import settings
from .database import get_db_stats

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Логируем входящий запрос
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Обрабатываем запрос
        try:
            response = await call_next(request)
            
            # Вычисляем время обработки
            process_time = time.time() - start_time
            
            # Логируем успешный ответ
            logger.info(
                f"Response: {response.status_code} "
                f"took {process_time:.3f}s "
                f"for {request.method} {request.url.path}"
            )
            
            # Добавляем заголовок с временем обработки
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Логируем ошибку
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} "
                f"took {process_time:.3f}s "
                f"for {request.method} {request.url.path}"
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_counts = {}
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Получаем IP клиента
        client_ip = request.client.host if request.client else "unknown"
        
        # Очищаем старые записи каждые 60 секунд
        current_time = time.time()
        if current_time - self.last_cleanup > 60:
            self._cleanup_old_requests(current_time)
            self.last_cleanup = current_time
        
        # Проверяем лимит запросов
        if not self._check_rate_limit(client_ip, current_time):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later."
                }
            )
        
        return await call_next(request)
    
    def _check_rate_limit(self, client_ip: str, current_time: float) -> bool:
        """Проверка лимита запросов"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Удаляем запросы старше 1 минуты
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if current_time - req_time < 60
        ]
        
        # Проверяем количество запросов
        if len(self.request_counts[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
            return False
        
        # Добавляем текущий запрос
        self.request_counts[client_ip].append(current_time)
        return True
    
    def _cleanup_old_requests(self, current_time: float):
        """Очистка старых записей"""
        for client_ip in list(self.request_counts.keys()):
            self.request_counts[client_ip] = [
                req_time for req_time in self.request_counts[client_ip]
                if current_time - req_time < 60
            ]
            if not self.request_counts[client_ip]:
                del self.request_counts[client_ip]


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware для аутентификации"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Пропускаем публичные эндпоинты
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Проверяем API ключ
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "API key required"}
            )
        
        if not self._validate_api_key(api_key):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Invalid API key"}
            )
        
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Проверка, является ли эндпоинт публичным"""
        public_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics"
        ]
        return any(path.startswith(public_path) for public_path in public_paths)
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Валидация API ключа"""
        # В реальной системе здесь будет проверка ключа в базе данных
        return api_key == settings.API_KEY


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware для мониторинга производительности"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_times = []
        self.error_counts = {}
        self.last_metrics_reset = time.time()
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Записываем метрики
            process_time = time.time() - start_time
            self._record_metrics(request, response, process_time, None)
            
            return response
            
        except Exception as e:
            # Записываем метрики ошибки
            process_time = time.time() - start_time
            self._record_metrics(request, None, process_time, str(e))
            raise
    
    def _record_metrics(self, request: Request, response: Optional[Response], 
                       process_time: float, error: Optional[str]):
        """Запись метрик"""
        # Очищаем старые метрики каждые 5 минут
        current_time = time.time()
        if current_time - self.last_metrics_reset > 300:
            self._reset_metrics()
            self.last_metrics_reset = current_time
        
        # Записываем время обработки
        self.request_times.append(process_time)
        
        # Записываем ошибки
        if error:
            endpoint = f"{request.method} {request.url.path}"
            self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1
    
    def _reset_metrics(self):
        """Сброс метрик"""
        self.request_times = []
        self.error_counts = {}
    
    def get_metrics(self) -> dict:
        """Получение текущих метрик"""
        if not self.request_times:
            return {
                "avg_response_time": 0,
                "total_requests": 0,
                "error_rate": 0
            }
        
        total_requests = len(self.request_times)
        avg_response_time = sum(self.request_times) / total_requests
        total_errors = sum(self.error_counts.values())
        error_rate = total_errors / total_requests if total_requests > 0 else 0
        
        return {
            "avg_response_time": avg_response_time,
            "total_requests": total_requests,
            "error_rate": error_rate,
            "error_counts": self.error_counts
        }


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware для безопасности"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Проверяем размер запроса
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"error": "Request too large"}
                )
        
        # Проверяем заголовки безопасности
        response = await call_next(request)
        
        # Добавляем заголовки безопасности
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class DatabaseHealthMiddleware(BaseHTTPMiddleware):
    """Middleware для проверки здоровья базы данных"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.last_check = 0
        self.db_healthy = True
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Проверяем здоровье БД каждые 30 секунд
        current_time = time.time()
        if current_time - self.last_check > 30:
            self.db_healthy = await check_db_connection()
            self.last_check = current_time
        
        # Если БД недоступна, возвращаем ошибку для критических эндпоинтов
        if not self.db_healthy and self._is_critical_endpoint(request.url.path):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "Database unavailable"}
            )
        
        return await call_next(request)
    
    def _is_critical_endpoint(self, path: str) -> bool:
        """Проверка, является ли эндпоинт критическим"""
        critical_paths = [
            "/api/models",
            "/api/routes",
            "/api/tuning",
            "/api/generate"
        ]
        return any(path.startswith(critical_path) for critical_path in critical_paths)


async def check_db_connection() -> bool:
    """Проверка подключения к базе данных"""
    try:
        stats = await get_db_stats()
        return stats.get("status") == "connected"
    except Exception:
        return False


def setup_middleware(app: ASGIApp):
    """Настройка всех middleware"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Gzip middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Database health middleware
    app.add_middleware(DatabaseHealthMiddleware)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware)
    
    # Authentication middleware
    app.add_middleware(AuthenticationMiddleware)
    
    # Monitoring middleware
    app.add_middleware(MonitoringMiddleware)
    
    # Request logging middleware (должен быть последним)
    app.add_middleware(RequestLoggingMiddleware)


@asynccontextmanager
async def lifespan_context():
    """Контекст жизненного цикла приложения"""
    # Инициализация при запуске
    logger.info("Starting LLM Tuning service...")
    
    # Проверяем подключение к БД
    db_healthy = await check_db_connection()
    if not db_healthy:
        logger.error("Database connection failed")
        raise RuntimeError("Database connection failed")
    
    logger.info("LLM Tuning service started successfully")
    
    yield
    
    # Очистка при остановке
    logger.info("Stopping LLM Tuning service...")
    logger.info("LLM Tuning service stopped") 