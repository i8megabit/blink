"""
Redis кэширование для микросервиса документации
"""

import json
import logging
from typing import Any, Optional, Union
import aioredis
from .config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Асинхронный класс для работы с Redis кэшем"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.prefix = settings.cache_prefix
        self.default_ttl = settings.cache_ttl
    
    async def connect(self) -> None:
        """Подключение к Redis"""
        try:
            self.redis = aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                password=settings.redis_password,
                encoding="utf-8",
                decode_responses=True
            )
            # Проверяем подключение
            await self.redis.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    async def disconnect(self) -> None:
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    def _get_key(self, key: str) -> str:
        """Получение полного ключа с префиксом"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        if not self.redis:
            return None
        
        try:
            full_key = self._get_key(key)
            value = await self.redis.get(full_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting value from cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Установка значения в кэш"""
        if not self.redis:
            return False
        
        try:
            full_key = self._get_key(key)
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, ensure_ascii=False)
            await self.redis.setex(full_key, ttl, serialized_value)
            logger.debug(f"Cached value for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting value in cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        if not self.redis:
            return False
        
        try:
            full_key = self._get_key(key)
            result = await self.redis.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting value from cache: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        if not self.redis:
            return False
        
        try:
            full_key = self._get_key(key)
            return await self.redis.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Error checking key existence: {e}")
            return False
    
    async def clear(self, pattern: str = "*") -> bool:
        """Очистка кэша по паттерну"""
        if not self.redis:
            return False
        
        try:
            full_pattern = self._get_key(pattern)
            keys = await self.redis.keys(full_pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """Получение статистики кэша"""
        if not self.redis:
            return {"connected": False}
        
        try:
            info = await self.redis.info()
            keys = await self.redis.keys(f"{self.prefix}*")
            
            return {
                "connected": True,
                "total_keys": len(keys),
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}


# Глобальный экземпляр кэша
cache = RedisCache()


async def get_cached_or_fetch(
    key: str,
    fetch_func,
    ttl: Optional[int] = None,
    force_refresh: bool = False
) -> Any:
    """
    Получение данных из кэша или их загрузка
    
    Args:
        key: Ключ кэша
        fetch_func: Функция для загрузки данных
        ttl: Время жизни кэша
        force_refresh: Принудительное обновление
    
    Returns:
        Данные из кэша или загруженные данные
    """
    if not force_refresh:
        cached_data = await cache.get(key)
        if cached_data is not None:
            logger.debug("Данные получены из кэша", key=key)
            return cached_data
    
    # Загружаем данные
    try:
        data = await fetch_func()
        await cache.set(key, data, ttl)
        logger.debug("Данные загружены и сохранены в кэш", key=key)
        return data
    except Exception as e:
        logger.error("Ошибка загрузки данных", key=key, error=str(e))
        # Возвращаем кэшированные данные если есть
        return await cache.get(key) 