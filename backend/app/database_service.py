"""
Сервис для работы с базой данных и RAG системой
Интеграция между базой данных, RAG и LLM для SEO анализа
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
import os
import inspect
import traceback

from .database import get_db
from .models import Domain, AnalysisHistory, WordPressPost, User
from .llm_integration import get_llm_integration_service, SEOServiceIntegration
from .llm.distributed_cache import DistributedCache

logger = logging.getLogger(__name__)

class DatabaseRAGService:
    """Сервис для интеграции базы данных с RAG системой"""
    
    def __init__(self):
        self.llm_service = None
        self.seo_integration = None
        self.cache_manager = None
        self._initialized = False
    
    def _log_method_call(self):
        stack = inspect.stack()
        caller = stack[1]
        logger.info(f"[DEBUG DatabaseRAGService] {caller.function} called from {caller.filename}:{caller.lineno}")
    
    async def initialize(self):
        """Инициализация сервиса"""
        self._log_method_call()
        if self._initialized:
            return
        
        try:
            # Инициализируем LLM сервис
            self.llm_service = await get_llm_integration_service()
            
            # Создаем SEO интеграцию
            self.seo_integration = SEOServiceIntegration(self.llm_service)
            
            # Инициализируем кэш менеджер с REDIS_URL из окружения
            redis_url = os.environ.get("REDIS_URL", "redis://redis:6379")
            self.cache_manager = DistributedCache(redis_url)
            await self.cache_manager.connect()
            
            self._initialized = True
            logger.info("DatabaseRAGService успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации DatabaseRAGService: {e}")
            raise
    
    async def analyze_domain_with_rag(self, domain_name: str, user_id: int, comprehensive: bool = True) -> Dict[str, Any]:
        """Анализ домена с использованием RAG и сохранением в БД"""
        self._log_method_call()
        if not self._initialized:
            await self.initialize()
        
        try:
            # Получаем данные из базы данных
            domain_data = await self._get_domain_data(domain_name)
            
            # Проверяем кэш
            cache_key = f"domain_analysis:{domain_name}:{comprehensive}"
            cached_result = await self.cache_manager.get_response(cache_key)
            
            if cached_result:
                logger.info(f"Найден кэшированный анализ для домена {domain_name}")
                return {
                    "domain": domain_name,
                    "analysis": cached_result.response,
                    "cached": True,
                    "cached_at": cached_result.created_at.isoformat()
                }
            
            # Создаем контекст для RAG
            rag_context = await self._build_rag_context(domain_data)
            
            # Добавляем контекст в базу знаний
            await self.cache_manager.add_to_knowledge_base([{
                "content": rag_context,
                "metadata": {
                    "domain": domain_name,
                    "type": "domain_analysis",
                    "created_at": datetime.utcnow().isoformat()
                }
            }])
            
            # Выполняем SEO анализ с RAG
            seo_analysis = await self.seo_integration.analyze_domain_seo(
                domain_name, 
                comprehensive=comprehensive
            )
            
            # Сохраняем результат в базу данных
            analysis_id = await self._save_analysis_result(
                domain_name, 
                user_id, 
                seo_analysis
            )
            
            # Кэшируем результат
            await self.cache_manager.cache_response(
                cache_key, 
                seo_analysis, 
                ttl=3600  # 1 час
            )
            
            return {
                "analysis_id": analysis_id,
                "domain": domain_name,
                "analysis": seo_analysis,
                "cached": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа домена {domain_name}: {e}")
            raise
    
    async def generate_content_recommendations(self, domain_name: str, user_id: int) -> List[Dict[str, Any]]:
        """Генерация рекомендаций по контенту с использованием RAG"""
        self._log_method_call()
        if not self._initialized:
            await self.initialize()
        try:
            # Получаем данные о контенте домена
            content_data = await self._get_domain_content(domain_name)
            # Создаем контекст для рекомендаций
            content_context = self._build_content_context(content_data)
            # Добавляем в базу знаний
            await self.cache_manager.add_to_knowledge_base([{
                "content": content_context,
                "metadata": {
                    "domain": domain_name,
                    "type": "content_recommendations",
                    "created_at": datetime.utcnow().isoformat()
                }
            }])
            # Генерируем рекомендации
            recommendations = await self.seo_integration.generate_content_recommendations(
                domain_name, 
                "articles"
            )
            return recommendations
        except Exception as e:
            logger.error(f"[TRACE] Ошибка генерации рекомендаций для {domain_name}: {e}\n{traceback.format_exc()}")
            raise
    
    async def optimize_keywords_with_history(self, domain_name: str, user_id: int) -> Dict[str, Any]:
        """Оптимизация ключевых слов с учетом истории"""
        self._log_method_call()
        if not self._initialized:
            await self.initialize()
        
        try:
            # Получаем историю ключевых слов
            keyword_history = await self._get_keyword_history(domain_name)
            
            # Текущие ключевые слова
            current_keywords = [kw["keyword"] for kw in keyword_history.get("current", [])]
            
            # Оптимизируем ключевые слова
            optimization_result = await self.seo_integration.optimize_keywords(
                domain_name, 
                current_keywords
            )
            
            # Сохраняем результат оптимизации
            await self._save_keyword_optimization(
                domain_name, 
                user_id, 
                optimization_result
            )
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации ключевых слов для {domain_name}: {e}")
            raise
    
    async def _get_domain_data(self, domain_name: str) -> Dict[str, Any]:
        """Получение данных домена из базы данных"""
        self._log_method_call()
        async for db in get_db():
            # Получаем домен
            domain_query = select(Domain).where(Domain.name == domain_name)
            domain_result = await db.execute(domain_query)
            domain = domain_result.scalar_one_or_none()
            
            if not domain:
                return {"domain": domain_name, "posts": [], "analyses": []}
            
            # Получаем посты домена
            posts_query = select(WordPressPost).where(WordPressPost.domain_id == domain.id)
            posts_result = await db.execute(posts_query)
            posts = posts_result.scalars().all()
            
            # Получаем историю анализов
            analyses_query = select(AnalysisHistory).where(AnalysisHistory.domain_id == domain.id)
            analyses_result = await db.execute(analyses_query)
            analyses = analyses_result.scalars().all()
            
            return {
                "domain": domain,
                "posts": posts,
                "analyses": analyses
            }
    
    async def _get_domain_content(self, domain_name: str) -> Dict[str, Any]:
        """Получение контента домена"""
        self._log_method_call()
        async for db in get_db():
            # Получаем домен
            domain_query = select(Domain).where(Domain.name == domain_name)
            domain_result = await db.execute(domain_query)
            domain = domain_result.scalar_one_or_none()
            
            if not domain:
                return {"posts": [], "categories": []}
            
            # Получаем посты с контентом
            posts_query = select(WordPressPost).where(WordPressPost.domain_id == domain.id)
            posts_result = await db.execute(posts_query)
            posts = posts_result.scalars().all()
            
            # Извлекаем категории из постов
            categories = set()
            for post in posts:
                if post.categories:
                    categories.update(post.categories.split(','))
            
            return {
                "posts": posts,
                "categories": list(categories)
            }
    
    async def _get_keyword_history(self, domain_name: str) -> Dict[str, Any]:
        """Получение истории ключевых слов"""
        # Заглушка - в реальной системе здесь была бы таблица ключевых слов
        return {
            "current": [
                {"keyword": "садоводство", "frequency": 15},
                {"keyword": "огород", "frequency": 12},
                {"keyword": "растения", "frequency": 8},
                {"keyword": "выращивание", "frequency": 10}
            ],
            "historical": [
                {"keyword": "цветы", "frequency": 5, "date": "2024-01-01"},
                {"keyword": "овощи", "frequency": 7, "date": "2024-01-15"}
            ]
        }
    
    async def _build_rag_context(self, domain_data: Dict[str, Any]) -> str:
        """Построение контекста для RAG"""
        self._log_method_call()
        context_parts = []
        
        # Информация о домене
        if domain_data.get("domain"):
            domain = domain_data["domain"]
            context_parts.append(f"Домен: {domain.name}")
            context_parts.append(f"Описание: {domain.description or 'Нет описания'}")
        
        # Информация о постах
        posts = domain_data.get("posts", [])
        if posts:
            context_parts.append(f"Количество постов: {len(posts)}")
            
            # Категории постов
            categories = {}
            for post in posts:
                if post.categories:
                    for cat in post.categories.split(','):
                        cat = cat.strip()
                        categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                context_parts.append("Категории постов:")
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    context_parts.append(f"  - {cat}: {count} постов")
        
        # История анализов
        analyses = domain_data.get("analyses", [])
        if analyses:
            context_parts.append(f"Количество предыдущих анализов: {len(analyses)}")
            
            # Последний анализ
            latest_analysis = max(analyses, key=lambda x: x.created_at)
            context_parts.append(f"Последний анализ: {latest_analysis.created_at.strftime('%Y-%m-%d')}")
            context_parts.append(f"Последний скор: {latest_analysis.score}")
        
        return "\n".join(context_parts)
    
    def _build_content_context(self, content_data: Dict[str, Any]) -> str:
        """Построение контекста контента"""
        self._log_method_call()
        context_parts = []
        
        posts = content_data.get("posts", [])
        categories = content_data.get("categories", [])
        
        context_parts.append(f"Общее количество постов: {len(posts)}")
        context_parts.append(f"Категории: {', '.join(categories)}")
        
        # Анализ длины контента
        if posts:
            avg_length = sum(len(post.content or '') for post in posts) / len(posts)
            context_parts.append(f"Средняя длина поста: {avg_length:.0f} символов")
        
        return "\n".join(context_parts)
    
    async def _save_analysis_result(self, domain_name: str, user_id: int, analysis: Dict[str, Any]) -> int:
        """Сохранение результата анализа в базу данных"""
        self._log_method_call()
        async for db in get_db():
            # Получаем или создаем домен
            domain_query = select(Domain).where(Domain.name == domain_name)
            domain_result = await db.execute(domain_query)
            domain = domain_result.scalar_one_or_none()
            
            if not domain:
                domain = Domain(
                    name=domain_name,
                    display_name=domain_name,
                    description=f"Домен {domain_name}",
                    owner_id=user_id,
                    created_at=datetime.utcnow()
                )
                db.add(domain)
                await db.commit()
                await db.refresh(domain)
            
            # Создаем запись анализа
            analysis_record = AnalysisHistory(
                domain_id=domain.id,
                user_id=user_id,
                score=analysis.get("metrics", {}).get("score", 75.0),
                analysis_data=analysis,
                created_at=datetime.utcnow()
            )
            
            db.add(analysis_record)
            await db.commit()
            await db.refresh(analysis_record)
            
            return analysis_record.id
    
    async def _save_keyword_optimization(self, domain_name: str, user_id: int, optimization: Dict[str, Any]):
        """Сохранение результата оптимизации ключевых слов"""
        # В реальной системе здесь была бы таблица для ключевых слов
        logger.info(f"Сохранена оптимизация ключевых слов для домена {domain_name}")
    
    async def get_analysis_history(self, domain_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение истории анализов домена"""
        self._log_method_call()
        async for db in get_db():
            # Получаем домен
            domain_query = select(Domain).where(Domain.name == domain_name)
            domain_result = await db.execute(domain_query)
            domain = domain_result.scalar_one_or_none()
            
            if not domain:
                return []
            
            # Получаем историю анализов
            analyses_query = (
                select(AnalysisHistory)
                .where(AnalysisHistory.domain_id == domain.id)
                .order_by(AnalysisHistory.created_at.desc())
                .limit(limit)
            )
            
            analyses_result = await db.execute(analyses_query)
            analyses = analyses_result.scalars().all()
            
            return [
                {
                    "id": analysis.id,
                    "score": analysis.score,
                    "created_at": analysis.created_at.isoformat(),
                    "analysis_data": analysis.analysis_data
                }
                for analysis in analyses
            ]

# Глобальный экземпляр сервиса
_database_rag_service: Optional[DatabaseRAGService] = None

async def get_database_rag_service() -> DatabaseRAGService:
    """Получение глобального экземпляра сервиса"""
    global _database_rag_service
    
    if _database_rag_service is None:
        _database_rag_service = DatabaseRAGService()
        await _database_rag_service.initialize()
    
    return _database_rag_service 