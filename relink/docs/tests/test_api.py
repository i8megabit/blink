"""
Тесты для API эндпоинтов
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models import VersionInfo, ReadmeInfo, FAQEntry


@pytest.fixture
def client():
    """Фикстура тестового клиента"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Фикстура асинхронного тестового клиента"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Тесты для health check эндпоинта"""
    
    def test_health_check(self, client):
        """Тест health check"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert "cache_status" in data
        assert "uptime" in data


class TestVersionEndpoint:
    """Тесты для version эндпоинта"""
    
    @pytest.mark.asyncio
    async def test_get_version_success(self, async_client):
        """Тест успешного получения версии"""
        with patch('app.main.docs_service.get_version_info') as mock_get:
            mock_get.return_value = VersionInfo(
                version="1.0.0",
                build_date="2024-01-01T12:00:00",
                environment="test"
            )
            
            response = await async_client.get("/api/v1/version")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Version information retrieved successfully"
            assert data["data"]["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_get_version_not_found(self, async_client):
        """Тест получения версии когда файл не найден"""
        with patch('app.main.docs_service.get_version_info') as mock_get:
            mock_get.return_value = None
            
            response = await async_client.get("/api/v1/version")
            
            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert "Version information not found" in data["error"]
    
    @pytest.mark.asyncio
    async def test_get_version_with_force_refresh(self, async_client):
        """Тест получения версии с принудительным обновлением"""
        with patch('app.main.docs_service.get_version_info') as mock_get:
            mock_get.return_value = VersionInfo(
                version="1.0.0",
                build_date="2024-01-01T12:00:00",
                environment="test"
            )
            
            response = await async_client.get("/api/v1/version?force_refresh=true")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(force_refresh=True)


class TestReadmeEndpoint:
    """Тесты для README эндпоинта"""
    
    @pytest.mark.asyncio
    async def test_get_readme_success(self, async_client):
        """Тест успешного получения README"""
        with patch('app.main.docs_service.get_readme_info') as mock_get:
            mock_get.return_value = ReadmeInfo(
                title="Test README",
                description="Test description",
                sections=[],
                content="<h1>Test</h1>"
            )
            
            response = await async_client.get("/api/v1/docs/readme")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "README retrieved successfully"
            assert data["data"]["title"] == "Test README"
    
    @pytest.mark.asyncio
    async def test_get_readme_not_found(self, async_client):
        """Тест получения README когда файл не найден"""
        with patch('app.main.docs_service.get_readme_info') as mock_get:
            mock_get.return_value = None
            
            response = await async_client.get("/api/v1/docs/readme")
            
            assert response.status_code == 404
            data = response.json()
            assert data["success"] is False
            assert "README not found" in data["error"]


class TestFAQEndpoint:
    """Тесты для FAQ эндпоинта"""
    
    @pytest.mark.asyncio
    async def test_get_faq_success(self, async_client):
        """Тест успешного получения FAQ"""
        with patch('app.main.docs_service.get_faq_entries') as mock_get:
            mock_get.return_value = [
                FAQEntry(
                    question="Test question?",
                    answer="Test answer",
                    category="Test",
                    tags=["test"]
                )
            ]
            
            response = await async_client.get("/api/v1/docs/faq")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "FAQ retrieved successfully"
            assert len(data["data"]) == 1
            assert data["data"][0]["question"] == "Test question?"


class TestAboutEndpoint:
    """Тесты для About эндпоинта"""
    
    @pytest.mark.asyncio
    async def test_get_about_success(self, async_client):
        """Тест успешного получения информации о проекте"""
        with patch('app.main.docs_service.get_about_info') as mock_get:
            mock_get.return_value = {
                "name": "Test Project",
                "description": "Test description",
                "version": "1.0.0",
                "author": "Test Author",
                "license": "MIT",
                "features": ["Feature 1", "Feature 2"]
            }
            
            response = await async_client.get("/api/v1/docs/about")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "About information retrieved successfully"
            assert data["data"]["name"] == "Test Project"


class TestHowItWorksEndpoint:
    """Тесты для How It Works эндпоинта"""
    
    @pytest.mark.asyncio
    async def test_get_how_it_works_success(self, async_client):
        """Тест успешного получения информации о работе системы"""
        with patch('app.main.docs_service.get_how_it_works_info') as mock_get:
            mock_get.return_value = {
                "title": "How It Works",
                "overview": "System overview",
                "steps": [],
                "technologies": ["Python", "React"]
            }
            
            response = await async_client.get("/api/v1/docs/how-it-works")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "How it works information retrieved successfully"
            assert data["data"]["title"] == "How It Works"


class TestCacheEndpoints:
    """Тесты для кэш эндпоинтов"""
    
    @pytest.mark.asyncio
    async def test_get_cache_stats_success(self, async_client):
        """Тест успешного получения статистики кэша"""
        with patch('app.main.cache.get_stats') as mock_get:
            mock_get.return_value = {
                "connected": True,
                "total_keys": 10,
                "memory_used": "1MB",
                "connected_clients": 1,
                "uptime": 3600
            }
            
            response = await async_client.get("/api/v1/cache/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Cache statistics retrieved successfully"
            assert data["data"]["connected"] is True
            assert data["data"]["total_keys"] == 10
    
    @pytest.mark.asyncio
    async def test_clear_cache_success(self, async_client):
        """Тест успешной очистки кэша"""
        with patch('app.main.cache.clear') as mock_clear:
            mock_clear.return_value = True
            
            response = await async_client.delete("/api/v1/cache/clear")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Cache cleared successfully"
    
    @pytest.mark.asyncio
    async def test_clear_cache_failure(self, async_client):
        """Тест неудачной очистки кэша"""
        with patch('app.main.cache.clear') as mock_clear:
            mock_clear.return_value = False
            
            response = await async_client.delete("/api/v1/cache/clear")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "Failed to clear cache" in data["error"]


class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    @pytest.mark.asyncio
    async def test_internal_server_error(self, async_client):
        """Тест внутренней ошибки сервера"""
        with patch('app.main.docs_service.get_version_info') as mock_get:
            mock_get.side_effect = Exception("Test error")
            
            response = await async_client.get("/api/v1/version")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "Internal server error"
            assert data["error_code"] == "INTERNAL_ERROR"
    
    def test_404_not_found(self, client):
        """Тест 404 ошибки"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Not Found" in data["error"]


class TestCORS:
    """Тесты CORS"""
    
    def test_cors_headers(self, client):
        """Тест CORS заголовков"""
        response = client.options("/api/v1/health")
        
        # Проверяем, что CORS заголовки присутствуют
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers 