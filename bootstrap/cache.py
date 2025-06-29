"""
💾 Кеширование с Redis для всех микросервисов
"""

from typing import Optional, Any
import json
import aioredis
import structlog

from .config import get_settings

logger = structlog.get_logger()

# Глобальный экземпляр Redis
_redis_client: Optional[aioredis.Redis] = None

async def get_cache() -> aioredis.Redis:
    """Получение Redis клиента"""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        logger.info("Redis client created", url=settings.REDIS_URL)
    
    return _redis_client

async def get_cached_data(key: str) -> Optional[Any]:
    """Получение данных из кеша"""
    try:
        redis_client = await get_cache()
        data = await redis_client.get(key)
        
        if data:
            return json.loads(data)
        
        return None
        
    except Exception as e:
        logger.error("Cache get error", key=key, error=str(e))
        return None

async def set_cached_data(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Сохранение данных в кеш"""
    try:
        redis_client = await get_cache()
        settings = get_settings()
        
        data = json.dumps(value)
        ttl = ttl or settings.CACHE_TTL
        
        await redis_client.setex(key, ttl, data)
        
        logger.debug("Data cached", key=key, ttl=ttl)
        return True
        
    except Exception as e:
        logger.error("Cache set error", key=key, error=str(e))
        return False

async def delete_cached_data(key: str) -> bool:
    """Удаление данных из кеша"""
    try:
        redis_client = await get_cache()
        await redis_client.delete(key)
        
        logger.debug("Data uncached", key=key)
        return True
        
    except Exception as e:
        logger.error("Cache delete error", key=key, error=str(e))
        return False

async def clear_cache() -> bool:
    """Очистка всего кеша"""
    try:
        redis_client = await get_cache()
        await redis_client.flushdb()
        
        logger.info("Cache cleared")
        return True
        
    except Exception as e:
        logger.error("Cache clear error", error=str(e))
        return False

async def close_cache():
    """Закрытие соединения с Redis"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        
        logger.info("Redis connection closed") 