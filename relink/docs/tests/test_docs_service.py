"""
Тесты для сервиса документации
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from app.services import DocumentationService
from app.models import VersionInfo, ReadmeInfo, FAQEntry


@pytest.fixture
def docs_service():
    """Фикстура сервиса документации"""
    return DocumentationService()


@pytest.fixture
def mock_cache():
    """Мок кэша"""
    with patch('app.services.cache') as mock:
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        yield mock


class TestDocumentationService:
    """Тесты для DocumentationService"""
    
    @pytest.mark.asyncio
    async def test_get_version_info_from_cache(self, docs_service, mock_cache):
        """Тест получения версии из кэша"""
        # Подготавливаем данные
        cached_data = {
            "version": "1.0.0",
            "build_date": "2024-01-01T12:00:00",
            "environment": "test"
        }
        mock_cache.get.return_value = cached_data
        
        # Выполняем тест
        result = await docs_service.get_version_info(force_refresh=False)
        
        # Проверяем результат
        assert result is not None
        assert result.version == "1.0.0"
        assert result.build_date == "2024-01-01T12:00:00"
        assert result.environment == "test"
        
        # Проверяем, что кэш был вызван
        mock_cache.get.assert_called_once_with("version_info")
    
    @pytest.mark.asyncio
    async def test_get_version_info_from_file(self, docs_service, mock_cache):
        """Тест получения версии из файла"""
        # Подготавливаем данные
        mock_cache.get.return_value = None  # Кэш пустой
        
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.read_text') as mock_read:
            
            mock_exists.return_value = True
            mock_read.return_value = "1.0.0"
            
            # Выполняем тест
            result = await docs_service.get_version_info(force_refresh=False)
            
            # Проверяем результат
            assert result is not None
            assert result.version == "1.0.0"
            
            # Проверяем, что данные были сохранены в кэш
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_version_info_file_not_found(self, docs_service, mock_cache):
        """Тест получения версии когда файл не найден"""
        # Подготавливаем данные
        mock_cache.get.return_value = None
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            # Выполняем тест
            result = await docs_service.get_version_info(force_refresh=False)
            
            # Проверяем результат
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_readme_info_from_cache(self, docs_service, mock_cache):
        """Тест получения README из кэша"""
        # Подготавливаем данные
        cached_data = {
            "title": "Test README",
            "description": "Test description",
            "sections": [],
            "content": "<h1>Test</h1>"
        }
        mock_cache.get.return_value = cached_data
        
        # Выполняем тест
        result = await docs_service.get_readme_info(force_refresh=False)
        
        # Проверяем результат
        assert result is not None
        assert result.title == "Test README"
        assert result.description == "Test description"
        
        # Проверяем, что кэш был вызван
        mock_cache.get.assert_called_once_with("readme_info")
    
    @pytest.mark.asyncio
    async def test_get_readme_info_from_file(self, docs_service, mock_cache):
        """Тест получения README из файла"""
        # Подготавливаем данные
        mock_cache.get.return_value = None
        
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.read_text') as mock_read:
            
            mock_exists.return_value = True
            mock_read.return_value = "# Test README\n\nTest description"
            
            # Выполняем тест
            result = await docs_service.get_readme_info(force_refresh=False)
            
            # Проверяем результат
            assert result is not None
            assert result.title == "Test README"
            assert result.description == "Test description"
            
            # Проверяем, что данные были сохранены в кэш
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_faq_entries_from_cache(self, docs_service, mock_cache):
        """Тест получения FAQ из кэша"""
        # Подготавливаем данные
        cached_data = [
            {
                "question": "Test question?",
                "answer": "Test answer",
                "category": "Test",
                "tags": ["test"]
            }
        ]
        mock_cache.get.return_value = cached_data
        
        # Выполняем тест
        result = await docs_service.get_faq_entries(force_refresh=False)
        
        # Проверяем результат
        assert len(result) == 1
        assert result[0].question == "Test question?"
        assert result[0].answer == "Test answer"
        
        # Проверяем, что кэш был вызван
        mock_cache.get.assert_called_once_with("faq_entries")
    
    @pytest.mark.asyncio
    async def test_get_faq_entries_created(self, docs_service, mock_cache):
        """Тест создания FAQ"""
        # Подготавливаем данные
        mock_cache.get.return_value = None
        
        # Выполняем тест
        result = await docs_service.get_faq_entries(force_refresh=False)
        
        # Проверяем результат
        assert len(result) > 0
        assert all(isinstance(entry, FAQEntry) for entry in result)
        
        # Проверяем, что данные были сохранены в кэш
        mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self, docs_service, mock_cache):
        """Тест принудительного обновления кэша"""
        # Подготавливаем данные
        cached_data = {"version": "1.0.0"}
        mock_cache.get.return_value = cached_data
        
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.read_text') as mock_read:
            
            mock_exists.return_value = True
            mock_read.return_value = "2.0.0"
            
            # Выполняем тест
            result = await docs_service.get_version_info(force_refresh=True)
            
            # Проверяем, что кэш не использовался
            mock_cache.get.assert_not_called()
            
            # Проверяем результат
            assert result is not None
            assert result.version == "2.0.0"
    
    def test_parse_markdown_sections(self, docs_service):
        """Тест парсинга секций Markdown"""
        # Подготавливаем данные
        content = """
# Main Title

## Section 1
Content for section 1

### Subsection 1.1
Subcontent

## Section 2
Content for section 2
"""
        
        # Выполняем тест
        sections = docs_service._parse_markdown_sections(content)
        
        # Проверяем результат
        assert len(sections) == 2
        assert sections[0]["title"] == "Section 1"
        assert sections[1]["title"] == "Section 2"
        assert len(sections[0]["content"]) > 0
    
    def test_parse_roadmap_phases(self, docs_service):
        """Тест парсинга фаз roadmap"""
        # Подготавливаем данные
        content = """
# Roadmap

## Phase 1: Foundation
Content

## Phase 2: Features
Content
"""
        
        # Выполняем тест
        phases = docs_service._parse_roadmap_phases(content)
        
        # Проверяем результат
        assert len(phases) == 2
        assert phases[0]["phase"] == 1
        assert phases[0]["title"] == "Foundation"
        assert phases[1]["phase"] == 2
        assert phases[1]["title"] == "Features"
    
    def test_parse_roadmap_features(self, docs_service):
        """Тест парсинга функций roadmap"""
        # Подготавливаем данные
        content = """
# Features

- [ ] Feature 1
- [x] Feature 2
- [ ] Feature 3
"""
        
        # Выполняем тест
        features = docs_service._parse_roadmap_features(content)
        
        # Проверяем результат
        assert len(features) == 3
        assert features[0]["feature"] == "Feature 1"
        assert features[0]["status"] == "planned"
        assert features[1]["feature"] == "Feature 2"
        assert features[1]["status"] == "completed" 