"""
Контекстуальный поиск для RAG системы
Семантический поиск с учетом контекста домена и типа контента
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .advanced_knowledge_base import AdvancedKnowledgeBase, SearchContext, CollectionType
from .types import LLMResponse


@dataclass
class SearchResult:
    """Результат поиска с метаданными"""
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    quality_score: float
    user_satisfaction: float
    total_score: float
    distance: float
    context_match_score: float
    domain_relevance: float
    content_type_match: float


@dataclass
class SearchFilters:
    """Фильтры для поиска"""
    min_quality_score: float = 0.5
    min_relevance_score: float = 0.3
    max_implementation_difficulty: str = "hard"  # easy, medium, hard
    min_estimated_impact: str = "low"  # low, medium, high
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    date_range: Optional[Tuple[datetime, datetime]] = None


class ContextualSearch:
    """Контекстуальный поиск с учетом домена и типа контента"""
    
    def __init__(self, knowledge_base: AdvancedKnowledgeBase):
        self.knowledge_base = knowledge_base
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
    async def search_recommendations(
        self,
        query: str,
        context: SearchContext,
        filters: Optional[SearchFilters] = None,
        limit: int = 10,
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> List[SearchResult]:
        """Поиск релевантных рекомендаций с контекстом"""
        
        if filters is None:
            filters = SearchFilters()
        
        # Создаем контекстуальный запрос
        contextual_query = self._build_contextual_query(query, context)
        
        # Поиск в базе знаний
        raw_results = await self.knowledge_base.search_recommendations(
            query=contextual_query,
            context=context,
            limit=limit * 3,  # Больше результатов для фильтрации
            min_quality_score=filters.min_quality_score,
            collection_type=collection_type
        )
        
        # Применяем дополнительные фильтры
        filtered_results = self._apply_filters(raw_results, filters, context)
        
        # Вычисляем дополнительные скоры
        enhanced_results = await self._enhance_search_results(
            filtered_results, query, context
        )
        
        # Финальное ранжирование
        final_results = self._final_ranking(enhanced_results, context)
        
        return final_results[:limit]
    
    def _build_contextual_query(self, query: str, context: SearchContext) -> str:
        """Создание контекстуального запроса"""
        
        # Базовый запрос
        contextual_parts = [query]
        
        # Добавляем контекст домена
        if context.domain:
            contextual_parts.append(f"domain: {context.domain}")
        
        # Добавляем тип контента
        if context.content_type:
            contextual_parts.append(f"content type: {context.content_type}")
        
        # Добавляем целевую аудиторию
        if context.target_audience:
            contextual_parts.append(f"target audience: {context.target_audience}")
        
        # Добавляем бизнес-цели
        if context.business_goals:
            goals_text = ", ".join(context.business_goals)
            contextual_parts.append(f"business goals: {goals_text}")
        
        # Добавляем текущие метрики
        if context.current_metrics:
            metrics_text = self._format_metrics(context.current_metrics)
            contextual_parts.append(f"current metrics: {metrics_text}")
        
        # Добавляем технические ограничения
        if context.technical_constraints:
            constraints_text = ", ".join(context.technical_constraints)
            contextual_parts.append(f"technical constraints: {constraints_text}")
        
        return " ".join(contextual_parts)
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Форматирование метрик для поиска"""
        formatted_parts = []
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                formatted_parts.append(f"{key}: {value}")
            elif isinstance(value, str):
                formatted_parts.append(f"{key}: {value}")
            elif isinstance(value, dict):
                formatted_parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        
        return ", ".join(formatted_parts)
    
    def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: SearchFilters,
        context: SearchContext
    ) -> List[Dict[str, Any]]:
        """Применение фильтров к результатам поиска"""
        
        filtered_results = []
        
        for result in results:
            metadata = result["metadata"]
            
            # Проверяем качество
            if metadata.get("quality_score", 0.0) < filters.min_quality_score:
                continue
            
            # Проверяем релевантность
            if result["relevance_score"] < filters.min_relevance_score:
                continue
            
            # Проверяем сложность реализации
            difficulty = metadata.get("implementation_difficulty", "medium")
            if self._compare_difficulty(difficulty, filters.max_implementation_difficulty) > 0:
                continue
            
            # Проверяем ожидаемый эффект
            impact = metadata.get("estimated_impact", "medium")
            if self._compare_impact(impact, filters.min_estimated_impact) < 0:
                continue
            
            # Проверяем категории
            if filters.categories:
                result_category = metadata.get("category", "")
                if result_category not in filters.categories:
                    continue
            
            # Проверяем теги
            if filters.tags:
                result_tags = metadata.get("tags", [])
                if not any(tag in result_tags for tag in filters.tags):
                    continue
            
            # Проверяем диапазон дат
            if filters.date_range:
                created_at = datetime.fromisoformat(metadata.get("created_at", "1970-01-01"))
                start_date, end_date = filters.date_range
                if not (start_date <= created_at <= end_date):
                    continue
            
            filtered_results.append(result)
        
        return filtered_results
    
    def _compare_difficulty(self, difficulty1: str, difficulty2: str) -> int:
        """Сравнение сложности реализации"""
        difficulty_levels = {"easy": 1, "medium": 2, "hard": 3}
        return difficulty_levels.get(difficulty1, 2) - difficulty_levels.get(difficulty2, 2)
    
    def _compare_impact(self, impact1: str, impact2: str) -> int:
        """Сравнение ожидаемого эффекта"""
        impact_levels = {"low": 1, "medium": 2, "high": 3}
        return impact_levels.get(impact1, 2) - impact_levels.get(impact2, 2)
    
    async def _enhance_search_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        context: SearchContext
    ) -> List[SearchResult]:
        """Улучшение результатов поиска дополнительными скорами"""
        
        enhanced_results = []
        
        for result in results:
            # Вычисляем скор соответствия контексту
            context_match_score = self._calculate_context_match_score(
                result, context
            )
            
            # Вычисляем релевантность домена
            domain_relevance = self._calculate_domain_relevance(
                result, context.domain
            )
            
            # Вычисляем соответствие типу контента
            content_type_match = self._calculate_content_type_match(
                result, context.content_type
            )
            
            # Создаем улучшенный результат
            enhanced_result = SearchResult(
                content=result["content"],
                metadata=result["metadata"],
                relevance_score=result["relevance_score"],
                quality_score=result["quality_score"],
                user_satisfaction=result["user_satisfaction"],
                total_score=result["total_score"],
                distance=result["distance"],
                context_match_score=context_match_score,
                domain_relevance=domain_relevance,
                content_type_match=content_type_match
            )
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    def _calculate_context_match_score(
        self,
        result: Dict[str, Any],
        context: SearchContext
    ) -> float:
        """Вычисление скора соответствия контексту"""
        
        score = 0.0
        metadata = result["metadata"]
        
        # Проверяем соответствие домена
        if metadata.get("domain") == context.domain:
            score += 0.3
        
        # Проверяем соответствие типа контента
        if metadata.get("content_type") == context.content_type:
            score += 0.2
        
        # Проверяем соответствие тегам
        result_tags = metadata.get("tags", [])
        context_tags = self._extract_context_tags(context)
        
        if context_tags:
            tag_matches = sum(1 for tag in context_tags if tag in result_tags)
            score += (tag_matches / len(context_tags)) * 0.2
        
        # Проверяем соответствие категории
        if metadata.get("category") in self._extract_context_categories(context):
            score += 0.1
        
        # Проверяем соответствие сложности
        difficulty = metadata.get("implementation_difficulty", "medium")
        if self._is_difficulty_appropriate(difficulty, context):
            score += 0.1
        
        # Проверяем соответствие ожидаемому эффекту
        impact = metadata.get("estimated_impact", "medium")
        if self._is_impact_appropriate(impact, context):
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_context_tags(self, context: SearchContext) -> List[str]:
        """Извлечение тегов из контекста"""
        tags = []
        
        # Добавляем теги из домена
        if context.domain:
            tags.append(context.domain.lower())
        
        # Добавляем теги из типа контента
        if context.content_type:
            tags.append(context.content_type.lower())
        
        # Добавляем теги из целевой аудитории
        if context.target_audience:
            tags.extend(context.target_audience.lower().split())
        
        # Добавляем теги из бизнес-целей
        for goal in context.business_goals:
            tags.extend(goal.lower().split())
        
        return list(set(tags))
    
    def _extract_context_categories(self, context: SearchContext) -> List[str]:
        """Извлечение категорий из контекста"""
        categories = ["general"]
        
        # Определяем категории на основе типа контента
        content_type = context.content_type.lower()
        if "technical" in content_type or "performance" in content_type:
            categories.append("technical")
        if "content" in content_type or "seo" in content_type:
            categories.append("content")
        if "user" in content_type or "experience" in content_type:
            categories.append("user_experience")
        
        # Определяем категории на основе бизнес-целей
        for goal in context.business_goals:
            goal_lower = goal.lower()
            if "conversion" in goal_lower or "sales" in goal_lower:
                categories.append("conversion")
            if "traffic" in goal_lower or "visibility" in goal_lower:
                categories.append("traffic")
            if "engagement" in goal_lower or "interaction" in goal_lower:
                categories.append("engagement")
        
        return list(set(categories))
    
    def _is_difficulty_appropriate(self, difficulty: str, context: SearchContext) -> bool:
        """Проверка соответствия сложности контексту"""
        # Простая логика - можно улучшить
        return difficulty in ["easy", "medium"]
    
    def _is_impact_appropriate(self, impact: str, context: SearchContext) -> bool:
        """Проверка соответствия ожидаемого эффекта контексту"""
        # Простая логика - можно улучшить
        return impact in ["medium", "high"]
    
    def _calculate_domain_relevance(
        self,
        result: Dict[str, Any],
        target_domain: str
    ) -> float:
        """Вычисление релевантности домена"""
        
        result_domain = result["metadata"].get("domain", "")
        
        if result_domain == target_domain:
            return 1.0
        
        # Проверяем схожесть доменов
        if self._are_domains_similar(result_domain, target_domain):
            return 0.7
        
        return 0.3
    
    def _are_domains_similar(self, domain1: str, domain2: str) -> bool:
        """Проверка схожести доменов"""
        
        # Извлекаем основные части доменов
        def extract_domain_parts(domain: str) -> List[str]:
            parts = domain.lower().replace("www.", "").split(".")
            return parts[:-1] if len(parts) > 1 else parts
        
        parts1 = extract_domain_parts(domain1)
        parts2 = extract_domain_parts(domain2)
        
        # Проверяем пересечение частей
        common_parts = set(parts1) & set(parts2)
        return len(common_parts) > 0
    
    def _calculate_content_type_match(
        self,
        result: Dict[str, Any],
        target_content_type: str
    ) -> float:
        """Вычисление соответствия типу контента"""
        
        result_content_type = result["metadata"].get("content_type", "")
        
        if result_content_type == target_content_type:
            return 1.0
        
        # Проверяем схожесть типов контента
        if self._are_content_types_similar(result_content_type, target_content_type):
            return 0.7
        
        return 0.3
    
    def _are_content_types_similar(self, type1: str, type2: str) -> bool:
        """Проверка схожести типов контента"""
        
        type1_lower = type1.lower()
        type2_lower = type2.lower()
        
        # Определяем категории типов контента
        categories = {
            "technical": ["technical", "performance", "speed", "optimization"],
            "content": ["content", "seo", "keywords", "meta"],
            "user_experience": ["ux", "ui", "user", "experience", "interface"],
            "conversion": ["conversion", "sales", "cta", "funnel"]
        }
        
        # Находим категории для каждого типа
        def find_category(content_type: str) -> List[str]:
            found_categories = []
            for category, keywords in categories.items():
                if any(keyword in content_type for keyword in keywords):
                    found_categories.append(category)
            return found_categories
        
        categories1 = find_category(type1_lower)
        categories2 = find_category(type2_lower)
        
        # Проверяем пересечение категорий
        return bool(set(categories1) & set(categories2))
    
    def _final_ranking(
        self,
        results: List[SearchResult],
        context: SearchContext
    ) -> List[SearchResult]:
        """Финальное ранжирование результатов"""
        
        for result in results:
            # Вычисляем финальный скор с учетом всех факторов
            final_score = (
                result.relevance_score * 0.25 +
                result.quality_score * 0.20 +
                result.user_satisfaction * 0.15 +
                result.context_match_score * 0.20 +
                result.domain_relevance * 0.10 +
                result.content_type_match * 0.10
            )
            
            # Обновляем total_score
            result.total_score = final_score
        
        # Сортируем по финальному скору
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        return results
    
    async def search_similar_recommendations(
        self,
        recommendation_id: str,
        context: SearchContext,
        limit: int = 5,
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> List[SearchResult]:
        """Поиск похожих рекомендаций"""
        
        # Получаем исходную рекомендацию
        collection = self.knowledge_base.collections[collection_type.value]
        original = collection.get(ids=[recommendation_id])
        
        if not original["documents"]:
            return []
        
        # Используем контент как запрос для поиска похожих
        similar_query = original["documents"][0]
        
        # Ищем похожие рекомендации
        similar_results = await self.search_recommendations(
            query=similar_query,
            context=context,
            limit=limit + 1,  # +1 чтобы исключить исходную
            collection_type=collection_type
        )
        
        # Исключаем исходную рекомендацию
        filtered_results = [
            result for result in similar_results
            if result.content != similar_query
        ]
        
        return filtered_results[:limit]
    
    async def search_trending_recommendations(
        self,
        context: SearchContext,
        days: int = 30,
        limit: int = 10,
        collection_type: CollectionType = CollectionType.SEO_RECOMMENDATIONS
    ) -> List[SearchResult]:
        """Поиск трендовых рекомендаций"""
        
        # Создаем фильтр по дате
        end_date = datetime.now(timezone.utc)
        start_date = end_date.replace(day=end_date.day - days)
        
        filters = SearchFilters(
            date_range=(start_date, end_date),
            min_quality_score=0.7
        )
        
        # Ищем рекомендации с высоким качеством за последние дни
        trending_results = await self.search_recommendations(
            query="trending recommendations",
            context=context,
            filters=filters,
            limit=limit,
            collection_type=collection_type
        )
        
        # Сортируем по дате создания (новые первыми)
        trending_results.sort(
            key=lambda x: x.metadata.get("created_at", ""),
            reverse=True
        )
        
        return trending_results 