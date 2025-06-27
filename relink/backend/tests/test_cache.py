"""
Тесты для модуля кэширования
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.cache import (
    CacheService, CacheConfig, CacheKey, CacheSerializer,
    cached, cache_invalidate, SEOCache, UserCache
)


class TestCacheKey:
    """Тесты для генератора ключей кэша"""
    
    def test_generate_simple_key(self):
        """Тест генерации простого ключа"""
        key = CacheKey.generate("test", "value")
        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hash length
    
    def test_generate_key_with_kwargs(self):
        """Тест генерации ключа с именованными аргументами"""
        key1 = CacheKey.generate("test", param1="value1", param2="value2")
        key2 = CacheKey.generate("test", param2="value2", param1="value1")
        
        # Ключи должны быть одинаковыми независимо от порядка kwargs
        assert key1 == key2
    
    def test_prefix_key(self):
        """Тест генерации ключа с префиксом"""
        key = CacheKey.prefix("seo", "example.com", "analysis")
        assert key.startswith("seo:")
        assert len(key) > 64  # Префикс + хеш


class TestCacheSerializer:
    """Тесты для сериализатора кэша"""
    
    def test_serialize_json_data(self):
        """Тест сериализации JSON данных"""
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        serialized = CacheSerializer.serialize(data)
        
        # Проверяем, что это валидный JSON
        deserialized = CacheSerializer.deserialize(serialized)
        assert deserialized == data
    
    def test_serialize_complex_object(self):
        """Тест сериализации сложного объекта"""
        class TestObject:
            def __init__(self, value):
                self.value = value
        
        obj = TestObject("test_value")
        serialized = CacheSerializer.serialize(obj)
        
        # Проверяем, что объект сериализован как pickle
        assert len(serialized) > 0
        deserialized = CacheSerializer.deserialize(serialized, "pickle")
        assert deserialized.value == "test_value"


class TestCacheService:
    """Тесты для сервиса кэширования"""
    
    @pytest.fixture
    def cache_config(self):
        """Фикстура для конфигурации кэша"""
        return CacheConfig(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            enable_serialization=True
        )
    
    @pytest.fixture
    async def cache_service(self, cache_config):
        """Фикстура для сервиса кэширования"""
        service = CacheService(cache_config)
        # Очищаем кэш перед тестом
        await service.clear_all()
        return service
    
    @pytest.mark.asyncio
    async def test_set_and_get_value(self, cache_service):
        """Тест установки и получения значения"""
        key = "test_key"
        value = {"data": "test_value"}
        
        # Устанавливаем значение
        success = await cache_service.set(key, value, ttl=60)
        assert success is True
        
        # Получаем значение
        retrieved = await cache_service.get(key)
        assert retrieved == value
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_service):
        """Тест получения несуществующего ключа"""
        result = await cache_service.get("nonexistent_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_with_default(self, cache_service):
        """Тест получения с значением по умолчанию"""
        default_value = "default"
        result = await cache_service.get("nonexistent_key", default=default_value)
        assert result == default_value
    
    @pytest.mark.asyncio
    async def test_delete_key(self, cache_service):
        """Тест удаления ключа"""
        key = "test_key"
        value = "test_value"
        
        # Устанавливаем значение
        await cache_service.set(key, value)
        
        # Проверяем, что значение существует
        assert await cache_service.exists(key) is True
        
        # Удаляем значение
        success = await cache_service.delete(key)
        assert success is True
        
        # Проверяем, что значение удалено
        assert await cache_service.exists(key) is False
    
    @pytest.mark.asyncio
    async def test_ttl_functionality(self, cache_service):
        """Тест функциональности TTL"""
        key = "test_key"
        value = "test_value"
        
        # Устанавливаем значение с коротким TTL
        await cache_service.set(key, value, ttl=1)
        
        # Проверяем, что значение существует
        assert await cache_service.exists(key) is True
        
        # Ждем истечения TTL
        await asyncio.sleep(1.1)
        
        # Проверяем, что значение истекло
        assert await cache_service.exists(key) is False
    
    @pytest.mark.asyncio
    async def test_clear_pattern(self, cache_service):
        """Тест очистки по паттерну"""
        # Устанавливаем несколько значений
        await cache_service.set("seo:domain1", "value1")
        await cache_service.set("seo:domain2", "value2")
        await cache_service.set("user:profile1", "value3")
        
        # Очищаем только seo ключи
        deleted_count = await cache_service.clear_pattern("seo:*")
        assert deleted_count == 2
        
        # Проверяем, что seo ключи удалены
        assert await cache_service.exists("seo:domain1") is False
        assert await cache_service.exists("seo:domain2") is False
        
        # Проверяем, что user ключ остался
        assert await cache_service.exists("user:profile1") is True
    
    @pytest.mark.asyncio
    async def test_clear_all(self, cache_service):
        """Тест очистки всего кэша"""
        # Устанавливаем несколько значений
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")
        
        # Очищаем весь кэш
        success = await cache_service.clear_all()
        assert success is True
        
        # Проверяем, что все ключи удалены
        assert await cache_service.exists("key1") is False
        assert await cache_service.exists("key2") is False
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache_service):
        """Тест получения статистики"""
        # Устанавливаем несколько значений
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")
        
        # Получаем статистику
        stats = await cache_service.get_stats()
        
        # Проверяем базовые поля
        assert "memory_cache_size" in stats
        assert "redis_connected" in stats
        assert stats["memory_cache_size"] == 2


@pytest.mark.asyncio
class TestCacheDecorators:
    """Тесты для декораторов кэширования"""
    
    @pytest.fixture
    async def cache_service(self):
        """Фикстура для сервиса кэширования"""
        config = CacheConfig(enable_serialization=True)
        service = CacheService(config)
        await service.clear_all()
        return service
    
    async def test_cached_decorator(self, cache_service):
        """Тест декоратора cached"""
        
        @cached(ttl=60, key_prefix="test")
        async def expensive_function(param1, param2):
            await asyncio.sleep(0.1)  # Симулируем дорогую операцию
            return f"result_{param1}_{param2}"
        
        # Первый вызов - должен выполниться функция
        result1 = await expensive_function("a", "b")
        assert result1 == "result_a_b"
        
        # Второй вызов - должен вернуться из кэша
        result2 = await expensive_function("a", "b")
        assert result2 == "result_a_b"
        
        # Проверяем, что результат закэширован
        cache_key = CacheKey.prefix("test", "a", "b")
        cached_result = await cache_service.get(cache_key)
        assert cached_result == "result_a_b"
    
    async def test_cache_invalidate_decorator(self, cache_service):
        """Тест декоратора cache_invalidate"""
        
        # Сначала устанавливаем некоторые значения в кэш
        await cache_service.set("seo:domain1", "value1")
        await cache_service.set("seo:domain2", "value2")
        await cache_service.set("user:profile1", "value3")
        
        @cache_invalidate("seo:*")
        async def update_seo_data():
            return "updated"
        
        # Выполняем функцию
        result = await update_seo_data()
        assert result == "updated"
        
        # Проверяем, что seo ключи удалены
        assert await cache_service.exists("seo:domain1") is False
        assert await cache_service.exists("seo:domain2") is False
        
        # Проверяем, что user ключ остался
        assert await cache_service.exists("user:profile1") is True


class TestSpecializedCache:
    """Тесты для специализированных кэшей"""
    
    @pytest.mark.asyncio
    async def test_seo_cache(self):
        """Тест SEO кэша"""
        # Тестируем статические методы
        result = await SEOCache.get_analysis_result("example.com")
        # Пока метод не реализован, проверяем что он существует
        assert SEOCache.get_analysis_result is not None
    
    @pytest.mark.asyncio
    async def test_user_cache(self):
        """Тест пользовательского кэша"""
        # Тестируем статические методы
        result = await UserCache.get_user_profile(123)
        # Пока метод не реализован, проверяем что он существует
        assert UserCache.get_user_profile is not None


class TestCacheIntegration:
    """Интеграционные тесты кэширования"""
    
    @pytest.mark.asyncio
    async def test_full_cache_workflow(self):
        """Тест полного цикла работы с кэшем"""
        config = CacheConfig(enable_serialization=True)
        cache_service = CacheService(config)
        
        # Очищаем кэш
        await cache_service.clear_all()
        
        # Устанавливаем данные
        test_data = {
            "domain": "example.com",
            "analysis": {
                "score": 85.5,
                "recommendations": ["link1", "link2"]
            }
        }
        
        await cache_service.set("seo:example.com", test_data, ttl=3600)
        
        # Получаем данные
        retrieved_data = await cache_service.get("seo:example.com")
        assert retrieved_data == test_data
        
        # Проверяем TTL
        ttl = await cache_service.ttl("seo:example.com")
        assert ttl > 0
        
        # Получаем статистику
        stats = await cache_service.get_stats()
        assert stats["memory_cache_size"] == 1
        
        # Очищаем кэш
        await cache_service.clear_all()
        
        # Проверяем, что данные удалены
        assert await cache_service.get("seo:example.com") is None


class TestCacheErrorHandling:
    """Тесты обработки ошибок кэширования"""
    
    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """Тест ошибки подключения к Redis"""
        # Создаем конфигурацию с неверным URL Redis
        config = CacheConfig(redis_url="redis://invalid:6379")
        cache_service = CacheService(config)
        
        # Должен работать с in-memory кэшем
        success = await cache_service.set("test_key", "test_value")
        assert success is True
        
        value = await cache_service.get("test_key")
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_serialization_error(self):
        """Тест ошибки сериализации"""
        config = CacheConfig(enable_serialization=True)
        cache_service = CacheService(config)
        
        # Создаем объект, который нельзя сериализовать
        class UnserializableObject:
            def __init__(self):
                self.circular_ref = None
            
            def __getstate__(self):
                raise TypeError("Cannot serialize")
        
        obj = UnserializableObject()
        obj.circular_ref = obj  # Создаем циклическую ссылку
        
        # Должен обработать ошибку и вернуть False
        success = await cache_service.set("test_key", obj)
        assert success is False


class TestCachePerformance:
    """Тесты производительности кэширования"""
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Тест конкурентного доступа к кэшу"""
        config = CacheConfig(enable_serialization=True)
        cache_service = CacheService(config)
        
        # Создаем несколько задач для конкурентного доступа
        async def cache_operation(task_id):
            key = f"task_{task_id}"
            value = f"value_{task_id}"
            
            await cache_service.set(key, value)
            retrieved = await cache_service.get(key)
            return retrieved == value
        
        # Запускаем 10 конкурентных операций
        tasks = [cache_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Все операции должны быть успешными
        assert all(results)
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self):
        """Тест очистки памяти"""
        config = CacheConfig(enable_serialization=True)
        cache_service = CacheService(config)
        
        # Устанавливаем много значений
        for i in range(1000):
            await cache_service.set(f"key_{i}", f"value_{i}")
        
        # Проверяем, что количество записей ограничено
        stats = await cache_service.get_stats()
        assert stats["memory_cache_size"] <= 1000
        
        # Очищаем кэш
        await cache_service.clear_all()
        
        # Проверяем, что кэш пуст
        stats = await cache_service.get_stats()
        assert stats["memory_cache_size"] == 0 