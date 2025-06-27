"""
Модуль кэширования для Blink
Поддержка Redis и in-memory кэша с TTL, инвалидацией и мониторингом
"""

import json
import hashlib
import time
from typing import Any, Optional, Union, Dict, List
from functools import wraps
import asyncio
from datetime import datetime, timedelta

import redis.asyncio as redis
from pydantic import BaseModel

from .monitoring import monitoring, monitor_function

class CacheConfig(BaseModel):
    """Конфигурация кэша"""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 час
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    enable_compression: bool = True
    enable_serialization: bool = True

class CacheKey:
    """Генератор ключей кэша"""
    
    @staticmethod
    def generate(*args, **kwargs) -> str:
        """Генерация ключа кэша из аргументов"""
        # Создаем строку из аргументов
        key_parts = [str(arg) for arg in args]
        
        # Добавляем именованные аргументы
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
        
        # Создаем хеш
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    @staticmethod
    def prefix(prefix: str, *args, **kwargs) -> str:
        """Генерация ключа с префиксом"""
        key = CacheKey.generate(*args, **kwargs)
        return f"{prefix}:{key}"

class CacheSerializer:
    """Сериализатор для кэша"""
    
    @staticmethod
    def serialize(data: Any) -> str:
        """Сериализация данных в JSON"""
        if isinstance(data, (dict, list, str, int, float, bool, type(None))):
            return json.dumps(data, ensure_ascii=False, default=str)
        else:
            # Для сложных объектов используем pickle
            import pickle
            return pickle.dumps(data).hex()
    
    @staticmethod
    def deserialize(data: str, data_type: str = "json") -> Any:
        """Десериализация данных"""
        if data_type == "json":
            return json.loads(data)
        else:
            # Для pickle данных
            import pickle
            return pickle.loads(bytes.fromhex(data))

