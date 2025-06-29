"""
🧠 RAG (Retrieval-Augmented Generation) сервис
Интеграция с векторными базами данных для улучшения ответов LLM
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import re
from dataclasses import dataclass

from .utils import EmbeddingManager, OllamaClient, CacheManager
from .models import RAGDocument, RAGQuery, RAGResponse
from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Результат поиска в RAG"""
    document: str
    doc_metadata: Dict[str, Any]
    similarity: float
    source: str
    chunk_id: str


class RAGService:
    """Сервис для работы с RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self):
        self.embedding_manager: Optional[EmbeddingManager] = None
        self.ollama_client: Optional[OllamaClient] = None
        self.cache_manager: Optional[CacheManager] = None
        self.collection_name: str = "relink_documents"
        self.chunk_size: int = 1000
        self.chunk_overlap: int = 200
        self.max_context_length: int = 4000
        self.top_k_results: int = 5
        self.similarity_threshold: float = 0.7
    
    async def initialize(self, embedding_manager: EmbeddingManager, 
                        ollama_client: OllamaClient, cache_manager: CacheManager):
        """Инициализация RAG сервиса"""
        self.embedding_manager = embedding_manager
        self.ollama_client = ollama_client
        self.cache_manager = cache_manager
        
        # Создание коллекции в ChromaDB
        try:
            if self.embedding_manager.chroma_client:
                self.embedding_manager.chroma_client.get_or_create_collection(
                    self.collection_name,
                    metadata={"description": "reLink documents for RAG"}
                )
                logger.info(f"RAG collection '{self.collection_name}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG collection: {e}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """Разбиение текста на чанки"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Если это не последний чанк, ищем хорошую точку разрыва
            if end < len(text):
                # Ищем ближайший конец предложения или абзаца
                for i in range(end, max(start + self.chunk_size - 100, start), -1):
                    if text[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        # Простая реализация - в продакшене использовать более сложные алгоритмы
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Удаление стоп-слов
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Подсчет частоты и выбор топ-10
        from collections import Counter
        keyword_counts = Counter(keywords)
        return [word for word, count in keyword_counts.most_common(10)]
    
    async def add_document(self, title: str, content: str, source: str = None,
                          document_type: str = None, tags: List[str] = None) -> str:
        """Добавление документа в RAG систему"""
        try:
            # Разбиение на чанки
            chunks = self.chunk_text(content)
            
            # Извлечение ключевых слов
            keywords = self.extract_keywords(content)
            
            # Подготовка метаданных
            doc_metadata_list = []
            for i, chunk in enumerate(chunks):
                doc_metadata = {
                    "title": title,
                    "source": source or "unknown",
                    "document_type": document_type or "text",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "keywords": keywords,
                    "tags": tags or [],
                    "created_at": datetime.utcnow().isoformat()
                }
                doc_metadata_list.append(doc_metadata)
            
            # Генерация ID для чанков
            chunk_ids = [f"{title}_{i}_{hash(chunk) % 10000}" for i, chunk in enumerate(chunks)]
            
            # Добавление в векторную базу
            await self.embedding_manager.add_documents(
                self.collection_name,
                chunks,
                doc_metadata_list,
                chunk_ids
            )
            
            # Кэширование документа
            if self.cache_manager:
                doc_key = f"doc:{hash(title + content) % 10000}"
                await self.cache_manager.set(
                    "documents",
                    {
                        "title": title,
                        "content": content,
                        "source": source,
                        "document_type": document_type,
                        "tags": tags,
                        "chunks_count": len(chunks),
                        "keywords": keywords
                    },
                    3600,  # 1 час
                    doc_key
                )
            
            logger.info(f"Added document '{title}' with {len(chunks)} chunks")
            return f"Document added with {len(chunks)} chunks"
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    async def search_documents(self, query: str, top_k: int = None) -> List[SearchResult]:
        """Поиск релевантных документов"""
        try:
            top_k = top_k or self.top_k_results
            
            # Поиск в векторной базе
            results = await self.embedding_manager.search_similar(
                self.collection_name,
                query,
                top_k,
                self.similarity_threshold
            )
            
            # Преобразование в SearchResult
            search_results = []
            for result in results:
                search_result = SearchResult(
                    document=result['document'],
                    doc_metadata=result['metadata'],
                    similarity=result['similarity'],
                    source=result['metadata'].get('source', 'unknown'),
                    chunk_id=result['id']
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def build_context(self, search_results: List[SearchResult], max_length: int = None) -> str:
        """Построение контекста из найденных документов"""
        max_length = max_length or self.max_context_length
        
        context_parts = []
        current_length = 0
        
        for result in search_results:
            # Добавляем метаданные
            metadata_text = f"[Source: {result.source}, Similarity: {result.similarity:.3f}]"
            
            # Формируем текст чанка
            chunk_text = f"{metadata_text}\n{result.document}\n\n"
            
            # Проверяем, не превысим ли лимит
            if current_length + len(chunk_text) > max_length:
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "".join(context_parts).strip()
    
    async def generate_response(self, query: str, context: str, 
                              model: str = None) -> str:
        """Генерация ответа с использованием контекста"""
        try:
            model = model or settings.ollama.default_model
            
            # Формирование промпта
            system_prompt = settings.rag.system_prompt
            query_template = settings.rag.query_template
            
            prompt = query_template.format(
                context=context,
                question=query
            )
            
            # Генерация ответа через Ollama
            response = await self.ollama_client.generate(
                model=model,
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.get('response', 'No response generated')
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    async def query(self, query: str, model: str = None, 
                   top_k: int = None, include_sources: bool = True) -> RAGResponse:
        """Основной метод для выполнения RAG запроса"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Поиск релевантных документов
            search_results = await self.search_documents(query, top_k)
            
            if not search_results:
                return RAGResponse(
                    query=query,
                    answer="No relevant documents found for your query.",
                    sources=[],
                    context="",
                    processing_time=asyncio.get_event_loop().time() - start_time
                )
            
            # Построение контекста
            context = self.build_context(search_results)
            
            # Генерация ответа
            answer = await self.generate_response(query, context, model)
            
            # Подготовка источников
            sources = []
            if include_sources:
                for result in search_results:
                    source = {
                        "title": result.doc_metadata.get("title", "Unknown"),
                        "source": result.source,
                        "similarity": result.similarity,
                        "chunk_id": result.chunk_id,
                        "document_type": result.doc_metadata.get("document_type", "text")
                    }
                    sources.append(source)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return RAGResponse(
                query=query,
                answer=answer,
                sources=sources,
                context=context,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return RAGResponse(
                query=query,
                answer=f"Error processing query: {str(e)}",
                sources=[],
                context="",
                processing_time=asyncio.get_event_loop().time() - start_time
            )
    
    async def batch_query(self, queries: List[str], model: str = None) -> List[RAGResponse]:
        """Пакетная обработка запросов"""
        tasks = [self.query(query, model) for query in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """Получение статистики документов"""
        try:
            if not self.embedding_manager.chroma_client:
                return {"error": "ChromaDB not initialized"}
            
            collection = self.embedding_manager.chroma_client.get_collection(self.collection_name)
            
            # Получение всех документов для анализа
            results = collection.get()
            
            if not results['documents']:
                return {
                    "total_documents": 0,
                    "total_chunks": 0,
                    "sources": [],
                    "document_types": []
                }
            
            # Анализ метаданных
            sources = set()
            document_types = set()
            titles = set()
            
            # ChromaDB возвращает метаданные в поле 'metadatas'
            if 'metadatas' in results and results['metadatas']:
                for metadata_list in results['metadatas']:
                    for metadata in metadata_list:
                        if metadata:
                            sources.add(metadata.get('source', 'unknown'))
                            document_types.add(metadata.get('document_type', 'text'))
                            titles.add(metadata.get('title', 'unknown'))
            
            return {
                "total_documents": len(titles),
                "total_chunks": len(results['documents']),
                "sources": list(sources),
                "document_types": list(document_types),
                "titles": list(titles)[:10]  # Первые 10 заголовков
            }
            
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {"error": str(e)}
    
    async def delete_document(self, title: str) -> bool:
        """Удаление документа из RAG системы"""
        try:
            if not self.embedding_manager.chroma_client:
                return False
            
            collection = self.embedding_manager.chroma_client.get_collection(self.collection_name)
            
            # Поиск чанков документа
            results = collection.get(
                where={"title": title}
            )
            
            if results['ids']:
                # Удаление чанков
                collection.delete(ids=results['ids'])
                logger.info(f"Deleted document '{title}' with {len(results['ids'])} chunks")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def update_document(self, title: str, new_content: str, 
                            source: str = None, document_type: str = None,
                            tags: List[str] = None) -> bool:
        """Обновление документа в RAG системе"""
        try:
            # Удаление старого документа
            await self.delete_document(title)
            
            # Добавление нового документа
            await self.add_document(title, new_content, source, document_type, tags)
            
            logger.info(f"Updated document '{title}'")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    async def search_by_keywords(self, keywords: List[str], top_k: int = 10) -> List[SearchResult]:
        """Поиск документов по ключевым словам"""
        try:
            # Создание запроса из ключевых слов
            query = " ".join(keywords)
            
            # Поиск документов
            search_results = await self.search_documents(query, top_k)
            
            # Фильтрация по ключевым словам
            filtered_results = []
            for result in search_results:
                result_keywords = result.doc_metadata.get('keywords', [])
                if any(keyword.lower() in [kw.lower() for kw in result_keywords] 
                      for keyword in keywords):
                    filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching by keywords: {e}")
            return []
    
    async def get_similar_documents(self, document_id: str, top_k: int = 5) -> List[SearchResult]:
        """Поиск похожих документов"""
        try:
            if not self.embedding_manager.chroma_client:
                return []
            
            collection = self.embedding_manager.chroma_client.get_collection(self.collection_name)
            
            # Получение эмбеддинга документа
            results = collection.get(ids=[document_id])
            
            if not results['embeddings']:
                return []
            
            # Поиск похожих документов
            similar_results = collection.query(
                query_embeddings=results['embeddings'],
                n_results=top_k + 1  # +1 чтобы исключить сам документ
            )
            
            # Преобразование результатов
            search_results = []
            for i, distance in enumerate(similar_results['distances'][0]):
                if similar_results['ids'][0][i] != document_id:  # Исключаем сам документ
                    similarity = 1 - distance
                    search_result = SearchResult(
                        document=similar_results['documents'][0][i],
                        doc_metadata=similar_results['metadatas'][0][i],
                        similarity=similarity,
                        source=similar_results['metadatas'][0][i].get('source', 'unknown'),
                        chunk_id=similar_results['ids'][0][i]
                    )
                    search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error getting similar documents: {e}")
            return [] 