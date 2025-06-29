"""
🧠 РАСШИРЕННЫЙ RAG МЕНЕДЖЕР
Автоматическое управление коллекциями ChromaDB + умное кеширование
"""

import asyncio
import time
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import structlog
import chromadb
from chromadb.config import Settings

from .config import get_settings

logger = structlog.get_logger()

class ChromaDBManager:
    """Умный менеджер ChromaDB с автоматическим управлением коллекциями"""
    
    def __init__(self):
        self.settings = get_settings()
        self.chroma_client: Optional[chromadb.Client] = None
        self._collections_cache: Dict[str, Any] = {}
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(hours=1)  # Очистка каждый час
        
        # Настройки автоматического управления
        self.max_collections = 50  # Максимум коллекций
        self.max_documents_per_collection = 10000  # Максимум документов в коллекции
        self.collection_ttl = timedelta(days=7)  # TTL для коллекций
        
        self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Инициализация ChromaDB с обработкой ошибок"""
        try:
            headers = {}
            if hasattr(self.settings, 'CHROMADB_AUTH_TOKEN') and self.settings.CHROMADB_AUTH_TOKEN:
                headers["X-Chroma-Token"] = self.settings.CHROMADB_AUTH_TOKEN
            
            self.chroma_client = chromadb.HttpClient(
                host=self.settings.CHROMADB_HOST,
                port=self.settings.CHROMADB_PORT,
                ssl=False,
                headers=headers if headers else None
            )
            
            # Тестируем подключение
            self.chroma_client.heartbeat()
            logger.info("ChromaDB client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize ChromaDB client", error=str(e))
            self.chroma_client = None
    
    async def get_or_create_collection(
        self, 
        name: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Получение или создание коллекции с умным кешированием"""
        
        if not self.chroma_client:
            logger.error("ChromaDB client not initialized")
            return None
        
        # Проверяем кеш
        if name in self._collections_cache:
            try:
                # Проверяем, что коллекция все еще существует
                collection = self.chroma_client.get_collection(name)
                return collection
            except:
                # Коллекция удалена, убираем из кеша
                del self._collections_cache[name]
        
        try:
            # Пытаемся получить существующую коллекцию
            collection = self.chroma_client.get_collection(name)
            self._collections_cache[name] = collection
            logger.info("Collection retrieved from cache", name=name)
            return collection
            
        except:
            # Создаем новую коллекцию
            try:
                default_metadata = {
                    "description": f"Collection for {self.settings.SERVICE_NAME}",
                    "created_at": datetime.now().isoformat(),
                    "service": self.settings.SERVICE_NAME
                }
                
                if metadata:
                    default_metadata.update(metadata)
                
                collection = self.chroma_client.create_collection(
                    name=name,
                    metadata=default_metadata
                )
                
                self._collections_cache[name] = collection
                logger.info("New collection created", name=name, metadata=default_metadata)
                
                # Проверяем лимиты
                await self._check_collection_limits()
                
                return collection
                
            except Exception as e:
                logger.error("Failed to create collection", name=name, error=str(e))
                return None
    
    async def add_documents_safe(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str = "default",
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """Безопасное добавление документов с обработкой ошибок"""
        
        if not self.chroma_client:
            return {"error": "ChromaDB not initialized"}
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            if not collection:
                return {"error": "Failed to get or create collection"}
            
            # Подготавливаем данные
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                # Извлекаем текст
                text = doc.get('text', doc.get('content', str(doc)))
                if not text or len(text.strip()) == 0:
                    continue
                
                texts.append(text)
                
                # Очищаем метаданные от проблемных полей
                metadata = doc.get('metadata', {}).copy()
                problematic_fields = ['_type', 'id', '__class__', '__module__']
                for field in problematic_fields:
                    if field in metadata:
                        del metadata[field]
                
                # Добавляем служебные метаданные
                metadata.update({
                    "added_at": datetime.now().isoformat(),
                    "service": self.settings.SERVICE_NAME,
                    "document_hash": hashlib.md5(text.encode()).hexdigest()
                })
                
                metadatas.append(metadata)
                ids.append(doc.get('id', f"doc_{i}_{hash(text)}"))
            
            # Добавляем документы батчами
            added_count = 0
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                
                collection.add(
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                added_count += len(batch_texts)
                
                # Небольшая пауза между батчами
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
            
            logger.info(
                "Documents added successfully",
                collection=collection_name,
                added_count=added_count,
                total_documents=len(documents)
            )
            
            return {
                "success": True,
                "added_count": added_count,
                "collection": collection_name,
                "batch_size": batch_size
            }
            
        except Exception as e:
            logger.error(
                "Failed to add documents",
                collection=collection_name,
                error=str(e),
                documents_count=len(documents)
            )
            return {"error": str(e)}
    
    async def search_safe(
        self,
        query: str,
        collection_name: str = "default",
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Безопасный поиск с обработкой ошибок"""
        
        if not self.chroma_client:
            return []
        
        try:
            collection = await self.get_or_create_collection(collection_name)
            if not collection:
                return []
            
            # Выполняем поиск
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter_metadata
            )
            
            # Форматируем результаты
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'document': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'id': results['ids'][0][i] if results['ids'] and results['ids'][0] else None,
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else None
                    })
            
            logger.info(
                "Search completed successfully",
                query=query[:100] + "..." if len(query) > 100 else query,
                results_count=len(formatted_results),
                collection=collection_name
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(
                "Search failed",
                query=query[:100] + "..." if len(query) > 100 else query,
                error=str(e),
                collection=collection_name
            )
            return []
    
    async def delete_collection(self, name: str) -> Dict[str, Any]:
        """Удаление коллекции"""
        
        if not self.chroma_client:
            return {"error": "ChromaDB not initialized"}
        
        try:
            self.chroma_client.delete_collection(name)
            
            # Убираем из кеша
            if name in self._collections_cache:
                del self._collections_cache[name]
            
            logger.info("Collection deleted", name=name)
            return {"success": True, "collection": name}
            
        except Exception as e:
            logger.error("Failed to delete collection", name=name, error=str(e))
            return {"error": str(e)}
    
    async def cleanup_old_collections(self) -> Dict[str, Any]:
        """Автоматическая очистка старых коллекций"""
        
        if not self.chroma_client:
            return {"error": "ChromaDB not initialized"}
        
        try:
            collections = self.chroma_client.list_collections()
            deleted_count = 0
            
            for collection in collections:
                metadata = collection.metadata or {}
                created_at_str = metadata.get('created_at')
                
                if created_at_str:
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                        if datetime.now() - created_at > self.collection_ttl:
                            self.chroma_client.delete_collection(collection.name)
                            deleted_count += 1
                            logger.info("Old collection deleted", name=collection.name)
                    except:
                        # Если не можем распарсить дату, пропускаем
                        continue
            
            logger.info("Cleanup completed", deleted_count=deleted_count)
            return {"success": True, "deleted_count": deleted_count}
            
        except Exception as e:
            logger.error("Cleanup failed", error=str(e))
            return {"error": str(e)}
    
    async def _check_collection_limits(self):
        """Проверка лимитов коллекций"""
        
        if not self.chroma_client:
            return
        
        try:
            collections = self.chroma_client.list_collections()
            
            # Проверяем количество коллекций
            if len(collections) > self.max_collections:
                logger.warning(
                    "Too many collections",
                    current=len(collections),
                    max=self.max_collections
                )
                await self.cleanup_old_collections()
            
            # Проверяем размер коллекций
            for collection in collections:
                if collection.count() > self.max_documents_per_collection:
                    logger.warning(
                        "Collection too large",
                        name=collection.name,
                        count=collection.count(),
                        max=self.max_documents_per_collection
                    )
            
        except Exception as e:
            logger.error("Failed to check collection limits", error=str(e))
    
    async def get_collections_info(self) -> List[Dict[str, Any]]:
        """Получение информации о коллекциях"""
        
        if not self.chroma_client:
            return []
        
        try:
            collections = self.chroma_client.list_collections()
            
            result = []
            for collection in collections:
                result.append({
                    "name": collection.name,
                    "metadata": collection.metadata,
                    "count": collection.count(),
                    "created_at": collection.metadata.get('created_at') if collection.metadata else None
                })
            
            return result
            
        except Exception as e:
            logger.error("Failed to get collections info", error=str(e))
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Расширенная проверка здоровья"""
        
        if not self.chroma_client:
            return {
                "status": "unhealthy",
                "error": "ChromaDB client not initialized"
            }
        
        try:
            # Проверяем подключение
            self.chroma_client.heartbeat()
            
            # Получаем информацию о коллекциях
            collections_info = await self.get_collections_info()
            
            # Проверяем, нужна ли очистка
            needs_cleanup = datetime.now() - self._last_cleanup > self._cleanup_interval
            
            return {
                "status": "healthy",
                "chromadb_connected": True,
                "collections_count": len(collections_info),
                "collections_info": collections_info,
                "needs_cleanup": needs_cleanup,
                "service": self.settings.SERVICE_NAME
            }
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": self.settings.SERVICE_NAME
            }
    
    async def close(self):
        """Закрытие соединения"""
        if self.chroma_client:
            try:
                self.chroma_client.close()
                self._collections_cache.clear()
                logger.info("ChromaDB Manager connection closed")
            except Exception as e:
                logger.error("Error closing ChromaDB Manager", error=str(e))

# Глобальный экземпляр
_chromadb_manager: Optional[ChromaDBManager] = None

def get_chromadb_manager() -> ChromaDBManager:
    """Получение глобального экземпляра ChromaDB менеджера"""
    global _chromadb_manager
    if _chromadb_manager is None:
        _chromadb_manager = ChromaDBManager()
    return _chromadb_manager

async def close_chromadb_manager():
    """Закрытие ChromaDB менеджера"""
    global _chromadb_manager
    if _chromadb_manager:
        await _chromadb_manager.close()
        _chromadb_manager = None 