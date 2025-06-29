"""
🗄️ Профессиональный оптимизатор ChromaDB
Production-ready конфигурация и оптимизация для reLink
"""

import asyncio
import structlog
from typing import Dict, Any, List, Optional, Tuple
import chromadb
from chromadb.config import Settings, HttpClientSettings
from chromadb.api.models.Collection import Collection
import numpy as np
from dataclasses import dataclass
import time
import hashlib
import json

from .config import get_settings

logger = structlog.get_logger()

@dataclass
class ChromaDBConfig:
    """Конфигурация ChromaDB для production"""
    host: str = "chromadb"
    port: int = 8000
    ssl: bool = False
    auth_token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    batch_size: int = 100
    embedding_dimension: int = 1536
    distance_metric: str = "cosine"
    collection_metadata: Dict[str, Any] = None

class ChromaDBOptimizer:
    """Профессиональный оптимизатор ChromaDB"""
    
    def __init__(self):
        self.settings = get_settings()
        self.config = ChromaDBConfig(
            host=self.settings.CHROMADB_HOST,
            port=self.settings.CHROMADB_PORT,
            auth_token=getattr(self.settings, 'CHROMADB_AUTH_TOKEN', None)
        )
        self.client: Optional[chromadb.Client] = None
        self.collections_cache: Dict[str, Collection] = {}
        self.performance_metrics: Dict[str, Any] = {}
        
        self._initialize_client()
        logger.info("ChromaDB Optimizer initialized", config=self.config)
    
    def _initialize_client(self):
        """Инициализация оптимизированного клиента"""
        try:
            # Настройки для production
            client_settings = HttpClientSettings(
                host=self.config.host,
                port=self.config.port,
                ssl=self.config.ssl,
                headers={
                    "X-Chroma-Token": self.config.auth_token
                } if self.config.auth_token else {},
                timeout=self.config.timeout
            )
            
            self.client = chromadb.HttpClient(settings=client_settings)
            
            # Проверка подключения
            self.client.heartbeat()
            logger.info("ChromaDB client connected successfully")
            
        except Exception as e:
            logger.error("Failed to initialize ChromaDB client", error=str(e))
            self.client = None
    
    async def create_optimized_collection(
        self, 
        name: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Collection]:
        """Создание оптимизированной коллекции"""
        
        if not self.client:
            logger.error("ChromaDB client not initialized")
            return None
        
        try:
            # Оптимизированные настройки коллекции
            collection_metadata = {
                "description": f"Optimized collection for {name}",
                "created_by": "reLink",
                "optimization_level": "production",
                "embedding_dimension": self.config.embedding_dimension,
                "distance_metric": self.config.distance_metric,
                **(metadata or {})
            }
            
            # Создание коллекции с оптимизированными параметрами
            collection = self.client.create_collection(
                name=name,
                metadata=collection_metadata,
                embedding_function=None  # Используем встроенные эмбеддинги
            )
            
            self.collections_cache[name] = collection
            
            logger.info("Optimized collection created", 
                       name=name, 
                       metadata=collection_metadata)
            
            return collection
            
        except Exception as e:
            logger.error("Failed to create optimized collection", 
                        error=str(e), name=name)
            return None
    
    async def batch_add_documents(
        self, 
        collection_name: str,
        documents: List[Dict[str, Any]],
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Батчевое добавление документов с оптимизацией"""
        
        if not self.client:
            return {"error": "ChromaDB not initialized"}
        
        batch_size = batch_size or self.config.batch_size
        start_time = time.time()
        
        try:
            collection = self._get_collection(collection_name)
            if not collection:
                return {"error": f"Collection {collection_name} not found"}
            
            # Разбиваем на батчи
            batches = [documents[i:i + batch_size] 
                      for i in range(0, len(documents), batch_size)]
            
            total_added = 0
            batch_metrics = []
            
            for i, batch in enumerate(batches):
                batch_start = time.time()
                
                # Подготавливаем данные батча
                texts = []
                metadatas = []
                ids = []
                
                for doc in batch:
                    texts.append(doc.get('text', doc.get('content', str(doc))))
                    metadatas.append(doc.get('metadata', {}))
                    ids.append(doc.get('id', self._generate_document_id(doc)))
                
                # Добавляем батч
                collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                batch_duration = time.time() - batch_start
                batch_metrics.append({
                    "batch_index": i,
                    "documents_count": len(batch),
                    "duration_seconds": batch_duration,
                    "documents_per_second": len(batch) / batch_duration
                })
                
                total_added += len(batch)
                
                logger.info("Batch added", 
                           batch_index=i,
                           documents_count=len(batch),
                           duration_seconds=batch_duration)
            
            total_duration = time.time() - start_time
            
            # Сохраняем метрики производительности
            self.performance_metrics[f"batch_add_{collection_name}"] = {
                "total_documents": total_added,
                "total_duration": total_duration,
                "average_documents_per_second": total_added / total_duration,
                "batch_metrics": batch_metrics,
                "timestamp": time.time()
            }
            
            return {
                "success": True,
                "total_added": total_added,
                "total_duration": total_duration,
                "average_documents_per_second": total_added / total_duration,
                "batch_metrics": batch_metrics
            }
            
        except Exception as e:
            logger.error("Batch add documents failed", 
                        error=str(e), 
                        collection_name=collection_name)
            return {"error": str(e)}
    
    async def optimized_search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Оптимизированный поиск с фильтрацией"""
        
        if not self.client:
            return []
        
        start_time = time.time()
        
        try:
            collection = self._get_collection(collection_name)
            if not collection:
                return []
            
            # Оптимизированные параметры поиска
            search_params = {
                "query_texts": [query],
                "n_results": top_k,
                "include": ["metadatas", "distances"] if include_metadata else ["distances"]
            }
            
            # Добавляем фильтры если есть
            if filter_metadata:
                search_params["where"] = filter_metadata
            
            # Выполняем поиск
            results = collection.query(**search_params)
            
            # Форматируем результаты
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'document': doc,
                        'id': results['ids'][0][i] if results['ids'] and results['ids'][0] else None,
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else None,
                        'relevance_score': self._calculate_relevance_score(
                            results['distances'][0][i] if results['distances'] and results['distances'][0] else 1.0
                        )
                    }
                    
                    if include_metadata and results['metadatas'] and results['metadatas'][0]:
                        result['metadata'] = results['metadatas'][0][i]
                    
                    formatted_results.append(result)
            
            # Сортируем по релевантности
            formatted_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            search_duration = time.time() - start_time
            
            # Логируем метрики поиска
            logger.info("Optimized search completed",
                       collection_name=collection_name,
                       query_length=len(query),
                       results_count=len(formatted_results),
                       duration_seconds=search_duration)
            
            return formatted_results
            
        except Exception as e:
            logger.error("Optimized search failed",
                        error=str(e),
                        collection_name=collection_name)
            return []
    
    def _get_collection(self, name: str) -> Optional[Collection]:
        """Получение коллекции с кешированием"""
        if name in self.collections_cache:
            return self.collections_cache[name]
        
        try:
            collection = self.client.get_collection(name)
            self.collections_cache[name] = collection
            return collection
        except:
            return None
    
    def _generate_document_id(self, document: Dict[str, Any]) -> str:
        """Генерация уникального ID документа"""
        content = str(document.get('text', document.get('content', str(document))))
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _calculate_relevance_score(self, distance: float) -> float:
        """Расчет релевантности на основе расстояния"""
        # Преобразуем расстояние в релевантность (0-1)
        # Меньшее расстояние = большая релевантность
        return max(0.0, 1.0 - distance)
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Получение статистики коллекции"""
        
        if not self.client:
            return {"error": "ChromaDB not initialized"}
        
        try:
            collection = self._get_collection(collection_name)
            if not collection:
                return {"error": f"Collection {collection_name} not found"}
            
            # Получаем базовую информацию
            count = collection.count()
            metadata = collection.metadata
            
            # Анализируем метаданные документов
            sample_docs = collection.peek(limit=100)
            metadata_keys = set()
            if sample_docs['metadatas']:
                for doc_metadata in sample_docs['metadatas']:
                    if doc_metadata:
                        metadata_keys.update(doc_metadata.keys())
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "metadata": metadata,
                "metadata_keys": list(metadata_keys),
                "sample_documents": len(sample_docs['documents']) if sample_docs['documents'] else 0,
                "embedding_dimension": metadata.get("embedding_dimension", "unknown"),
                "distance_metric": metadata.get("distance_metric", "unknown")
            }
            
        except Exception as e:
            logger.error("Failed to get collection stats",
                        error=str(e),
                        collection_name=collection_name)
            return {"error": str(e)}
    
    async def optimize_collection(self, collection_name: str) -> Dict[str, Any]:
        """Оптимизация коллекции для лучшей производительности"""
        
        if not self.client:
            return {"error": "ChromaDB not initialized"}
        
        try:
            collection = self._get_collection(collection_name)
            if not collection:
                return {"error": f"Collection {collection_name} not found"}
            
            # Получаем текущую статистику
            stats = await self.get_collection_stats(collection_name)
            
            # Рекомендации по оптимизации
            recommendations = []
            
            if stats.get("document_count", 0) > 10000:
                recommendations.append("Consider sharding for large collections")
            
            if stats.get("document_count", 0) < 100:
                recommendations.append("Collection is small, consider batching additions")
            
            # Проверяем метрики производительности
            perf_key = f"batch_add_{collection_name}"
            if perf_key in self.performance_metrics:
                perf = self.performance_metrics[perf_key]
                if perf["average_documents_per_second"] < 10:
                    recommendations.append("Consider reducing batch size for better performance")
            
            return {
                "collection_name": collection_name,
                "current_stats": stats,
                "recommendations": recommendations,
                "optimization_status": "analyzed"
            }
            
        except Exception as e:
            logger.error("Failed to optimize collection",
                        error=str(e),
                        collection_name=collection_name)
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья с детальной диагностикой"""
        
        if not self.client:
            return {
                "status": "unhealthy",
                "error": "ChromaDB client not initialized"
            }
        
        try:
            # Проверка подключения
            heartbeat = self.client.heartbeat()
            
            # Получение списка коллекций
            collections = self.client.list_collections()
            
            # Анализ производительности
            performance_summary = {}
            for key, metrics in self.performance_metrics.items():
                if "batch_add" in key:
                    performance_summary[key] = {
                        "total_documents": metrics["total_documents"],
                        "average_documents_per_second": metrics["average_documents_per_second"]
                    }
            
            return {
                "status": "healthy",
                "chromadb_connected": True,
                "collections_count": len(collections),
                "collections": [col.name for col in collections],
                "performance_summary": performance_summary,
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "batch_size": self.config.batch_size,
                    "embedding_dimension": self.config.embedding_dimension
                }
            }
            
        except Exception as e:
            logger.error("ChromaDB health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Глобальный экземпляр оптимизатора
_chromadb_optimizer: Optional[ChromaDBOptimizer] = None

def get_chromadb_optimizer() -> ChromaDBOptimizer:
    """Получение глобального экземпляра ChromaDB оптимизатора"""
    global _chromadb_optimizer
    if _chromadb_optimizer is None:
        _chromadb_optimizer = ChromaDBOptimizer()
    return _chromadb_optimizer 