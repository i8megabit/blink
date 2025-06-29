"""
🔍 Профессиональный RAG менеджер для reLink
Оптимизирован для production с ChromaDB
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
import structlog
from dataclasses import dataclass
import hashlib
import json
from datetime import datetime

from .config import get_settings

logger = structlog.get_logger()

@dataclass
class Document:
    """Структура документа для RAG"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class RAGManager:
    """Профессиональный RAG менеджер"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[chromadb.Client] = None
        self.collections: Dict[str, chromadb.Collection] = {}
        self._initialize_client()
    
    def _initialize_client(self):
        """Инициализация ChromaDB клиента"""
        try:
            # Production-ready конфигурация
            self.client = chromadb.HttpClient(
                host=self.settings.CHROMADB_HOST,
                port=self.settings.CHROMADB_PORT,
                ssl=False,
                headers={
                    "X-Chroma-Token": self.settings.CHROMADB_AUTH_TOKEN
                } if self.settings.CHROMADB_AUTH_TOKEN else {}
            )
            logger.info("RAG Manager initialized", 
                       host=self.settings.CHROMADB_HOST,
                       port=self.settings.CHROMADB_PORT)
        except Exception as e:
            logger.error("Failed to initialize RAG Manager", error=str(e))
            raise
    
    async def create_collection(
        self, 
        name: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> chromadb.Collection:
        """Создание коллекции с метаданными"""
        
        if not self.client:
            raise RuntimeError("ChromaDB client not initialized")
        
        try:
            # Проверяем существование коллекции
            try:
                collection = self.client.get_collection(name)
                logger.info(f"Collection {name} already exists")
            except:
                # Создаем новую коллекцию
                collection = self.client.create_collection(
                    name=name,
                    metadata=metadata or {
                        "description": f"Collection for {self.settings.SERVICE_NAME}",
                        "created_at": datetime.utcnow().isoformat(),
                        "version": "1.0.0"
                    }
                )
                logger.info(f"Collection {name} created successfully")
            
            self.collections[name] = collection
            return collection
            
        except Exception as e:
            logger.error(f"Failed to create collection {name}", error=str(e))
            raise
    
    async def add_documents(
        self,
        documents: List[Document],
        collection_name: str = "default"
    ) -> Dict[str, Any]:
        """Добавление документов с оптимизацией"""
        
        if not documents:
            return {"success": True, "added_count": 0}
        
        try:
            collection = await self.create_collection(collection_name)
            
            # Подготавливаем данные
            ids = []
            texts = []
            metadatas = []
            
            for doc in documents:
                # Генерируем ID если не указан
                if not doc.id:
                    doc.id = hashlib.md5(
                        (doc.content + str(doc.metadata)).encode()
                    ).hexdigest()
                
                ids.append(doc.id)
                texts.append(doc.content)
                
                # Обогащаем метаданные
                enriched_metadata = {
                    **doc.metadata,
                    "created_at": doc.created_at.isoformat(),
                    "service": self.settings.SERVICE_NAME,
                    "content_length": len(doc.content),
                    "content_hash": hashlib.md5(doc.content.encode()).hexdigest()
                }
                metadatas.append(enriched_metadata)
            
            # Добавляем документы батчами для оптимизации
            batch_size = 100
            total_added = 0
            
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_texts = texts[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                
                collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
                total_added += len(batch_ids)
                
                logger.info(f"Added batch {i//batch_size + 1}", 
                           batch_size=len(batch_ids),
                           total_added=total_added)
            
            return {
                "success": True,
                "added_count": total_added,
                "collection": collection_name,
                "batch_count": (len(ids) + batch_size - 1) // batch_size
            }
            
        except Exception as e:
            logger.error("Failed to add documents", error=str(e))
            return {"error": str(e)}
    
    async def search(
        self,
        query: str,
        collection_name: str = "default",
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Поиск с фильтрацией и ранжированием"""
        
        try:
            collection = await self.create_collection(collection_name)
            
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
                        'id': results['ids'][0][i],
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else None,
                        'relevance_score': 1.0 - (results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0)
                    })
            
            logger.info(
                "RAG search completed",
                query=query[:100] + "..." if len(query) > 100 else query,
                results_count=len(formatted_results),
                collection=collection_name
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error("RAG search failed", error=str(e))
            return []
    
    async def delete_documents(
        self,
        document_ids: List[str],
        collection_name: str = "default"
    ) -> Dict[str, Any]:
        """Удаление документов"""
        
        try:
            collection = await self.create_collection(collection_name)
            collection.delete(ids=document_ids)
            
            logger.info(f"Deleted {len(document_ids)} documents", 
                       collection=collection_name)
            
            return {
                "success": True,
                "deleted_count": len(document_ids),
                "collection": collection_name
            }
            
        except Exception as e:
            logger.error("Failed to delete documents", error=str(e))
            return {"error": str(e)}
    
    async def get_collection_stats(self, collection_name: str = "default") -> Dict[str, Any]:
        """Получение статистики коллекции"""
        
        try:
            collection = await self.create_collection(collection_name)
            
            # Получаем базовую информацию
            count = collection.count()
            
            # Анализируем метаданные
            all_metadata = collection.get()['metadatas']
            
            stats = {
                "collection_name": collection_name,
                "document_count": count,
                "metadata_fields": set(),
                "services": set(),
                "date_range": {"min": None, "max": None}
            }
            
            if all_metadata:
                for metadata in all_metadata:
                    if metadata:
                        stats["metadata_fields"].update(metadata.keys())
                        if "service" in metadata:
                            stats["services"].add(metadata["service"])
                        if "created_at" in metadata:
                            try:
                                date = datetime.fromisoformat(metadata["created_at"])
                                if stats["date_range"]["min"] is None or date < stats["date_range"]["min"]:
                                    stats["date_range"]["min"] = date
                                if stats["date_range"]["max"] is None or date > stats["date_range"]["max"]:
                                    stats["date_range"]["max"] = date
                            except:
                                pass
            
            # Преобразуем множества в списки для JSON сериализации
            stats["metadata_fields"] = list(stats["metadata_fields"])
            stats["services"] = list(stats["services"])
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья RAG системы"""
        
        try:
            if not self.client:
                return {"status": "unhealthy", "error": "Client not initialized"}
            
            # Проверяем подключение
            collections = self.client.list_collections()
            
            # Проверяем основную коллекцию
            default_collection = await self.create_collection("default")
            count = default_collection.count()
            
            return {
                "status": "healthy",
                "chromadb_connected": True,
                "collections_count": len(collections),
                "default_collection_count": count,
                "service": self.settings.SERVICE_NAME
            }
            
        except Exception as e:
            logger.error("RAG health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": self.settings.SERVICE_NAME
            }

# Глобальный экземпляр
_rag_manager: Optional[RAGManager] = None

def get_rag_manager() -> RAGManager:
    """Получение глобального экземпляра RAG менеджера"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager()
    return _rag_manager 