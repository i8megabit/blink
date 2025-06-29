import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Тест проверки здоровья"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "frontend"

def test_endpoints():
    """Тест получения эндпоинтов"""
    response = client.get("/api/v1/endpoints")
    assert response.status_code == 200
    assert response.json()["service"] == "frontend"

def test_metrics():
    """Тест получения метрик"""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert response.json()["service"] == "frontend"
