"""
Тесты для модуля мониторинга
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.monitoring import (
    MonitoringService, StructuredFormatter, monitor_function,
    monitor_database_operation, monitoring_middleware
)
from app.validation import ValidationError


class TestStructuredFormatter:
    """Тесты для структурированного форматтера логов"""
    
    def test_format_basic_log(self):
        """Тест базового форматирования лога"""
        formatter = StructuredFormatter()
        
        # Создаем mock запись лога
        log_record = Mock()
        log_record.levelname = "INFO"
        log_record.name = "test_logger"
        log_record.getMessage.return_value = "Test message"
        log_record.module = "test_module"
        log_record.funcName = "test_function"
        log_record.lineno = 42
        log_record.exc_info = None
        
        result = formatter.format(log_record)
        
        # Проверяем, что результат - валидный JSON
        import json
        parsed = json.loads(result)
        
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test_module"
        assert parsed["function"] == "test_function"
        assert parsed["line"] == 42
        assert "timestamp" in parsed
    
    def test_format_log_with_extra_fields(self):
        """Тест форматирования лога с дополнительными полями"""
        formatter = StructuredFormatter()
        
        log_record = Mock()
        log_record.levelname = "ERROR"
        log_record.name = "test_logger"
        log_record.getMessage.return_value = "Error message"
        log_record.module = "test_module"
        log_record.funcName = "test_function"
        log_record.lineno = 42
        log_record.exc_info = None
        
        # Добавляем дополнительные поля
        log_record.user_id = 123
        log_record.request_id = "req-456"
        log_record.duration = 1.5
        log_record.status_code = 500
        
        result = formatter.format(log_record)
        parsed = json.loads(result)
        
        assert parsed["user_id"] == 123
        assert parsed["request_id"] == "req-456"
        assert parsed["duration"] == 1.5
        assert parsed["status_code"] == 500


class TestMonitoringService:
    """Тесты для сервиса мониторинга"""
    
    @pytest.fixture
    def monitoring_service(self):
        """Фикстура для сервиса мониторинга"""
        return MonitoringService("test-service")
    
    def test_initialization(self, monitoring_service):
        """Тест инициализации сервиса мониторинга"""
        assert monitoring_service.service_name == "test-service"
        assert monitoring_service.logger is not None
        assert monitoring_service.tracer is not None
        assert monitoring_service.meter is not None
    
    def test_log_request(self, monitoring_service):
        """Тест логирования HTTP запроса"""
        # Создаем mock объекты
        request = Mock()
        request.method = "GET"
        request.url.path = "/api/test"
        request.headers.get.return_value = "req-123"
        
        response = Mock()
        response.status_code = 200
        
        # Логируем запрос
        monitoring_service.log_request(request, response, 0.5)
        
        # Проверяем, что метрики обновлены
        assert monitoring_service.http_requests_total._value.sum() == 1
        assert monitoring_service.http_request_duration._sum.sum() == 0.5
    
    def test_log_seo_analysis(self, monitoring_service):
        """Тест логирования SEO анализа"""
        monitoring_service.log_seo_analysis("example.com", "completed", 2.5)
        
        # Проверяем, что метрика обновлена
        assert monitoring_service.seo_analyses_total._value.sum() == 1
    
    def test_log_error(self, monitoring_service):
        """Тест логирования ошибок"""
        error = ValueError("Test error")
        context = {"operation": "test", "user_id": 123}
        
        monitoring_service.log_error(error, context)
        
        # Проверяем, что ошибка залогирована
        # В реальном тесте здесь можно проверить логи


@pytest.mark.asyncio
class TestMonitoringDecorators:
    """Тесты для декораторов мониторинга"""
    
    @pytest.fixture
    def monitoring_service(self):
        """Фикстура для сервиса мониторинга"""
        return MonitoringService("test-service")
    
    async def test_monitor_function_decorator(self, monitoring_service):
        """Тест декоратора monitor_function"""
        
        @monitor_function("test_operation")
        async def test_function():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await test_function()
        assert result == "success"
        
        # Проверяем, что операция залогирована
        # В реальном тесте здесь можно проверить логи
    
    async def test_monitor_function_with_error(self, monitoring_service):
        """Тест декоратора monitor_function с ошибкой"""
        
        @monitor_function("test_operation")
        async def test_function_with_error():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await test_function_with_error()
        
        # Проверяем, что ошибка залогирована
        # В реальном тесте здесь можно проверить логи
    
    async def test_monitor_database_operation(self, monitoring_service):
        """Тест декоратора monitor_database_operation"""
        
        @monitor_database_operation("select")
        async def test_db_operation():
            await asyncio.sleep(0.1)
            return {"result": "data"}
        
        result = await test_db_operation()
        assert result == {"result": "data"}
        
        # Проверяем, что операция БД залогирована
        # В реальном тесте здесь можно проверить логи


@pytest.mark.asyncio
class TestMonitoringMiddleware:
    """Тесты для middleware мониторинга"""
    
    async def test_monitoring_middleware_success(self):
        """Тест middleware для успешного запроса"""
        # Создаем mock объекты
        request = Mock()
        request.method = "GET"
        request.url.path = "/api/test"
        request.headers = {}
        
        response = Mock()
        response.status_code = 200
        response.headers = {}
        
        async def mock_call_next(req):
            return response
        
        # Выполняем middleware
        result = await monitoring_middleware(request, mock_call_next)
        
        assert result == response
        assert "X-Request-ID" in result.headers
        assert "X-Response-Time" in result.headers
    
    async def test_monitoring_middleware_with_error(self):
        """Тест middleware с ошибкой"""
        request = Mock()
        request.method = "POST"
        request.url.path = "/api/test"
        request.headers = {}
        
        async def mock_call_next_with_error(req):
            raise ValueError("Test error")
        
        # Проверяем, что ошибка пробрасывается
        with pytest.raises(ValueError):
            await monitoring_middleware(request, mock_call_next_with_error)


class TestMonitoringIntegration:
    """Интеграционные тесты мониторинга"""
    
    @pytest.mark.asyncio
    async def test_full_monitoring_flow(self):
        """Тест полного цикла мониторинга"""
        monitoring_service = MonitoringService("test-service")
        
        # Симулируем HTTP запрос
        request = Mock()
        request.method = "POST"
        request.url.path = "/api/seo/analyze"
        request.headers.get.return_value = "req-456"
        
        response = Mock()
        response.status_code = 201
        
        # Логируем запрос
        monitoring_service.log_request(request, response, 1.2)
        
        # Логируем SEO анализ
        monitoring_service.log_seo_analysis("example.com", "completed", 2.5)
        
        # Проверяем метрики
        assert monitoring_service.http_requests_total._value.sum() == 1
        assert monitoring_service.http_request_duration._sum.sum() == 1.2
        assert monitoring_service.seo_analyses_total._value.sum() == 1
    
    @pytest.mark.asyncio
    async def test_trace_operation_context_manager(self):
        """Тест контекстного менеджера для трассировки"""
        monitoring_service = MonitoringService("test-service")
        
        async with monitoring_service.trace_operation("test_operation") as span:
            span.set_attribute("test.attribute", "test_value")
            await asyncio.sleep(0.1)
        
        # Проверяем, что span создан и закрыт
        # В реальном тесте здесь можно проверить трассировку


# Тесты для метрик
class TestMetrics:
    """Тесты для метрик Prometheus"""
    
    def test_metrics_generation(self):
        """Тест генерации метрик"""
        monitoring_service = MonitoringService("test-service")
        
        # Обновляем некоторые метрики
        monitoring_service.update_active_users(10)
        monitoring_service.update_database_connections(5)
        
        # Получаем метрики
        metrics = monitoring_service.get_metrics()
        
        # Проверяем, что метрики содержат ожидаемые данные
        assert "active_users" in metrics
        assert "database_connections" in metrics
        assert "http_requests_total" in metrics


# Тесты для обработки ошибок
class TestErrorHandling:
    """Тесты для обработки ошибок"""
    
    def test_validation_error_handling(self):
        """Тест обработки ошибок валидации"""
        from app.validation import ValidationErrorHandler
        
        # Создаем mock ошибку валидации
        error = ValidationError(errors=[
            {
                "loc": ("field",),
                "msg": "Field is required",
                "type": "value_error.missing"
            }
        ], model=Mock())
        
        response = ValidationErrorHandler.handle_validation_error(error)
        
        assert response.status_code == 422
        assert "validation_error" in response.body.decode()
    
    def test_http_error_handling(self):
        """Тест обработки HTTP ошибок"""
        from app.validation import ValidationErrorHandler
        from fastapi import HTTPException
        
        error = HTTPException(status_code=404, detail="Not found")
        
        response = ValidationErrorHandler.handle_http_error(error)
        
        assert response.status_code == 404
        assert "http_error" in response.body.decode() 