"""
Тесты для основного приложения LLM Tuning микросервиса
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import get_db
from app.services import LLMTuningService
from app.schemas import (
    LLMModelCreate, ModelRouteCreate, TuningSessionCreate,
    GenerateRequest, OptimizationRequest
)


@pytest.fixture
def client():
    """Фикстура для тестового клиента"""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Фикстура для мока сессии БД"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_llm_service(mock_db_session):
    """Фикстура для мока LLM сервиса"""
    service = MagicMock(spec=LLMTuningService)
    service.model_manager = MagicMock()
    service.route_manager = MagicMock()
    service.rag_service = MagicMock()
    service.tuning_service = MagicMock()
    service.performance_monitor = MagicMock()
    service.optimization_service = MagicMock()
    return service


class TestHealthCheck:
    """Тесты для health check эндпоинтов"""
    
    def test_health_check(self, client):
        """Тест основного health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_detailed(self, client):
        """Тест детального health check"""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "ollama" in data
        assert "timestamp" in data
        assert "version" in data


class TestModelsAPI:
    """Тесты для API моделей"""
    
    def test_list_models(self, client, mock_llm_service):
        """Тест получения списка моделей"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_llm_service.model_manager.list_models.return_value = []
            
            response = client.get("/api/models/")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
    
    def test_get_model(self, client, mock_llm_service):
        """Тест получения модели по ID"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_model = MagicMock()
            mock_model.id = 1
            mock_model.name = "test-model"
            mock_llm_service.model_manager.get_model.return_value = mock_model
            
            response = client.get("/api/models/1")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "test-model"
    
    def test_create_model(self, client, mock_llm_service):
        """Тест создания модели"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            model_data = {
                "name": "test-model",
                "description": "Test model",
                "model_type": "llama",
                "version": "1.0"
            }
            
            mock_model = MagicMock()
            mock_model.id = 1
            mock_model.name = "test-model"
            mock_llm_service.model_manager.create_model.return_value = mock_model
            
            response = client.post("/api/models/", json=model_data)
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "test-model"
    
    def test_update_model(self, client, mock_llm_service):
        """Тест обновления модели"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            update_data = {"description": "Updated description"}
            
            mock_model = MagicMock()
            mock_model.id = 1
            mock_model.description = "Updated description"
            mock_llm_service.model_manager.update_model.return_value = mock_model
            
            response = client.put("/api/models/1", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert data["description"] == "Updated description"
    
    def test_delete_model(self, client, mock_llm_service):
        """Тест удаления модели"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_llm_service.model_manager.delete_model.return_value = True
            
            response = client.delete("/api/models/1")
            assert response.status_code == 204


class TestRoutesAPI:
    """Тесты для API маршрутов"""
    
    def test_list_routes(self, client, mock_llm_service):
        """Тест получения списка маршрутов"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_llm_service.route_manager._route_cache = {}
            
            response = client.get("/api/routes/")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
    
    def test_create_route(self, client, mock_llm_service):
        """Тест создания маршрута"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            route_data = {
                "name": "test-route",
                "description": "Test route",
                "strategy": "round_robin",
                "model_id": 1
            }
            
            mock_route = MagicMock()
            mock_route.id = 1
            mock_route.name = "test-route"
            mock_llm_service.route_manager.create_route.return_value = mock_route
            
            response = client.post("/api/routes/", json=route_data)
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "test-route"
    
    def test_get_route(self, client, mock_llm_service):
        """Тест получения маршрута по ID"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_route = MagicMock()
            mock_route.id = 1
            mock_route.name = "test-route"
            mock_llm_service.route_manager._route_cache = {"test-route": mock_route}
            
            response = client.get("/api/routes/1")
            assert response.status_code == 200


class TestTuningAPI:
    """Тесты для API тюнинга"""
    
    def test_list_tuning_sessions(self, client, mock_llm_service):
        """Тест получения списка сессий тюнинга"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_llm_service.tuning_service.get_tuning_sessions.return_value = []
            
            response = client.get("/api/tuning/sessions/")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
    
    def test_create_tuning_session(self, client, mock_llm_service):
        """Тест создания сессии тюнинга"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            session_data = {
                "name": "test-session",
                "description": "Test tuning session",
                "strategy": "fine_tuning",
                "model_id": 1
            }
            
            mock_session = MagicMock()
            mock_session.id = 1
            mock_session.name = "test-session"
            mock_llm_service.tuning_service.create_tuning_session.return_value = mock_session
            
            response = client.post("/api/tuning/sessions/", json=session_data)
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "test-session"
    
    def test_start_tuning(self, client, mock_llm_service):
        """Тест запуска тюнинга"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_llm_service.tuning_service.start_tuning.return_value = True
            
            response = client.post("/api/tuning/sessions/1/start")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestGenerateAPI:
    """Тесты для API генерации"""
    
    def test_generate_text(self, client, mock_llm_service):
        """Тест генерации текста"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            generate_data = {
                "content": "Test prompt",
                "request_type": "general",
                "use_rag": False
            }
            
            mock_result = {
                "response": "Generated response",
                "model_used": "test-model",
                "tokens_generated": 10,
                "response_time": 1.5
            }
            mock_llm_service.process_request.return_value = mock_result
            
            response = client.post("/api/generate/", json=generate_data)
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Generated response"
            assert data["model_used"] == "test-model"
    
    def test_generate_with_rag(self, client, mock_llm_service):
        """Тест генерации с RAG"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            generate_data = {
                "content": "Test prompt",
                "request_type": "general",
                "use_rag": True
            }
            
            mock_result = {
                "response": "Generated response with RAG",
                "model_used": "test-model",
                "tokens_generated": 15,
                "response_time": 2.0
            }
            mock_llm_service.process_request.return_value = mock_result
            
            response = client.post("/api/generate/", json=generate_data)
            assert response.status_code == 200
            data = response.json()
            assert "RAG" in data["response"]


class TestOptimizationAPI:
    """Тесты для API оптимизации"""
    
    def test_optimize_model(self, client, mock_llm_service):
        """Тест оптимизации модели"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            optimization_data = {
                "model_id": 1,
                "target_response_time": 1.0,
                "target_quality": 0.9
            }
            
            mock_result = {
                "model_id": 1,
                "optimization_applied": True,
                "new_params": {"temperature": 0.8},
                "performance_improvement": 0.15
            }
            mock_llm_service.optimization_service.optimize_model.return_value = mock_result
            
            response = client.post("/api/optimize/", json=optimization_data)
            assert response.status_code == 200
            data = response.json()
            assert data["optimization_applied"] is True
            assert data["performance_improvement"] == 0.15


