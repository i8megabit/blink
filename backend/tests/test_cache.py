"""
Тесты для модуля кэширования reLink
"""

import pytest
import asyncio
import time
import pickle
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.cache import (
    CacheSerializer,
    MemoryCache,
    RedisCache,
    CacheManager,
    cache_result,
    invalidate_cache,
    SEOCache,
    UserCache
)


class TestCacheSerializer:
    """Тесты для CacheSerializer"""
    
    def test_serialize_deserialize_simple_data(self):
        """Тест сериализации/десериализации простых данных"""
        test_data = {"key": "value", "number": 42, "boolean": True}
        
        serialized = CacheSerializer.serialize(test_data)
        deserialized = CacheSerializer.deserialize(serialized)
        
        assert deserialized == test_data
        assert isinstance(serialized, bytes)
    
    def test_serialize_deserialize_complex_data(self):
        """Тест сериализации/десериализации сложных данных"""
        test_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
            "set": {1, 2, 3},
            "datetime": datetime.now()
        }
        
        serialized = CacheSerializer.serialize(test_data)
        deserialized = CacheSerializer.deserialize(serialized)
        
        assert deserialized["list"] == test_data["list"]
        assert deserialized["dict"] == test_data["dict"]
        assert deserialized["tuple"] == test_data["tuple"]
        assert deserialized["set"] == test_data["set"]
    
    def test_serialize_error_handling(self):
        """Тест обработки ошибок сериализации"""
        # Создаем объект, который нельзя сериализовать
        class UnserializableObject:
            def __init__(self):
                self.self_ref = self
        
        obj = UnserializableObject()
        
        with pytest.raises(Exception):
            CacheSerializer.serialize(obj)
    
    def test_deserialize_error_handling(self):
        """Тест обработки ошибок десериализации"""
        invalid_data = b"invalid pickle data"
        
        with pytest.raises(Exception):
            CacheSerializer.deserialize(invalid_data)


