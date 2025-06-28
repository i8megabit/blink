"""
Кастомные исключения для LLM Tuning микросервиса
Обеспечивают единообразную обработку ошибок
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class LLMTuningException(Exception):
    """Базовое исключение для LLM Tuning микросервиса"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = None, 
        details: Dict[str, Any] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ModelNotFoundException(LLMTuningException):
    """Исключение для случая, когда модель не найдена"""
    
    def __init__(self, model_id: int, message: str = None):
        super().__init__(
            message or f"Модель с ID {model_id} не найдена",
            error_code="MODEL_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"model_id": model_id}
        )


class ModelAlreadyExistsException(LLMTuningException):
    """Исключение для случая, когда модель уже существует"""
    
    def __init__(self, model_name: str, message: str = None):
        super().__init__(
            message or f"Модель с названием '{model_name}' уже существует",
            error_code="MODEL_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
            details={"model_name": model_name}
        )


class ModelNotAvailableException(LLMTuningException):
    """Исключение для случая, когда модель недоступна"""
    
    def __init__(self, model_name: str, message: str = None):
        super().__init__(
            message or f"Модель '{model_name}' недоступна",
            error_code="MODEL_NOT_AVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"model_name": model_name}
        )


class RouteNotFoundException(LLMTuningException):
    """Исключение для случая, когда маршрут не найден"""
    
    def __init__(self, route_id: int, message: str = None):
        super().__init__(
            message or f"Маршрут с ID {route_id} не найден",
            error_code="ROUTE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"route_id": route_id}
        )


class RouteAlreadyExistsException(LLMTuningException):
    """Исключение для случая, когда маршрут уже существует"""
    
    def __init__(self, route_name: str, message: str = None):
        super().__init__(
            message or f"Маршрут с названием '{route_name}' уже существует",
            error_code="ROUTE_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
            details={"route_name": route_name}
        )


class TuningSessionNotFoundException(LLMTuningException):
    """Исключение для случая, когда сессия тюнинга не найдена"""
    
    def __init__(self, session_id: int, message: str = None):
        super().__init__(
            message or f"Сессия тюнинга с ID {session_id} не найдена",
            error_code="TUNING_SESSION_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"session_id": session_id}
        )


class TuningSessionAlreadyRunningException(LLMTuningException):
    """Исключение для случая, когда сессия тюнинга уже запущена"""
    
    def __init__(self, session_id: int, message: str = None):
        super().__init__(
            message or f"Сессия тюнинга с ID {session_id} уже запущена",
            error_code="TUNING_SESSION_ALREADY_RUNNING",
            status_code=status.HTTP_409_CONFLICT,
            details={"session_id": session_id}
        )


class TuningSessionFailedException(LLMTuningException):
    """Исключение для случая, когда сессия тюнинга завершилась с ошибкой"""
    
    def __init__(self, session_id: int, error_message: str, message: str = None):
        super().__init__(
            message or f"Сессия тюнинга с ID {session_id} завершилась с ошибкой",
            error_code="TUNING_SESSION_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"session_id": session_id, "error_message": error_message}
        )


class OllamaConnectionException(LLMTuningException):
    """Исключение для проблем с подключением к Ollama"""
    
    def __init__(self, error_message: str, message: str = None):
        super().__init__(
            message or "Ошибка подключения к Ollama",
            error_code="OLLAMA_CONNECTION_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"ollama_error": error_message}
        )


class OllamaModelNotFoundException(LLMTuningException):
    """Исключение для случая, когда модель не найдена в Ollama"""
    
    def __init__(self, model_name: str, message: str = None):
        super().__init__(
            message or f"Модель '{model_name}' не найдена в Ollama",
            error_code="OLLAMA_MODEL_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"model_name": model_name}
        )


class OllamaGenerationException(LLMTuningException):
    """Исключение для ошибок генерации в Ollama"""
    
    def __init__(self, model_name: str, error_message: str, message: str = None):
        super().__init__(
            message or f"Ошибка генерации для модели '{model_name}'",
            error_code="OLLAMA_GENERATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"model_name": model_name, "error_message": error_message}
        )


class RAGDocumentNotFoundException(LLMTuningException):
    """Исключение для случая, когда RAG документ не найден"""
    
    def __init__(self, document_id: int, message: str = None):
        super().__init__(
            message or f"RAG документ с ID {document_id} не найден",
            error_code="RAG_DOCUMENT_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"document_id": document_id}
        )


class RAGSearchException(LLMTuningException):
    """Исключение для ошибок поиска в RAG"""
    
    def __init__(self, query: str, error_message: str, message: str = None):
        super().__init__(
            message or f"Ошибка поиска в RAG для запроса '{query}'",
            error_code="RAG_SEARCH_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"query": query, "error_message": error_message}
        )


class ValidationException(LLMTuningException):
    """Исключение для ошибок валидации"""
    
    def __init__(self, field: str, value: Any, message: str = None):
        super().__init__(
            message or f"Ошибка валидации поля '{field}' со значением '{value}'",
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": field, "value": value}
        )


class ConfigurationException(LLMTuningException):
    """Исключение для ошибок конфигурации"""
    
    def __init__(self, config_key: str, message: str = None):
        super().__init__(
            message or f"Ошибка конфигурации для ключа '{config_key}'",
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"config_key": config_key}
        )


class DatabaseException(LLMTuningException):
    """Исключение для ошибок базы данных"""
    
    def __init__(self, operation: str, error_message: str, message: str = None):
        super().__init__(
            message or f"Ошибка базы данных при операции '{operation}'",
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"operation": operation, "error_message": error_message}
        )


class RateLimitExceededException(LLMTuningException):
    """Исключение для превышения лимита запросов"""
    
    def __init__(self, client_ip: str, limit: int, message: str = None):
        super().__init__(
            message or f"Превышен лимит запросов для IP {client_ip}",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"client_ip": client_ip, "limit": limit}
        )


class AuthenticationException(LLMTuningException):
    """Исключение для ошибок аутентификации"""
    
    def __init__(self, message: str = "Ошибка аутентификации"):
        super().__init__(
            message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(LLMTuningException):
    """Исключение для ошибок авторизации"""
    
    def __init__(self, resource: str, message: str = None):
        super().__init__(
            message or f"Нет доступа к ресурсу '{resource}'",
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"resource": resource}
        )


class OptimizationException(LLMTuningException):
    """Исключение для ошибок оптимизации"""
    
    def __init__(self, model_id: int, error_message: str, message: str = None):
        super().__init__(
            message or f"Ошибка оптимизации модели с ID {model_id}",
            error_code="OPTIMIZATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"model_id": model_id, "error_message": error_message}
        )


class MonitoringException(LLMTuningException):
    """Исключение для ошибок мониторинга"""
    
    def __init__(self, metric_name: str, error_message: str, message: str = None):
        super().__init__(
            message or f"Ошибка мониторинга метрики '{metric_name}'",
            error_code="MONITORING_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"metric_name": metric_name, "error_message": error_message}
        )


def handle_llm_tuning_exception(exc: LLMTuningException) -> Dict[str, Any]:
    """Обработчик для кастомных исключений"""
    return {
        "success": False,
        "error": exc.message,
        "error_code": exc.error_code,
        "details": exc.details,
        "status_code": exc.status_code
    }


def convert_to_http_exception(exc: LLMTuningException) -> HTTPException:
    """Конвертация кастомного исключения в HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    ) 