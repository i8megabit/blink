"""
🔍 Интеграция с RAG сервисом для всех микросервисов
"""

from typing import List, Dict, Any, Optional
import httpx
import structlog

from .config import get_settings

logger = structlog.get_logger()

# Глобальный экземпляр RAG сервиса
_rag_service: Optional['RAGService'] = None

class RAGService:
    """Нативная интеграция с RAG сервисом"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.RAG_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("RAG Service initialized", base_url=self.base_url)
    
    async def search(
        self, 
        query: str, 
        collection: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Поиск в векторной базе данных"""
        
        try:
            payload = {
                "query": query,
                "collection": collection,
                "top_k": top_k,
                "service": self.settings.SERVICE_NAME
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/search",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "RAG search completed",
                query=query[:100] + "..." if len(query) > 100 else query,
                results_count=len(result.get("results", [])),
                collection=collection
            )
            
            return result.get("results", [])
            
        except Exception as e:
            logger.error(
                "RAG search error",
                error=str(e),
                query=query[:100] + "..." if len(query) > 100 else query
            )
            raise
    
    async def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        collection: str = "default"
    ) -> Dict[str, Any]:
        """Добавление документов в векторную БД"""
        
        try:
            payload = {
                "documents": documents,
                "collection": collection,
                "service": self.settings.SERVICE_NAME
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/add",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "Documents added to RAG",
                documents_count=len(documents),
                collection=collection
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "RAG add documents error",
                error=str(e),
                documents_count=len(documents)
            )
            raise
    
    async def delete_documents(
        self,
        document_ids: List[str],
        collection: str = "default"
    ) -> Dict[str, Any]:
        """Удаление документов из векторной БД"""
        
        try:
            payload = {
                "document_ids": document_ids,
                "collection": collection,
                "service": self.settings.SERVICE_NAME
            }
            
            response = await self.client.delete(
                f"{self.base_url}/api/v1/delete",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "Documents deleted from RAG",
                deleted_count=len(document_ids),
                collection=collection
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "RAG delete documents error",
                error=str(e),
                document_ids=document_ids
            )
            raise
    
    async def get_collections(self) -> List[Dict[str, Any]]:
        """Получение списка коллекций"""
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/collections")
            response.raise_for_status()
            
            result = response.json()
            
            logger.info("RAG collections retrieved", count=len(result.get("collections", [])))
            
            return result.get("collections", [])
            
        except Exception as e:
            logger.error("Failed to get RAG collections", error=str(e))
            raise
    
    async def close(self):
        """Закрытие соединения"""
        await self.client.aclose()
        logger.info("RAG Service connection closed")

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