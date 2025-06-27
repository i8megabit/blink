"""
Middleware для централизованной обработки ошибок
Обеспечивает единообразную обработку всех исключений
"""

from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
import time
import traceback
from datetime import datetime

from ..exceptions import (
    BlinkBaseException,
    ErrorHandler,
    ErrorResponse,
    HTTPException
)

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware:
    """Middleware для обработки ошибок"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        try:
            # Обрабатываем запрос
            await self.app(scope, receive, send)
            
            # Логируем успешные запросы (опционально)
            process_time = time.time() - start_time
            logger.info(
                f"Request processed successfully: {request.method} {request.url.path} "
                f"in {process_time:.3f}s"
            )
            
        except Exception as exc:
            # Обрабатываем исключения
            await self._handle_exception(exc, request, start_time)
    
    async def _handle_exception(
        self,
        exc: Exception,
        request: Request,
        start_time: float
    ):
        """Обработка исключения"""
        process_time = time.time() - start_time
        
        # Логируем ошибку
        self._log_error(exc, request, process_time)
        
        # Создаем ответ с ошибкой
        error_response = self._create_error_response(exc)
        
        # Отправляем ответ
        response = JSONResponse(
            content=error_response,
            status_code=error_response["error"].get("status_code", 500)
        )
        
        # Добавляем заголовки
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Error-Code"] = error_response["error"]["code"]
        
        # Отправляем ответ
        await response(scope, receive, send)
    
    def _log_error(self, exc: Exception, request: Request, process_time: float):
        """Логирование ошибки"""
        error_info = {
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "request_method": request.method,
            "request_url": str(request.url),
            "request_headers": dict(request.headers),
            "process_time": process_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Добавляем контекст запроса
        if hasattr(request, "client"):
            error_info["client_ip"] = request.client.host
            error_info["client_port"] = request.client.port
        
        # Добавляем параметры запроса
        error_info["query_params"] = dict(request.query_params)
        
        # Логируем в зависимости от типа ошибки
        if isinstance(exc, BlinkBaseException):
            logger.error(f"Blink exception: {error_info}")
        elif isinstance(exc, HTTPException):
            logger.warning(f"HTTP exception: {error_info}")
        elif isinstance(exc, ValidationError):
            logger.warning(f"Validation error: {error_info}")
        else:
            logger.error(f"Unexpected exception: {error_info}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _create_error_response(self, exc: Exception) -> Dict[str, Any]:
        """Создание стандартизированного ответа с ошибкой"""
        if isinstance(exc, BlinkBaseException):
            return ErrorHandler.handle_blink_exception(exc)
        elif isinstance(exc, HTTPException):
            return ErrorHandler.handle_http_exception(exc)
        elif isinstance(exc, ValidationError):
            return ErrorHandler.handle_validation_error(exc)
        else:
            return ErrorHandler.handle_generic_exception(exc)


class RequestLoggingMiddleware:
    """Middleware для логирования запросов"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # Логируем начало запроса
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Логируем ошибку
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"with error: {type(exc).__name__}: {str(exc)}"
            )
            raise
        finally:
            # Логируем завершение запроса
            process_time = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"in {process_time:.3f}s"
            )


class RateLimitMiddleware:
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"
        
        # Проверяем лимит запросов
        if self._is_rate_limited(client_ip):
            response = JSONResponse(
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded",
                        "details": {"retry_after": 60},
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                status_code=429
            )
            await response(scope, receive, send)
            return
        
        # Увеличиваем счетчик запросов
        self._increment_request_count(client_ip)
        
        await self.app(scope, receive, send)
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Проверка, превышен ли лимит запросов"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Очищаем старые записи
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip]
                if timestamp > minute_ago
            ]
        
        # Проверяем количество запросов
        request_count = len(self.request_counts.get(client_ip, []))
        return request_count >= self.requests_per_minute
    
    def _increment_request_count(self, client_ip: str):
        """Увеличение счетчика запросов"""
        current_time = time.time()
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append(current_time)


class SecurityMiddleware:
    """Middleware для безопасности"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Добавляем заголовки безопасности
        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                
                # Добавляем заголовки безопасности
                security_headers = [
                    (b"X-Content-Type-Options", b"nosniff"),
                    (b"X-Frame-Options", b"DENY"),
                    (b"X-XSS-Protection", b"1; mode=block"),
                    (b"Strict-Transport-Security", b"max-age=31536000; includeSubDomains"),
                    (b"Content-Security-Policy", b"default-src 'self'"),
                ]
                
                headers.extend(security_headers)
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, secure_send)


class PerformanceMiddleware:
    """Middleware для мониторинга производительности"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # Добавляем информацию о времени выполнения
        async def performance_send(message):
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                headers = message.get("headers", [])
                
                # Добавляем заголовки производительности
                performance_headers = [
                    (b"X-Process-Time", str(process_time).encode()),
                    (b"X-Request-ID", str(hash(request.url)).encode()),
                ]
                
                headers.extend(performance_headers)
                message["headers"] = headers
                
                # Логируем медленные запросы
                if process_time > 1.0:  # Больше 1 секунды
                    logger.warning(
                        f"Slow request: {request.method} {request.url.path} "
                        f"took {process_time:.3f}s"
                    )
            
            await send(message)
        
        await self.app(scope, receive, performance_send)


def setup_error_handlers(app):
    """Настройка обработчиков ошибок для FastAPI приложения"""
    
    @app.exception_handler(BlinkBaseException)
    async def blink_exception_handler(request: Request, exc: BlinkBaseException):
        """Обработчик кастомных исключений Blink"""
        ErrorHandler.log_error(exc, {"request_url": str(request.url)})
        return JSONResponse(
            content=ErrorHandler.handle_blink_exception(exc),
            status_code=exc.status_code
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Обработчик ошибок валидации Pydantic"""
        ErrorHandler.log_error(exc, {"request_url": str(request.url)})
        return JSONResponse(
            content=ErrorHandler.handle_validation_error(exc),
            status_code=422
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Обработчик HTTP исключений FastAPI"""
        ErrorHandler.log_error(exc, {"request_url": str(request.url)})
        return JSONResponse(
            content=ErrorHandler.handle_http_exception(exc),
            status_code=exc.status_code
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Обработчик общих исключений"""
        ErrorHandler.log_error(exc, {"request_url": str(request.url)})
        return JSONResponse(
            content=ErrorHandler.handle_generic_exception(exc),
            status_code=500
        ) 