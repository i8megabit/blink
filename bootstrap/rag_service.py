"""
🔍 Интеграция с RAG сервисом для всех микросервисов
"""

from typing import List, Dict, Any, Optional
import httpx
import structlog
import chromadb
from chromadb.config import Settings

from .config import get_settings

logger = structlog.get_logger()

# Глобальный экземпляр RAG сервиса
_rag_service: Optional['RAGService'] = None

class RAGService:
    """Нативная интеграция с RAG сервисом через ChromaDB"""
    
    def __init__(self):
        self.settings = get_settings()
        self.chroma_client: Optional[chromadb.Client] = None
        self._initialize_chromadb()
        
        logger.info("RAG Service initialized with ChromaDB")
    
    def _initialize_chromadb(self):
        """Инициализация ChromaDB клиента"""
        try:
            # Используем HTTP клиент для подключения к серверу ChromaDB
            self.chroma_client = chromadb.HttpClient(
                host=self.settings.CHROMADB_HOST,
                port=self.settings.CHROMADB_PORT
            )
            logger.info("ChromaDB client initialized", 
                       host=self.settings.CHROMADB_HOST, 
                       port=self.settings.CHROMADB_PORT)
        except Exception as e:
            logger.error("Failed to initialize ChromaDB client", error=str(e))
            self.chroma_client = None
    
    async def search(
        self, 
        query: str, 
        collection: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Поиск в векторной базе данных"""
        
        if not self.chroma_client:
            logger.error("ChromaDB client not initialized")
            return []
        
        try:
            # Получаем коллекцию
            chroma_collection = self.chroma_client.get_collection(collection)
            
            # Выполняем поиск
            results = chroma_collection.query(
                query_texts=[query],
                n_results=top_k
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
                "RAG search completed",
                query=query[:100] + "..." if len(query) > 100 else query,
                results_count=len(formatted_results),
                collection=collection
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(
                "RAG search error",
                error=str(e),
                query=query[:100] + "..." if len(query) > 100 else query
            )
            return []
    
    async def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        collection: str = "default"
    ) -> Dict[str, Any]:
        """Добавление документов в векторную БД"""
        
        if not self.chroma_client:
            logger.error("ChromaDB client not initialized")
            return {"error": "ChromaDB not initialized"}
        
        try:
            # Получаем или создаем коллекцию
            try:
                chroma_collection = self.chroma_client.get_collection(collection)
            except:
                chroma_collection = self.chroma_client.create_collection(
                    name=collection,
                    metadata={"description": f"Collection for {self.settings.SERVICE_NAME}"}
                )
            
            # Подготавливаем данные
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                texts.append(doc.get('text', doc.get('content', str(doc))))
                metadatas.append(doc.get('metadata', {}))
                ids.append(doc.get('id', f"doc_{i}_{hash(str(doc))}"))
            
            # Добавляем документы
            chroma_collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(
                "Documents added to RAG",
                documents_count=len(documents),
                collection=collection
            )
            
            return {
                "success": True,
                "added_count": len(documents),
                "collection": collection
            }
            
        except Exception as e:
            logger.error(
                "RAG add documents error",
                error=str(e),
                documents_count=len(documents)
            )
            return {"error": str(e)}
    
    async def delete_documents(
        self,
        document_ids: List[str],
        collection: str = "default"
    ) -> Dict[str, Any]:
        """Удаление документов из векторной БД"""
        
        if not self.chroma_client:
            logger.error("ChromaDB client not initialized")
            return {"error": "ChromaDB not initialized"}
        
        try:
            chroma_collection = self.chroma_client.get_collection(collection)
            
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
    
    async def get_collections(self) -> List[Dict[str, Any]]:
        """Получение списка коллекций"""
        
        if not self.chroma_client:
            logger.error("ChromaDB client not initialized")
            return []
        
        try:
            collections = self.chroma_client.list_collections()
            
            result = []
            for collection in collections:
                result.append({
                    "name": collection.name,
                    "metadata": collection.metadata,
                    "count": collection.count()
                })
            
            logger.info("RAG collections retrieved", count=len(result))
            
            return result
            
        except Exception as e:
            logger.error("Failed to get RAG collections", error=str(e))
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья RAG сервиса"""
        
        if not self.chroma_client:
            return {
                "status": "unhealthy",
                "error": "ChromaDB client not initialized"
            }
        
        try:
            # Проверяем подключение
            collections = self.chroma_client.list_collections()
            
            return {
                "status": "healthy",
                "chromadb_connected": True,
                "collections_count": len(collections),
                "service": self.settings.SERVICE_NAME
            }
            
        except Exception as e:
            logger.error("RAG health check failed", error=str(e))
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
                logger.info("RAG Service connection closed")
            except Exception as e:
                logger.error("Error closing RAG service", error=str(e))

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