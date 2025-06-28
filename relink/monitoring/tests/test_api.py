"""
Тесты API эндпоинтов микросервиса мониторинга
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from app.main import app
from app.models import AlertSeverity, AlertStatus, ServiceStatus

client = TestClient(app)


class TestHealthEndpoint:
    """Тесты эндпоинта здоровья"""
    
    def test_health_check(self):
        """Тест проверки здоровья сервиса"""
        with patch('app.main.redis_client') as mock_redis:
            mock_redis.ping = AsyncMock()
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "version" in data
            assert "uptime" in data
            assert "services" in data
    
    def test_health_check_redis_down(self):
        """Тест проверки здоровья при недоступности Redis"""
        with patch('app.main.redis_client') as mock_redis:
            mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["services"]["redis"] == "down"


class TestMetricsEndpoint:
    """Тесты эндпоинта метрик"""
    
    def test_get_metrics(self):
        """Тест получения метрик"""
        with patch('app.main.metrics_collector') as mock_collector:
            mock_collector.collect_all_metrics = AsyncMock(return_value={
                'system': {'cpu_usage': 50.0, 'memory_usage': 60.0},
                'database': {'active_connections': 5},
                'cache': {'hit_rate': 85.0},
                'ollama': {'response_time': 1.5}
            })
            
            response = client.get("/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert "system" in data
            assert "database" in data
            assert "cache" in data
            assert "ollama" in data
    
    def test_get_metrics_collector_not_initialized(self):
        """Тест получения метрик при неинициализированном коллекторе"""
        with patch('app.main.metrics_collector', None):
            response = client.get("/metrics")
            
            assert response.status_code == 503
            assert "Metrics collector not initialized" in response.json()["detail"]


class TestAlertsEndpoint:
    """Тесты эндпоинта алертов"""
    
    def test_get_alerts(self):
        """Тест получения алертов"""
        with patch('app.main.alert_service') as mock_service:
            mock_service.get_alerts = AsyncMock(return_value=[])
            
            response = client.get("/alerts")
            
            assert response.status_code == 200
            data = response.json()
            assert "alerts" in data
            assert "total" in data
            assert "active" in data
            assert "resolved" in data
    
    def test_get_alerts_with_filters(self):
        """Тест получения алертов с фильтрами"""
        with patch('app.main.alert_service') as mock_service:
            mock_service.get_alerts = AsyncMock(return_value=[])
            
            response = client.get("/alerts?status=active&severity=warning&limit=10")
            
            assert response.status_code == 200
            mock_service.get_alerts.assert_called_once()
    
    def test_create_alert(self):
        """Тест создания алерта"""
        with patch('app.main.alert_service') as mock_service:
            mock_service.save_alerts = AsyncMock()
            
            alert_data = {
                "name": "Test Alert",
                "description": "Test description",
                "severity": "warning",
                "source": "system",
                "metric_name": "cpu_usage",
                "threshold": 80.0,
                "current_value": 85.0
            }
            
            response = client.post("/alerts", json=alert_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Alert"
            assert data["severity"] == "warning"
    
    def test_update_alert(self):
        """Тест обновления алерта"""
        with patch('app.main.alert_service') as mock_service:
            mock_service.update_alert_status = AsyncMock()
            
            update_data = {
                "status": "resolved",
                "acknowledged_by": "test_user"
            }
            
            response = client.put("/alerts/test-alert-id", json=update_data)
            
            assert response.status_code == 200
            assert "Alert updated successfully" in response.json()["message"]


class TestServicesEndpoint:
    """Тесты эндпоинта сервисов"""
    
    def test_get_services(self):
        """Тест получения статуса сервисов"""
        with patch('app.main.health_checker') as mock_checker:
            mock_checker.check_all_services = AsyncMock(return_value=[])
            
            response = client.get("/services")
            
            assert response.status_code == 200
            data = response.json()
            assert "services" in data
            assert "total" in data
            assert "healthy" in data
            assert "degraded" in data
            assert "down" in data


class TestDashboardEndpoint:
    """Тесты эндпоинта дашборда"""
    
    def test_get_dashboard(self):
        """Тест получения данных дашборда"""
        with patch('app.main.dashboard_service') as mock_service:
            mock_service.get_dashboard_data = AsyncMock(return_value={
                "metrics": "test_metrics",
                "alerts_count": 5,
                "services": "test_services",
                "timestamp": "2023-01-01T00:00:00"
            })
            
            response = client.get("/dashboard")
            
            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data
            assert "alerts_count" in data
            assert "services" in data
            assert "timestamp" in data


class TestMetricsCollectionEndpoint:
    """Тесты эндпоинта сбора метрик"""
    
    def test_trigger_metrics_collection(self):
        """Тест принудительного сбора метрик"""
        with patch('app.main.metrics_collector') as mock_collector:
            response = client.post("/metrics/collect")
            
            assert response.status_code == 200
            assert "Metrics collection triggered" in response.json()["message"]


class TestPrometheusEndpoint:
    """Тесты эндпоинта Prometheus"""
    
    def test_prometheus_metrics(self):
        """Тест получения метрик Prometheus"""
        response = client.get("/prometheus")
        
        assert response.status_code == 200
        # Пока что возвращает заглушку
        assert "not implemented yet" in response.json()["message"]


class TestRootEndpoint:
    """Тесты корневого эндпоинта"""
    
    def test_root(self):
        """Тест корневого эндпоинта"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "timestamp" in data


class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    def test_global_exception_handler(self):
        """Тест глобального обработчика исключений"""
        with patch('app.main.metrics_collector') as mock_collector:
            mock_collector.collect_all_metrics = AsyncMock(side_effect=Exception("Test error"))
            
            response = client.get("/metrics")
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]
    
    def test_http_exception_handler(self):
        """Тест обработчика HTTP исключений"""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
        assert "Not Found" in response.json()["detail"]


class TestMiddleware:
    """Тесты middleware"""
    
    def test_request_logging_middleware(self):
        """Тест middleware логирования запросов"""
        with patch('app.main.logger') as mock_logger:
            response = client.get("/health")
            
            # Проверяем, что логгер был вызван
            assert mock_logger.info.called


class TestCORS:
    """Тесты CORS"""
    
    def test_cors_headers(self):
        """Тест CORS заголовков"""
        response = client.options("/health")
        
        # Проверяем наличие CORS заголовков
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers


# Фикстуры для тестов
@pytest.fixture
def sample_alert():
    """Фикстура с примером алерта"""
    return {
        "name": "Test Alert",
        "description": "Test description",
        "severity": "warning",
        "source": "system",
        "metric_name": "cpu_usage",
        "threshold": 80.0,
        "current_value": 85.0
    }


@pytest.fixture
def sample_metrics():
    """Фикстура с примером метрик"""
    return {
        'system': {
            'cpu_usage': 50.0,
            'memory_usage': 60.0,
            'disk_usage': 70.0,
            'network_in': 1000,
            'network_out': 500,
            'load_average': [1.0, 1.5, 2.0]
        },
        'database': {
            'active_connections': 5,
            'total_connections': 10,
            'query_time': 0.1,
            'slow_queries': 0,
            'errors': 0
        },
        'cache': {
            'hit_rate': 85.0,
            'miss_rate': 15.0,
            'memory_usage': 50.0,
            'keys_count': 1000,
            'evictions': 0
        },
        'ollama': {
            'model': 'qwen2.5:7b-instruct-turbo',
            'response_time': 1.5,
            'tokens_per_second': 100.0,
            'memory_usage': 2048.0,
            'requests_per_minute': 10,
            'errors': 0
        }
    } 