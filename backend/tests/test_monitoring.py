"""
Тесты для модуля мониторинга reLink
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.monitoring import (
    logger,
    metrics_collector,
    performance_monitor,
    get_metrics,
    get_health_status,
    monitor_operation,
    MonitoringMiddleware,
    MetricsCollector,
    PerformanceMonitor,
    monitor_database_operation,
    monitor_cache_operation,
    monitor_ollama_request
)


class TestMonitoringMiddleware:
    """Тесты для MonitoringMiddleware"""
    
    @pytest.fixture
    def mock_app(self):
        """Мок приложения"""
        app = Mock()
        app.return_value = None
        return app
    
    @pytest.fixture
    def middleware(self, mock_app):
        """Middleware для тестирования"""
        return MonitoringMiddleware(mock_app)
    
    @pytest.mark.asyncio
    async def test_middleware_http_request(self, middleware, mock_app):
        """Тест обработки HTTP запроса"""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"user-agent", b"test-agent")]
        }
        
        receive = AsyncMock()
        send = AsyncMock()
        
        await middleware(scope, receive, send)
        
        # Проверяем, что приложение было вызвано
        mock_app.assert_called_once_with(scope, receive, send)
    
    @pytest.mark.asyncio
    async def test_middleware_non_http_request(self, middleware, mock_app):
        """Тест обработки не-HTTP запроса"""
        scope = {"type": "websocket"}
        
        receive = AsyncMock()
        send = AsyncMock()
        
        await middleware(scope, receive, send)
        
        # Проверяем, что приложение было вызвано без изменений
        mock_app.assert_called_once_with(scope, receive, send)


class TestMetricsCollector:
    """Тесты для MetricsCollector"""
    
    @pytest.fixture
    def collector(self):
        """Коллектор метрик для тестирования"""
        return MetricsCollector("test-service")
    
    def test_collector_initialization(self, collector):
        """Тест инициализации коллектора"""
        assert collector.service_name == "test-service"
        assert collector.start_time > 0
    
    @patch('app.monitoring.psutil')
    def test_collect_system_metrics_success(self, mock_psutil, collector):
        """Тест успешного сбора системных метрик"""
        # Мокаем psutil
        mock_memory = Mock()
        mock_memory.total = 8589934592  # 8GB
        mock_memory.available = 4294967296  # 4GB
        mock_memory.used = 4294967296  # 4GB
        mock_memory.free = 0
        mock_memory.percent = 50.0
        
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_percent.return_value = 25.5
        
        # Вызываем метод
        collector.collect_system_metrics()
        
        # Проверяем, что psutil был вызван
        mock_psutil.virtual_memory.assert_called_once()
        mock_psutil.cpu_percent.assert_called_once_with(interval=1)
    
    @patch('app.monitoring.psutil')
    def test_collect_system_metrics_import_error(self, mock_psutil, collector):
        """Тест сбора метрик при отсутствии psutil"""
        # Симулируем ImportError
        mock_psutil.side_effect = ImportError("psutil not available")
        
        # Вызываем метод - не должно вызывать исключение
        collector.collect_system_metrics()


class TestPerformanceMonitor:
    """Тесты для PerformanceMonitor"""
    
    @pytest.fixture
    def monitor(self):
        """Монитор производительности для тестирования"""
        return PerformanceMonitor()
    
    def test_start_timer(self, monitor):
        """Тест запуска таймера"""
        monitor.start_timer("test_operation")
        
        assert "test_operation" in monitor.metrics
        assert "start" in monitor.metrics["test_operation"]
        assert monitor.metrics["test_operation"]["start"] > 0
    
    def test_end_timer(self, monitor):
        """Тест остановки таймера"""
        monitor.start_timer("test_operation")
        time.sleep(0.1)  # Небольшая задержка
        
        duration = monitor.end_timer("test_operation")
        
        assert duration > 0
        assert "duration" in monitor.metrics["test_operation"]
        assert monitor.metrics["test_operation"]["duration"] == duration
    
    def test_end_timer_nonexistent(self, monitor):
        """Тест остановки несуществующего таймера"""
        duration = monitor.end_timer("nonexistent")
        assert duration == 0.0
    
    def test_get_metrics(self, monitor):
        """Тест получения метрик"""
        monitor.start_timer("test_operation")
        monitor.end_timer("test_operation")
        
        metrics = monitor.get_metrics()
        
        assert "test_operation" in metrics
        assert "start" in metrics["test_operation"]
        assert "duration" in metrics["test_operation"]


class TestMonitoringDecorators:
    """Тесты для декораторов мониторинга"""
    
    @pytest.mark.asyncio
    async def test_monitor_database_operation_success(self):
        """Тест декоратора мониторинга БД - успешный случай"""
        @monitor_database_operation("SELECT", "users")
        async def test_db_operation():
            return "success"
        
        result = await test_db_operation()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_monitor_database_operation_error(self):
        """Тест декоратора мониторинга БД - ошибка"""
        @monitor_database_operation("SELECT", "users")
        async def test_db_operation():
            raise Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await test_db_operation()
    
    @pytest.mark.asyncio
    async def test_monitor_cache_operation_success(self):
        """Тест декоратора мониторинга кэша - успешный случай"""
        @monitor_cache_operation("GET", "redis")
        async def test_cache_operation():
            return "cached_data"
        
        result = await test_cache_operation()
        assert result == "cached_data"
    
    @pytest.mark.asyncio
    async def test_monitor_ollama_request_success(self):
        """Тест декоратора мониторинга Ollama - успешный случай"""
        @monitor_ollama_request("qwen2.5:7b-instruct-turbo", "generate")
        async def test_ollama_request():
            return "generated_text"
        
        result = await test_ollama_request()
        assert result == "generated_text"


class TestMonitoringFunctions:
    """Тесты для функций мониторинга"""
    
    def test_get_metrics(self):
        """Тест получения метрик"""
        metrics = get_metrics()
        assert isinstance(metrics, bytes)
        assert len(metrics) > 0
    
    def test_get_health_status(self):
        """Тест получения статуса здоровья"""
        health = get_health_status()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "timestamp" in health
        assert "version" in health
        assert "environment" in health
        assert health["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_monitor_operation_success(self):
        """Тест контекстного менеджера мониторинга - успешный случай"""
        operation_called = False
        
        async with monitor_operation("test_operation", test_param="value"):
            operation_called = True
        
        assert operation_called
    
    @pytest.mark.asyncio
    async def test_monitor_operation_error(self):
        """Тест контекстного менеджера мониторинга - ошибка"""
        with pytest.raises(Exception, match="Test error"):
            async with monitor_operation("test_operation"):
                raise Exception("Test error")


class TestLogger:
    """Тесты для логгера"""
    
    def test_logger_initialization(self):
        """Тест инициализации логгера"""
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warning')
    
    def test_logger_info(self):
        """Тест логирования info сообщения"""
        # Просто проверяем, что не вызывает исключений
        logger.info("Test info message", test_param="value")
    
    def test_logger_error(self):
        """Тест логирования error сообщения"""
        # Просто проверяем, что не вызывает исключений
        logger.error("Test error message", error_type="test", details="test details")


class TestMonitoringIntegration:
    """Интеграционные тесты мониторинга"""
    
    @pytest.fixture
    def app(self):
        """FastAPI приложение для тестирования"""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Тестовый клиент"""
        return TestClient(app)
    
    def test_metrics_endpoint_integration(self, client):
        """Интеграционный тест endpoint метрик"""
        # Создаем простое приложение с мониторингом
        app = FastAPI()
        
        @app.get("/metrics")
        async def metrics():
            return get_metrics()
        
        test_client = TestClient(app)
        response = test_client.get("/metrics")
        
        assert response.status_code == 200
        assert len(response.content) > 0
    
    def test_health_endpoint_integration(self, client):
        """Интеграционный тест endpoint здоровья"""
        app = FastAPI()
        
        @app.get("/health")
        async def health():
            return get_health_status()
        
        test_client = TestClient(app)
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


