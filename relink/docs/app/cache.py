"""
Модуль кэширования с Redis
"""

import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import aioredis
import structlog
from .config import settings, get_redis_url, get_cache_key

logger = structlog.get_logger(__name__)


class RedisCache:
    """Класс для работы с Redis кэшем"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._connection_pool: Optional[aioredis.ConnectionPool] = None
    
    async def connect(self) -> None:
        """Подключение к Redis"""
        try:
            redis_url = get_redis_url()
            self._connection_pool = aioredis.ConnectionPool.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            self.redis = aioredis.Redis(connection_pool=self._connection_pool)
            
            # Проверяем подключение
            await self.redis.ping()
            logger.info("Redis подключен успешно", url=redis_url)
            
        except Exception as e:
            logger.error("Ошибка подключения к Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
        logger.info("Redis отключен")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Получение значения из кэша"""
        if not self.redis:
            return default
        
        try:
            cache_key = get_cache_key("data", key)
            value = await self.redis.get(cache_key)
            
            if value is None:
                return default
            
            # Пытаемся десериализовать JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Если не JSON, возвращаем как есть
                return value
                
        except Exception as e:
            logger.error("Ошибка получения из кэша", key=key, error=str(e))
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """Установка значения в кэш"""
        if not self.redis:
            return False
        
        try:
            cache_key = get_cache_key("data", key)
            ttl = ttl or settings.cache_ttl
            
            if serialize and not isinstance(value, (str, bytes)):
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            else:
                serialized_value = value
            
            await self.redis.setex(cache_key, ttl, serialized_value)
            logger.debug("Значение установлено в кэш", key=key, ttl=ttl)
            return True
            
        except Exception as e:
            logger.error("Ошибка установки в кэш", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        if not self.redis:
            return False
        
        try:
            cache_key = get_cache_key("data", key)
            result = await self.redis.delete(cache_key)
            logger.debug("Значение удалено из кэша", key=key, deleted=bool(result))
            return bool(result)
            
        except Exception as e:
            logger.error("Ошибка удаления из кэша", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        if not self.redis:
            return False
        
        try:
            cache_key = get_cache_key("data", key)
            return bool(await self.redis.exists(cache_key))
        except Exception as e:
            logger.error("Ошибка проверки существования ключа", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Установка TTL для ключа"""
        if not self.redis:
            return False
        
        try:
            cache_key = get_cache_key("data", key)
            return bool(await self.redis.expire(cache_key, ttl))
        except Exception as e:
            logger.error("Ошибка установки TTL", key=key, error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Очистка ключей по паттерну"""
        if not self.redis:
            return 0
        
        try:
            cache_pattern = get_cache_key("data", pattern)
            keys = await self.redis.keys(cache_pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info("Очищены ключи по паттерну", pattern=pattern, deleted=deleted)
                return deleted
            return 0
            
        except Exception as e:
            logger.error("Ошибка очистки по паттерну", pattern=pattern, error=str(e))
            return 0
    
    async def get_stats(self) -> dict:
        """Получение статистики кэша"""
        if not self.redis:
            return {"connected": False}
        
        try:
            info = await self.redis.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error("Ошибка получения статистики Redis", error=str(e))
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