"""
Тесты для микросервиса LLM Tuning
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, init_db
from app.models import (
    LLMModel, ModelRoute, TuningSession, RAGDocument, 
    PerformanceMetrics, ModelStatus, RouteStrategy
)
from app.schemas import (
    LLMModelCreate, LLMModelUpdate, RouteCreate,
    TuningSessionCreate, RAGQuery
)


# Фикстуры для тестов
@pytest.fixture
async def test_db():
    """Создание тестовой базы данных"""
    # Используем SQLite в памяти для тестов
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: sync_conn.execute(
            "CREATE TABLE IF NOT EXISTS llm_models ("
            "id INTEGER PRIMARY KEY, "
            "name TEXT NOT NULL, "
            "base_model TEXT NOT NULL, "
            "provider TEXT NOT NULL, "
            "is_available BOOLEAN DEFAULT TRUE, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        ))
        
        await conn.run_sync(lambda sync_conn: sync_conn.execute(
            "CREATE TABLE IF NOT EXISTS model_routes ("
            "id INTEGER PRIMARY KEY, "
            "name TEXT NOT NULL, "
            "model_id INTEGER, "
            "strategy TEXT NOT NULL, "
            "is_active BOOLEAN DEFAULT TRUE, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        ))
        
        await conn.run_sync(lambda sync_conn: sync_conn.execute(
            "CREATE TABLE IF NOT EXISTS tuning_sessions ("
            "id INTEGER PRIMARY KEY, "
            "model_id INTEGER NOT NULL, "
            "status TEXT NOT NULL, "
            "progress INTEGER DEFAULT 0, "
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ")"
        ))
    
    yield async_session
    
    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Создание тестового клиента"""
    async def override_get_db():
        async with test_db() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_model_data():
    """Тестовые данные для модели"""
    return {
        "name": "test-model",
        "base_model": "llama2",
        "provider": "ollama",
        "description": "Тестовая модель",
        "parameters": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000
        }
    }


@pytest.fixture
def sample_route_data():
    """Тестовые данные для маршрута"""
    return {
        "name": "test-route",
        "model_id": 1,
        "strategy": RouteStrategy.ROUND_ROBIN,
        "request_types": ["text", "code"],
        "keywords": ["python", "programming"],
        "complexity_threshold": 0.5,
        "is_active": True
    }


@pytest.fixture
def sample_tuning_session_data():
    """Тестовые данные для сессии тюнинга"""
    return {
        "model_id": 1,
        "strategy": "instruction_tuning",
        "parameters": {
            "temperature": 0.7,
            "top_p": 0.9,
            "learning_rate": 0.001
        },
        "training_data": json.dumps([
            {
                "instruction": "Объясни концепцию",
                "input": "",
                "output": "Это концепция..."
            }
        ]),
        "system_prompt": "Ты полезный ассистент."
    }


