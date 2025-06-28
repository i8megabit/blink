"""
Модуль кэширования для reLink
Поддержка Redis и in-memory кэша с TTL и инвалидацией
"""

import asyncio
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging

import redis.asyncio as redis
from .config import settings

logger = logging.getLogger(__name__)


class CacheSerializer:
    """Сериализатор для кэша"""
    
    @staticmethod
    def serialize(data: Any) -> bytes:
        """Сериализация данных"""
        try:
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    @staticmethod
    def deserialize(data: bytes) -> Any:
        """Десериализация данных"""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise


class MemoryCache:
    """In-memory кэш с TTL"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: List[str] = []
    
    def _get_cache_key(self, key: str) -> str:
        """Генерация ключа кэша"""
        return f"memory:{key}"
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """Проверка истечения срока действия"""
        if 'expires_at' not in item:
            return False
        return datetime.utcnow() > item['expires_at']
    
    def _cleanup_expired(self):
        """Очистка истекших элементов"""
        expired_keys = [
            key for key, item in self._cache.items()
            if self._is_expired(item)
        ]
        for key in expired_keys:
            self._remove_item(key)
    
    def _remove_item(self, key: str):
        """Удаление элемента из кэша"""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    def _update_access_order(self, key: str):
        """Обновление порядка доступа (LRU)"""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _evict_if_needed(self):
        """Вытеснение элементов при превышении размера"""
        while len(self._cache) >= self.max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            if oldest_key in self._cache:
                del self._cache[oldest_key]
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        cache_key = self._get_cache_key(key)
        
        # Очистка истекших элементов
        self._cleanup_expired()
        
        if cache_key in self._cache:
            item = self._cache[cache_key]
            if not self._is_expired(item):
                self._update_access_order(cache_key)
                return item['value']
            else:
                self._remove_item(cache_key)
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Установка значения в кэш"""
        cache_key = self._get_cache_key(key)
        
        # Очистка истекших элементов
        self._cleanup_expired()
        
        # Вытеснение при необходимости
        self._evict_if_needed()
        
        # Установка значения
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[cache_key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.utcnow()
        }
        self._update_access_order(cache_key)
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        cache_key = self._get_cache_key(key)
        if cache_key in self._cache:
            self._remove_item(cache_key)
            return True
        return False
    
    async def clear(self) -> bool:
        """Очистка всего кэша"""
        self._cache.clear()
        self._access_order.clear()
        return True
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        cache_key = self._get_cache_key(key)
        self._cleanup_expired()
        return cache_key in self._cache and not self._is_expired(self._cache[cache_key])
    
    async def ttl(self, key: str) -> int:
        """Получение оставшегося времени жизни"""
        cache_key = self._get_cache_key(key)
        if cache_key in self._cache:
            item = self._cache[cache_key]
            if not self._is_expired(item):
                remaining = (item['expires_at'] - datetime.utcnow()).total_seconds()
                return max(0, int(remaining))
        return -1
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Получение ключей по паттерну"""
        self._cleanup_expired()
        # Простая реализация паттерна
        if pattern == "*":
            return [key.replace("memory:", "") for key in self._cache.keys()]
        return [key.replace("memory:", "") for key in self._cache.keys() if pattern in key]


class RedisCache:
    """Redis кэш"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Получение Redis клиента"""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=False)
        return self._client
    
    def _get_cache_key(self, key: str) -> str:
        """Генерация ключа кэша"""
        return f"redis:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        try:
            client = await self._get_client()
            cache_key = self._get_cache_key(key)
            data = await client.get(cache_key)
            
            if data is not None:
                return CacheSerializer.deserialize(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Установка значения в кэш"""
        try:
            client = await self._get_client()
            cache_key = self._get_cache_key(key)
            data = CacheSerializer.serialize(value)
            
            await client.setex(cache_key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        try:
            client = await self._get_client()
            cache_key = self._get_cache_key(key)
            result = await client.delete(cache_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Очистка всего кэша"""
        try:
            client = await self._get_client()
            # Удаляем только ключи нашего приложения
            pattern = self._get_cache_key("*")
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        try:
            client = await self._get_client()
            cache_key = self._get_cache_key(key)
            return await client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Получение оставшегося времени жизни"""
        try:
            client = await self._get_client()
            cache_key = self._get_cache_key(key)
            return await client.ttl(cache_key)
        except Exception as e:
            logger.error(f"Redis ttl error: {e}")
            return -1
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Получение ключей по паттерну"""
        try:
            client = await self._get_client()
            cache_pattern = self._get_cache_key(pattern)
            keys = await client.keys(cache_pattern)
            return [key.decode().replace("redis:", "") for key in keys]
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            return []
    
    async def close(self):
        """Закрытие соединения с Redis"""
        if self._client:
            await self._client.close()
            self._client = None


class RAGCache:
    """RAG-специфичный кэш для векторных операций"""
    
    def __init__(self, ttl: int = 7200):  # 2 часа для эмбеддингов
        self.ttl = ttl
        self.embedding_cache = {}
        self.similarity_cache = {}
        self.context_cache = {}
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Получение эмбеддинга из кэша"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"embedding:{text_hash}"
        
        # Проверяем in-memory кэш
        if cache_key in self.embedding_cache:
            item = self.embedding_cache[cache_key]
            if not self._is_expired(item):
                return item['value']
            else:
                del self.embedding_cache[cache_key]
        
        return None
    
    async def set_embedding(self, text: str, embedding: List[float]) -> bool:
        """Сохранение эмбеддинга в кэш"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"embedding:{text_hash}"
        
        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl)
        self.embedding_cache[cache_key] = {
            'value': embedding,
            'expires_at': expires_at,
            'created_at': datetime.utcnow()
        }
        
        return True
    
    async def get_similarity_results(self, query: str, top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Получение результатов поиска похожести"""
        query_hash = hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()
        cache_key = f"similarity:{query_hash}"
        
        if cache_key in self.similarity_cache:
            item = self.similarity_cache[cache_key]
            if not self._is_expired(item):
                return item['value']
            else:
                del self.similarity_cache[cache_key]
        
        return None
    
    async def set_similarity_results(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> bool:
        """Сохранение результатов поиска похожести"""
        query_hash = hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()
        cache_key = f"similarity:{query_hash}"
        
        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl // 2)  # 1 час для результатов
        self.similarity_cache[cache_key] = {
            'value': results,
            'expires_at': expires_at,
            'created_at': datetime.utcnow()
        }
        
        return True
    
    async def get_context(self, prompt: str, service_type: str) -> Optional[str]:
        """Получение RAG контекста из кэша"""
        prompt_hash = hashlib.md5(f"{prompt}:{service_type}".encode()).hexdigest()
        cache_key = f"context:{prompt_hash}"
        
        if cache_key in self.context_cache:
            item = self.context_cache[cache_key]
            if not self._is_expired(item):
                return item['value']
            else:
                del self.context_cache[cache_key]
        
        return None
    
    async def set_context(self, prompt: str, context: str, service_type: str) -> bool:
        """Сохранение RAG контекста в кэш"""
        prompt_hash = hashlib.md5(f"{prompt}:{service_type}".encode()).hexdigest()
        cache_key = f"context:{prompt_hash}"
        
        expires_at = datetime.utcnow() + timedelta(seconds=self.ttl // 4)  # 30 минут для контекста
        self.context_cache[cache_key] = {
            'value': context,
            'expires_at': expires_at,
            'created_at': datetime.utcnow()
        }
        
        return True
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """Проверка истечения срока действия"""
        if 'expires_at' not in item:
            return False
        return datetime.utcnow() > item['expires_at']
    
    async def clear_expired(self):
        """Очистка истекших элементов"""
        current_time = datetime.utcnow()
        
        # Очистка эмбеддингов
        expired_keys = [
            key for key, item in self.embedding_cache.items()
            if self._is_expired(item)
        ]
        for key in expired_keys:
            del self.embedding_cache[key]
        
        # Очистка результатов поиска
        expired_keys = [
            key for key, item in self.similarity_cache.items()
            if self._is_expired(item)
        ]
        for key in expired_keys:
            del self.similarity_cache[key]
        
        # Очистка контекстов
        expired_keys = [
            key for key, item in self.context_cache.items()
            if self._is_expired(item)
        ]
        for key in expired_keys:
            del self.context_cache[key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики RAG кэша"""
        await self.clear_expired()
        
        return {
            "embedding_cache_size": len(self.embedding_cache),
            "similarity_cache_size": len(self.similarity_cache),
            "context_cache_size": len(self.context_cache),
            "total_items": len(self.embedding_cache) + len(self.similarity_cache) + len(self.context_cache)
        }


class CacheManager:
    """Универсальный менеджер кэша с поддержкой RAG"""
    
    def __init__(self):
        self.memory_cache = MemoryCache()
        self.redis_cache = RedisCache(settings.REDIS_URL) if settings.REDIS_URL else None
        self.rag_cache = RAGCache()  # Новый RAG-специфичный кэш
        
    async def get(self, key: str, use_redis: bool = True) -> Optional[Any]:
        """Получение значения из кэша"""
        # Сначала проверяем memory cache
        if settings.cache.enable_memory:
            value = await self.memory_cache.get(key)
            if value is not None:
                return value
        
        # Затем проверяем Redis
        if use_redis and self.redis_cache and settings.cache.enable_redis:
            value = await self.redis_cache.get(key)
            if value is not None and settings.cache.enable_memory:
                # Кэшируем в memory для быстрого доступа
                await self.memory_cache.set(key, value, settings.cache.default_ttl)
            return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None, use_redis: bool = True) -> bool:
        """Установка значения в кэш"""
        if ttl is None:
            ttl = settings.cache.default_ttl
        
        success = True
        
        # Устанавливаем в memory cache
        if settings.cache.enable_memory:
            success &= await self.memory_cache.set(key, value, ttl)
        
        # Устанавливаем в Redis
        if use_redis and self.redis_cache and settings.cache.enable_redis:
            success &= await self.redis_cache.set(key, value, ttl)
        
        return success
    
    async def delete(self, key: str, use_redis: bool = True) -> bool:
        """Удаление значения из кэша"""
        success = True
        
        # Удаляем из memory cache
        if settings.cache.enable_memory:
            success &= await self.memory_cache.delete(key)
        
        # Удаляем из Redis
        if use_redis and self.redis_cache and settings.cache.enable_redis:
            success &= await self.redis_cache.delete(key)
        
        return success
    
    async def clear(self, use_redis: bool = True) -> bool:
        """Очистка всего кэша"""
        success = True
        
        # Очищаем memory cache
        if settings.cache.enable_memory:
            success &= await self.memory_cache.clear()
        
        # Очищаем Redis
        if use_redis and self.redis_cache and settings.cache.enable_redis:
            success &= await self.redis_cache.clear()
        
        return success
    
    async def exists(self, key: str, use_redis: bool = True) -> bool:
        """Проверка существования ключа"""
        # Проверяем memory cache
        if settings.cache.enable_memory:
            if await self.memory_cache.exists(key):
                return True
        
        # Проверяем Redis
        if use_redis and self.redis_cache and settings.cache.enable_redis:
            return await self.redis_cache.exists(key)
        
        return False
    
    async def ttl(self, key: str, use_redis: bool = True) -> int:
        """Получение оставшегося времени жизни"""
        # Проверяем memory cache
        if settings.cache.enable_memory:
            ttl = await self.memory_cache.ttl(key)
            if ttl > 0:
                return ttl
        
        # Проверяем Redis
        if use_redis and self.redis_cache and settings.cache.enable_redis:
            return await self.redis_cache.ttl(key)
        
        return -1
    
    async def keys(self, pattern: str = "*", use_redis: bool = True) -> List[str]:
        """Получение ключей по паттерну"""
        keys = set()
        
        # Получаем ключи из memory cache
        if settings.cache.enable_memory:
            memory_keys = await self.memory_cache.keys(pattern)
            keys.update(memory_keys)
        
        # Получаем ключи из Redis
        if use_redis and self.redis_cache and settings.cache.enable_redis:
            redis_keys = await self.redis_cache.keys(pattern)
            keys.update(redis_keys)
        
        return list(keys)
    
    async def close(self):
        """Закрытие соединений"""
        if self.redis_cache:
            await self.redis_cache.close()
    
    async def get_rag_embedding(self, text: str) -> Optional[List[float]]:
        """Получение эмбеддинга из RAG кэша"""
        return await self.rag_cache.get_embedding(text)
    
    async def set_rag_embedding(self, text: str, embedding: List[float]) -> bool:
        """Сохранение эмбеддинга в RAG кэш"""
        return await self.rag_cache.set_embedding(text, embedding)
    
    async def get_rag_similarity(self, query: str, top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Получение результатов поиска похожести из RAG кэша"""
        return await self.rag_cache.get_similarity_results(query, top_k)
    
    async def set_rag_similarity(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> bool:
        """Сохранение результатов поиска похожести в RAG кэш"""
        return await self.rag_cache.set_similarity_results(query, results, top_k)
    
    async def get_rag_context(self, prompt: str, service_type: str) -> Optional[str]:
        """Получение RAG контекста из кэша"""
        return await self.rag_cache.get_context(prompt, service_type)
    
    async def set_rag_context(self, prompt: str, context: str, service_type: str) -> bool:
        """Сохранение RAG контекста в кэш"""
        return await self.rag_cache.set_context(prompt, context, service_type)
    
    async def get_rag_stats(self) -> Dict[str, Any]:
        """Получение статистики RAG кэша"""
        return await self.rag_cache.get_stats()


# Глобальный экземпляр менеджера кэша
cache_manager = CacheManager()


# Декораторы для кэширования
def cache_result(ttl: int = None, key_prefix: str = "", use_redis: bool = True):
    """Декоратор для кэширования результатов функций"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Генерация ключа кэша
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Попытка получить из кэша
            cached_result = await cache_manager.get(cache_key, use_redis)
            if cached_result is not None:
                return cached_result
            
            # Выполнение функции
            result = await func(*args, **kwargs)
            
            # Сохранение в кэш
            await cache_manager.set(cache_key, result, ttl, use_redis)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str = "*", use_redis: bool = True):
    """Декоратор для инвалидации кэша"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Выполнение функции
            result = await func(*args, **kwargs)
            
            # Инвалидация кэша
            keys = await cache_manager.keys(pattern, use_redis)
            for key in keys:
                await cache_manager.delete(key, use_redis)
            
            return result
        return wrapper
    return decorator


# Специализированные кэши
class SEOCache:
    """Специализированный кэш для SEO данных"""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.prefix = "seo"
    
    async def get_analysis(self, domain: str) -> Optional[Dict[str, Any]]:
        """Получение SEO анализа из кэша"""
        key = f"{self.prefix}:analysis:{domain}"
        return await cache_manager.get(key)
    
    async def set_analysis(self, domain: str, analysis: Dict[str, Any]) -> bool:
        """Сохранение SEO анализа в кэш"""
        key = f"{self.prefix}:analysis:{domain}"
        return await cache_manager.set(key, analysis, self.ttl)
    
    async def get_recommendations(self, domain: str) -> Optional[List[Dict[str, Any]]]:
        """Получение рекомендаций из кэша"""
        key = f"{self.prefix}:recommendations:{domain}"
        return await cache_manager.get(key)
    
    async def set_recommendations(self, domain: str, recommendations: List[Dict[str, Any]]) -> bool:
        """Сохранение рекомендаций в кэш"""
        key = f"{self.prefix}:recommendations:{domain}"
        return await cache_manager.set(key, recommendations, self.ttl)
    
    async def invalidate_domain(self, domain: str) -> bool:
        """Инвалидация всех данных домена"""
        pattern = f"{self.prefix}:*:{domain}"
        keys = await cache_manager.keys(pattern)
        success = True
        for key in keys:
            success &= await cache_manager.delete(key)
        return success


class UserCache:
    """Специализированный кэш для пользователей"""
    
    def __init__(self, ttl: int = 1800):
        self.ttl = ttl
        self.prefix = "user"
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя из кэша"""
        key = f"{self.prefix}:{user_id}"
        return await cache_manager.get(key)
    
    async def set_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Сохранение пользователя в кэш"""
        key = f"{self.prefix}:{user_id}"
        return await cache_manager.set(key, user_data, self.ttl)
    
    async def invalidate_user(self, user_id: int) -> bool:
        """Инвалидация данных пользователя"""
        key = f"{self.prefix}:{user_id}"
        return await cache_manager.delete(key)


# Экспорт для обратной совместимости
RelinkCache = {
    "cache_manager": cache_manager,
    "cache_result": cache_result,
    "invalidate_cache": invalidate_cache,
    "SEOCache": SEOCache,
    "UserCache": UserCache,
} 