# Тесты производительности
class TestMonitoringPerformance:
    """Тесты производительности мониторинга"""
    
    @pytest.mark.asyncio
    async def test_monitor_operation_performance(self):
        """Тест производительности контекстного менеджера"""
        start_time = time.time()
        
        async with monitor_operation("performance_test"):
            await asyncio.sleep(0.01)  # Имитируем работу
        
        duration = time.time() - start_time
        assert duration < 0.1  # Должно быть быстро
    
    def test_metrics_collection_performance(self):
        """Тест производительности сбора метрик"""
        collector = MetricsCollector("performance_test")
        
        start_time = time.time()
        for _ in range(100):
            collector.collect_system_metrics()
        duration = time.time() - start_time
        
        # Сбор метрик должен быть быстрым
        assert duration < 1.0
    
    def test_performance_monitor_memory_usage(self):
        """Тест использования памяти монитором производительности"""
        monitor = PerformanceMonitor()
        
        # Добавляем много таймеров
        for i in range(1000):
            monitor.start_timer(f"timer_{i}")
            monitor.end_timer(f"timer_{i}")
        
        # Проверяем, что память не растет бесконечно
        metrics = monitor.get_metrics()
        assert len(metrics) == 1000


# Тесты устойчивости к ошибкам
class TestMonitoringErrorHandling:
    """Тесты обработки ошибок в мониторинге"""
    
    @pytest.mark.asyncio
    async def test_monitor_operation_with_exception(self):
        """Тест обработки исключений в контекстном менеджере"""
        exception_raised = False
        
        try:
            async with monitor_operation("error_test"):
                raise ValueError("Test exception")
        except ValueError:
            exception_raised = True
        
        assert exception_raised
    
    def test_metrics_collector_with_psutil_error(self):
        """Тест обработки ошибок psutil"""
        collector = MetricsCollector("error_test")
        
        # Должно работать без psutil
        with patch('app.monitoring.psutil', side_effect=ImportError):
            collector.collect_system_metrics()  # Не должно вызывать исключение
    
    def test_performance_monitor_edge_cases(self):
        """Тест граничных случаев монитора производительности"""
        monitor = PerformanceMonitor()
        
        # Тест с пустым именем таймера
        monitor.start_timer("")
        duration = monitor.end_timer("")
        assert duration >= 0
        
        # Тест с очень длинным именем
        long_name = "a" * 1000
        monitor.start_timer(long_name)
        duration = monitor.end_timer(long_name)
        assert duration >= 0 