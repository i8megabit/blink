"""
Тесты для сервисов микросервиса тестирования reLink.
Покрывает бизнес-логику, обработку данных и интеграции.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from app.services import TestingService
from app.models import (
    TestRequest, TestResponse, TestSuiteRequest, TestSuiteResponse,
    TestExecution, TestExecutionResponse, TestReport, TestMetrics,
    TestFilter, TestStatus, TestType, TestPriority, TestEnvironment
)
from app.database import Database

# Тестовые данные
SAMPLE_TEST_REQUEST = TestRequest(
    name="API Test",
    description="Тест API эндпоинта",
    test_type=TestType.api,
    priority=TestPriority.high,
    environment=TestEnvironment.development,
    config={
        "url": "https://api.example.com/test",
        "method": "GET",
        "timeout": 30,
        "headers": {"Authorization": "Bearer token"},
        "expected_status": 200
    }
)

SAMPLE_TEST_SUITE_REQUEST = TestSuiteRequest(
    name="API Test Suite",
    description="Набор тестов для API",
    test_ids=["test-1", "test-2", "test-3"],
    config={
        "parallel": True,
        "timeout": 60,
        "retry_count": 3
    }
)

class TestTestingService:
    """Тесты для основного сервиса тестирования"""
    
    @pytest.fixture
    def testing_service(self):
        """Фикстура сервиса тестирования"""
        return TestingService()
    
    @pytest.fixture
    def mock_database(self):
        """Фикстура мока базы данных"""
        mock_db = AsyncMock(spec=Database)
        mock_db.get_session.return_value.__aenter__.return_value = AsyncMock()
        return mock_db
    
    @pytest.mark.asyncio
    async def test_initialize(self, testing_service):
        """Тест инициализации сервиса"""
        with patch('app.services.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            await testing_service.initialize()
            
            mock_get_db.assert_called_once()
            assert testing_service.db is not None
    
    @pytest.mark.asyncio
    async def test_cleanup(self, testing_service):
        """Тест очистки ресурсов сервиса"""
        testing_service.db = AsyncMock()
        
        await testing_service.cleanup()
        
        # Проверяем, что ресурсы очищены
        assert testing_service.db is None
    
    @pytest.mark.asyncio
    async def test_create_test(self, testing_service, mock_database):
        """Тест создания теста"""
        testing_service.db = mock_database
        
        with patch('app.services.DatabaseUtils.generate_id') as mock_generate_id:
            mock_generate_id.return_value = "test-123"
            
            result = await testing_service.create_test(SAMPLE_TEST_REQUEST, "test_user")
            
            assert result is not None
            assert result.id == "test-123"
            assert result.name == "API Test"
            assert result.test_type == TestType.api
            assert result.created_by == "test_user"
            assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_test(self, testing_service, mock_database):
        """Тест получения теста"""
        testing_service.db = mock_database
        
        # Мокаем данные из базы
        mock_test_data = {
            "id": "test-123",
            "name": "API Test",
            "description": "Тест API эндпоинта",
            "test_type": "api",
            "status": "active",
            "priority": "high",
            "environment": "development",
            "config": {"url": "https://api.example.com/test"},
            "created_by": "test_user",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "is_active": True
        }
        
        with patch.object(mock_database, 'execute_query') as mock_execute:
            mock_execute.return_value = [mock_test_data]
            
            result = await testing_service.get_test("test-123")
            
            assert result is not None
            assert result.id == "test-123"
            assert result.name == "API Test"
    
    @pytest.mark.asyncio
    async def test_get_test_not_found(self, testing_service, mock_database):
        """Тест получения несуществующего теста"""
        testing_service.db = mock_database
        
        with patch.object(mock_database, 'execute_query') as mock_execute:
            mock_execute.return_value = []
            
            result = await testing_service.get_test("nonexistent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_tests_with_filters(self, testing_service, mock_database):
        """Тест получения тестов с фильтрами"""
        testing_service.db = mock_database
        
        filters = TestFilter(
            test_type=TestType.api,
            status=TestStatus.active,
            priority=TestPriority.high
        )
        
        mock_tests_data = [
            {
                "id": "test-1",
                "name": "API Test 1",
                "test_type": "api",
                "status": "active",
                "priority": "high",
                "environment": "development",
                "created_by": "test_user",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            },
            {
                "id": "test-2",
                "name": "API Test 2",
                "test_type": "api",
                "status": "active",
                "priority": "high",
                "environment": "staging",
                "created_by": "test_user",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            }
        ]
        
        with patch.object(mock_database, 'execute_query') as mock_execute:
            mock_execute.return_value = mock_tests_data
            
            result = await testing_service.get_tests(filters, skip=0, limit=10)
            
            assert len(result) == 2
            assert all(test.test_type == TestType.api for test in result)
            assert all(test.status == TestStatus.active for test in result)
            assert all(test.priority == TestPriority.high for test in result)
    
    @pytest.mark.asyncio
    async def test_update_test(self, testing_service, mock_database):
        """Тест обновления теста"""
        testing_service.db = mock_database
        
        update_request = TestRequest(
            name="Updated API Test",
            description="Обновленное описание",
            test_type=TestType.api,
            priority=TestPriority.medium,
            environment=TestEnvironment.staging,
            config={"url": "https://api.example.com/updated"}
        )
        
        with patch.object(mock_database, 'execute_query') as mock_execute:
            mock_execute.return_value = [{"id": "test-123"}]
            
            result = await testing_service.update_test("test-123", update_request)
            
            assert result is not None
            assert result.name == "Updated API Test"
            assert result.priority == TestPriority.medium
            assert result.environment == TestEnvironment.staging
    
    @pytest.mark.asyncio
    async def test_delete_test(self, testing_service, mock_database):
        """Тест удаления теста"""
        testing_service.db = mock_database
        
        with patch.object(mock_database, 'execute_query') as mock_execute:
            mock_execute.return_value = [{"id": "test-123"}]
            
            result = await testing_service.delete_test("test-123")
            
            assert result is True
            mock_execute.assert_called()

class TestTestExecution:
    """Тесты для выполнения тестов"""
    
    @pytest.fixture
    def testing_service(self):
        return TestingService()
    
    @pytest.mark.asyncio
    async def test_execute_test(self, testing_service):
        """Тест выполнения теста"""
        with patch.object(testing_service, 'get_test') as mock_get_test:
            mock_test = TestResponse(
                id="test-123",
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
            mock_get_test.return_value = mock_test
            
            with patch.object(testing_service, 'db') as mock_db:
                mock_db.execute_query.return_value = [{"id": "exec-123"}]
                
                result = await testing_service.execute_test("test-123", "test_user")
                
                assert result is not None
                assert result.test_id == "test-123"
                assert result.status == TestStatus.pending
                assert result.created_by == "test_user"
    
    @pytest.mark.asyncio
    async def test_run_test_execution_api(self, testing_service):
        """Тест выполнения API теста"""
        execution = TestExecution(
            id="exec-123",
            test_id="test-123",
            status=TestStatus.pending,
            created_by="test_user",
            created_at=datetime.now()
        )
        
        test = TestResponse(
            id="test-123",
            name="API Test",
            test_type=TestType.api,
            config={
                "url": "https://httpbin.org/get",
                "method": "GET",
                "timeout": 30
            },
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        
        with patch.object(testing_service, 'get_test') as mock_get_test:
            mock_get_test.return_value = test
            
            with patch.object(testing_service, 'db') as mock_db:
                mock_db.execute_query.return_value = [{"id": "exec-123"}]
                
                await testing_service.run_test_execution("exec-123")
                
                # Проверяем, что статус обновлен
                mock_db.execute_query.assert_called()
    
    @pytest.mark.asyncio
    async def test_run_test_execution_ui(self, testing_service):
        """Тест выполнения UI теста"""
        execution = TestExecution(
            id="exec-123",
            test_id="test-123",
            status=TestStatus.pending,
            created_by="test_user",
            created_at=datetime.now()
        )
        
        test = TestResponse(
            id="test-123",
            name="UI Test",
            test_type=TestType.ui,
            config={
                "url": "https://example.com",
                "browser": "chrome",
                "viewport": {"width": 1920, "height": 1080}
            },
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        
        with patch.object(testing_service, 'get_test') as mock_get_test:
            mock_get_test.return_value = test
            
            with patch.object(testing_service, 'db') as mock_db:
                mock_db.execute_query.return_value = [{"id": "exec-123"}]
                
                await testing_service.run_test_execution("exec-123")
                
                # Проверяем, что статус обновлен
                mock_db.execute_query.assert_called()
    
    @pytest.mark.asyncio
    async def test_run_test_execution_performance(self, testing_service):
        """Тест выполнения теста производительности"""
        execution = TestExecution(
            id="exec-123",
            test_id="test-123",
            status=TestStatus.pending,
            created_by="test_user",
            created_at=datetime.now()
        )
        
        test = TestResponse(
            id="test-123",
            name="Performance Test",
            test_type=TestType.performance,
            config={
                "url": "https://example.com",
                "users": 10,
                "duration": 60,
                "ramp_up": 10
            },
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        
        with patch.object(testing_service, 'get_test') as mock_get_test:
            mock_get_test.return_value = test
            
            with patch.object(testing_service, 'db') as mock_db:
                mock_db.execute_query.return_value = [{"id": "exec-123"}]
                
                await testing_service.run_test_execution("exec-123")
                
                # Проверяем, что статус обновлен
                mock_db.execute_query.assert_called()
    
    @pytest.mark.asyncio
    async def test_cancel_execution(self, testing_service):
        """Тест отмены выполнения"""
        with patch.object(testing_service, 'db') as mock_db:
            mock_db.execute_query.return_value = [{"id": "exec-123"}]
            
            result = await testing_service.cancel_execution("exec-123")
            
            assert result is True
            mock_db.execute_query.assert_called()

class TestTestSuites:
    """Тесты для наборов тестов"""
    
    @pytest.fixture
    def testing_service(self):
        return TestingService()
    
    @pytest.mark.asyncio
    async def test_create_test_suite(self, testing_service, mock_database):
        """Тест создания набора тестов"""
        testing_service.db = mock_database
        
        with patch('app.services.DatabaseUtils.generate_id') as mock_generate_id:
            mock_generate_id.return_value = "suite-123"
            
            result = await testing_service.create_test_suite(SAMPLE_TEST_SUITE_REQUEST, "test_user")
            
            assert result is not None
            assert result.id == "suite-123"
            assert result.name == "API Test Suite"
            assert len(result.test_ids) == 3
            assert result.created_by == "test_user"
    
    @pytest.mark.asyncio
    async def test_execute_test_suite(self, testing_service):
        """Тест выполнения набора тестов"""
        suite = TestSuiteResponse(
            id="suite-123",
            name="API Test Suite",
            test_ids=["test-1", "test-2", "test-3"],
            config={"parallel": True},
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        
        with patch.object(testing_service, 'get_test_suite') as mock_get_suite:
            mock_get_suite.return_value = suite
            
            with patch.object(testing_service, 'execute_test') as mock_execute_test:
                mock_execute_test.return_value = TestExecutionResponse(
                    id="exec-123",
                    test_id="test-1",
                    status=TestStatus.pending,
                    created_by="test_user",
                    created_at=datetime.now()
                )
                
                result = await testing_service.execute_test_suite("suite-123", "test_user")
                
                assert len(result) == 3
                assert all(isinstance(execution, TestExecutionResponse) for execution in result)
                assert mock_execute_test.call_count == 3

class TestReports:
    """Тесты для отчетов"""
    
    @pytest.fixture
    def testing_service(self):
        return TestingService()
    
    @pytest.mark.asyncio
    async def test_generate_report(self, testing_service):
        """Тест генерации отчета"""
        execution = TestExecutionResponse(
            id="exec-123",
            test_id="test-123",
            status=TestStatus.completed,
            started_at=datetime.now() - timedelta(minutes=5),
            completed_at=datetime.now(),
            duration=300,
            result={"success": True, "response_time": 1.2},
            created_by="test_user",
            created_at=datetime.now()
        )
        
        with patch.object(testing_service, 'get_execution') as mock_get_execution:
            mock_get_execution.return_value = execution
            
            with patch.object(testing_service, 'db') as mock_db:
                mock_db.execute_query.return_value = [{"id": "report-123"}]
                
                result = await testing_service.generate_report("exec-123")
                
                assert result is not None
                assert result.execution_id == "exec-123"
                assert result.report_type == "detailed"
                assert "summary" in result.content
    
    @pytest.mark.asyncio
    async def test_get_reports(self, testing_service, mock_database):
        """Тест получения отчетов"""
        testing_service.db = mock_database
        
        mock_reports_data = [
            {
                "id": "report-1",
                "execution_id": "exec-1",
                "report_type": "detailed",
                "content": {"summary": "Test passed"},
                "summary": "Тест прошел успешно",
                "recommendations": [],
                "created_at": datetime.now()
            },
            {
                "id": "report-2",
                "execution_id": "exec-2",
                "report_type": "summary",
                "content": {"summary": "Test failed"},
                "summary": "Тест завершился с ошибкой",
                "recommendations": ["Проверить конфигурацию"],
                "created_at": datetime.now()
            }
        ]
        
        with patch.object(mock_database, 'execute_query') as mock_execute:
            mock_execute.return_value = mock_reports_data
            
            result = await testing_service.get_reports("test-123", None, 0, 10)
            
            assert len(result) == 2
            assert result[0].id == "report-1"
            assert result[1].id == "report-2"

class TestMetrics:
    """Тесты для метрик"""
    
    @pytest.fixture
    def testing_service(self):
        return TestingService()
    
    @pytest.mark.asyncio
    async def test_collect_metrics(self, testing_service, mock_database):
        """Тест сбора метрик"""
        testing_service.db = mock_database
        
        mock_executions_data = [
            {
                "id": "exec-1",
                "test_id": "test-1",
                "status": "completed",
                "duration": 30,
                "created_at": datetime.now() - timedelta(hours=1)
            },
            {
                "id": "exec-2",
                "test_id": "test-2",
                "status": "completed",
                "duration": 45,
                "created_at": datetime.now() - timedelta(hours=2)
            },
            {
                "id": "exec-3",
                "test_id": "test-3",
                "status": "failed",
                "duration": 60,
                "created_at": datetime.now() - timedelta(hours=3)
            }
        ]
        
        with patch.object(mock_database, 'execute_query') as mock_execute:
            mock_execute.return_value = mock_executions_data
            
            result = await testing_service.collect_metrics("test-1", "exec-1", "24h")
            
            assert result is not None
            assert "total_executions" in result
            assert "success_rate" in result
            assert "average_duration" in result
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, testing_service):
        """Тест получения метрик"""
        with patch.object(testing_service, 'collect_metrics') as mock_collect:
            mock_collect.return_value = {
                "total_tests": 100,
                "total_executions": 85,
                "successful_executions": 75,
                "failed_executions": 10,
                "average_duration": 45.5,
                "success_rate": 88.2
            }
            
            result = await testing_service.get_metrics("test-123", "exec-123", "24h")
            
            assert result is not None
            assert result.total_tests == 100
            assert result.total_executions == 85
            assert result.success_rate == 88.2

class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    @pytest.fixture
    def testing_service(self):
        return TestingService()
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, testing_service):
        """Тест ошибки подключения к базе данных"""
        with patch('app.services.get_database') as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                await testing_service.initialize()
    
    @pytest.mark.asyncio
    async def test_test_execution_timeout(self, testing_service):
        """Тест таймаута выполнения теста"""
        execution = TestExecution(
            id="exec-123",
            test_id="test-123",
            status=TestStatus.pending,
            created_by="test_user",
            created_at=datetime.now()
        )
        
        test = TestResponse(
            id="test-123",
            name="Timeout Test",
            test_type=TestType.api,
            config={"url": "https://httpbin.org/delay/10", "timeout": 5},
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True
        )
        
        with patch.object(testing_service, 'get_test') as mock_get_test:
            mock_get_test.return_value = test
            
            with patch.object(testing_service, 'db') as mock_db:
                mock_db.execute_query.return_value = [{"id": "exec-123"}]
                
                await testing_service.run_test_execution("exec-123")
                
                # Проверяем, что ошибка обработана
                mock_db.execute_query.assert_called()

class TestConcurrency:
    """Тесты конкурентности"""
    
    @pytest.mark.asyncio
    async def test_concurrent_test_executions(self, testing_service):
        """Тест конкурентных выполнений тестов"""
        async def execute_test(test_id):
            execution = TestExecution(
                id=f"exec-{test_id}",
                test_id=f"test-{test_id}",
                status=TestStatus.pending,
                created_by="test_user",
                created_at=datetime.now()
            )
            
            test = TestResponse(
                id=f"test-{test_id}",
                name=f"Test {test_id}",
                test_type=TestType.api,
                config={"url": "https://httpbin.org/get"},
                created_by="test_user",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            
            with patch.object(testing_service, 'get_test') as mock_get_test:
                mock_get_test.return_value = test
                
                with patch.object(testing_service, 'db') as mock_db:
                    mock_db.execute_query.return_value = [{"id": f"exec-{test_id}"}]
                    
                    await testing_service.run_test_execution(f"exec-{test_id}")
        
        # Запускаем 5 конкурентных выполнений
        tasks = [execute_test(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Проверяем, что все выполнились без ошибок
        assert len(tasks) == 5

# Тесты производительности
class TestPerformance:
    """Тесты производительности сервисов"""
    
    @pytest.mark.asyncio
    async def test_bulk_test_creation(self, testing_service, mock_database):
        """Тест массового создания тестов"""
        testing_service.db = mock_database
        
        with patch('app.services.DatabaseUtils.generate_id') as mock_generate_id:
            mock_generate_id.side_effect = [f"test-{i}" for i in range(100)]
            
            with patch.object(mock_database, 'execute_query') as mock_execute:
                mock_execute.return_value = [{"id": "test-0"}]
                
                start_time = datetime.now()
                
                # Создаем 100 тестов
                tasks = []
                for i in range(100):
                    test_request = TestRequest(
                        name=f"Test {i}",
                        test_type=TestType.api,
                        priority=TestPriority.medium,
                        environment=TestEnvironment.development,
                        config={"url": f"https://api.example.com/test{i}"}
                    )
                    tasks.append(testing_service.create_test(test_request, "test_user"))
                
                results = await asyncio.gather(*tasks)
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                assert len(results) == 100
                assert duration < 10.0  # Должно быть меньше 10 секунд
    
    @pytest.mark.asyncio
    async def test_large_dataset_query(self, testing_service, mock_database):
        """Тест запроса большого набора данных"""
        testing_service.db = mock_database
        
        # Создаем большой набор тестовых данных
        large_dataset = [
            {
                "id": f"test-{i}",
                "name": f"Test {i}",
                "test_type": "api",
                "status": "active",
                "priority": "medium",
                "environment": "development",
                "created_by": "test_user",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True
            }
            for i in range(1000)
        ]
        
        with patch.object(mock_database, 'execute_query') as mock_execute:
            mock_execute.return_value = large_dataset
            
            start_time = datetime.now()
            result = await testing_service.get_tests(TestFilter(), skip=0, limit=1000)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            assert len(result) == 1000
            assert duration < 5.0  # Должно быть меньше 5 секунд

# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_test_lifecycle_integration(self, testing_service, mock_database):
        """Интеграционный тест полного жизненного цикла теста"""
        testing_service.db = mock_database
        
        # 1. Создание теста
        with patch('app.services.DatabaseUtils.generate_id') as mock_generate_id:
            mock_generate_id.return_value = "test-123"
            
            with patch.object(mock_database, 'execute_query') as mock_execute:
                mock_execute.return_value = [{"id": "test-123"}]
                
                test = await testing_service.create_test(SAMPLE_TEST_REQUEST, "test_user")
                assert test.id == "test-123"
        
        # 2. Выполнение теста
        with patch.object(testing_service, 'get_test') as mock_get_test:
            mock_get_test.return_value = test
            
            with patch.object(mock_database, 'execute_query') as mock_execute:
                mock_execute.return_value = [{"id": "exec-123"}]
                
                execution = await testing_service.execute_test("test-123", "test_user")
                assert execution.test_id == "test-123"
        
        # 3. Генерация отчета
        with patch.object(testing_service, 'get_execution') as mock_get_execution:
            mock_get_execution.return_value = execution
            
            with patch.object(mock_database, 'execute_query') as mock_execute:
                mock_execute.return_value = [{"id": "report-123"}]
                
                report = await testing_service.generate_report("exec-123")
                assert report.execution_id == "exec-123"
    
    @pytest.mark.asyncio
    async def test_test_suite_execution_integration(self, testing_service, mock_database):
        """Интеграционный тест выполнения набора тестов"""
        testing_service.db = mock_database
        
        # Создание набора тестов
        with patch('app.services.DatabaseUtils.generate_id') as mock_generate_id:
            mock_generate_id.return_value = "suite-123"
            
            with patch.object(mock_database, 'execute_query') as mock_execute:
                mock_execute.return_value = [{"id": "suite-123"}]
                
                suite = await testing_service.create_test_suite(SAMPLE_TEST_SUITE_REQUEST, "test_user")
                assert suite.id == "suite-123"
        
        # Выполнение набора тестов
        with patch.object(testing_service, 'get_test_suite') as mock_get_suite:
            mock_get_suite.return_value = suite
            
            with patch.object(testing_service, 'execute_test') as mock_execute_test:
                mock_execute_test.return_value = TestExecutionResponse(
                    id="exec-123",
                    test_id="test-1",
                    status=TestStatus.pending,
                    created_by="test_user",
                    created_at=datetime.now()
                )
                
                executions = await testing_service.execute_test_suite("suite-123", "test_user")
                assert len(executions) == 3 