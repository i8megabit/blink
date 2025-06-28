"""
Распределенный кэш для RAG операций
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import pickle

import redis.asyncio as redis
from redis.asyncio import Redis

from .centralized_architecture import LLMResponse

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Конфигурация кэша"""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 час
    max_cache_size: int = 10000
    embedding_ttl: int = 86400  # 24 часа
    response_ttl: int = 1800  # 30 минут
    knowledge_base_ttl: int = 604800  # 1 неделя

@dataclass
class CachedDocument:
    """Кэшированный документ"""
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: datetime
    access_count: int = 0

class DistributedRAGCache:
    """Распределенный кэш для RAG операций"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig(redis_url=redis_url)
        self.redis: Optional[Redis] = None
        
        # Локальный кэш для быстрого доступа
        self.local_cache: Dict[str, Any] = {}
        self.local_cache_ttl: Dict[str, float] = {}
        
        # Счетчики метрик
        self.cache_hits = 0
        self.cache_misses = 0
        self.embedding_generations = 0
        
        logger.info(f"DistributedRAGCache инициализирован с Redis: {redis_url}")
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Завершение работы"""
        await self.disconnect()
    
    async def connect(self):
        """Подключение к Redis"""
        if self.redis is None:
            try:
                self.redis = redis.from_url(self.config.redis_url)
                await self.redis.ping()
                logger.info("Подключение к Redis установлено")
            except Exception as e:
                logger.error(f"Ошибка подключения к Redis: {e}")
                raise
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Соединение с Redis закрыто")
    
    async def cache_response(self, key: str, response: LLMResponse, ttl: Optional[int] = None) -> bool:
        """Кэширование ответа LLM"""
        try:
            if self.redis is None:
                await self.connect()
            
            ttl = ttl or self.config.response_ttl
            
            # Сериализуем ответ
            response_data = {
                "request_id": response.request_id,
                "response": response.response,
                "model_used": response.model_used,
                "tokens_used": response.tokens_used,
                "response_time": response.response_time,
                "rag_enhanced": response.rag_enhanced,
                "cache_hit": response.cache_hit,
                "created_at": response.created_at.isoformat()
            }
            
            # Кэшируем в Redis
            await self.redis.setex(
                f"response:{key}",
                ttl,
                json.dumps(response_data)
            )
            
            # Кэшируем локально
            self.local_cache[f"response:{key}"] = response
            self.local_cache_ttl[f"response:{key}"] = time.time() + ttl
            
            logger.debug(f"Ответ кэширован с ключом {key}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка кэширования ответа: {e}")
            return False
    
    async def get_response(self, key: str) -> Optional[LLMResponse]:
        """Получение кэшированного ответа"""
        try:
            # Проверяем локальный кэш
            local_key = f"response:{key}"
            if local_key in self.local_cache:
                if time.time() < self.local_cache_ttl.get(local_key, 0):
                    self.cache_hits += 1
                    logger.debug(f"Локальный кэш-хит для {key}")
                    return self.local_cache[local_key]
                else:
                    # Удаляем устаревший элемент
                    del self.local_cache[local_key]
                    del self.local_cache_ttl[local_key]
            
            if self.redis is None:
                await self.connect()
            
            # Проверяем Redis
            cached_data = await self.redis.get(f"response:{key}")
            if cached_data:
                response_data = json.loads(cached_data)
                
                # Создаем объект ответа
                response = LLMResponse(
                    request_id=response_data["request_id"],
                    response=response_data["response"],
                    model_used=response_data["model_used"],
                    tokens_used=response_data["tokens_used"],
                    response_time=response_data["response_time"],
                    rag_enhanced=response_data["rag_enhanced"],
                    cache_hit=True,
                    created_at=datetime.fromisoformat(response_data["created_at"])
                )
                
                # Кэшируем локально
                self.local_cache[local_key] = response
                self.local_cache_ttl[local_key] = time.time() + self.config.response_ttl
                
                self.cache_hits += 1
                logger.debug(f"Redis кэш-хит для {key}")
                return response
            
            self.cache_misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения кэшированного ответа: {e}")
            self.cache_misses += 1
            return None
    
    async def cache_embedding(self, text: str, embedding: List[float], ttl: Optional[int] = None) -> bool:
        """Кэширование эмбеддинга"""
        try:
            if self.redis is None:
                await self.connect()
            
            ttl = ttl or self.config.embedding_ttl
            key = self._generate_embedding_key(text)
            
            # Сериализуем эмбеддинг
            embedding_data = {
                "text": text,
                "embedding": embedding,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Кэшируем в Redis
            await self.redis.setex(
                f"embedding:{key}",
                ttl,
                json.dumps(embedding_data)
            )
            
            logger.debug(f"Эмбеддинг кэширован для текста длиной {len(text)}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка кэширования эмбеддинга: {e}")
            return False
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Получение кэшированного эмбеддинга"""
        try:
            if self.redis is None:
                await self.connect()
            
            key = self._generate_embedding_key(text)
            cached_data = await self.redis.get(f"embedding:{key}")
            
            if cached_data:
                embedding_data = json.loads(cached_data)
                self.cache_hits += 1
                logger.debug(f"Кэш-хит для эмбеддинга текста длиной {len(text)}")
                return embedding_data["embedding"]
            
            self.cache_misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения кэшированного эмбеддинга: {e}")
            self.cache_misses += 1
            return None
    
    async def add_to_knowledge_base(self, documents: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """Добавление документов в базу знаний"""
        try:
            if self.redis is None:
                await self.connect()
            
            ttl = ttl or self.config.knowledge_base_ttl
            
            for doc in documents:
                doc_id = doc.get("id", hashlib.md5(doc["content"].encode()).hexdigest())
                
                # Кэшируем документ
                await self.redis.setex(
                    f"knowledge:{doc_id}",
                    ttl,
                    json.dumps(doc)
                )
                
                # Добавляем в индекс для поиска
                await self.redis.sadd("knowledge_index", doc_id)
            
            logger.info(f"Добавлено {len(documents)} документов в базу знаний")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления в базу знаний: {e}")
            return False
    
    async def search_knowledge_base(self, query: str, limit: int = 5) -> List[str]:
        """Поиск в базе знаний"""
        try:
            if self.redis is None:
                await self.connect()
            
            # Получаем все документы из индекса
            doc_ids = await self.redis.smembers("knowledge_index")
            
            if not doc_ids:
                return []
            
            # Получаем документы
            documents = []
            for doc_id in doc_ids:
                doc_data = await self.redis.get(f"knowledge:{doc_id}")
                if doc_data:
                    doc = json.loads(doc_data)
                    documents.append(doc)
            
            # Простой поиск по ключевым словам (в реальной системе здесь будет векторный поиск)
            query_words = query.lower().split()
            relevant_docs = []
            
            for doc in documents:
                content = doc.get("content", "").lower()
                score = sum(1 for word in query_words if word in content)
                
                if score > 0:
                    relevant_docs.append((score, doc["content"]))
            
            # Сортируем по релевантности и возвращаем топ результаты
            relevant_docs.sort(key=lambda x: x[0], reverse=True)
            
            return [doc[1] for doc in relevant_docs[:limit]]
            
        except Exception as e:
            logger.error(f"Ошибка поиска в базе знаний: {e}")
            return []
    
    async def clear_cache(self, pattern: str = "*") -> int:
        """Очистка кэша"""
        try:
            if self.redis is None:
                await self.connect()
            
            # Очищаем Redis
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            
            # Очищаем локальный кэш
            local_keys = [k for k in self.local_cache.keys() if pattern == "*" or pattern in k]
            for key in local_keys:
                del self.local_cache[key]
                if key in self.local_cache_ttl:
                    del self.local_cache_ttl[key]
            
            logger.info(f"Кэш очищен, удалено {len(keys)} ключей")
            return len(keys)
            
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        try:
            if self.redis is None:
                await self.connect()
            
            # Получаем информацию о Redis
            info = await self.redis.info()
            
            # Подсчитываем ключи по типам
            response_keys = await self.redis.keys("response:*")
            embedding_keys = await self.redis.keys("embedding:*")
            knowledge_keys = await self.redis.keys("knowledge:*")
            
            return {
                "redis_connected": True,
                "redis_memory_usage": info.get("used_memory_human", "N/A"),
                "redis_keyspace_hits": info.get("keyspace_hits", 0),
                "redis_keyspace_misses": info.get("keyspace_misses", 0),
                "response_cache_size": len(response_keys),
                "embedding_cache_size": len(embedding_keys),
                "knowledge_base_size": len(knowledge_keys),
                "local_cache_size": len(self.local_cache),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {e}")
            return {
                "redis_connected": False,
                "error": str(e),
                "local_cache_size": len(self.local_cache),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья кэша"""
        try:
            if self.redis is None:
                await self.connect()
            
            # Проверяем подключение
            await self.redis.ping()
            
            # Получаем базовую статистику
            stats = await self.get_cache_stats()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "cache_stats": stats
            }
            
        except Exception as e:
            return {
                "status": "error",
                "redis_connected": False,
                "error": str(e)
            }
    
    def _generate_embedding_key(self, text: str) -> str:
        """Генерация ключа для эмбеддинга"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _cleanup_local_cache(self):
        """Очистка устаревших элементов локального кэша"""
        current_time = time.time()
        expired_keys = [
            key for key, ttl in self.local_cache_ttl.items()
            if current_time > ttl
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
            del self.local_cache_ttl[key]
        
        if expired_keys:
            logger.debug(f"Очищено {len(expired_keys)} устаревших элементов локального кэша")
    
    async def optimize_cache(self):
        """Оптимизация кэша"""
        try:
            # Очищаем локальный кэш
            self._cleanup_local_cache()
            
            # Ограничиваем размер локального кэша
            if len(self.local_cache) > self.config.max_cache_size:
                # Удаляем самые старые элементы
                sorted_keys = sorted(
                    self.local_cache_ttl.items(),
                    key=lambda x: x[1]
                )
                
                keys_to_remove = sorted_keys[:len(sorted_keys) - self.config.max_cache_size]
                for key, _ in keys_to_remove:
                    del self.local_cache[key]
                    del self.local_cache_ttl[key]
                
                logger.info(f"Локальный кэш оптимизирован, удалено {len(keys_to_remove)} элементов")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации кэша: {e}") 