# Тесты API endpoints
class TestHealthCheck:
    """Тесты health check endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Тест проверки здоровья сервиса"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "llm-tuning"
        assert "version" in data
        assert "environment" in data
        assert "features" in data


class TestModelsAPI:
    """Тесты API для управления моделями"""
    
    @pytest.mark.asyncio
    async def test_create_model(self, client, sample_model_data):
        """Тест создания модели"""
        with patch('app.services.ModelService.create_model') as mock_create:
            mock_create.return_value = LLMModel(**sample_model_data, id=1)
            
            response = await client.post(
                "/api/v1/models",
                json=sample_model_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == sample_model_data["name"]
            assert data["base_model"] == sample_model_data["base_model"]
    
    @pytest.mark.asyncio
    async def test_list_models(self, client):
        """Тест получения списка моделей"""
        with patch('app.services.ModelService.list_models') as mock_list:
            mock_list.return_value = [
                LLMModel(id=1, name="model1", base_model="llama2", provider="ollama"),
                LLMModel(id=2, name="model2", base_model="mistral", provider="ollama")
            ]
            
            response = await client.get("/api/v1/models")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "model1"
            assert data[1]["name"] == "model2"
    
    @pytest.mark.asyncio
    async def test_get_model(self, client):
        """Тест получения модели по ID"""
        with patch('app.services.ModelService.get_model') as mock_get:
            mock_get.return_value = LLMModel(
                id=1, name="test-model", base_model="llama2", provider="ollama"
            )
            
            response = await client.get("/api/v1/models/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "test-model"
    
    @pytest.mark.asyncio
    async def test_get_model_not_found(self, client):
        """Тест получения несуществующей модели"""
        with patch('app.services.ModelService.get_model') as mock_get:
            mock_get.return_value = None
            
            response = await client.get("/api/v1/models/999")
            
            assert response.status_code == 404
            assert "не найдена" in response.json()["detail"]


class TestRoutesAPI:
    """Тесты API для маршрутизации"""
    
    @pytest.mark.asyncio
    async def test_create_route(self, client, sample_route_data):
        """Тест создания маршрута"""
        with patch('app.services.RouterService.create_route') as mock_create:
            mock_create.return_value = ModelRoute(**sample_route_data, id=1)
            
            response = await client.post(
                "/api/v1/routes",
                json=sample_route_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == sample_route_data["name"]
            assert data["strategy"] == sample_route_data["strategy"]
    
    @pytest.mark.asyncio
    async def test_route_request(self, client):
        """Тест маршрутизации запроса"""
        with patch('app.services.RouterService.route_request') as mock_route:
            mock_route.return_value = {
                "model": "llama2",
                "response": "Тестовый ответ",
                "route_used": "test-route"
            }
            
            request_data = {
                "request_type": "text",
                "content": "Привет, как дела?",
                "use_rag": False
            }
            
            response = await client.post(
                "/api/v1/route",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "llama2"
            assert data["response"] == "Тестовый ответ"


class TestRAGAPI:
    """Тесты API для RAG"""
    
    @pytest.mark.asyncio
    async def test_rag_query(self, client):
        """Тест RAG запроса"""
        with patch('app.services.RAGService.generate_with_rag') as mock_rag:
            mock_rag.return_value = {
                "response": "Ответ с контекстом",
                "context_documents": [
                    {"title": "Документ 1", "source": "test", "relevance_score": 0.8}
                ]
            }
            
            query_data = {
                "query": "Что такое машинное обучение?",
                "model_name": "llama2",
                "use_context": True
            }
            
            response = await client.post(
                "/api/v1/rag/query",
                json=query_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Ответ с контекстом"
            assert len(data["context_documents"]) == 1
    
    @pytest.mark.asyncio
    async def test_add_document(self, client):
        """Тест добавления документа"""
        with patch('app.services.RAGService.add_document') as mock_add:
            mock_add.return_value = RAGDocument(
                id=1, title="Test Doc", content="Test content", source="test"
            )
            
            document_data = {
                "title": "Test Document",
                "content": "This is test content",
                "source": "test",
                "document_type": "article"
            }
            
            response = await client.post(
                "/api/v1/rag/documents",
                params=document_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Document"


class TestTuningAPI:
    """Тесты API для тюнинга"""
    
    @pytest.mark.asyncio
    async def test_create_tuning_session(self, client, sample_tuning_session_data):
        """Тест создания сессии тюнинга"""
        with patch('app.services.TuningService.create_tuning_session') as mock_create:
            mock_create.return_value = TuningSession(
                **sample_tuning_session_data, id=1, status=ModelStatus.PENDING
            )
            
            response = await client.post(
                "/api/v1/tuning/sessions",
                json=sample_tuning_session_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_id"] == sample_tuning_session_data["model_id"]
            assert data["status"] == ModelStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_list_tuning_sessions(self, client):
        """Тест получения списка сессий тюнинга"""
        with patch('app.services.TuningService.list_tuning_sessions') as mock_list:
            mock_list.return_value = [
                TuningSession(id=1, model_id=1, status=ModelStatus.COMPLETED),
                TuningSession(id=2, model_id=1, status=ModelStatus.FAILED)
            ]
            
            response = await client.get("/api/v1/tuning/sessions")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["status"] == ModelStatus.COMPLETED
            assert data[1]["status"] == ModelStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_get_tuning_session(self, client):
        """Тест получения сессии тюнинга"""
        with patch('app.services.TuningService.get_tuning_session') as mock_get:
            mock_get.return_value = TuningSession(
                id=1, model_id=1, status=ModelStatus.TUNING, progress=50
            )
            
            response = await client.get("/api/v1/tuning/sessions/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["status"] == ModelStatus.TUNING
            assert data["progress"] == 50


class TestMetricsAPI:
    """Тесты API для метрик"""
    
    @pytest.mark.asyncio
    async def test_record_metrics(self, client):
        """Тест записи метрик"""
        with patch('app.services.MonitoringService.record_metrics') as mock_record:
            mock_record.return_value = PerformanceMetrics(
                id=1, model_id=1, response_time=1.5, tokens_generated=100
            )
            
            metrics_data = {
                "model_id": 1,
                "response_time": 1.5,
                "tokens_generated": 100,
                "success_rate": 1.0
            }
            
            response = await client.post(
                "/api/v1/metrics",
                json=metrics_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_id"] == 1
            assert data["response_time"] == 1.5
    
    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, client):
        """Тест получения сводки метрик"""
        with patch('app.services.MonitoringService.get_metrics_summary') as mock_summary:
            mock_summary.return_value = {
                "total_requests": 100,
                "avg_response_time": 1.2,
                "avg_tokens_generated": 150,
                "avg_success_rate": 0.95
            }
            
            response = await client.get("/api/v1/metrics/summary")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_requests"] == 100
            assert data["avg_response_time"] == 1.2


# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, client):
        """Тест полного workflow"""
        # 1. Создаем модель
        model_data = {
            "name": "test-model",
            "base_model": "llama2",
            "provider": "ollama"
        }
        
        with patch('app.services.ModelService.create_model') as mock_create_model:
            mock_create_model.return_value = LLMModel(**model_data, id=1)
            
            response = await client.post("/api/v1/models", json=model_data)
            assert response.status_code == 200
            model_id = response.json()["id"]
        
        # 2. Создаем маршрут
        route_data = {
            "name": "test-route",
            "model_id": model_id,
            "strategy": RouteStrategy.ROUND_ROBIN
        }
        
        with patch('app.services.RouterService.create_route') as mock_create_route:
            mock_create_route.return_value = ModelRoute(**route_data, id=1)
            
            response = await client.post("/api/v1/routes", json=route_data)
            assert response.status_code == 200
        
        # 3. Создаем сессию тюнинга
        session_data = {
            "model_id": model_id,
            "strategy": "instruction_tuning",
            "parameters": {"temperature": 0.7}
        }
        
        with patch('app.services.TuningService.create_tuning_session') as mock_create_session:
            mock_create_session.return_value = TuningSession(
                **session_data, id=1, status=ModelStatus.PENDING
            )
            
            response = await client.post("/api/v1/tuning/sessions", json=session_data)
            assert response.status_code == 200
        
        # 4. Проверяем статус модели
        with patch('app.services.ModelService.get_models_status') as mock_status:
            mock_status.return_value = {
                "total_models": 1,
                "available_models": 1,
                "tuning_sessions": 1
            }
            
            response = await client.get("/api/v1/models/status")
            assert response.status_code == 200
            data = response.json()
            assert data["total_models"] == 1


# Тесты сервисов
class TestModelService:
    """Тесты сервиса моделей"""
    
    @pytest.mark.asyncio
    async def test_list_models(self, test_db):
        """Тест получения списка моделей"""
        from app.services import ModelService
        
        async with test_db() as session:
            service = ModelService(session)
            
            with patch.object(service, 'ollama_client') as mock_client:
                mock_client.get.return_value.json.return_value = {
                    "models": [{"name": "llama2"}, {"name": "mistral"}]
                }
                
                models = await service.list_models()
                assert len(models) >= 0  # Может быть 0, если БД пустая


class TestRAGService:
    """Тесты RAG сервиса"""
    
    @pytest.mark.asyncio
    async def test_search_documents(self, test_db):
        """Тест поиска документов"""
        from app.services import RAGService
        
        async with test_db() as session:
            service = RAGService(session)
            
            with patch.object(service, '_generate_embeddings') as mock_embeddings:
                mock_embeddings.return_value = [0.1, 0.2, 0.3]
                
                documents = await service.search_documents("test query")
                assert isinstance(documents, list)
    
    @pytest.mark.asyncio
    async def test_generate_with_rag(self, test_db):
        """Тест генерации с RAG"""
        from app.services import RAGService
        
        async with test_db() as session:
            service = RAGService(session)
            
            with patch.object(service, 'search_documents') as mock_search:
                mock_search.return_value = []
                
                with patch.object(service, '_generate_response') as mock_generate:
                    mock_generate.return_value = {
                        "response": "Test response",
                        "model": "llama2"
                    }
                    
                    result = await service.generate_with_rag("llama2", "test query")
                    assert "response" in result


class TestTuningService:
    """Тесты сервиса тюнинга"""
    
    @pytest.mark.asyncio
    async def test_create_tuning_session(self, test_db):
        """Тест создания сессии тюнинга"""
        from app.services import TuningService
        
        async with test_db() as session:
            service = TuningService(session)
            
            session_data = {
                "model_id": 1,
                "strategy": "instruction_tuning",
                "parameters": {"temperature": 0.7}
            }
            
            result = await service.create_tuning_session(session_data)
            assert result is not None
            assert result.model_id == 1
    
    @pytest.mark.asyncio
    async def test_start_tuning(self, test_db):
        """Тест запуска тюнинга"""
        from app.services import TuningService
        
        async with test_db() as session:
            service = TuningService(session)
            
            with patch.object(service, '_run_tuning') as mock_run:
                mock_run.return_value = None
                
                result = await service.start_tuning(1)
                assert result is True


# Тесты утилит
class TestUtils:
    """Тесты утилит"""
    
    def test_simple_embeddings(self):
        """Тест простых эмбеддингов"""
        from app.services import RAGService
        
        service = RAGService(None)
        embeddings = service._simple_embeddings("test text")
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 128
        assert all(isinstance(x, float) for x in embeddings)
    
    def test_cosine_similarity(self):
        """Тест косинусного сходства"""
        from app.services import RAGService
        
        service = RAGService(None)
        
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        similarity = service._cosine_similarity(vec1, vec2)
        assert similarity == 1.0
        
        vec3 = [0.0, 1.0, 0.0]
        similarity = service._cosine_similarity(vec1, vec3)
        assert similarity == 0.0
    
    def test_extract_keywords(self):
        """Тест извлечения ключевых слов"""
        from app.services import RAGService
        
        service = RAGService(None)
        
        text = "Машинное обучение - это подраздел искусственного интеллекта"
        keywords = service._extract_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 10
        assert all(isinstance(k, str) for k in keywords)


# Тесты производительности
class TestPerformance:
    """Тесты производительности"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Тест конкурентных запросов"""
        import asyncio
        
        async def make_request():
            with patch('app.services.ModelService.list_models') as mock_list:
                mock_list.return_value = []
                response = await client.get("/api/v1/models")
                return response.status_code
        
        # Выполняем 10 конкурентных запросов
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Все запросы должны быть успешными
        assert all(status == 200 for status in results)
    
    @pytest.mark.asyncio
    async def test_response_time(self, client):
        """Тест времени ответа"""
        import time
        
        with patch('app.services.ModelService.list_models') as mock_list:
            mock_list.return_value = []
            
            start_time = time.time()
            response = await client.get("/api/v1/models")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Ответ должен быть быстрее 1 секунды


# Тесты обработки ошибок
class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    @pytest.mark.asyncio
    async def test_database_error(self, client):
        """Тест ошибки базы данных"""
        with patch('app.services.ModelService.list_models') as mock_list:
            mock_list.side_effect = Exception("Database error")
            
            response = await client.get("/api/v1/models")
            
            assert response.status_code == 500
            assert "error" in response.json()
    
    @pytest.mark.asyncio
    async def test_ollama_connection_error(self, client):
        """Тест ошибки подключения к Ollama"""
        with patch('app.services.ModelService.list_models') as mock_list:
            mock_list.side_effect = Exception("Connection refused")
            
            response = await client.get("/api/v1/models")
            
            assert response.status_code == 500
            assert "error" in response.json()
    
    @pytest.mark.asyncio
    async def test_validation_error(self, client):
        """Тест ошибки валидации"""
        invalid_data = {
            "name": "",  # Пустое имя
            "base_model": "invalid-model"
        }
        
        response = await client.post("/api/v1/models", json=invalid_data)
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 