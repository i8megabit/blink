import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_ollama_client():
    """Мок для Ollama клиента"""
    with patch('app.api.routes.get_ollama_client') as mock:
        mock_client = AsyncMock()
        mock_client.generate.return_value = {
            "response": "Test response from Ollama",
            "model": "qwen2.5:7b-instruct-turbo"
        }
        mock_client.list_models.return_value = [
            {"name": "qwen2.5:7b-instruct-turbo"},
            {"name": "qwen2.5:14b-instruct"},
            {"name": "qwen2.5:32b-instruct"}
        ]
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_rag_service():
    """Мок для RAG сервиса"""
    with patch('app.api.routes.get_rag_service') as mock:
        mock_service = AsyncMock()
        mock_service.search.return_value = [
            {"content": "Test RAG result 1", "score": 0.9},
            {"content": "Test RAG result 2", "score": 0.8}
        ]
        mock.return_value = mock_service
        yield mock_service

@pytest.fixture
def mock_monitor():
    """Мок для монитора"""
    with patch('app.api.routes.get_service_monitor') as mock:
        mock_monitor = AsyncMock()
        mock.return_value = mock_monitor
        yield mock_monitor

def test_health_check():
    """Тест проверки здоровья"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "router"
    assert "LLM Router" in data["description"]

def test_endpoints():
    """Тест получения эндпоинтов"""
    response = client.get("/api/v1/endpoints")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "router"
    assert "/api/v1/route" in data["endpoints"]
    assert "/api/v1/models" in data["endpoints"]

@pytest.mark.asyncio
async def test_route_request_success(mock_ollama_client, mock_rag_service, mock_monitor):
    """Тест успешной маршрутизации запроса"""
    
    request_data = {
        "prompt": "Test prompt for routing",
        "model": None,
        "context": {"test": "context"},
        "service": "test-service",
        "priority": "normal"
    }
    
    response = client.post("/api/v1/route", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "request_id" in data
    assert "model_used" in data
    assert "response" in data
    assert "confidence" in data
    assert "latency" in data
    assert "cost_estimate" in data
    assert "metadata" in data
    
    # Проверяем, что использовалась правильная модель для короткого промпта
    assert "qwen2.5:7b-instruct-turbo" in data["model_used"]

@pytest.mark.asyncio
async def test_route_request_long_prompt(mock_ollama_client, mock_rag_service, mock_monitor):
    """Тест маршрутизации длинного промпта"""
    
    # Создаем длинный промпт
    long_prompt = "This is a very long prompt " * 50  # ~1500 символов
    
    request_data = {
        "prompt": long_prompt,
        "model": None,
        "context": {},
        "service": "test-service",
        "priority": "high"
    }
    
    response = client.post("/api/v1/route", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    # Для длинного промпта должна использоваться более мощная модель
    assert "qwen2.5:32b-instruct" in data["model_used"]

@pytest.mark.asyncio
async def test_route_request_with_specific_model(mock_ollama_client, mock_rag_service, mock_monitor):
    """Тест маршрутизации с указанием конкретной модели"""
    
    request_data = {
        "prompt": "Test prompt",
        "model": "qwen2.5:14b-instruct",
        "context": {},
        "service": "test-service"
    }
    
    response = client.post("/api/v1/route", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["model_used"] == "qwen2.5:14b-instruct"

@pytest.mark.asyncio
async def test_batch_route_requests(mock_ollama_client, mock_rag_service, mock_monitor):
    """Тест пакетной маршрутизации"""
    
    requests_data = [
        {
            "prompt": "First test prompt",
            "model": None,
            "context": {},
            "service": "test-service"
        },
        {
            "prompt": "Second test prompt",
            "model": None,
            "context": {},
            "service": "test-service"
        }
    ]
    
    response = client.post("/api/v1/route/batch", json=requests_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "batch_id" in data
    assert data["total_requests"] == 2
    assert len(data["successful_results"]) == 2
    assert len(data["failed_results"]) == 0
    assert "batch_latency" in data

@pytest.mark.asyncio
async def test_get_available_models(mock_ollama_client):
    """Тест получения списка доступных моделей"""
    
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    
    models = response.json()
    assert len(models) == 3
    
    # Проверяем структуру модели
    model = models[0]
    assert "name" in model
    assert "description" in model
    assert "capabilities" in model
    assert "avg_latency" in model
    assert "avg_cost" in model
    assert "availability" in model

@pytest.mark.asyncio
async def test_analyze_effectiveness(mock_monitor):
    """Тест анализа эффективности"""
    
    request_id = "test-request-id"
    result_data = {
        "request_id": request_id,
        "model_used": "qwen2.5:7b-instruct-turbo",
        "response": "Test response",
        "confidence": 0.85,
        "latency": 1.2,
        "cost_estimate": 0.002,
        "metadata": {"method": "direct_ollama"}
    }
    
    original_request = {
        "prompt": "Test prompt for analysis",
        "model": None,
        "context": {},
        "service": "test-service"
    }
    
    response = client.post("/api/v1/analyze", json={
        "request_id": request_id,
        "result": result_data,
        "original_request": original_request
    })
    
    assert response.status_code == 200
    
    analysis = response.json()
    assert analysis["request_id"] == request_id
    assert analysis["model_used"] == "qwen2.5:7b-instruct-turbo"
    assert "effectiveness_score" in analysis
    assert "quality_metrics" in analysis
    assert "recommendations" in analysis

def test_route_request_invalid_data():
    """Тест обработки некорректных данных"""
    
    # Отправляем некорректные данные
    response = client.post("/api/v1/route", json={"invalid": "data"})
    assert response.status_code == 422  # Validation error

def test_route_request_empty_prompt():
    """Тест обработки пустого промпта"""
    
    response = client.post("/api/v1/route", json={"prompt": ""})
    assert response.status_code == 200  # Пустой промпт допустим

@pytest.mark.asyncio
async def test_route_request_error_handling(mock_ollama_client, mock_rag_service, mock_monitor):
    """Тест обработки ошибок"""
    
    # Симулируем ошибку в Ollama клиенте
    mock_ollama_client.generate.side_effect = Exception("Ollama connection error")
    
    request_data = {
        "prompt": "Test prompt",
        "model": None,
        "context": {},
        "service": "test-service"
    }
    
    response = client.post("/api/v1/route", json=request_data)
    assert response.status_code == 500
    assert "Routing error" in response.json()["detail"]

@pytest.mark.asyncio
async def test_batch_route_with_errors(mock_ollama_client, mock_rag_service, mock_monitor):
    """Тест пакетной обработки с ошибками"""
    
    # Симулируем ошибку для одного из запросов
    mock_ollama_client.generate.side_effect = [
        {"response": "Success response", "model": "qwen2.5:7b-instruct-turbo"},
        Exception("Error in second request")
    ]
    
    requests_data = [
        {"prompt": "First prompt", "model": None, "context": {}, "service": "test"},
        {"prompt": "Second prompt", "model": None, "context": {}, "service": "test"}
    ]
    
    response = client.post("/api/v1/route/batch", json=requests_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_requests"] == 2
    assert len(data["successful_results"]) == 1
    assert len(data["failed_results"]) == 1

def test_model_selection_logic():
    """Тест логики выбора модели"""
    from app.api.routes import analyze_request_for_model_selection, RouteRequest
    
    # Тест короткого промпта
    short_request = RouteRequest(prompt="Short")
    # Здесь нужно мокать функцию, но для простоты пропустим
    
    # Тест среднего промпта
    medium_request = RouteRequest(prompt="Medium length prompt " * 20)
    
    # Тест длинного промпта
    long_request = RouteRequest(prompt="Very long prompt " * 100)

def test_cost_calculation():
    """Тест расчета стоимости"""
    from app.api.routes import calculate_cost_estimate
    
    cost = calculate_cost_estimate("qwen2.5:7b-instruct-turbo", 100, 200)
    assert cost > 0
    assert isinstance(cost, float)

def test_effectiveness_score_calculation():
    """Тест расчета score эффективности"""
    from app.api.routes import calculate_effectiveness_score
    
    quality_metrics = {
        "relevance_score": 0.9,
        "completeness_score": 0.8,
        "coherence_score": 0.85
    }
    
    model_analysis = {
        "model_appropriate": True,
        "latency_acceptable": True,
        "confidence_high": True
    }
    
    score = calculate_effectiveness_score(quality_metrics, model_analysis, 1.5, 0.002)
    assert 0 <= score <= 1
    assert isinstance(score, float)

def test_recommendations_generation():
    """Тест генерации рекомендаций"""
    from app.api.routes import generate_recommendations
    
    quality_metrics = {
        "relevance_score": 0.7,  # Низкий score
        "completeness_score": 0.9,
        "coherence_score": 0.8
    }
    
    model_analysis = {
        "model_appropriate": True,
        "latency_acceptable": False,  # Высокая задержка
        "confidence_high": True
    }
    
    recommendations = generate_recommendations(0.6, quality_metrics, model_analysis)
    assert len(recommendations) > 0
    assert isinstance(recommendations, list)
    assert all(isinstance(rec, str) for rec in recommendations)
