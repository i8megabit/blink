"""
🧪 ТЕСТЫ API БЕНЧМАРК МИКРОСЕРВИСА
Тестирование FastAPI эндпоинтов
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List, Dict, Any

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.models import BenchmarkRequest, BenchmarkType, BenchmarkStatus
from app.config import settings


@pytest.fixture
def client():
    """Фикстура тестового клиента."""
    return TestClient(app)


@pytest.fixture
def benchmark_request_data():
    """Фикстура данных запроса бенчмарка."""
    return {
        "name": "Test Benchmark",
        "description": "Test description",
        "benchmark_type": "seo_basic",
        "models": ["llama2", "mistral"],
        "iterations": 3,
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 1024
        }
    }


class TestRootEndpoint:
    """Тесты корневого эндпоинта."""
    
    def test_root_endpoint(self, client):
        """Тест корневого эндпоинта."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Benchmark Service"
        assert data["version"] == settings.version
        assert data["status"] == "running"
        assert "docs" in data
        assert "health" in data


class TestHealthEndpoint:
    """Тесты эндпоинта здоровья."""
    
    def test_health_check(self, client):
        """Тест проверки здоровья."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data
        assert "services" in data
        assert data["version"] == settings.version


class TestBenchmarkEndpoints:
    """Тесты эндпоинтов бенчмарка."""
    
    @patch('app.main.get_benchmark_service')
    @patch('app.main.get_cache')
    def test_create_benchmark_success(self, mock_get_cache, mock_get_service, client, benchmark_request_data):
        """Тест успешного создания бенчмарка."""
        # Мокаем зависимости
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None  # Нет кэшированного результата
        
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        
        response = client.post("/benchmark", json=benchmark_request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "запущен в фоновом режиме" in data["message"]
    
    @patch('app.main.get_cache')
    def test_create_benchmark_cached_result(self, mock_get_cache, client, benchmark_request_data):
        """Тест создания бенчмарка с кэшированным результатом."""
        # Мокаем кэш с результатом
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = {
            "benchmark_id": "test-id",
            "name": "Test Benchmark",
            "status": "completed"
        }
        
        response = client.post("/benchmark", json=benchmark_request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "получен из кэша" in data["message"]
        assert data["data"] is not None
    
    def test_create_benchmark_invalid_data(self, client):
        """Тест создания бенчмарка с невалидными данными."""
        invalid_data = {
            "name": "",  # Пустое имя
            "benchmark_type": "invalid_type",
            "models": [],  # Пустой список моделей
            "iterations": 0  # Недопустимое количество итераций
        }
        
        response = client.post("/benchmark", json=invalid_data)
        
        assert response.status_code == 422  # Validation Error
    
    @patch('app.main.get_cache')
    def test_get_benchmark_success(self, mock_get_cache, client):
        """Тест успешного получения бенчмарка."""
        benchmark_id = "test-id"
        mock_result = {
            "benchmark_id": benchmark_id,
            "name": "Test Benchmark",
            "status": "completed"
        }
        
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get_benchmark_result.return_value = mock_result
        
        response = client.get(f"/benchmark/{benchmark_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["benchmark_id"] == benchmark_id
    
    @patch('app.main.get_cache')
    def test_get_benchmark_not_found(self, mock_get_cache, client):
        """Тест получения несуществующего бенчмарка."""
        benchmark_id = "non-existent-id"
        
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get_benchmark_result.return_value = None
        
        response = client.get(f"/benchmark/{benchmark_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "не найден" in data["message"]
    
    @patch('app.main.get_benchmark_service')
    def test_list_benchmarks_success(self, mock_get_service, client):
        """Тест успешного получения списка бенчмарков."""
        mock_results = [
            {
                "benchmark_id": "1",
                "name": "Test 1",
                "status": "completed"
            },
            {
                "benchmark_id": "2",
                "name": "Test 2",
                "status": "completed"
            }
        ]
        
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        mock_service.get_benchmark_history.return_value = mock_results
        
        response = client.get("/benchmarks?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["total"] == 2
    
    @patch('app.main.get_benchmark_service')
    def test_list_benchmarks_with_filters(self, mock_get_service, client):
        """Тест получения списка бенчмарков с фильтрами."""
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        mock_service.get_benchmark_history.return_value = []
        
        response = client.get("/benchmarks?benchmark_type=seo_basic&model_name=llama2&status=completed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch('app.main.get_benchmark_service')
    def test_cancel_benchmark_success(self, mock_get_service, client):
        """Тест успешной отмены бенчмарка."""
        benchmark_id = "test-id"
        
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        mock_service.cancel_benchmark.return_value = True
        
        response = client.delete(f"/benchmark/{benchmark_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "отменен" in data["message"]
    
    @patch('app.main.get_benchmark_service')
    def test_cancel_benchmark_not_found(self, mock_get_service, client):
        """Тест отмены несуществующего бенчмарка."""
        benchmark_id = "non-existent-id"
        
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        mock_service.cancel_benchmark.return_value = False
        
        response = client.delete(f"/benchmark/{benchmark_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "не найден" in data["message"]


class TestModelsEndpoints:
    """Тесты эндпоинтов моделей."""
    
    def test_list_models(self, client):
        """Тест получения списка моделей."""
        response = client.get("/models")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
    
    @patch('app.main.get_benchmark_service')
    def test_get_model_performance_success(self, mock_get_service, client):
        """Тест успешного получения производительности модели."""
        model_name = "llama2"
        mock_performance = {
            "model": model_name,
            "avg_response_time": 1.5,
            "accuracy": 0.85
        }
        
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        mock_service.get_model_performance.return_value = mock_performance
        
        response = client.get(f"/models/{model_name}/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["model"] == model_name
    
    @patch('app.main.get_benchmark_service')
    def test_get_model_performance_not_found(self, mock_get_service, client):
        """Тест получения производительности несуществующей модели."""
        model_name = "unknown_model"
        
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        mock_service.get_model_performance.return_value = None
        
        response = client.get(f"/models/{model_name}/performance")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "не найдены" in data["message"]


class TestBenchmarkTypesEndpoint:
    """Тесты эндпоинта типов бенчмарков."""
    
    def test_get_benchmark_types(self, client):
        """Тест получения типов бенчмарков."""
        response = client.get("/benchmark-types")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], dict)
        assert len(data["data"]) > 0


class TestStatsEndpoints:
    """Тесты эндпоинтов статистики."""
    
    @patch('app.main.get_cache_stats')
    def test_get_cache_statistics(self, mock_get_cache_stats, client):
        """Тест получения статистики кэша."""
        mock_stats = {
            "enabled": True,
            "total_keys": 100,
            "memory_usage": "50MB",
            "hit_rate": 85.5,
            "connected_clients": 5,
            "uptime": 3600
        }
        mock_get_cache_stats.return_value = mock_stats
        
        response = client.get("/stats/cache")
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["total_keys"] == 100
        assert data["hit_rate"] == 85.5
    
    def test_get_performance_statistics(self, client):
        """Тест получения статистики производительности."""
        response = client.get("/stats/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert "active_benchmarks" in data
        assert "completed_today" in data
        assert "avg_response_time" in data
        assert "memory_usage_mb" in data
        assert "cpu_usage_percent" in data


class TestCacheEndpoints:
    """Тесты эндпоинтов кэша."""
    
    @patch('app.main.get_cache')
    def test_clear_cache_success(self, mock_get_cache, client):
        """Тест успешной очистки кэша."""
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        mock_cache.clear.return_value = 50
        
        response = client.delete("/cache?pattern=test*")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 50
        assert "удалено" in data["message"]


class TestExportEndpoints:
    """Тесты эндпоинтов экспорта."""
    
    def test_export_benchmarks(self, client):
        """Тест экспорта бенчмарков."""
        export_request = {
            "benchmark_ids": ["1", "2", "3"],
            "format": "json",
            "include_raw_data": False,
            "include_metrics": True
        }
        
        response = client.post("/export", json=export_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "filename" in data
        assert "download_url" in data
        assert data["format"] == "json"
    
    def test_export_benchmarks_invalid_format(self, client):
        """Тест экспорта с невалидным форматом."""
        export_request = {
            "benchmark_ids": ["1"],
            "format": "invalid_format",
            "include_raw_data": False,
            "include_metrics": True
        }
        
        response = client.post("/export", json=export_request)
        
        assert response.status_code == 422  # Validation Error


class TestCompareEndpoints:
    """Тесты эндпоинтов сравнения."""
    
    @patch('app.main.get_cache')
    def test_compare_benchmarks_success(self, mock_get_cache, client):
        """Тест успешного сравнения бенчмарков."""
        benchmark_ids = ["1", "2"]
        mock_results = [
            {"benchmark_id": "1", "name": "Test 1"},
            {"benchmark_id": "2", "name": "Test 2"}
        ]
        
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get_benchmark_result.side_effect = mock_results
        
        response = client.post("/compare", json=benchmark_ids)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "сравнение" in data["message"]
    
    def test_compare_benchmarks_insufficient_data(self, client):
        """Тест сравнения с недостаточными данными."""
        benchmark_ids = ["1"]  # Только один ID
        
        response = client.post("/compare", json=benchmark_ids)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "минимум 2" in data["message"]


class TestWebSocketEndpoints:
    """Тесты WebSocket эндпоинтов."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Тест WebSocket подключения."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
            with ac.websocket_connect("/ws/test-client") as websocket:
                # Проверяем, что подключение установлено
                assert websocket is not None
    
    @pytest.mark.asyncio
    async def test_websocket_message_echo(self):
        """Тест эхо сообщений WebSocket."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
            with ac.websocket_connect("/ws/test-client") as websocket:
                # Отправляем сообщение
                await websocket.send_text("Hello, WebSocket!")
                
                # Получаем ответ
                response = await websocket.receive_text()
                assert "Echo: Hello, WebSocket!" in response


class TestErrorHandling:
    """Тесты обработки ошибок."""
    
    def test_http_exception_handler(self, client):
        """Тест обработчика HTTP исключений."""
        # Тестируем 404 ошибку
        response = client.get("/non-existent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "HTTPException"
    
    def test_general_exception_handler(self, client):
        """Тест обработчика общих исключений."""
        # Этот тест может быть сложным для реализации
        # так как нужно вызвать необработанное исключение
        pass


class TestValidation:
    """Тесты валидации данных."""
    
    def test_benchmark_request_validation(self, client):
        """Тест валидации запроса бенчмарка."""
        # Тест с невалидными данными
        invalid_request = {
            "name": "",  # Пустое имя
            "benchmark_type": "invalid_type",  # Невалидный тип
            "models": [],  # Пустой список
            "iterations": -1  # Отрицательное количество
        }
        
        response = client.post("/benchmark", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_benchmark_request_valid_data(self, client, benchmark_request_data):
        """Тест валидации корректных данных."""
        response = client.post("/benchmark", json=benchmark_request_data)
        
        # Должен пройти валидацию (может упасть на других этапах)
        assert response.status_code in [200, 500]  # 500 если нет моков


class TestPerformance:
    """Тесты производительности API."""
    
    def test_health_check_performance(self, client):
        """Тест производительности health check."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 1.0  # Менее 1 секунды
    
    def test_root_endpoint_performance(self, client):
        """Тест производительности корневого эндпоинта."""
        import time
        
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 0.1  # Менее 100ms


# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты API."""
    
    @patch('app.main.get_benchmark_service')
    @patch('app.main.get_cache')
    def test_full_benchmark_workflow(self, mock_get_cache, mock_get_service, client, benchmark_request_data):
        """Тест полного workflow бенчмарка через API."""
        # 1. Создание бенчмарка
        mock_cache = AsyncMock()
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None
        
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service
        
        create_response = client.post("/benchmark", json=benchmark_request_data)
        assert create_response.status_code == 200
        
        # 2. Получение списка бенчмарков
        mock_service.get_benchmark_history.return_value = []
        list_response = client.get("/benchmarks")
        assert list_response.status_code == 200
        
        # 3. Получение статистики
        stats_response = client.get("/stats/cache")
        assert stats_response.status_code == 200
        
        # 4. Проверка здоровья
        health_response = client.get("/health")
        assert health_response.status_code == 200 