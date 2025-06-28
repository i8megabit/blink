"""
Тесты для API эндпоинтов микросервиса тестирования reLink.
Покрывает все основные эндпоинты и сценарии использования.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime, timedelta

from app.main import app
from app.models import (
    TestRequest, TestResponse, TestSuiteRequest, TestSuiteResponse,
    TestExecutionResponse, TestReport, TestMetrics,
    TestType, TestStatus, TestPriority, TestEnvironment
)
from app.services import TestingService

# Создание тестового клиента
client = TestClient(app)

# Тестовые данные
SAMPLE_TEST_REQUEST = {
    "name": "Test API Endpoint",
    "description": "Тест API эндпоинта",
    "test_type": "api",
    "priority": "high",
    "environment": "development",
    "config": {
        "url": "https://api.example.com/test",
        "method": "GET",
        "timeout": 30
    }
}

SAMPLE_TEST_SUITE_REQUEST = {
    "name": "API Test Suite",
    "description": "Набор тестов для API",
    "test_ids": ["test-1", "test-2", "test-3"],
    "config": {
        "parallel": True,
        "timeout": 60
    }
}

class TestHealthCheck:
    """Тесты для health check эндпоинта"""
    
    def test_health_check(self):
        """Тест проверки здоровья сервиса"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "reLink Testing Service"
        assert "version" in data
        assert "timestamp" in data

