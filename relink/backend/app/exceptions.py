"""
Модуль для централизованной обработки ошибок
Содержит кастомные исключения и обработчики
"""

from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from pydantic import ValidationError
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


class RelinkBaseException(Exception):
    """Базовое исключение для приложения reLink"""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)


class ValidationException(RelinkBaseException):
    """Исключение для ошибок валидации"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {"field": field, "value": value} if field else {}
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AuthenticationException(RelinkBaseException):
    """Исключение для ошибок аутентификации"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(RelinkBaseException):
    """Исключение для ошибок авторизации"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(RelinkBaseException):
    """Исключение для ресурсов, которые не найдены"""
    
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" with id: {resource_id}"
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id},
            status_code=status.HTTP_404_NOT_FOUND
        )


class DatabaseException(RelinkBaseException):
    """Исключение для ошибок базы данных"""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        details = {"operation": operation, "table": table} if operation else {}
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CacheException(RelinkBaseException):
    """Исключение для ошибок кэширования"""
    
    def __init__(self, message: str, cache_type: str = None, key: str = None):
        details = {"cache_type": cache_type, "key": key} if cache_type else {}
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class OllamaException(RelinkBaseException):
    """Исключение для ошибок Ollama"""
    
    def __init__(self, message: str, model: str = None, operation: str = None):
        details = {"model": model, "operation": operation} if model else {}
        super().__init__(
            message=message,
            error_code="OLLAMA_ERROR",
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class RateLimitException(RelinkBaseException):
    """Исключение для превышения лимита запросов"""
    
    def __init__(self, limit: int = None, window: int = None):
        message = "Rate limit exceeded"
        details = {"limit": limit, "window": window} if limit else {}
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class FileProcessingException(RelinkBaseException):
    """Исключение для ошибок обработки файлов"""
    
    def __init__(self, message: str, file_path: str = None, file_type: str = None):
        details = {"file_path": file_path, "file_type": file_type} if file_path else {}
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ExternalServiceException(RelinkBaseException):
    """Исключение для ошибок внешних сервисов"""
    
    def __init__(self, message: str, service: str = None, endpoint: str = None):
        details = {"service": service, "endpoint": endpoint} if service else {}
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class ConfigurationException(RelinkBaseException):
    """Исключение для ошибок конфигурации"""
    
    def __init__(self, message: str, config_key: str = None):
        details = {"config_key": config_key} if config_key else {}
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class BusinessLogicException(RelinkBaseException):
    """Исключение для ошибок бизнес-логики"""
    
    def __init__(self, message: str, operation: str = None, context: Dict[str, Any] = None):
        details = {"operation": operation, "context": context} if operation else {}
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ErrorHandler:
    """Класс для централизованной обработки ошибок"""
    
    @staticmethod
    def handle_relink_exception(error: RelinkBaseException) -> Dict[str, Any]:
        """Обработка кастомных исключений reLink"""
        error_response = ErrorResponse(
            message=error.message,
            error_code=error.error_code,
            status_code=error.status_code,
            details=error.details
        )
        
        # Логирование ошибки
        logger.error(
            f"reLink exception: {error.error_code} - {error.message}",
            extra={
                "error_code": error.error_code,
                "status_code": error.status_code,
                "details": error.details,
                "traceback": traceback.format_exc()
            }
        )
        
        return error_response.to_dict()
    
    @staticmethod
    def handle_validation_error(error: ValidationError) -> Dict[str, Any]:
        """Обработка ошибок валидации Pydantic"""
        error_details = []
        for err in error.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"]
            })
        
        error_response = ErrorResponse(
            message="Validation error",
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": error_details}
        )
        
        logger.warning(f"Validation error: {error_details}")
        return error_response.to_dict()
    
    @staticmethod
    def handle_http_exception(error: HTTPException) -> Dict[str, Any]:
        """Обработка HTTP исключений FastAPI"""
        error_response = ErrorResponse(
            message=error.detail,
            error_code="HTTP_ERROR",
            status_code=error.status_code
        )
        
        logger.warning(f"HTTP exception: {error.status_code} - {error.detail}")
        return error_response.to_dict()
    
    @staticmethod
    def handle_generic_exception(error: Exception) -> Dict[str, Any]:
        """Обработка общих исключений"""
        error_response = ErrorResponse(
            message="Internal server error",
            error_code="INTERNAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"exception_type": type(error).__name__}
        )
        
        # Логирование с полным стеком
        logger.error(
            f"Unhandled exception: {type(error).__name__} - {str(error)}",
            exc_info=True
        )
        
        return error_response.to_dict()


class ErrorResponse:
    """Модель для стандартизированных ответов с ошибками"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int,
        details: Dict[str, Any] = None,
        timestamp: str = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "status_code": self.status_code,
                "details": self.details,
                "timestamp": self.timestamp
            }
        }
    
    @classmethod
    def from_exception(cls, error: Exception) -> 'ErrorResponse':
        """Создание ответа из исключения"""
        if isinstance(error, RelinkBaseException):
            return cls(
                message=error.message,
                error_code=error.error_code,
                status_code=error.status_code,
                details=error.details
            )
        elif isinstance(error, HTTPException):
            return cls(
                message=error.detail,
                error_code="HTTP_ERROR",
                status_code=error.status_code
            )
        else:
            return cls(
                message="Internal server error",
                error_code="INTERNAL_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Утилиты для создания исключений
def raise_not_found(resource: str, resource_id: Any = None):
    """Создание исключения NotFoundException"""
    raise NotFoundException(resource, resource_id)


def raise_validation_error(message: str, field: str = None, value: Any = None):
    """Создание исключения ValidationException"""
    raise ValidationException(message, field, value)


def raise_authentication_error(message: str = "Authentication failed"):
    """Создание исключения AuthenticationException"""
    raise AuthenticationException(message)


def raise_authorization_error(message: str = "Access denied"):
    """Создание исключения AuthorizationException"""
    raise AuthorizationException(message)


def raise_database_error(message: str, operation: str = None, table: str = None):
    """Создание исключения DatabaseException"""
    raise DatabaseException(message, operation, table)


def raise_ollama_error(message: str, model: str = None, operation: str = None):
    """Создание исключения OllamaException"""
    raise OllamaException(message, model, operation)


def raise_rate_limit_error(limit: int = None, window: int = None):
    """Создание исключения RateLimitException"""
    raise RateLimitException(limit, window)


def raise_business_logic_error(message: str, operation: str = None, context: Dict[str, Any] = None):
    """Создание исключения BusinessLogicException"""
    raise BusinessLogicException(message, operation, context)


def setup_exception_handlers(app):
    """Настройка обработчиков исключений для FastAPI приложения"""
    
    @app.exception_handler(RelinkBaseException)
    async def relink_exception_handler(request, exc: RelinkBaseException):
        """Обработчик кастомных исключений reLink"""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorHandler.handle_relink_exception(exc)
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request, exc: ValidationError):
        """Обработчик ошибок валидации"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorHandler.handle_validation_error(exc)
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        """Обработчик HTTP исключений"""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorHandler.handle_http_exception(exc)
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc: Exception):
        """Обработчик общих исключений"""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorHandler.handle_generic_exception(exc)
        )


# Экспорт для обратной совместимости
RelinkBaseException = RelinkBaseException 