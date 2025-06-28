"""
🚀 КЭШИРОВАНИЕ БЕНЧМАРК МИКРОСЕРВИСА
Высокопроизводительное кэширование с Redis для ускорения бенчмарков
"""

import json
import pickle
import asyncio
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import aioredis
import structlog
from .config import settings

logger = structlog.get_logger(__name__)


class BenchmarkCache:
    """Высокопроизводительный кэш для бенчмарк результатов."""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.prefix = settings.cache_prefix
        self.default_ttl = settings.cache_ttl
        self._connection_lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Подключение к Redis."""
        if self.redis is None:
            async with self._connection_lock:
                if self.redis is None:
                    try:
                        self.redis = aioredis.from_url(
                            settings.redis_url,
                            encoding="utf-8",
                            decode_responses=False,
                            max_connections=settings.redis_pool_size
                        )
                        await self.redis.ping()
                        logger.info("Redis подключен успешно")
                    except Exception as e:
                        logger.error(f"Ошибка подключения к Redis: {e}")
                        raise
    
    async def disconnect(self) -> None:
        """Отключение от Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Redis отключен")
    
    def _make_key(self, key: str) -> str:
        """Создание ключа с префиксом."""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Получение значения из кэша."""
        if not settings.cache_enabled:
            return default
        
        try:
            await self.connect()
            cache_key = self._make_key(key)
            value = await self.redis.get(cache_key)
            
            if value is None:
                return default
            
            # Пробуем десериализовать как JSON, затем как pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    return pickle.loads(value)
                except pickle.UnpicklingError:
                    return value.decode('utf-8')
                    
        except Exception as e:
            logger.error(f"Ошибка получения из кэша: {e}")
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """Установка значения в кэш."""
        if not settings.cache_enabled:
            return False
        
        try:
            await self.connect()
            cache_key = self._make_key(key)
            
            if serialize:
                # Пробуем сериализовать как JSON, если не получается - как pickle
                try:
                    serialized_value = json.dumps(value, default=str).encode('utf-8')
                except (TypeError, ValueError):
                    serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value).encode('utf-8')
            
            ttl = ttl or self.default_ttl
            await self.redis.setex(cache_key, ttl, serialized_value)
            logger.debug(f"Значение сохранено в кэш: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша."""
        if not settings.cache_enabled:
            return False
        
        try:
            await self.connect()
            cache_key = self._make_key(key)
            result = await self.redis.delete(cache_key)
            return result > 0
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа."""
        if not settings.cache_enabled:
            return False
        
        try:
            await self.connect()
            cache_key = self._make_key(key)
            return await self.redis.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Ошибка проверки существования ключа: {e}")
            return False
    
    async def clear(self, pattern: str = "*") -> int:
        """Очистка кэша по паттерну."""
        if not settings.cache_enabled:
            return 0
        
        try:
            await self.connect()
            cache_pattern = self._make_key(pattern)
            keys = await self.redis.keys(cache_pattern)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Удалено {deleted} ключей из кэша")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша."""
        if not settings.cache_enabled:
            return {"enabled": False}
        
        try:
            await self.connect()
            info = await self.redis.info()
            
            # Подсчет ключей с префиксом бенчмарка
            benchmark_keys = await self.redis.keys(f"{self.prefix}*")
            
            return {
                "enabled": True,
                "total_keys": len(benchmark_keys),
                "memory_usage": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {e}")
            return {"enabled": False, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Расчет hit rate кэша."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    async def get_benchmark_result(self, benchmark_id: str) -> Optional[Dict]:
        """Получение результата бенчмарка из кэша."""
        return await self.get(f"result:{benchmark_id}")
    
    async def set_benchmark_result(
        self, 
        benchmark_id: str, 
        result: Dict, 
        ttl: Optional[int] = None
    ) -> bool:
        """Сохранение результата бенчмарка в кэш."""
        return await self.set(f"result:{benchmark_id}", result, ttl)
    
    async def get_model_performance(self, model_name: str) -> Optional[Dict]:
        """Получение производительности модели из кэша."""
        return await self.get(f"performance:{model_name}")
    
    async def set_model_performance(
        self, 
        model_name: str, 
        performance: Dict, 
        ttl: Optional[int] = None
    ) -> bool:
        """Сохранение производительности модели в кэш."""
        return await self.set(f"performance:{model_name}", performance, ttl)
    
    async def get_benchmark_history(self, limit: int = 100) -> List[Dict]:
        """Получение истории бенчмарков из кэша."""
        try:
            await self.connect()
            pattern = self._make_key("result:*")
            keys = await self.redis.keys(pattern)
            
            # Сортируем по времени создания (новые первыми)
            keys.sort(reverse=True)
            keys = keys[:limit]
            
            if not keys:
                return []
            
            # Получаем значения
            pipeline = self.redis.pipeline()
            for key in keys:
                pipeline.get(key)
            
            values = await pipeline.execute()
            results = []
            
            for value in values:
                if value:
                    try:
                        result = json.loads(value.decode('utf-8'))
                        results.append(result)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка получения истории бенчмарков: {e}")
            return []
    
    async def invalidate_model_cache(self, model_name: str) -> bool:
        """Инвалидация кэша для конкретной модели."""
        patterns = [
            f"performance:{model_name}",
            f"result:*:{model_name}",
            f"benchmark:*:{model_name}"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.clear(pattern)
            total_deleted += deleted
        
        logger.info(f"Инвалидирован кэш для модели {model_name}: {total_deleted} ключей")
        return total_deleted > 0
    
    async def get_cache_size(self) -> Dict[str, int]:
        """Получение размера кэша по категориям."""
        try:
            await self.connect()
            
            categories = {
                "results": len(await self.redis.keys(self._make_key("result:*"))),
                "performance": len(await self.redis.keys(self._make_key("performance:*"))),
                "benchmarks": len(await self.redis.keys(self._make_key("benchmark:*"))),
                "models": len(await self.redis.keys(self._make_key("model:*"))),
                "total": len(await self.redis.keys(self._make_key("*")))
            }
            
            return categories
            
        except Exception as e:
            logger.error(f"Ошибка получения размера кэша: {e}")
            return {}


# Глобальный экземпляр кэша
cache_manager = BenchmarkCache()


async def get_cache() -> BenchmarkCache:
    """Получение экземпляра кэша."""
    return cache_manager


async def cache_benchmark_result(benchmark_id: str, result: Dict, ttl: Optional[int] = None) -> bool:
    """Кэширование результата бенчмарка."""
    return await cache_manager.set_benchmark_result(benchmark_id, result, ttl)


async def get_cached_benchmark_result(benchmark_id: str) -> Optional[Dict]:
    """Получение закэшированного результата бенчмарка."""
    return await cache_manager.get_benchmark_result(benchmark_id)


async def invalidate_cache(pattern: str = "*") -> int:
    """Инвалидация кэша по паттерну."""
    return await cache_manager.clear(pattern)


async def get_cache_stats() -> Dict[str, Any]:
    """Получение статистики кэша."""
    return await cache_manager.get_stats() 