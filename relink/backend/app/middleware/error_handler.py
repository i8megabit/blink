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
    RelinkBaseException,
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
        
        start_time = time.time()
        
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Обрабатываем исключение
            await self._handle_exception(scope, exc, start_time)
    
    async def _handle_exception(self, scope, exc, start_time):
        """Обработка исключения"""
        duration = time.time() - start_time
        
        # Логируем ошибку
        error_info = {
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "duration": duration,
            "path": scope.get("path", "unknown"),
            "method": scope.get("method", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if isinstance(exc, RelinkBaseException):
            logger.error(f"reLink exception: {error_info}")
        else:
            logger.error(f"Unexpected exception: {error_info}", exc_info=True)
        
        # Создаем ответ с ошибкой
        if isinstance(exc, RelinkBaseException):
            response_data = ErrorHandler.handle_relink_exception(exc)
            status_code = exc.status_code
        elif isinstance(exc, ValidationError):
            response_data = ErrorHandler.handle_validation_error(exc)
            status_code = 422
        elif isinstance(exc, HTTPException):
            response_data = ErrorHandler.handle_http_exception(exc)
            status_code = exc.status_code
        else:
            response_data = ErrorHandler.handle_generic_exception(exc)
            status_code = 500
        
        # Отправляем ответ
        await self._send_error_response(scope, response_data, status_code)
    
    async def _send_error_response(self, scope, response_data, status_code):
        """Отправка ответа с ошибкой"""
        response = JSONResponse(
            content=response_data,
            status_code=status_code,
            headers={
                "Content-Type": "application/json",
                "X-Error-Type": type(response_data.get("error", {})).__name__
            }
        )
        
        await response(scope, None, None)


class RequestLoggingMiddleware:
    """Middleware для логирования запросов"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        # Логируем входящий запрос
        logger.info(
            "Incoming request",
            request_id=request_id,
            method=scope.get("method", "unknown"),
            path=scope.get("path", "unknown"),
            client_ip=scope.get("client", ("unknown", 0))[0],
            user_agent=dict(scope.get("headers", [])).get(b"user-agent", b"").decode("utf-8", errors="ignore")
        )
        
        # Обрабатываем запрос
        try:
            await self.app(scope, receive, send)
            duration = time.time() - start_time
            
            # Логируем успешный ответ
            logger.info(
                "Request completed",
                request_id=request_id,
                duration=duration,
                status="success"
            )
            
        except Exception as exc:
            duration = time.time() - start_time
            
            # Логируем ошибку
            logger.error(
                "Request failed",
                request_id=request_id,
                duration=duration,
                error=str(exc),
                error_type=type(exc).__name__,
                status="error"
            )
            raise


class RateLimitMiddleware:
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, app, requests_per_minute=60):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        client_ip = scope.get("client", ("unknown", 0))[0]
        current_time = time.time()
        
        # Очищаем старые записи
        self._cleanup_old_requests(current_time)
        
        # Проверяем лимит
        if not self._check_rate_limit(client_ip, current_time):
            await self._send_rate_limit_response(scope)
            return
        
        # Добавляем запрос
        self._add_request(client_ip, current_time)
        
        # Обрабатываем запрос
        await self.app(scope, receive, send)
    
    def _cleanup_old_requests(self, current_time):
        """Очистка старых записей"""
        cutoff_time = current_time - 60  # 1 минута
        for client_ip in list(self.requests.keys()):
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > cutoff_time
            ]
            if not self.requests[client_ip]:
                del self.requests[client_ip]
    
    def _check_rate_limit(self, client_ip, current_time):
        """Проверка лимита запросов"""
        if client_ip not in self.requests:
            return True
        
        requests_count = len(self.requests[client_ip])
        return requests_count < self.requests_per_minute
    
    def _add_request(self, client_ip, current_time):
        """Добавление запроса"""
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
    
    async def _send_rate_limit_response(self, scope):
        """Отправка ответа о превышении лимита"""
        response_data = {
            "error": {
                "message": "Rate limit exceeded",
                "code": "RATE_LIMIT_EXCEEDED",
                "status_code": 429,
                "details": {
                    "limit": self.requests_per_minute,
                    "window": "1 minute"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        response = JSONResponse(
            content=response_data,
            status_code=429,
            headers={
                "Content-Type": "application/json",
                "Retry-After": "60"
            }
        )
        
        await response(scope, None, None)


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
                headers = dict(message.get("headers", []))
                
                # Добавляем заголовки безопасности
                security_headers = {
                    b"X-Content-Type-Options": b"nosniff",
                    b"X-Frame-Options": b"DENY",
                    b"X-XSS-Protection": b"1; mode=block",
                    b"Strict-Transport-Security": b"max-age=31536000; includeSubDomains",
                    b"Content-Security-Policy": b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
                    b"Referrer-Policy": b"strict-origin-when-cross-origin"
                }
                
                # Обновляем заголовки
                for key, value in security_headers.items():
                    headers[key] = value
                
                # Преобразуем обратно в список
                message["headers"] = list(headers.items())
            
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
        
        start_time = time.time()
        
        # Обрабатываем запрос
        await self.app(scope, receive, send)
        
        duration = time.time() - start_time
        
        # Логируем производительность
        if duration > 1.0:  # Запросы дольше 1 секунды
            logger.warning(
                "Slow request detected",
                path=scope.get("path", "unknown"),
                method=scope.get("method", "unknown"),
                duration=duration
            )
        elif duration > 0.5:  # Запросы дольше 0.5 секунды
            logger.info(
                "Moderate request duration",
                path=scope.get("path", "unknown"),
                method=scope.get("method", "unknown"),
                duration=duration
            )


def setup_error_handlers(app):
    """Настройка обработчиков ошибок для FastAPI приложения"""
    
    @app.exception_handler(RelinkBaseException)
    async def relink_exception_handler(request: Request, exc: RelinkBaseException):
        """Обработчик кастомных исключений reLink"""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorHandler.handle_relink_exception(exc)
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Обработчик ошибок валидации"""
        return JSONResponse(
            status_code=422,
            content=ErrorHandler.handle_validation_error(exc)
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Обработчик HTTP исключений"""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorHandler.handle_http_exception(exc)
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Обработчик общих исключений"""
        return JSONResponse(
            status_code=500,
            content=ErrorHandler.handle_generic_exception(exc)
        )


# Экспорт для обратной совместимости
BlinkErrorHandlerMiddleware = ErrorHandlerMiddleware 