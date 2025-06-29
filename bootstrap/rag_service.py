"""
🔍 Интеграция с RAG сервисом для всех микросервисов
Использует расширенный ChromaDB менеджер с автоматическим управлением
"""

from typing import List, Dict, Any, Optional
import httpx
import structlog

from .config import get_settings
from .rag_manager import get_chromadb_manager

logger = structlog.get_logger()

# Глобальный экземпляр RAG сервиса
_rag_service: Optional['RAGService'] = None

class RAGService:
    """Нативная интеграция с RAG сервисом через расширенный ChromaDB менеджер"""
    
    def __init__(self):
        self.settings = get_settings()
        self.chromadb_manager = get_chromadb_manager()
        
        logger.info("RAG Service initialized with ChromaDB Manager")
    
    async def search(
        self, 
        query: str, 
        collection: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Поиск в векторной базе данных"""
        
        return await self.chromadb_manager.search_safe(
            query=query,
            collection_name=collection,
            top_k=top_k
        )
    
    async def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        collection: str = "default"
    ) -> Dict[str, Any]:
        """Добавление документов в векторную БД"""
        
        return await self.chromadb_manager.add_documents_safe(
            documents=documents,
            collection_name=collection
        )
    
    async def delete_documents(
        self,
        document_ids: List[str],
        collection: str = "default"
    ) -> Dict[str, Any]:
        """Удаление документов из векторной БД"""
        
        if not self.chromadb_manager.chroma_client:
            return {"error": "ChromaDB not initialized"}
        
        try:
            chroma_collection = await self.chromadb_manager.get_or_create_collection(collection)
            if not chroma_collection:
                return {"error": "Collection not found"}
            
            # Удаляем документы
            chroma_collection.delete(ids=document_ids)
            
            logger.info(
                "Documents deleted from RAG",
                deleted_count=len(document_ids),
                collection=collection
            )
            
            return {
                "success": True,
                "deleted_count": len(document_ids),
                "collection": collection
            }
            
        except Exception as e:
            logger.error(
                "RAG delete documents error",
                error=str(e),
                document_ids=document_ids
            )
            return {"error": str(e)}
    
    async def delete_collection(self, collection: str) -> Dict[str, Any]:
        """Удаление коллекции"""
        
        return await self.chromadb_manager.delete_collection(collection)
    
    async def cleanup_old_collections(self) -> Dict[str, Any]:
        """Автоматическая очистка старых коллекций"""
        
        return await self.chromadb_manager.cleanup_old_collections()
    
    async def get_collections(self) -> List[Dict[str, Any]]:
        """Получение списка коллекций"""
        
        return await self.chromadb_manager.get_collections_info()
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья RAG сервиса"""
        
        return await self.chromadb_manager.health_check()
    
    async def close(self):
        """Закрытие соединения"""
        await self.chromadb_manager.close()

def get_rag_service() -> RAGService:
    """Получение глобального экземпляра RAG сервиса"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

async def close_rag_service():
    """Закрытие RAG сервиса"""
    global _rag_service
    if _rag_service:
        await _rag_service.close()
        _rag_service = None 