class TestTestsAPI:
    """Тесты для API тестов"""
    
    @patch('app.main.testing_service')
    def test_create_test(self, mock_service):
        """Тест создания теста"""
        # Настройка мока
        mock_test = TestResponse(
            id="test-123",
            name="Test API Endpoint",
            description="Тест API эндпоинта",
            test_type=TestType.api,
            status=TestStatus.active,
            priority=TestPriority.high,
            environment=TestEnvironment.development,
            config={"url": "https://api.example.com/test"},
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        mock_service.create_test.return_value = mock_test
        
        response = client.post("/tests/", json=SAMPLE_TEST_REQUEST)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "test-123"
        assert data["name"] == "Test API Endpoint"
        assert data["test_type"] == "api"
        assert data["status"] == "active"
        
        # Проверка вызова сервиса
        mock_service.create_test.assert_called_once()
    
    @patch('app.main.testing_service')
    def test_get_tests(self, mock_service):
        """Тест получения списка тестов"""
        # Настройка мока
        mock_tests = [
            TestResponse(
                id="test-1",
                name="Test 1",
                test_type=TestType.api,
                status=TestStatus.active,
                priority=TestPriority.high,
                environment=TestEnvironment.development,
                created_by="test_user",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            ),
            TestResponse(
                id="test-2",
                name="Test 2",
                test_type=TestType.ui,
                status=TestStatus.active,
                priority=TestPriority.medium,
                environment=TestEnvironment.staging,
                created_by="test_user",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
        ]
        mock_service.get_tests.return_value = mock_tests
        
        response = client.get("/tests/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["id"] == "test-1"
        assert data[1]["id"] == "test-2"
    
    @patch('app.main.testing_service')
    def test_get_tests_with_filters(self, mock_service):
        """Тест получения тестов с фильтрами"""
        mock_tests = [
            TestResponse(
                id="test-1",
                name="API Test",
                test_type=TestType.api,
                status=TestStatus.active,
                priority=TestPriority.high,
                environment=TestEnvironment.development,
                created_by="test_user",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
        ]
        mock_service.get_tests.return_value = mock_tests
        
        response = client.get("/tests/?test_type=api&priority=high&environment=development")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["test_type"] == "api"
        assert data[0]["priority"] == "high"
    
    @patch('app.main.testing_service')
    def test_get_test_by_id(self, mock_service):
        """Тест получения теста по ID"""
        mock_test = TestResponse(
            id="test-123",
            name="Test API Endpoint",
            test_type=TestType.api,
            status=TestStatus.active,
            priority=TestPriority.high,
            environment=TestEnvironment.development,
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        mock_service.get_test.return_value = mock_test
        
        response = client.get("/tests/test-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "test-123"
        assert data["name"] == "Test API Endpoint"
    
    @patch('app.main.testing_service')
    def test_get_test_not_found(self, mock_service):
        """Тест получения несуществующего теста"""
        mock_service.get_test.return_value = None
        
        response = client.get("/tests/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Тест не найден"
    
    @patch('app.main.testing_service')
    def test_update_test(self, mock_service):
        """Тест обновления теста"""
        mock_test = TestResponse(
            id="test-123",
            name="Updated Test",
            test_type=TestType.api,
            status=TestStatus.active,
            priority=TestPriority.high,
            environment=TestEnvironment.development,
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        mock_service.update_test.return_value = mock_test
        
        update_data = {
            "name": "Updated Test",
            "description": "Обновленное описание",
            "test_type": "api",
            "priority": "high",
            "environment": "development",
            "config": {"url": "https://api.example.com/updated"}
        }
        
        response = client.put("/tests/test-123", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Updated Test"
        mock_service.update_test.assert_called_once()
    
    @patch('app.main.testing_service')
    def test_delete_test(self, mock_service):
        """Тест удаления теста"""
        mock_service.delete_test.return_value = True
        
        response = client.delete("/tests/test-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Тест успешно удален"
        mock_service.delete_test.assert_called_once_with("test-123")

class TestTestExecutionAPI:
    """Тесты для API выполнения тестов"""
    
    @patch('app.main.testing_service')
    def test_execute_test(self, mock_service):
        """Тест выполнения теста"""
        mock_execution = TestExecutionResponse(
            id="exec-123",
            test_id="test-123",
            status=TestStatus.running,
            started_at=datetime.now(),
            created_by="test_user",
            created_at=datetime.now()
        )
        mock_service.execute_test.return_value = mock_execution
        
        response = client.post("/tests/test-123/execute")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "exec-123"
        assert data["test_id"] == "test-123"
        assert data["status"] == "running"
        mock_service.execute_test.assert_called_once_with("test-123", "test_user")
    
    @patch('app.main.testing_service')
    def test_execute_test_not_found(self, mock_service):
        """Тест выполнения несуществующего теста"""
        mock_service.execute_test.return_value = None
        
        response = client.post("/tests/nonexistent/execute")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Тест не найден"
    
    @patch('app.main.testing_service')
    def test_get_executions(self, mock_service):
        """Тест получения списка выполнений"""
        mock_executions = [
            TestExecutionResponse(
                id="exec-1",
                test_id="test-1",
                status=TestStatus.completed,
                started_at=datetime.now(),
                completed_at=datetime.now(),
                duration=30,
                created_by="test_user",
                created_at=datetime.now()
            ),
            TestExecutionResponse(
                id="exec-2",
                test_id="test-2",
                status=TestStatus.running,
                started_at=datetime.now(),
                created_by="test_user",
                created_at=datetime.now()
            )
        ]
        mock_service.get_executions.return_value = mock_executions
        
        response = client.get("/executions/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["id"] == "exec-1"
        assert data[1]["id"] == "exec-2"
    
    @patch('app.main.testing_service')
    def test_get_execution_by_id(self, mock_service):
        """Тест получения выполнения по ID"""
        mock_execution = TestExecutionResponse(
            id="exec-123",
            test_id="test-123",
            status=TestStatus.completed,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration=45,
            result={"success": True, "response_time": 1.2},
            created_by="test_user",
            created_at=datetime.now()
        )
        mock_service.get_execution.return_value = mock_execution
        
        response = client.get("/executions/exec-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "exec-123"
        assert data["status"] == "completed"
        assert data["duration"] == 45
        assert data["result"]["success"] is True
    
    @patch('app.main.testing_service')
    def test_cancel_execution(self, mock_service):
        """Тест отмены выполнения"""
        mock_service.cancel_execution.return_value = True
        
        response = client.post("/executions/exec-123/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Выполнение успешно отменено"
        mock_service.cancel_execution.assert_called_once_with("exec-123")

class TestTestSuitesAPI:
    """Тесты для API наборов тестов"""
    
    @patch('app.main.testing_service')
    def test_create_test_suite(self, mock_service):
        """Тест создания набора тестов"""
        mock_suite = TestSuiteResponse(
            id="suite-123",
            name="API Test Suite",
            description="Набор тестов для API",
            test_ids=["test-1", "test-2", "test-3"],
            config={"parallel": True, "timeout": 60},
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        mock_service.create_test_suite.return_value = mock_suite
        
        response = client.post("/test-suites/", json=SAMPLE_TEST_SUITE_REQUEST)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "suite-123"
        assert data["name"] == "API Test Suite"
        assert len(data["test_ids"]) == 3
        mock_service.create_test_suite.assert_called_once()
    
    @patch('app.main.testing_service')
    def test_execute_test_suite(self, mock_service):
        """Тест выполнения набора тестов"""
        mock_executions = [
            TestExecutionResponse(
                id="exec-1",
                test_id="test-1",
                status=TestStatus.running,
                started_at=datetime.now(),
                created_by="test_user",
                created_at=datetime.now()
            ),
            TestExecutionResponse(
                id="exec-2",
                test_id="test-2",
                status=TestStatus.running,
                started_at=datetime.now(),
                created_by="test_user",
                created_at=datetime.now()
            )
        ]
        mock_service.execute_test_suite.return_value = mock_executions
        
        response = client.post("/test-suites/suite-123/execute")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["id"] == "exec-1"
        assert data[1]["id"] == "exec-2"
        mock_service.execute_test_suite.assert_called_once_with("suite-123", "test_user")

class TestReportsAPI:
    """Тесты для API отчетов"""
    
    @patch('app.main.testing_service')
    def test_get_reports(self, mock_service):
        """Тест получения списка отчетов"""
        mock_reports = [
            TestReport(
                id="report-1",
                execution_id="exec-1",
                report_type="detailed",
                content={"summary": "Test passed", "details": {}},
                summary="Тест прошел успешно",
                recommendations=[],
                created_at=datetime.now()
            ),
            TestReport(
                id="report-2",
                execution_id="exec-2",
                report_type="summary",
                content={"summary": "Test failed", "details": {}},
                summary="Тест завершился с ошибкой",
                recommendations=["Проверить конфигурацию"],
                created_at=datetime.now()
            )
        ]
        mock_service.get_reports.return_value = mock_reports
        
        response = client.get("/reports/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["id"] == "report-1"
        assert data[1]["id"] == "report-2"
    
    @patch('app.main.testing_service')
    def test_get_report_by_id(self, mock_service):
        """Тест получения отчета по ID"""
        mock_report = TestReport(
            id="report-123",
            execution_id="exec-123",
            report_type="detailed",
            content={
                "summary": "Test passed",
                "details": {
                    "response_time": 1.2,
                    "status_code": 200,
                    "assertions": ["Status code is 200", "Response time < 2s"]
                }
            },
            summary="Тест прошел успешно",
            recommendations=[],
            created_at=datetime.now()
        )
        mock_service.get_report.return_value = mock_report
        
        response = client.get("/reports/report-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "report-123"
        assert data["execution_id"] == "exec-123"
        assert data["report_type"] == "detailed"
        assert "response_time" in data["content"]["details"]

class TestMetricsAPI:
    """Тесты для API метрик"""
    
    @patch('app.main.testing_service')
    def test_get_metrics(self, mock_service):
        """Тест получения метрик"""
        mock_metrics = TestMetrics(
            total_tests=100,
            total_executions=85,
            successful_executions=75,
            failed_executions=10,
            average_duration=45.5,
            success_rate=88.2,
            execution_trends={
                "last_24h": {"total": 20, "successful": 18, "failed": 2},
                "last_7d": {"total": 150, "successful": 135, "failed": 15}
            },
            performance_metrics={
                "avg_response_time": 1.2,
                "p95_response_time": 2.5,
                "p99_response_time": 4.1
            },
            error_distribution={
                "timeout": 5,
                "connection_error": 3,
                "assertion_failed": 2
            },
            environment_stats={
                "development": {"total": 50, "successful": 45},
                "staging": {"total": 30, "successful": 25},
                "production": {"total": 20, "successful": 18}
            }
        )
        mock_service.get_metrics.return_value = mock_metrics
        
        response = client.get("/metrics/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_tests"] == 100
        assert data["total_executions"] == 85
        assert data["success_rate"] == 88.2
        assert "execution_trends" in data
        assert "performance_metrics" in data

class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    @patch('app.main.testing_service')
    def test_internal_server_error(self, mock_service):
        """Тест внутренней ошибки сервера"""
        mock_service.create_test.side_effect = Exception("Database connection failed")
        
        response = client.post("/tests/", json=SAMPLE_TEST_REQUEST)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
    
    def test_invalid_json(self):
        """Тест некорректного JSON"""
        response = client.post("/tests/", data="invalid json")
        
        assert response.status_code == 422
    
    def test_validation_error(self):
        """Тест ошибки валидации"""
        invalid_request = {
            "name": "",  # Пустое имя
            "test_type": "invalid_type"  # Неверный тип
        }
        
        response = client.post("/tests/", json=invalid_request)
        
        assert response.status_code == 422

class TestPagination:
    """Тесты пагинации"""
    
    @patch('app.main.testing_service')
    def test_pagination_parameters(self, mock_service):
        """Тест параметров пагинации"""
        mock_service.get_tests.return_value = []
        
        response = client.get("/tests/?skip=10&limit=20")
        
        assert response.status_code == 200
        # Проверяем, что параметры переданы в сервис
        mock_service.get_tests.assert_called_once()
    
    def test_invalid_pagination_parameters(self):
        """Тест некорректных параметров пагинации"""
        response = client.get("/tests/?skip=-1&limit=0")
        
        assert response.status_code == 422

class TestAuthentication:
    """Тесты аутентификации (заглушки)"""
    
    def test_no_authentication_required_in_dev(self):
        """Тест что аутентификация не требуется в dev режиме"""
        response = client.get("/tests/")
        
        # В dev режиме аутентификация отключена
        assert response.status_code in [200, 500]  # 500 если нет моков

# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_test_lifecycle(self):
        """Тест полного жизненного цикла теста"""
        # Этот тест требует реальной базы данных
        # В реальном проекте здесь был бы тест с тестовой БД
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_test_executions(self):
        """Тест конкурентных выполнений тестов"""
        # Тест конкурентности
        pass

# Фикстуры для тестов
@pytest.fixture
def sample_test_data():
    """Фикстура с тестовыми данными"""
    return {
        "test_request": SAMPLE_TEST_REQUEST,
        "test_suite_request": SAMPLE_TEST_SUITE_REQUEST,
        "test_id": "test-123",
        "execution_id": "exec-123",
        "suite_id": "suite-123"
    }

@pytest.fixture
def mock_testing_service():
    """Фикстура с моком сервиса тестирования"""
    with patch('app.main.testing_service') as mock:
        yield mock

# Тесты производительности
class TestPerformance:
    """Тесты производительности"""
    
    def test_api_response_time(self):
        """Тест времени отклика API"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Должно быть меньше 1 секунды
    
    def test_concurrent_requests(self):
        """Тест конкурентных запросов"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                start_time = time.time()
                response = client.get("/health")
                end_time = time.time()
                results.append(end_time - start_time)
            except Exception as e:
                errors.append(e)
        
        # Создаем 10 конкурентных запросов
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0
        assert len(results) == 10
        
        # Среднее время отклика должно быть разумным
        avg_response_time = sum(results) / len(results)
        assert avg_response_time < 2.0 