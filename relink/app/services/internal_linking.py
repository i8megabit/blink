"""
🔗 Сервис внутренней перелинковки
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import re

from ..models import InternalLink, LinkRecommendation, LinkType
from bootstrap.config import get_settings

logger = logging.getLogger(__name__)

class InternalLinkingService:
    """Сервис анализа и оптимизации внутренних ссылок"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
    
    async def analyze_domain(
        self, 
        domain: str,
        llm_router=None,
        rag_service=None,
        ollama_client=None
    ) -> Dict[str, Any]:
        """Анализ внутренних ссылок для домена"""
        
        try:
            self.logger.info(f"Начинаю анализ внутренних ссылок для домена: {domain}")
            
            # Получение данных о постах (здесь должна быть интеграция с базой данных)
            posts = await self._get_domain_posts(domain)
            
            if not posts:
                return {
                    "status": "warning",
                    "message": f"Не найдено постов для домена {domain}",
                    "domain": domain,
                    "analysis_date": datetime.now().isoformat()
                }
            
            # Анализ внутренних ссылок
            internal_links_analysis = await self._analyze_internal_links(posts)
            
            # Анализ через LLM (если доступен)
            llm_analysis = []
            if llm_router:
                llm_analysis = await self._analyze_with_llm(posts, domain, llm_router)
            
            # Анализ через RAG (если доступен)
            rag_analysis = []
            if rag_service:
                rag_analysis = await self._analyze_with_rag(posts, domain, rag_service)
            
            # Генерация рекомендаций
            recommendations = await self._generate_recommendations(
                posts, internal_links_analysis, llm_analysis, rag_analysis
            )
            
            # Расчет метрик
            metrics = await self._calculate_metrics(posts, internal_links_analysis)
            
            return {
                "status": "success",
                "domain": domain,
                "analysis_date": datetime.now().isoformat(),
                "posts_analyzed": len(posts),
                "internal_links_found": len(internal_links_analysis),
                "recommendations": recommendations,
                "metrics": metrics,
                "llm_analysis": llm_analysis,
                "rag_analysis": rag_analysis
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе домена {domain}: {e}")
            raise
    
    async def generate_recommendations(
        self,
        domain: str,
        llm_router=None,
        rag_service=None,
        ollama_client=None
    ) -> List[Dict[str, Any]]:
        """Генерация рекомендаций по внутренним ссылкам"""
        
        try:
            posts = await self._get_domain_posts(domain)
            if not posts:
                return []
            
            # Анализ внутренних ссылок
            internal_links_analysis = await self._analyze_internal_links(posts)
            
            # Поиск статей без внутренних ссылок
            posts_without_links = []
            for post in posts:
                content_lower = post.get('content', '').lower()
                has_internal_links = any(
                    other_post.get('title', '').lower() in content_lower 
                    for other_post in posts 
                    if other_post.get('id') != post.get('id')
                )
                
                if not has_internal_links:
                    posts_without_links.append(post)
            
            recommendations = []
            
            # Рекомендация по добавлению внутренних ссылок
            if posts_without_links:
                recommendations.append({
                    "type": "internal_linking",
                    "priority": "high",
                    "title": "Добавить внутренние ссылки",
                    "description": f"Найдено {len(posts_without_links)} статей без внутренних ссылок",
                    "details": [
                        {
                            "post_title": post.get('title', ''),
                            "post_url": post.get('link', ''),
                            "suggested_links": [
                                other_post.get('title', '') 
                                for other_post in posts[:3] 
                                if other_post.get('id') != post.get('id')
                            ]
                        }
                        for post in posts_without_links[:5]  # Показываем только первые 5
                    ]
                })
            
            # Рекомендация по оптимизации существующих ссылок
            if internal_links_analysis:
                recommendations.append({
                    "type": "link_optimization",
                    "priority": "medium",
                    "title": "Оптимизировать существующие ссылки",
                    "description": f"Проанализировано {len(internal_links_analysis)} внутренних ссылок",
                    "details": {
                        "total_links": len(internal_links_analysis),
                        "avg_links_per_post": len(internal_links_analysis) / len(posts),
                        "recommendation": "Проверьте релевантность и качество анкоров"
                    }
                })
            
            # Рекомендация по семантической группировке
            recommendations.append({
                "type": "semantic_clustering",
                "priority": "medium",
                "title": "Семантическая группировка статей",
                "description": "Создайте тематические кластеры для лучшей внутренней перелинковки",
                "details": {
                    "total_posts": len(posts),
                    "recommendation": "Группируйте статьи по темам и создавайте связи между кластерами"
                }
            })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации рекомендаций: {e}")
            return []
    
    async def _get_domain_posts(self, domain: str) -> List[Dict[str, Any]]:
        """Получение постов домена (заглушка - в реальности должна быть интеграция с БД)"""
        # Здесь должна быть интеграция с базой данных
        # Пока возвращаем тестовые данные
        return [
            {
                "id": 1,
                "title": "Как выращивать помидоры",
                "content": "Подробное руководство по выращиванию томатов в домашних условиях...",
                "link": f"https://{domain}/tomatoes",
                "content_type": "guide"
            },
            {
                "id": 2,
                "title": "Лучшие сорта огурцов",
                "content": "Обзор популярных сортов огурцов для открытого грунта...",
                "link": f"https://{domain}/cucumbers",
                "content_type": "review"
            },
            {
                "id": 3,
                "title": "Уход за садом весной",
                "content": "Основные работы в саду в весенний период...",
                "link": f"https://{domain}/spring-garden",
                "content_type": "guide"
            }
        ]
    
    async def _analyze_internal_links(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Анализ внутренних ссылок между постами"""
        internal_links = []
        
        for post in posts:
            content = post.get('content', '')
            post_title = post.get('title', '')
            
            # Поиск упоминаний других постов в контенте
            for other_post in posts:
                if other_post.get('id') == post.get('id'):
                    continue
                
                other_title = other_post.get('title', '')
                if other_title.lower() in content.lower():
                    internal_links.append({
                        "source_post_id": post.get('id'),
                        "source_post_title": post_title,
                        "target_post_id": other_post.get('id'),
                        "target_post_title": other_title,
                        "link_type": "implicit",
                        "strength": 1.0
                    })
        
        return internal_links
    
    async def _analyze_with_llm(
        self, 
        posts: List[Dict[str, Any]], 
        domain: str,
        llm_router
    ) -> List[Dict[str, Any]]:
        """Анализ через LLM"""
        try:
            # Подготовка данных для LLM
            posts_data = []
            for post in posts:
                posts_data.append({
                    'title': post.get('title', ''),
                    'content': post.get('content', ''),
                    'link': post.get('link', ''),
                    'content_type': post.get('content_type', '')
                })
            
            # Анализ через LLM Router
            prompt = f"""
            Проанализируй следующие статьи с сайта {domain} и предложи рекомендации по внутренней перелинковке:
            
            Статьи:
            {posts_data}
            
            Предложи:
            1. Какие статьи можно связать внутренними ссылками
            2. Какие анкоры использовать для ссылок
            3. Как улучшить структуру внутренних ссылок
            """
            
            llm_result = await llm_router.route_request(prompt)
            
            return [{
                "type": "llm_analysis",
                "content": llm_result.get('response', ''),
                "confidence": llm_result.get('confidence', 0.8)
            }]
            
        except Exception as e:
            self.logger.error(f"Ошибка при LLM анализе: {e}")
            return []
    
    async def _analyze_with_rag(
        self, 
        posts: List[Dict[str, Any]], 
        domain: str,
        rag_service
    ) -> List[Dict[str, Any]]:
        """Анализ через RAG"""
        try:
            # Поиск релевантной информации в RAG
            query = f"internal linking best practices for {domain}"
            rag_results = await rag_service.search(query, top_k=5)
            
            return [{
                "type": "rag_analysis",
                "content": result.get('content', ''),
                "source": result.get('source', ''),
                "relevance": result.get('relevance', 0.0)
            } for result in rag_results]
            
        except Exception as e:
            self.logger.error(f"Ошибка при RAG анализе: {e}")
            return []
    
    async def _generate_recommendations(
        self,
        posts: List[Dict[str, Any]],
        internal_links_analysis: List[Dict[str, Any]],
        llm_analysis: List[Dict[str, Any]],
        rag_analysis: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Генерация рекомендаций на основе всех анализов"""
        recommendations = []
        
        # Анализ внутренних ссылок
        posts_without_links = []
        for post in posts:
            has_links = any(
                link['source_post_id'] == post.get('id') 
                for link in internal_links_analysis
            )
            if not has_links:
                posts_without_links.append(post)
        
        if posts_without_links:
            recommendations.append({
                "type": "internal_linking",
                "priority": "high",
                "title": "Добавить внутренние ссылки",
                "description": f"Найдено {len(posts_without_links)} статей без внутренних ссылок",
                "details": [
                    {
                        "post_title": post.get('title', ''),
                        "post_url": post.get('link', ''),
                        "suggested_links": [
                            other_post.get('title', '') 
                            for other_post in posts[:3] 
                            if other_post.get('id') != post.get('id')
                        ]
                    }
                    for post in posts_without_links[:5]
                ]
            })
        
        # Добавление рекомендаций из LLM анализа
        for analysis in llm_analysis:
            if analysis.get('content'):
                recommendations.append({
                    "type": "llm_recommendation",
                    "priority": "medium",
                    "title": "AI рекомендация",
                    "description": analysis.get('content', '')[:200] + "...",
                    "confidence": analysis.get('confidence', 0.8)
                })
        
        return recommendations
    
    async def _calculate_metrics(
        self,
        posts: List[Dict[str, Any]],
        internal_links_analysis: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Расчет метрик внутренней перелинковки"""
        total_posts = len(posts)
        total_links = len(internal_links_analysis)
        
        # Посты с внутренними ссылками
        posts_with_links = set(link['source_post_id'] for link in internal_links_analysis)
        posts_without_links = total_posts - len(posts_with_links)
        
        # Среднее количество ссылок на пост
        avg_links_per_post = total_links / total_posts if total_posts > 0 else 0
        
        # Покрытие внутренними ссылками
        coverage_percentage = (len(posts_with_links) / total_posts * 100) if total_posts > 0 else 0
        
        return {
            "total_posts": total_posts,
            "total_internal_links": total_links,
            "posts_with_links": len(posts_with_links),
            "posts_without_links": posts_without_links,
            "avg_links_per_post": round(avg_links_per_post, 2),
            "coverage_percentage": round(coverage_percentage, 2),
            "link_density_score": round(total_links / max(total_posts, 1), 2)
        } 