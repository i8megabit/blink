"""
Продвинутая база знаний для RAG системы
Интеллектуальное хранение и поиск рекомендаций с метаданными
"""

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
import numpy as np

from .types import LLMResponse, RecommendationType
from ..config import settings


class CollectionType(Enum):
    """Типы коллекций в базе знаний"""
    SEO_RECOMMENDATIONS = "seo_recommendations"
    DOMAIN_ANALYSIS = "domain_analysis"
    USER_FEEDBACK = "user_feedback"
    PERFORMANCE_METRICS = "performance_metrics"
    CONTENT_OPTIMIZATION = "content_optimization"
    TECHNICAL_SEO = "technical_seo"


@dataclass
class RecommendationMetadata:
    """Метаданные для рекомендаций"""
    domain: str
    content_type: str
    quality_score: float
    user_satisfaction: float
    performance_metrics: Dict[str, Any]
    created_at: str
    updated_at: str
    tags: List[str]
    context_hash: str
    model_used: str
    generation_time: float
    token_count: int
    relevance_score: float
    uniqueness_score: float
    actionability_score: float
    implementation_difficulty: str  # easy, medium, hard
    estimated_impact: str  # low, medium, high
    category: str  # technical, content, user_experience, etc.


@dataclass
class SearchContext:
    """Контекст для поиска"""
    domain: str
    content_type: str
    user_preferences: Dict[str, Any]
    current_metrics: Dict[str, Any]
    target_audience: str
    business_goals: List[str]
    technical_constraints: List[str]


