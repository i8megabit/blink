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


class BlinkBaseException(Exception):
    """Базовое исключение для приложения Blink"""
    
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


class ValidationException(BlinkBaseException):
    """Исключение для ошибок валидации"""
    
    def __init__(self, message: str, field_errors: Dict[str, str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or {}},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class AuthenticationException(BlinkBaseException):
    """Исключение для ошибок аутентификации"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(BlinkBaseException):
    """Исключение для ошибок авторизации"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundException(BlinkBaseException):
    """Исключение для ресурсов, которые не найдены"""
    
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id is not None:
            message += f" with id: {resource_id}"
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id},
            status_code=status.HTTP_404_NOT_FOUND
        )


class DatabaseException(BlinkBaseException):
    """Исключение для ошибок базы данных"""
    
    def __init__(self, message: str, operation: str = None, table: str = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={"operation": operation, "table": table},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CacheException(BlinkBaseException):
    """Исключение для ошибок кэширования"""
    
    def __init__(self, message: str, cache_type: str = None):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details={"cache_type": cache_type},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class OllamaException(BlinkBaseException):
    """Исключение для ошибок Ollama"""
    
    def __init__(self, message: str, model: str = None, operation: str = None):
        super().__init__(
            message=message,
            error_code="OLLAMA_ERROR",
            details={"model": model, "operation": operation},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class RateLimitException(BlinkBaseException):
    """Исключение для превышения лимита запросов"""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class FileProcessingException(BlinkBaseException):
    """Исключение для ошибок обработки файлов"""
    
    def __init__(self, message: str, file_type: str = None, file_size: int = None):
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details={"file_type": file_type, "file_size": file_size},
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ExternalServiceException(BlinkBaseException):
    """Исключение для ошибок внешних сервисов"""
    
    def __init__(self, message: str, service: str = None, status_code: int = None):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "external_status_code": status_code},
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class ConfigurationException(BlinkBaseException):
    """Исключение для ошибок конфигурации"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class BusinessLogicException(BlinkBaseException):
    """Исключение для ошибок бизнес-логики"""
    
    def __init__(self, message: str, business_rule: str = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details={"business_rule": business_rule},
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ErrorHandler:
    """Класс для централизованной обработки ошибок"""
    
    @staticmethod
    def handle_validation_error(error: ValidationError) -> Dict[str, Any]:
        """Обработка ошибок валидации Pydantic"""
        field_errors = {}
        for err in error.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            field_errors[field] = err["msg"]
        
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {"field_errors": field_errors},
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    def handle_blink_exception(error: BlinkBaseException) -> Dict[str, Any]:
        """Обработка кастомных исключений Blink"""
        return {
            "error": {
                "code": error.error_code,
                "message": error.message,
                "details": error.details,
                "timestamp": error.timestamp.isoformat()
            }
        }
    
    @staticmethod
    def handle_http_exception(error: HTTPException) -> Dict[str, Any]:
        """Обработка HTTP исключений FastAPI"""
        return {
            "error": {
                "code": "HTTP_ERROR",
                "message": error.detail,
                "status_code": error.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    def handle_generic_exception(error: Exception) -> Dict[str, Any]:
        """Обработка общих исключений"""
        # Логируем полную информацию об ошибке
        logger.error(f"Unhandled exception: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    def log_error(error: Exception, context: Dict[str, Any] = None):
        """Логирование ошибки с контекстом"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        if isinstance(error, BlinkBaseException):
            logger.error(f"Blink exception: {error_info}")
        elif isinstance(error, HTTPException):
            logger.warning(f"HTTP exception: {error_info}")
        else:
            logger.error(f"Unexpected exception: {error_info}")


class ErrorResponse:
    """Модель для стандартизированных ответов с ошибками"""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat()
            }
        }
    
    @classmethod
    def from_exception(cls, error: Exception) -> 'ErrorResponse':
        """Создание ответа из исключения"""
        if isinstance(error, BlinkBaseException):
            return cls(
                code=error.error_code,
                message=error.message,
                details=error.details,
                status_code=error.status_code
            )
        elif isinstance(error, HTTPException):
            return cls(
                code="HTTP_ERROR",
                message=error.detail,
                status_code=error.status_code
            )
        else:
            return cls(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Утилиты для создания исключений
def raise_not_found(resource: str, resource_id: Any = None):
    """Создание исключения NotFoundException"""
    raise NotFoundException(resource, resource_id)


def raise_validation_error(message: str, field_errors: Dict[str, str] = None):
    """Создание исключения ValidationException"""
    raise ValidationException(message, field_errors)


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


def raise_rate_limit_error(retry_after: int = 60):
    """Создание исключения RateLimitException"""
    raise RateLimitException(retry_after)


def raise_business_logic_error(message: str, business_rule: str = None):
    """Создание исключения BusinessLogicException"""
    raise BusinessLogicException(message, business_rule) 