class CacheService:
    """Сервис кэширования"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self._setup_redis()
    
    async def _setup_redis(self):
        """Настройка подключения к Redis"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Проверяем подключение
            await self.redis_client.ping()
            monitoring.logger.info("Redis connection established")
            
        except Exception as e:
            monitoring.logger.warning(f"Redis connection failed: {e}. Using memory cache only.")
            self.redis_client = None
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Получение значения из кэша"""
        try:
            # Сначала проверяем Redis
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    if self.config.enable_serialization:
                        return CacheSerializer.deserialize(value)
                    return value
            
            # Затем проверяем память
            if key in self.memory_cache:
                cache_entry = self.memory_cache[key]
                if cache_entry['expires_at'] > time.time():
                    return cache_entry['value']
                else:
                    # Удаляем истекший кэш
                    del self.memory_cache[key]
            
            return default
            
        except Exception as e:
            monitoring.log_error(e, {'operation': 'cache_get', 'key': key})
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Установка значения в кэш"""
        try:
            ttl = ttl or self.config.default_ttl
            
            # Сохраняем в Redis
            if self.redis_client:
                if self.config.enable_serialization:
                    serialized_value = CacheSerializer.serialize(value)
                else:
                    serialized_value = str(value)
                
                await self.redis_client.setex(key, ttl, serialized_value)
            
            # Сохраняем в память
            self.memory_cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
            
            # Ограничиваем размер памяти
            self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            monitoring.log_error(e, {'operation': 'cache_set', 'key': key})
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        try:
            # Удаляем из Redis
            if self.redis_client:
                await self.redis_client.delete(key)
            
            # Удаляем из памяти
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            return True
            
        except Exception as e:
            monitoring.log_error(e, {'operation': 'cache_delete', 'key': key})
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        try:
            # Проверяем Redis
            if self.redis_client:
                return await self.redis_client.exists(key) > 0
            
            # Проверяем память
            if key in self.memory_cache:
                return self.memory_cache[key]['expires_at'] > time.time()
            
            return False
            
        except Exception as e:
            monitoring.log_error(e, {'operation': 'cache_exists', 'key': key})
            return False
    
    async def ttl(self, key: str) -> int:
        """Получение времени жизни ключа"""
        try:
            # Проверяем Redis
            if self.redis_client:
                return await self.redis_client.ttl(key)
            
            # Проверяем память
            if key in self.memory_cache:
                expires_at = self.memory_cache[key]['expires_at']
                return max(0, int(expires_at - time.time()))
            
            return -1
            
        except Exception as e:
            monitoring.log_error(e, {'operation': 'cache_ttl', 'key': key})
            return -1
    
    async def clear_pattern(self, pattern: str) -> int:
        """Очистка ключей по паттерну"""
        try:
            deleted_count = 0
            
            # Очищаем Redis
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
            
            # Очищаем память
            memory_keys = [k for k in self.memory_cache.keys() if pattern in k]
            for key in memory_keys:
                del self.memory_cache[key]
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            monitoring.log_error(e, {'operation': 'cache_clear_pattern', 'pattern': pattern})
            return 0
    
    async def clear_all(self) -> bool:
        """Очистка всего кэша"""
        try:
            # Очищаем Redis
            if self.redis_client:
                await self.redis_client.flushdb()
            
            # Очищаем память
            self.memory_cache.clear()
            
            return True
            
        except Exception as e:
            monitoring.log_error(e, {'operation': 'cache_clear_all'})
            return False
    
    def _cleanup_memory_cache(self):
        """Очистка устаревших записей в памяти"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry['expires_at'] <= current_time
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Если память превышает лимит, удаляем старые записи
        if len(self.memory_cache) > 1000:  # Максимум 1000 записей
            sorted_keys = sorted(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]['expires_at']
            )
            
            # Удаляем 20% самых старых записей
            keys_to_remove = sorted_keys[:len(sorted_keys) // 5]
            for key in keys_to_remove:
                del self.memory_cache[key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        try:
            stats = {
                'memory_cache_size': len(self.memory_cache),
                'redis_connected': self.redis_client is not None
            }
            
            if self.redis_client:
                info = await self.redis_client.info()
                stats.update({
                    'redis_used_memory': info.get('used_memory', 0),
                    'redis_connected_clients': info.get('connected_clients', 0),
                    'redis_keyspace_hits': info.get('keyspace_hits', 0),
                    'redis_keyspace_misses': info.get('keyspace_misses', 0)
                })
            
            return stats
            
        except Exception as e:
            monitoring.log_error(e, {'operation': 'cache_stats'})
            return {'error': str(e)}

# Глобальный экземпляр сервиса кэширования
cache_service = CacheService(CacheConfig())

# Декораторы для кэширования
def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """Декоратор для кэширования результатов функций"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = CacheKey.prefix(key_prefix or func.__name__, *args, **kwargs)
            
            # Пытаемся получить из кэша
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию
            result = await func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def cache_invalidate(pattern: str):
    """Декоратор для инвалидации кэша после выполнения функции"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Выполняем функцию
            result = await func(*args, **kwargs)
            
            # Инвалидируем кэш
            await cache_service.clear_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator

# Специализированные методы кэширования
class SEOCache:
    """Специализированный кэш для SEO данных"""
    
    @staticmethod
    @cached(ttl=3600, key_prefix="seo_analysis")
    async def get_analysis_result(domain: str) -> Dict[str, Any]:
        """Кэширование результатов SEO анализа"""
        # Здесь будет логика получения результатов анализа
        pass
    
    @staticmethod
    @cache_invalidate("seo_analysis:*")
    async def invalidate_analysis_cache(domain: str):
        """Инвалидация кэша анализа"""
        pass
    
    @staticmethod
    @cached(ttl=1800, key_prefix="domain_info")
    async def get_domain_info(domain: str) -> Dict[str, Any]:
        """Кэширование информации о домене"""
        # Здесь будет логика получения информации о домене
        pass

class UserCache:
    """Специализированный кэш для пользовательских данных"""
    
    @staticmethod
    @cached(ttl=300, key_prefix="user_profile")
    async def get_user_profile(user_id: int) -> Dict[str, Any]:
        """Кэширование профиля пользователя"""
        # Здесь будет логика получения профиля пользователя
        pass
    
    @staticmethod
    @cache_invalidate("user_profile:*")
    async def invalidate_user_cache(user_id: int):
        """Инвалидация кэша пользователя"""
        pass

# Middleware для кэширования HTTP ответов
async def cache_middleware(request, call_next):
    """Middleware для кэширования HTTP ответов"""
    # Проверяем, можно ли кэшировать запрос
    if request.method != "GET":
        return await call_next(request)
    
    # Генерируем ключ кэша
    cache_key = CacheKey.prefix("http", request.url.path, dict(request.query_params))
    
    # Пытаемся получить из кэша
    cached_response = await cache_service.get(cache_key)
    if cached_response:
        return cached_response
    
    # Выполняем запрос
    response = await call_next(request)
    
    # Кэшируем только успешные ответы
    if response.status_code == 200:
        await cache_service.set(cache_key, response, ttl=300)  # 5 минут
    
    return response

# Endpoint для управления кэшем
async def cache_stats():
    """Endpoint для получения статистики кэша"""
    return await cache_service.get_stats()

async def cache_clear():
    """Endpoint для очистки кэша"""
    success = await cache_service.clear_all()
    return {"success": success} 