class AdvancedKnowledgeBase:
    """Продвинутая база знаний с метаданными и связями"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./data/chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collections = {}
        self._initialize_collections()
        
    def _initialize_collections(self):
        """Инициализация коллекций"""
        for collection_type in CollectionType:
            try:
                collection = self.client.get_collection(
                    name=collection_type.value,
                    embedding_function=self._get_embedding_function()
                )
                self.collections[collection_type.value] = collection
            except:
                # Создаем новую коллекцию если не существует
                collection = self.client.create_collection(
                    name=collection_type.value,
                    embedding_function=self._get_embedding_function(),
                    metadata={"description": f"Collection for {collection_type.value}"}
                )
                self.collections[collection_type.value] = collection
    
    def _get_embedding_function(self):
        """Получение функции эмбеддинга"""
        # Используем OpenAI эмбеддинги для лучшего качества
        try:
            import openai
            return chromadb.utils.embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.OPENAI_API_KEY,
                model_name="text-embedding-3-small"
            )
        except:
            # Fallback на локальные эмбеддинги
            return chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
    
    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Создание хеша контекста для дедупликации"""
        context_str = json.dumps(context, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(context_str.encode()).hexdigest()
    
    async def store_recommendation(
        self, 
        recommendation: Dict[str, Any], 
        metadata: Dict[str, Any],
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> str:
        """Сохранение рекомендации с полными метаданными с проверкой уникальности"""
        
        # Подготавливаем контент для сохранения
        content = recommendation.get("content", "")
        if isinstance(content, list):
            content = "\n".join(content)
        domain = metadata.get("domain", "")

        # Проверка на уникальность: ищем существующую рекомендацию с тем же контентом и доменом
        collection = self.collections[collection_type.value]
        existing = collection.get(where={"domain": domain})
        if existing and "documents" in existing and existing["documents"]:
            for i, doc in enumerate(existing["documents"][0]):
                if doc.strip() == content.strip():
                    # Уже есть такая рекомендация, возвращаем её id
                    return existing["ids"][i]

        # Создаем полные метаданные
        full_metadata = RecommendationMetadata(
            domain=domain,
            content_type=metadata.get("content_type", ""),
            quality_score=metadata.get("quality_score", 0.0),
            user_satisfaction=metadata.get("user_satisfaction", 0.0),
            performance_metrics=metadata.get("performance_metrics", {}),
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            tags=metadata.get("tags", []),
            context_hash=self._hash_context(metadata.get("context", {})),
            model_used=metadata.get("model_used", "unknown"),
            generation_time=metadata.get("generation_time", 0.0),
            token_count=metadata.get("token_count", 0),
            relevance_score=metadata.get("relevance_score", 0.0),
            uniqueness_score=metadata.get("uniqueness_score", 0.0),
            actionability_score=metadata.get("actionability_score", 0.0),
            implementation_difficulty=metadata.get("implementation_difficulty", "medium"),
            estimated_impact=metadata.get("estimated_impact", "medium"),
            category=metadata.get("category", "general")
        )
        
        # Получаем эмбеддинг
        embedding = await self._get_embedding(content)
        
        # Сохраняем в коллекцию
        result = collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[asdict(full_metadata)],
            ids=[f"rec_{datetime.now().timestamp()}_{hash(content)}"]
        )
        
        return result["ids"][0]
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Получение эмбеддинга для текста"""
        # Простая реализация - в продакшене используйте OpenAI или другие сервисы
        # Здесь используем базовый эмбеддинг через ChromaDB
        return [0.0] * 384  # Placeholder
    
    async def search_recommendations(
        self,
        query: str,
        context: SearchContext,
        limit: int = 10,
        min_quality_score: float = 0.5,
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> List[Dict[str, Any]]:
        """Поиск релевантных рекомендаций с контекстом"""
        
        # Создаем контекстуальный запрос
        contextual_query = self._build_contextual_query(query, context)
        
        # Получаем эмбеддинг запроса
        query_embedding = await self._get_embedding(contextual_query)
        
        # Поиск в коллекции
        collection = self.collections[collection_type.value]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit * 2,  # Больше результатов для фильтрации
            where={
                "domain": context.domain,
                "content_type": context.content_type,
                "quality_score": {"$gte": min_quality_score}
            }
        )
        
        # Фильтрация и ранжирование
        filtered_results = self._filter_and_rank_results(
            results, query, context, limit
        )
        
        return filtered_results
    
    def _build_contextual_query(self, query: str, context: SearchContext) -> str:
        """Создание контекстуального запроса"""
        contextual_query = f"""
        Query: {query}
        Domain: {context.domain}
        Content Type: {context.content_type}
        Target Audience: {context.target_audience}
        Business Goals: {', '.join(context.business_goals)}
        Technical Constraints: {', '.join(context.technical_constraints)}
        Current Metrics: {json.dumps(context.current_metrics, ensure_ascii=False)}
        """
        return contextual_query
    
    def _filter_and_rank_results(
        self,
        results: Dict[str, Any],
        query: str,
        context: SearchContext,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Фильтрация и ранжирование результатов"""
        
        if not results["documents"]:
            return []
        
        # Создаем список результатов с метаданными
        ranked_results = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i] if results["distances"] else 0.0
            
            # Вычисляем общий скор
            relevance_score = 1.0 - distance  # Инвертируем расстояние
            quality_score = metadata.get("quality_score", 0.0)
            user_satisfaction = metadata.get("user_satisfaction", 0.0)
            
            # Взвешенный скор
            total_score = (
                relevance_score * 0.4 +
                quality_score * 0.3 +
                user_satisfaction * 0.3
            )
            
            ranked_results.append({
                "content": doc,
                "metadata": metadata,
                "relevance_score": relevance_score,
                "quality_score": quality_score,
                "user_satisfaction": user_satisfaction,
                "total_score": total_score,
                "distance": distance
            })
        
        # Сортируем по общему скору
        ranked_results.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Возвращаем топ результаты
        return ranked_results[:limit]
    
    async def update_recommendation_metadata(
        self,
        recommendation_id: str,
        updates: Dict[str, Any],
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> bool:
        """Обновление метаданных рекомендации"""
        try:
            collection = self.collections[collection_type.value]
            
            # Получаем текущие метаданные
            current = collection.get(ids=[recommendation_id])
            if not current["metadatas"]:
                return False
            
            # Обновляем метаданные
            metadata = current["metadatas"][0]
            metadata.update(updates)
            metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Обновляем в коллекции
            collection.update(
                ids=[recommendation_id],
                metadatas=[metadata]
            )
            
            return True
        except Exception as e:
            print(f"Error updating recommendation metadata: {e}")
            return False
    
    async def get_recommendation_statistics(
        self,
        domain: Optional[str] = None,
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> Dict[str, Any]:
        """Получение статистики по рекомендациям"""
        
        collection = self.collections[collection_type.value]
        
        # Получаем все метаданные
        where_filter = {}
        if domain:
            where_filter["domain"] = domain
        
        results = collection.get(where=where_filter)
        
        if not results["metadatas"]:
            return {
                "total_recommendations": 0,
                "average_quality_score": 0.0,
                "average_user_satisfaction": 0.0,
                "top_categories": [],
                "recent_recommendations": 0
            }
        
        # Анализируем статистику
        quality_scores = [m.get("quality_score", 0.0) for m in results["metadatas"]]
        satisfaction_scores = [m.get("user_satisfaction", 0.0) for m in results["metadatas"]]
        categories = [m.get("category", "unknown") for m in results["metadatas"]]
        
        # Подсчитываем категории
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Сортируем категории по популярности
        top_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Подсчитываем недавние рекомендации (последние 7 дней)
        week_ago = datetime.now(timezone.utc).timestamp() - 7 * 24 * 3600
        recent_count = sum(
            1 for m in results["metadatas"]
            if datetime.fromisoformat(m.get("created_at", "1970-01-01")).timestamp() > week_ago
        )
        
        return {
            "total_recommendations": len(results["metadatas"]),
            "average_quality_score": np.mean(quality_scores) if quality_scores else 0.0,
            "average_user_satisfaction": np.mean(satisfaction_scores) if satisfaction_scores else 0.0,
            "top_categories": top_categories,
            "recent_recommendations": recent_count,
            "quality_score_distribution": {
                "excellent": sum(1 for s in quality_scores if s >= 0.9),
                "good": sum(1 for s in quality_scores if 0.7 <= s < 0.9),
                "average": sum(1 for s in quality_scores if 0.5 <= s < 0.7),
                "poor": sum(1 for s in quality_scores if s < 0.5)
            }
        }
    
    async def delete_recommendation(
        self,
        recommendation_id: str,
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> bool:
        """Удаление рекомендации"""
        try:
            collection = self.collections[collection_type.value]
            collection.delete(ids=[recommendation_id])
            return True
        except Exception as e:
            print(f"Error deleting recommendation: {e}")
            return False
    
    async def cleanup_old_recommendations(
        self,
        days_old: int = 90,
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> int:
        """Очистка старых рекомендаций"""
        try:
            collection = self.collections[collection_type.value]
            
            # Получаем все рекомендации
            results = collection.get()
            
            if not results["metadatas"]:
                return 0
            
            # Находим старые рекомендации
            cutoff_date = datetime.now(timezone.utc).timestamp() - days_old * 24 * 3600
            old_ids = []
            
            for i, metadata in enumerate(results["metadatas"]):
                created_at = datetime.fromisoformat(metadata.get("created_at", "1970-01-01")).timestamp()
                if created_at < cutoff_date:
                    old_ids.append(results["ids"][i])
            
            # Удаляем старые рекомендации
            if old_ids:
                collection.delete(ids=old_ids)
            
            return len(old_ids)
        except Exception as e:
            print(f"Error cleaning up old recommendations: {e}")
            return 0 