class TestMemoryCache:
    """Тесты для MemoryCache"""
    
    @pytest.fixture
    def cache(self):
        """Кэш для тестирования"""
        return MemoryCache(max_size=5)
    
    @pytest.mark.asyncio
    async def test_set_get_basic(self, cache):
        """Тест базовой установки и получения"""
        await cache.set("test_key", "test_value", ttl=3600)
        result = await cache.get("test_key")
        
        assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_set_get_with_ttl(self, cache):
        """Тест TTL функциональности"""
        await cache.set("test_key", "test_value", ttl=1)
        
        # Значение должно быть доступно сразу
        result = await cache.get("test_key")
        assert result == "test_value"
        
        # Ждем истечения TTL
        await asyncio.sleep(1.1)
        
        # Значение должно быть удалено
        result = await cache.get("test_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Тест удаления ключа"""
        await cache.set("test_key", "test_value")
        await cache.delete("test_key")
        
        result = await cache.get("test_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Тест очистки кэша"""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_exists(self, cache):
        """Тест проверки существования ключа"""
        await cache.set("test_key", "test_value")
        
        assert await cache.exists("test_key") is True
        assert await cache.exists("nonexistent_key") is False
    
    @pytest.mark.asyncio
    async def test_ttl(self, cache):
        """Тест получения TTL"""
        await cache.set("test_key", "test_value", ttl=3600)
        
        ttl = await cache.ttl("test_key")
        assert ttl > 0
        assert ttl <= 3600
    
    @pytest.mark.asyncio
    async def test_max_size_eviction(self, cache):
        """Тест вытеснения при превышении размера"""
        # Заполняем кэш до максимума
        for i in range(5):
            await cache.set(f"key{i}", f"value{i}")
        
        # Добавляем еще один ключ
        await cache.set("new_key", "new_value")
        
        # Первый ключ должен быть вытеснен
        assert await cache.get("key0") is None
        assert await cache.get("new_key") == "new_value"
    
    @pytest.mark.asyncio
    async def test_keys_pattern(self, cache):
        """Тест получения ключей по паттерну"""
        await cache.set("user:1", "value1")
        await cache.set("user:2", "value2")
        await cache.set("post:1", "value3")
        
        user_keys = await cache.keys("user:*")
        assert len(user_keys) == 2
        assert "user:1" in user_keys
        assert "user:2" in user_keys
        
        all_keys = await cache.keys("*")
        assert len(all_keys) == 3


class TestRedisCache:
    """Тесты для RedisCache"""
    
    @pytest.fixture
    def redis_cache(self):
        """Redis кэш для тестирования"""
        return RedisCache("redis://localhost:6379")
    
    @pytest.mark.asyncio
    async def test_redis_initialization(self, redis_cache):
        """Тест инициализации Redis кэша"""
        assert redis_cache.redis_url == "redis://localhost:6379"
        assert redis_cache._client is None
    
    @pytest.mark.asyncio
    async def test_get_client(self, redis_cache):
        """Тест получения Redis клиента"""
        with patch('app.cache.redis') as mock_redis:
            mock_client = Mock()
            mock_redis.from_url.return_value = mock_client
            
            client = await redis_cache._get_client()
            
            assert client == mock_client
            mock_redis.from_url.assert_called_once_with(
                "redis://localhost:6379", 
                decode_responses=False
            )
    
    @pytest.mark.asyncio
    async def test_set_get_with_mock(self, redis_cache):
        """Тест установки и получения с моком Redis"""
        with patch('app.cache.redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            
            test_data = {"key": "value"}
            serialized_data = CacheSerializer.serialize(test_data)
            
            # Тестируем set
            await redis_cache.set("test_key", test_data, ttl=3600)
            
            mock_client.setex.assert_called_once_with(
                "redis:test_key", 3600, serialized_data
            )
            
            # Тестируем get
            mock_client.get.return_value = serialized_data
            result = await redis_cache.get("test_key")
            
            assert result == test_data
            mock_client.get.assert_called_once_with("redis:test_key")
    
    @pytest.mark.asyncio
    async def test_delete_with_mock(self, redis_cache):
        """Тест удаления с моком Redis"""
        with patch('app.cache.redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.delete.return_value = 1
            
            result = await redis_cache.delete("test_key")
            
            assert result is True
            mock_client.delete.assert_called_once_with("redis:test_key")
    
    @pytest.mark.asyncio
    async def test_close(self, redis_cache):
        """Тест закрытия соединения"""
        with patch('app.cache.redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            
            # Получаем клиента
            await redis_cache._get_client()
            
            # Закрываем соединение
            await redis_cache.close()
            
            mock_client.close.assert_called_once()
            assert redis_cache._client is None


class TestCacheManager:
    """Тесты для CacheManager"""
    
    @pytest.fixture
    def cache_manager(self):
        """Менеджер кэша для тестирования"""
        return CacheManager()
    
    @pytest.mark.asyncio
    async def test_get_from_memory_cache(self, cache_manager):
        """Тест получения из memory кэша"""
        await cache_manager.memory_cache.set("test_key", "test_value")
        
        result = await cache_manager.get("test_key", use_redis=False)
        assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_set_to_memory_cache(self, cache_manager):
        """Тест установки в memory кэш"""
        result = await cache_manager.set("test_key", "test_value", use_redis=False)
        assert result is True
        
        cached_value = await cache_manager.memory_cache.get("test_key")
        assert cached_value == "test_value"
    
    @pytest.mark.asyncio
    async def test_delete_from_memory_cache(self, cache_manager):
        """Тест удаления из memory кэша"""
        await cache_manager.memory_cache.set("test_key", "test_value")
        
        result = await cache_manager.delete("test_key", use_redis=False)
        assert result is True
        
        cached_value = await cache_manager.memory_cache.get("test_key")
        assert cached_value is None
    
    @pytest.mark.asyncio
    async def test_exists_in_memory_cache(self, cache_manager):
        """Тест проверки существования в memory кэше"""
        await cache_manager.memory_cache.set("test_key", "test_value")
        
        assert await cache_manager.exists("test_key", use_redis=False) is True
        assert await cache_manager.exists("nonexistent_key", use_redis=False) is False
    
    @pytest.mark.asyncio
    async def test_ttl_from_memory_cache(self, cache_manager):
        """Тест получения TTL из memory кэша"""
        await cache_manager.memory_cache.set("test_key", "test_value", ttl=3600)
        
        ttl = await cache_manager.ttl("test_key", use_redis=False)
        assert ttl > 0
        assert ttl <= 3600
    
    @pytest.mark.asyncio
    async def test_keys_from_memory_cache(self, cache_manager):
        """Тест получения ключей из memory кэша"""
        await cache_manager.memory_cache.set("user:1", "value1")
        await cache_manager.memory_cache.set("user:2", "value2")
        
        keys = await cache_manager.keys("user:*", use_redis=False)
        assert len(keys) == 2
        assert "user:1" in keys
        assert "user:2" in keys


class TestCacheDecorators:
    """Тесты для декораторов кэширования"""
    
    @pytest.mark.asyncio
    async def test_cache_result_decorator(self):
        """Тест декоратора cache_result"""
        call_count = 0
        
        @cache_result(ttl=3600, key_prefix="test")
        async def test_function(param1, param2):
            nonlocal call_count
            call_count += 1
            return f"result_{param1}_{param2}"
        
        # Первый вызов - функция выполняется
        result1 = await test_function("a", "b")
        assert result1 == "result_a_b"
        assert call_count == 1
        
        # Второй вызов с теми же параметрами - результат из кэша
        result2 = await test_function("a", "b")
        assert result2 == "result_a_b"
        assert call_count == 1  # Функция не вызывалась повторно
        
        # Вызов с другими параметрами - функция выполняется снова
        result3 = await test_function("c", "d")
        assert result3 == "result_c_d"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_invalidate_cache_decorator(self):
        """Тест декоратора invalidate_cache"""
        # Сначала кэшируем некоторые данные
        cache_manager = CacheManager()
        await cache_manager.set("test:key1", "value1")
        await cache_manager.set("test:key2", "value2")
        
        @invalidate_cache("test:*")
        async def test_function():
            return "result"
        
        # Выполняем функцию
        result = await test_function()
        assert result == "result"
        
        # Проверяем, что кэш очищен
        assert await cache_manager.get("test:key1") is None
        assert await cache_manager.get("test:key2") is None


class TestSEOCache:
    """Тесты для SEOCache"""
    
    @pytest.fixture
    def seo_cache(self):
        """SEO кэш для тестирования"""
        return SEOCache(ttl=3600)
    
    @pytest.mark.asyncio
    async def test_get_set_analysis(self, seo_cache):
        """Тест получения и установки SEO анализа"""
        analysis_data = {"score": 85, "recommendations": ["test"]}
        
        # Устанавливаем анализ
        result = await seo_cache.set_analysis("example.com", analysis_data)
        assert result is True
        
        # Получаем анализ
        cached_analysis = await seo_cache.get_analysis("example.com")
        assert cached_analysis == analysis_data
    
    @pytest.mark.asyncio
    async def test_get_set_recommendations(self, seo_cache):
        """Тест получения и установки рекомендаций"""
        recommendations = [{"type": "link", "text": "test"}]
        
        # Устанавливаем рекомендации
        result = await seo_cache.set_recommendations("example.com", recommendations)
        assert result is True
        
        # Получаем рекомендации
        cached_recommendations = await seo_cache.get_recommendations("example.com")
        assert cached_recommendations == recommendations
    
    @pytest.mark.asyncio
    async def test_invalidate_domain(self, seo_cache):
        """Тест инвалидации данных домена"""
        # Устанавливаем данные
        await seo_cache.set_analysis("example.com", {"score": 85})
        await seo_cache.set_recommendations("example.com", [{"type": "link"}])
        
        # Инвалидируем домен
        result = await seo_cache.invalidate_domain("example.com")
        assert result is True
        
        # Проверяем, что данные удалены
        assert await seo_cache.get_analysis("example.com") is None
        assert await seo_cache.get_recommendations("example.com") is None


class TestUserCache:
    """Тесты для UserCache"""
    
    @pytest.fixture
    def user_cache(self):
        """User кэш для тестирования"""
        return UserCache(ttl=1800)
    
    @pytest.mark.asyncio
    async def test_get_set_user(self, user_cache):
        """Тест получения и установки пользователя"""
        user_data = {"id": 1, "email": "test@example.com", "username": "testuser"}
        
        # Устанавливаем пользователя
        result = await user_cache.set_user(1, user_data)
        assert result is True
        
        # Получаем пользователя
        cached_user = await user_cache.get_user(1)
        assert cached_user == user_data
    
    @pytest.mark.asyncio
    async def test_invalidate_user(self, user_cache):
        """Тест инвалидации пользователя"""
        user_data = {"id": 1, "email": "test@example.com"}
        
        # Устанавливаем пользователя
        await user_cache.set_user(1, user_data)
        
        # Инвалидируем пользователя
        result = await user_cache.invalidate_user(1)
        assert result is True
        
        # Проверяем, что данные удалены
        assert await user_cache.get_user(1) is None


class TestCacheIntegration:
    """Интеграционные тесты кэширования"""
    
    @pytest.mark.asyncio
    async def test_memory_redis_fallback(self):
        """Тест fallback между memory и Redis кэшем"""
        cache_manager = CacheManager()
        
        # Устанавливаем значение только в memory
        await cache_manager.set("test_key", "test_value", use_redis=False)
        
        # Получаем значение (должно быть из memory)
        result = await cache_manager.get("test_key")
        assert result == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_manager_close(self):
        """Тест закрытия менеджера кэша"""
        cache_manager = CacheManager()
        
        # Если Redis доступен, закрываем соединение
        if cache_manager.redis_cache:
            await cache_manager.close()
            assert cache_manager.redis_cache._client is None


class TestCachePerformance:
    """Тесты производительности кэширования"""
    
    @pytest.mark.asyncio
    async def test_memory_cache_performance(self):
        """Тест производительности memory кэша"""
        cache = MemoryCache(max_size=1000)
        
        start_time = time.time()
        
        # Устанавливаем много значений
        for i in range(100):
            await cache.set(f"key{i}", f"value{i}")
        
        # Получаем значения
        for i in range(100):
            await cache.get(f"key{i}")
        
        duration = time.time() - start_time
        
        # Операции должны быть быстрыми
        assert duration < 1.0
    
    @pytest.mark.asyncio
    async def test_cache_decorator_performance(self):
        """Тест производительности декоратора кэширования"""
        call_count = 0
        
        @cache_result(ttl=3600)
        async def expensive_function(param):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Имитируем дорогую операцию
            return f"result_{param}"
        
        start_time = time.time()
        
        # Первый вызов
        result1 = await expensive_function("test")
        
        # Второй вызов (должен быть из кэша)
        result2 = await expensive_function("test")
        
        duration = time.time() - start_time
        
        assert result1 == result2
        assert call_count == 1  # Функция вызвалась только один раз
        assert duration < 0.2  # Второй вызов должен быть быстрым


class TestCacheErrorHandling:
    """Тесты обработки ошибок в кэшировании"""
    
    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """Тест обработки ошибки подключения к Redis"""
        cache_manager = CacheManager()
        
        # Если Redis недоступен, операции должны работать с memory кэшем
        result = await cache_manager.set("test_key", "test_value")
        assert result is True
        
        cached_value = await cache_manager.get("test_key")
        assert cached_value == "test_value"
    
    @pytest.mark.asyncio
    async def test_serialization_error_handling(self):
        """Тест обработки ошибок сериализации"""
        # Создаем объект, который нельзя сериализовать
        class UnserializableObject:
            def __init__(self):
                self.self_ref = self
        
        obj = UnserializableObject()
        
        with pytest.raises(Exception):
            CacheSerializer.serialize(obj)
    
    @pytest.mark.asyncio
    async def test_cache_manager_edge_cases(self):
        """Тест граничных случаев менеджера кэша"""
        cache_manager = CacheManager()
        
        # Тест с пустым ключом
        result = await cache_manager.set("", "value")
        assert result is True
        
        cached_value = await cache_manager.get("")
        assert cached_value == "value"
        
        # Тест с None значением
        result = await cache_manager.set("none_key", None)
        assert result is True
        
        cached_value = await cache_manager.get("none_key")
        assert cached_value is None 