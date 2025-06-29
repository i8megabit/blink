"""
Продвинутый сервис ChromaDB с интеллектуальной оптимизацией
"""

import asyncio
import logging
import time
import json
import hashlib
import gzip
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import psutil
import redis
from functools import lru_cache

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Стратегии кеширования"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    ADAPTIVE = "adaptive"


class CompressionType(Enum):
    """Типы компрессии"""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"


@dataclass
class ShardConfig:
    """Конфигурация шарда"""
    shard_id: str
    collection_name: str
    max_documents: int = 100000
    max_size_mb: int = 1024
    compression_type: CompressionType = CompressionType.GZIP
    cache_strategy: CacheStrategy = CacheStrategy.ADAPTIVE


@dataclass
class QueryMetrics:
    """Метрики запроса"""
    query_time: float
    cache_hit: bool
    shard_used: str
    documents_returned: int
    embedding_dimensions: int
    compression_ratio: float = 1.0


@dataclass
class PerformanceStats:
    """Статистика производительности"""
    total_queries: int = 0
    cache_hits: int = 0
    avg_query_time: float = 0.0
    total_documents: int = 0
    memory_usage_mb: int = 0
    disk_usage_mb: int = 0
    last_optimization: float = 0.0


class AdvancedChromaDBService:
    """
    Продвинутый сервис ChromaDB с интеллектуальной оптимизацией
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        redis_url: str = "redis://localhost:6379",
        max_cache_size: int = 1000,
        enable_compression: bool = True,
        enable_sharding: bool = True,
        shard_size_threshold: int = 50000
    ):
        self.persist_directory = persist_directory
        self.enable_compression = enable_compression
        self.enable_sharding = enable_sharding
        self.shard_size_threshold = shard_size_threshold
        
        # Инициализация ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Redis для кеширования
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Redis подключен для кеширования")
        except Exception as e:
            logger.warning(f"Redis недоступен: {e}")
            self.redis_available = False
        
        # Локальный кеш
        self.local_cache = {}
        self.max_cache_size = max_cache_size
        
        # Конфигурация шардов
        self.shards: Dict[str, ShardConfig] = {}
        self.collection_shards: Dict[str, List[str]] = {}
        
        # Статистика производительности
        self.performance_stats = PerformanceStats()
        
        # Thread pool для асинхронных операций
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Мониторинг ресурсов
        self.resource_monitor = ResourceMonitor()
        
        logger.info("AdvancedChromaDBService инициализирован")
    
    async def create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_function: Optional[Any] = None
    ) -> Collection:
        """Создание коллекции с автоматическим шардированием"""
        
        try:
            # Создание основной коллекции
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {},
                embedding_function=embedding_function
            )
            
            # Инициализация шардов если включено
            if self.enable_sharding:
                await self._initialize_shards(name)
            
            logger.info(f"Коллекция {name} создана успешно")
            return collection
            
        except Exception as e:
            logger.error(f"Ошибка создания коллекции {name}: {e}")
            raise
    
    async def _initialize_shards(self, collection_name: str):
        """Инициализация шардов для коллекции"""
        shard_ids = []
        
        # Создание начального шарда
        shard_id = f"{collection_name}_shard_0"
        shard_config = ShardConfig(
            shard_id=shard_id,
            collection_name=collection_name
        )
        
        self.shards[shard_id] = shard_config
        shard_ids.append(shard_id)
        
        # Создание коллекции шарда
        try:
            shard_collection = self.client.create_collection(
                name=shard_id,
                metadata={
                    "type": "shard",
                    "parent_collection": collection_name,
                    "shard_id": shard_id
                }
            )
            logger.info(f"Шард {shard_id} создан")
        except Exception as e:
            logger.error(f"Ошибка создания шарда {shard_id}: {e}")
        
        self.collection_shards[collection_name] = shard_ids
    
    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """Добавление документов с автоматическим шардированием"""
        
        start_time = time.time()
        
        try:
            # Определение целевого шарда
            target_shard = await self._select_target_shard(collection_name)
            
            # Компрессия документов если включена
            if self.enable_compression:
                documents, compression_ratio = await self._compress_documents(documents)
            else:
                compression_ratio = 1.0
            
            # Добавление в шард
            shard_collection = self.client.get_collection(target_shard)
            
            # Генерация ID если не предоставлены
            if ids is None:
                ids = [f"{target_shard}_{i}_{int(time.time())}" for i in range(len(documents))]
            
            # Добавление документов
            shard_collection.add(
                documents=documents,
                metadatas=metadatas or [{}] * len(documents),
                ids=ids,
                embeddings=embeddings
            )
            
            # Обновление статистики
            self.performance_stats.total_documents += len(documents)
            self.performance_stats.total_queries += 1
            
            # Проверка необходимости создания нового шарда
            await self._check_shard_expansion(collection_name, target_shard)
            
            logger.info(f"Добавлено {len(documents)} документов в шард {target_shard}")
            return ids
            
        except Exception as e:
            logger.error(f"Ошибка добавления документов: {e}")
            raise
    
    async def _select_target_shard(self, collection_name: str) -> str:
        """Выбор целевого шарда для добавления документов"""
        
        if not self.enable_sharding:
            return collection_name
        
        shard_ids = self.collection_shards.get(collection_name, [collection_name])
        
        # Выбор шарда с наименьшей нагрузкой
        min_docs = float('inf')
        target_shard = shard_ids[0]
        
        for shard_id in shard_ids:
            try:
                shard_collection = self.client.get_collection(shard_id)
                count = shard_collection.count()
                
                if count < min_docs:
                    min_docs = count
                    target_shard = shard_id
                    
            except Exception as e:
                logger.warning(f"Ошибка получения статистики шарда {shard_id}: {e}")
        
        return target_shard
    
    async def _compress_documents(self, documents: List[str]) -> Tuple[List[str], float]:
        """Компрессия документов"""
        compressed_docs = []
        total_original = 0
        total_compressed = 0
        
        for doc in documents:
            original_size = len(doc.encode('utf-8'))
            compressed = gzip.compress(doc.encode('utf-8'))
            compressed_docs.append(compressed.decode('latin1'))
            
            total_original += original_size
            total_compressed += len(compressed)
        
        compression_ratio = total_compressed / total_original if total_original > 0 else 1.0
        
        return compressed_docs, compression_ratio
    
    async def _check_shard_expansion(self, collection_name: str, current_shard: str):
        """Проверка необходимости расширения шардов"""
        
        try:
            shard_collection = self.client.get_collection(current_shard)
            count = shard_collection.count()
            
            if count > self.shard_size_threshold:
                await self._create_new_shard(collection_name)
                
        except Exception as e:
            logger.error(f"Ошибка проверки расширения шарда: {e}")
    
    async def _create_new_shard(self, collection_name: str):
        """Создание нового шарда"""
        
        existing_shards = self.collection_shards.get(collection_name, [])
        new_shard_id = f"{collection_name}_shard_{len(existing_shards)}"
        
        shard_config = ShardConfig(
            shard_id=new_shard_id,
            collection_name=collection_name
        )
        
        self.shards[new_shard_id] = shard_config
        existing_shards.append(new_shard_id)
        self.collection_shards[collection_name] = existing_shards
        
        # Создание коллекции шарда
        try:
            self.client.create_collection(
                name=new_shard_id,
                metadata={
                    "type": "shard",
                    "parent_collection": collection_name,
                    "shard_id": new_shard_id
                }
            )
            logger.info(f"Создан новый шард {new_shard_id}")
        except Exception as e:
            logger.error(f"Ошибка создания нового шарда {new_shard_id}: {e}")
    
    async def query(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Интеллектуальный запрос с кешированием и оптимизацией"""
        
        start_time = time.time()
        
        # Генерация ключа кеша
        cache_key = self._generate_cache_key(
            collection_name, query_texts, query_embeddings, 
            n_results, where, where_document, include
        )
        
        # Проверка кеша
        cached_result = await self._get_cached_result(cache_key)
        if cached_result:
            self.performance_stats.cache_hits += 1
            return {
                **cached_result,
                "cache_hit": True,
                "query_time": time.time() - start_time
            }
        
        try:
            # Выполнение запроса
            if self.enable_sharding:
                result = await self._query_sharded(
                    collection_name, query_texts, query_embeddings,
                    n_results, where, where_document, include
                )
            else:
                collection = self.client.get_collection(collection_name)
                result = collection.query(
                    query_texts=query_texts,
                    query_embeddings=query_embeddings,
                    n_results=n_results,
                    where=where,
                    where_document=where_document,
                    include=include
                )
            
            # Кеширование результата
            await self._cache_result(cache_key, result)
            
            # Обновление статистики
            query_time = time.time() - start_time
            self.performance_stats.total_queries += 1
            self.performance_stats.avg_query_time = (
                (self.performance_stats.avg_query_time * (self.performance_stats.total_queries - 1) + query_time) /
                self.performance_stats.total_queries
            )
            
            return {
                **result,
                "cache_hit": False,
                "query_time": query_time
            }
            
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            raise
    
    async def _query_sharded(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Запрос по всем шардам с объединением результатов"""
        
        shard_ids = self.collection_shards.get(collection_name, [collection_name])
        all_results = []
        
        # Параллельные запросы к шардам
        tasks = []
        for shard_id in shard_ids:
            task = self._query_single_shard(
                shard_id, query_texts, query_embeddings,
                n_results, where, where_document, include
            )
            tasks.append(task)
        
        shard_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Объединение результатов
        for i, result in enumerate(shard_results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка запроса к шарду {shard_ids[i]}: {result}")
                continue
            
            if result and 'ids' in result:
                all_results.append(result)
        
        # Объединение и ранжирование результатов
        return self._merge_shard_results(all_results, n_results)
    
    async def _query_single_shard(
        self,
        shard_id: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Запрос к одному шарду"""
        
        try:
            collection = self.client.get_collection(shard_id)
            return collection.query(
                query_texts=query_texts,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=include
            )
        except Exception as e:
            logger.error(f"Ошибка запроса к шарду {shard_id}: {e}")
            return None
    
    def _merge_shard_results(self, shard_results: List[Dict[str, Any]], n_results: int) -> Dict[str, Any]:
        """Объединение результатов из разных шардов"""
        
        if not shard_results:
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}
        
        # Объединение всех результатов
        all_ids = []
        all_documents = []
        all_metadatas = []
        all_distances = []
        
        for result in shard_results:
            if 'ids' in result and result['ids']:
                all_ids.extend(result['ids'])
                all_documents.extend(result.get('documents', []))
                all_metadatas.extend(result.get('metadatas', []))
                all_distances.extend(result.get('distances', []))
        
        # Сортировка по расстоянию (если есть)
        if all_distances:
            sorted_indices = np.argsort(all_distances)
            all_ids = [all_ids[i] for i in sorted_indices]
            all_documents = [all_documents[i] for i in sorted_indices]
            all_metadatas = [all_metadatas[i] for i in sorted_indices]
            all_distances = [all_distances[i] for i in sorted_indices]
        
        # Возврат топ результатов
        return {
            "ids": all_ids[:n_results],
            "documents": all_documents[:n_results],
            "metadatas": all_metadatas[:n_results],
            "distances": all_distances[:n_results]
        }
    
    def _generate_cache_key(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> str:
        """Генерация ключа кеша для запроса"""
        
        cache_data = {
            "collection": collection_name,
            "query_texts": query_texts,
            "n_results": n_results,
            "where": where,
            "where_document": where_document,
            "include": include
        }
        
        # Для эмбеддингов используем хеш
        if query_embeddings:
            embedding_hash = hashlib.md5(
                str(query_embeddings).encode()
            ).hexdigest()
            cache_data["embedding_hash"] = embedding_hash
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return f"chromadb_query:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Получение результата из кеша"""
        
        # Проверка Redis
        if self.redis_available:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Ошибка получения из Redis: {e}")
        
        # Проверка локального кеша
        if cache_key in self.local_cache:
            return self.local_cache[cache_key]
        
        return None
    
    async def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Кеширование результата"""
        
        # Кеширование в Redis
        if self.redis_available:
            try:
                self.redis_client.setex(
                    cache_key,
                    3600,  # TTL 1 час
                    json.dumps(result)
                )
            except Exception as e:
                logger.warning(f"Ошибка кеширования в Redis: {e}")
        
        # Кеширование локально
        if len(self.local_cache) >= self.max_cache_size:
            # Удаление самого старого элемента
            oldest_key = next(iter(self.local_cache))
            del self.local_cache[oldest_key]
        
        self.local_cache[cache_key] = result
    
    async def optimize_collections(self):
        """Оптимизация коллекций"""
        
        try:
            # Получение всех коллекций
            collections = self.client.list_collections()
            
            for collection in collections:
                await self._optimize_collection(collection.name)
            
            self.performance_stats.last_optimization = time.time()
            logger.info("Оптимизация коллекций завершена")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации коллекций: {e}")
    
    async def _optimize_collection(self, collection_name: str):
        """Оптимизация отдельной коллекции"""
        
        try:
            collection = self.client.get_collection(collection_name)
            
            # Проверка размера коллекции
            count = collection.count()
            
            # Перебалансировка шардов если необходимо
            if self.enable_sharding and count > self.shard_size_threshold * 2:
                await self._rebalance_shards(collection_name)
            
            # Очистка кеша
            await self._cleanup_cache()
            
            logger.info(f"Коллекция {collection_name} оптимизирована")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации коллекции {collection_name}: {e}")
    
    async def _rebalance_shards(self, collection_name: str):
        """Перебалансировка шардов"""
        
        shard_ids = self.collection_shards.get(collection_name, [])
        if len(shard_ids) < 2:
            return
        
        # Анализ распределения документов
        shard_counts = {}
        for shard_id in shard_ids:
            try:
                collection = self.client.get_collection(shard_id)
                shard_counts[shard_id] = collection.count()
            except Exception as e:
                logger.error(f"Ошибка получения статистики шарда {shard_id}: {e}")
        
        # Проверка необходимости перебалансировки
        counts = list(shard_counts.values())
        if max(counts) - min(counts) > self.shard_size_threshold:
            logger.info(f"Начинается перебалансировка шардов для {collection_name}")
            # Здесь можно добавить логику перебалансировки
    
    async def _cleanup_cache(self):
        """Очистка кеша"""
        
        # Очистка локального кеша
        if len(self.local_cache) > self.max_cache_size * 0.8:
            # Удаление 20% самых старых записей
            keys_to_remove = list(self.local_cache.keys())[:len(self.local_cache) // 5]
            for key in keys_to_remove:
                del self.local_cache[key]
        
        # Очистка Redis кеша (если доступен)
        if self.redis_available:
            try:
                # Удаление устаревших ключей
                pattern = "chromadb_query:*"
                keys = self.redis_client.keys(pattern)
                if len(keys) > 1000:  # Если слишком много ключей
                    # Удаление старых ключей
                    for key in keys[:100]:
                        self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Ошибка очистки Redis кеша: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Получение статистики производительности"""
        
        # Обновление метрик ресурсов
        memory_usage = self.resource_monitor.get_memory_usage()
        disk_usage = self.resource_monitor.get_disk_usage(self.persist_directory)
        
        return {
            "total_queries": self.performance_stats.total_queries,
            "cache_hits": self.performance_stats.cache_hits,
            "cache_hit_rate": (
                self.performance_stats.cache_hits / self.performance_stats.total_queries
                if self.performance_stats.total_queries > 0 else 0
            ),
            "avg_query_time": self.performance_stats.avg_query_time,
            "total_documents": self.performance_stats.total_documents,
            "memory_usage_mb": memory_usage,
            "disk_usage_mb": disk_usage,
            "local_cache_size": len(self.local_cache),
            "shards_count": len(self.shards),
            "last_optimization": self.performance_stats.last_optimization,
            "redis_available": self.redis_available
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса"""
        
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {}
        }
        
        # Проверка ChromaDB
        try:
            collections = self.client.list_collections()
            health_status["checks"]["chromadb"] = {
                "status": "healthy",
                "collections_count": len(collections)
            }
        except Exception as e:
            health_status["checks"]["chromadb"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        # Проверка Redis
        if self.redis_available:
            try:
                self.redis_client.ping()
                health_status["checks"]["redis"] = {"status": "healthy"}
            except Exception as e:
                health_status["checks"]["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"
        else:
            health_status["checks"]["redis"] = {"status": "not_configured"}
        
        # Проверка ресурсов
        try:
            memory_usage = self.resource_monitor.get_memory_usage()
            disk_usage = self.resource_monitor.get_disk_usage(self.persist_directory)
            
            health_status["checks"]["resources"] = {
                "status": "healthy" if memory_usage < 80 else "warning",
                "memory_usage_mb": memory_usage,
                "disk_usage_mb": disk_usage
            }
        except Exception as e:
            health_status["checks"]["resources"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        return health_status


class ResourceMonitor:
    """Мониторинг ресурсов системы"""
    
    def get_memory_usage(self) -> float:
        """Получение использования памяти в MB"""
        try:
            memory = psutil.virtual_memory()
            return memory.used / (1024 * 1024)  # MB
        except Exception:
            return 0.0
    
    def get_disk_usage(self, path: str) -> float:
        """Получение использования диска в MB"""
        try:
            disk_usage = psutil.disk_usage(path)
            return disk_usage.used / (1024 * 1024)  # MB
        except Exception:
            return 0.0
    
    def get_cpu_usage(self) -> float:
        """Получение использования CPU в процентах"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            return 0.0


# Глобальный экземпляр сервиса
chromadb_service = AdvancedChromaDBService() 