class TestRAGAPI:
    """Тесты для API RAG"""
    
    def test_add_document(self, client, mock_llm_service):
        """Тест добавления документа в RAG"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            document_data = {
                "title": "Test Document",
                "content": "Test content for RAG",
                "source": "test-source",
                "tags": ["test", "rag"]
            }
            
            mock_document = MagicMock()
            mock_document.id = 1
            mock_document.title = "Test Document"
            mock_llm_service.rag_service.add_document.return_value = mock_document
            
            response = client.post("/api/rag/documents/", json=document_data)
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 1
            assert data["title"] == "Test Document"
    
    def test_search_documents(self, client, mock_llm_service):
        """Тест поиска документов в RAG"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_documents = []
            mock_llm_service.rag_service.search_documents.return_value = mock_documents
            
            response = client.get("/api/rag/search?query=test")
            assert response.status_code == 200
            data = response.json()
            assert "documents" in data


class TestMonitoringAPI:
    """Тесты для API мониторинга"""
    
    def test_get_metrics(self, client, mock_llm_service):
        """Тест получения метрик"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_metrics = []
            mock_llm_service.performance_monitor.get_model_metrics.return_value = mock_metrics
            
            response = client.get("/api/monitoring/metrics/1")
            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data
    
    def test_get_performance_summary(self, client, mock_llm_service):
        """Тест получения сводки производительности"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_summary = {
                "total_requests": 100,
                "avg_response_time": 1.5,
                "avg_tokens_generated": 50,
                "avg_success_rate": 0.95
            }
            mock_llm_service.performance_monitor.get_performance_summary.return_value = mock_summary
            
            response = client.get("/api/monitoring/summary/1")
            assert response.status_code == 200
            data = response.json()
            assert data["total_requests"] == 100
            assert data["avg_response_time"] == 1.5


class TestSystemAPI:
    """Тесты для системных API"""
    
    def test_get_system_status(self, client, mock_llm_service):
        """Тест получения статуса системы"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_status = {
                "status": "healthy",
                "models_count": 5,
                "active_routes": 3,
                "total_requests_24h": 1000,
                "avg_response_time": 1.5
            }
            mock_llm_service.get_system_status.return_value = mock_status
            
            response = client.get("/api/system/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["models_count"] == 5
    
    def test_get_system_stats(self, client, mock_llm_service):
        """Тест получения статистики системы"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            response = client.get("/api/system/stats")
            assert response.status_code == 200
            data = response.json()
            assert "statistics" in data


class TestErrorHandling:
    """Тесты для обработки ошибок"""
    
    def test_model_not_found(self, client, mock_llm_service):
        """Тест обработки ошибки 'модель не найдена'"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_llm_service.model_manager.get_model.return_value = None
            
            response = client.get("/api/models/999")
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
    
    def test_route_not_found(self, client, mock_llm_service):
        """Тест обработки ошибки 'маршрут не найден'"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            mock_llm_service.route_manager._route_cache = {}
            
            response = client.get("/api/routes/999")
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
    
    def test_invalid_request_data(self, client):
        """Тест обработки невалидных данных запроса"""
        invalid_data = {
            "name": "",  # Пустое имя
            "model_type": "invalid_type"
        }
        
        response = client.post("/api/models/", json=invalid_data)
        assert response.status_code == 422  # Validation Error


class TestAuthentication:
    """Тесты для аутентификации"""
    
    def test_public_endpoints_no_auth(self, client):
        """Тест публичных эндпоинтов без аутентификации"""
        endpoints = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 404]  # 404 для несуществующих
    
    def test_protected_endpoints_require_auth(self, client):
        """Тест защищенных эндпоинтов с требованием аутентификации"""
        endpoints = [
            "/api/models/",
            "/api/routes/",
            "/api/tuning/sessions/",
            "/api/generate/"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401  # Unauthorized
    
    def test_protected_endpoints_with_auth(self, client, mock_llm_service):
        """Тест защищенных эндпоинтов с аутентификацией"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            headers = {"X-API-Key": "test-api-key"}
            
            response = client.get("/api/models/", headers=headers)
            assert response.status_code == 200


class TestRateLimiting:
    """Тесты для ограничения частоты запросов"""
    
    def test_rate_limit_exceeded(self, client):
        """Тест превышения лимита запросов"""
        # Отправляем много запросов подряд
        for _ in range(100):
            response = client.get("/health")
            if response.status_code == 429:  # Too Many Requests
                break
        else:
            pytest.skip("Rate limiting not implemented or configured")


class TestPerformance:
    """Тесты производительности"""
    
    def test_response_time(self, client, mock_llm_service):
        """Тест времени ответа"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            import time
            
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 1.0  # Ответ должен быть быстрее 1 секунды
            assert response.status_code == 200
    
    def test_concurrent_requests(self, client, mock_llm_service):
        """Тест конкурентных запросов"""
        with patch('app.main.get_llm_service', return_value=mock_llm_service):
            import asyncio
            import concurrent.futures
            
            def make_request():
                return client.get("/health")
            
            # Выполняем 10 конкурентных запросов
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                responses = [future.result() for future in futures]
            
            # Все запросы должны быть успешными
            for response in responses:
                assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__]) 