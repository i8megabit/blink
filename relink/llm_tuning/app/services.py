"""
Сервисный слой для LLM Tuning микросервиса
Обеспечивает бизнес-логику для управления моделями, маршрутизации и тюнинга
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import httpx
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from .models import (
    LLMModel, ModelRoute, TuningSession, PerformanceMetrics,
    RAGDocument, APILog, ModelStatus, RouteStrategy, TuningStrategy
)
from .config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """Менеджер для управления LLM моделями"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=settings.OLLAMA_TIMEOUT
        )
    
    async def list_models(self) -> List[LLMModel]:
        """Получение списка всех моделей"""
        try:
            # Получаем модели из Ollama
            response = await self.ollama_client.get("/api/tags")
            ollama_models = response.json().get("models", [])
            
            # Получаем модели из БД
            stmt = select(LLMModel).options(selectinload(LLMModel.routes))
            result = await self.db.execute(stmt)
            db_models = result.scalars().all()
            
            # Обновляем статусы моделей
            for model in db_models:
                model.is_available = any(
                    m["name"] == model.name for m in ollama_models
                )
            
            await self.db.commit()
            return db_models
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей: {e}")
            raise
    
    async def get_model(self, model_id: int) -> Optional[LLMModel]:
        """Получение модели по ID"""
        stmt = select(LLMModel).options(
            selectinload(LLMModel.routes),
            selectinload(LLMModel.metrics)
        ).where(LLMModel.id == model_id)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_model(self, model_data: Dict[str, Any]) -> LLMModel:
        """Создание новой модели"""
        model = LLMModel(**model_data)
        self.db.add(model)
        await self.db.commit()
        await self.db.refresh(model)
        return model
    
    async def update_model(self, model_id: int, model_data: Dict[str, Any]) -> Optional[LLMModel]:
        """Обновление модели"""
        stmt = update(LLMModel).where(LLMModel.id == model_id).values(**model_data)
        await self.db.execute(stmt)
        await self.db.commit()
        
        return await self.get_model(model_id)
    
    async def delete_model(self, model_id: int) -> bool:
        """Удаление модели"""
        stmt = delete(LLMModel).where(LLMModel.id == model_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Получение информации о модели из Ollama"""
        try:
            response = await self.ollama_client.get(f"/api/show", params={"name": model_name})
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка при получении информации о модели {model_name}: {e}")
            return {}


class RouteManager:
    """Менеджер для управления маршрутизацией запросов"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self._route_cache: Dict[str, ModelRoute] = {}
        self._cache_updated = datetime.now()
    
    async def get_route(self, request_type: str, content: str = "") -> Optional[ModelRoute]:
        """Получение оптимального маршрута для запроса"""
        # Обновляем кэш каждые 5 минут
        if datetime.now() - self._cache_updated > timedelta(minutes=5):
            await self._update_cache()
        
        # Ищем подходящий маршрут
        for route in self._route_cache.values():
            if route.is_active and self._matches_route(route, request_type, content):
                return route
        
        # Возвращаем маршрут по умолчанию
        return self._get_default_route()
    
    def _matches_route(self, route: ModelRoute, request_type: str, content: str) -> bool:
        """Проверка соответствия запроса маршруту"""
        # Проверяем тип запроса
        if route.request_types and request_type not in route.request_types:
            return False
        
        # Проверяем ключевые слова
        if route.keywords and not any(
            keyword.lower() in content.lower() for keyword in route.keywords
        ):
            return False
        
        # Проверяем сложность контента
        if route.complexity_threshold:
            complexity = self._calculate_complexity(content)
            if complexity < route.complexity_threshold:
                return False
        
        return True
    
    def _calculate_complexity(self, content: str) -> float:
        """Расчет сложности контента"""
        if not content:
            return 0.0
        
        # Простая эвристика сложности
        words = content.split()
        sentences = content.split('.')
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Учитываем специальные символы и числа
        special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
        numbers = sum(1 for c in content if c.isdigit())
        
        complexity = (
            avg_sentence_length * 0.4 +
            (special_chars / len(content)) * 0.3 +
            (numbers / len(content)) * 0.3
        )
        
        return min(complexity, 1.0)
    
    def _get_default_route(self) -> Optional[ModelRoute]:
        """Получение маршрута по умолчанию"""
        for route in self._route_cache.values():
            if route.is_default:
                return route
        return None
    
    async def _update_cache(self):
        """Обновление кэша маршрутов"""
        stmt = select(ModelRoute).options(selectinload(ModelRoute.model))
        result = await self.db.execute(stmt)
        routes = result.scalars().all()
        
        self._route_cache = {route.name: route for route in routes}
        self._cache_updated = datetime.now()
    
    async def create_route(self, route_data: Dict[str, Any]) -> ModelRoute:
        """Создание нового маршрута"""
        route = ModelRoute(**route_data)
        self.db.add(route)
        await self.db.commit()
        await self.db.refresh(route)
        
        # Обновляем кэш
        await self._update_cache()
        return route
    
    async def update_route(self, route_id: int, route_data: Dict[str, Any]) -> Optional[ModelRoute]:
        """Обновление маршрута"""
        stmt = update(ModelRoute).where(ModelRoute.id == route_id).values(**route_data)
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Обновляем кэш
        await self._update_cache()
        
        stmt = select(ModelRoute).where(ModelRoute.id == route_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class RAGService:
    """Сервис для работы с RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        self._vector_cache: Dict[str, List[float]] = {}
    
    async def add_document(self, document_data: Dict[str, Any]) -> RAGDocument:
        """Добавление документа в RAG систему"""
        try:
            # Создаем документ
            document = RAGDocument(**document_data)
            
            # Генерируем эмбеддинги для документа
            embeddings = await self._generate_embeddings(document.content)
            document.embeddings = json.dumps(embeddings)
            
            # Извлекаем ключевые слова
            document.keywords = await self._extract_keywords(document.content)
            
            # Сохраняем в БД
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            # Кэшируем эмбеддинги
            self._vector_cache[f"doc_{document.id}"] = embeddings
            
            logger.info(f"Документ {document.title} добавлен в RAG систему")
            return document
            
        except Exception as e:
            logger.error(f"Ошибка добавления документа: {e}")
            raise
    
    async def search_documents(self, query: str, limit: int = 5) -> List[RAGDocument]:
        """Поиск релевантных документов"""
        try:
            # Генерируем эмбеддинги для запроса
            query_embeddings = await self._generate_embeddings(query)
            
            # Получаем все документы
            stmt = select(RAGDocument).where(RAGDocument.is_active == True)
            result = await self.db.execute(stmt)
            documents = result.scalars().all()
            
            # Вычисляем косинусное сходство
            similarities = []
            for doc in documents:
                if doc.embeddings:
                    doc_embeddings = json.loads(doc.embeddings)
                    similarity = self._cosine_similarity(query_embeddings, doc_embeddings)
                    similarities.append((similarity, doc))
            
            # Сортируем по сходству и возвращаем топ результаты
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_documents = [doc for _, doc in similarities[:limit]]
            
            logger.info(f"Найдено {len(top_documents)} релевантных документов для запроса")
            return top_documents
            
        except Exception as e:
            logger.error(f"Ошибка поиска документов: {e}")
            return []
    
    async def generate_with_rag(
        self, 
        model_name: str, 
        query: str, 
        context_documents: List[RAGDocument] = None
    ) -> Dict[str, Any]:
        """Генерация ответа с использованием RAG"""
        try:
            # Если документы не переданы, ищем их
            if not context_documents:
                context_documents = await self.search_documents(query, limit=3)
            
            # Формируем контекст из документов
            context = self._build_context(context_documents)
            
            # Создаем промпт с контекстом
            system_prompt = """Ты полезный ассистент. Используй предоставленный контекст для ответа на вопросы пользователя. 
            Если в контексте нет информации для ответа, скажи об этом честно."""
            
            user_prompt = f"""Контекст:
{context}

Вопрос: {query}

Ответ:"""
            
            # Генерируем ответ
            response = await self._generate_response(model_name, user_prompt, system_prompt)
            
            # Добавляем информацию о контексте
            response["context_documents"] = [
                {
                    "title": doc.title,
                    "source": doc.source,
                    "relevance_score": doc.relevance_score
                }
                for doc in context_documents
            ]
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка генерации с RAG: {e}")
            return {
                "error": str(e),
                "response": "Извините, произошла ошибка при обработке запроса."
            }
    
    async def _generate_embeddings(self, text: str) -> List[float]:
        """Генерация эмбеддингов для текста"""
        try:
            # Используем простую модель для эмбеддингов
            response = await self.ollama_client.post(
                "/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding", [])
            else:
                # Fallback: используем простые эмбеддинги
                return self._simple_embeddings(text)
                
        except Exception as e:
            logger.warning(f"Ошибка генерации эмбеддингов, используем fallback: {e}")
            return self._simple_embeddings(text)
    
    def _simple_embeddings(self, text: str) -> List[float]:
        """Простая реализация эмбеддингов для fallback"""
        # Простая реализация на основе частоты символов
        import string
        from collections import Counter
        
        # Нормализуем текст
        text = text.lower()
        text = ''.join(c for c in text if c.isalnum() or c.isspace())
        
        # Считаем частоту символов
        char_freq = Counter(text)
        
        # Создаем вектор фиксированной длины
        embedding = [0.0] * 128
        for i, (char, freq) in enumerate(char_freq.most_common(128)):
            if i < 128:
                embedding[i] = freq / len(text)
        
        return embedding
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Вычисление косинусного сходства между векторами"""
        try:
            import numpy as np
            
            # Приводим к одинаковой длине
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]
            
            # Вычисляем косинусное сходство
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Ошибка вычисления косинусного сходства: {e}")
            return 0.0
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста"""
        try:
            # Простая реализация извлечения ключевых слов
            import re
            from collections import Counter
            
            # Удаляем стоп-слова
            stop_words = {
                'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она',
                'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее',
                'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда',
                'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до',
                'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей',
                'может', 'они', 'тут', 'где', 'есть', 'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем',
                'была', 'сам', 'чтоб', 'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет',
                'ж', 'тогда', 'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь',
                'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были', 'куда', 'зачем',
                'всех', 'никогда', 'можно', 'при', 'наконец', 'два', 'об', 'другой', 'хоть', 'после',
                'над', 'больше', 'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 'какая', 'много',
                'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой', 'перед', 'иногда',
                'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им', 'более', 'всегда', 'притом', 'будет',
                'очень', 'нас', 'вдвоем', 'под', 'оборот', 'теперь', 'долго', 'ли', 'очень', 'либо',
                'впрочем', 'все', 'таки', 'более', 'всегда', 'между'
            }
            
            # Нормализуем текст
            text = text.lower()
            text = re.sub(r'[^\w\s]', '', text)
            
            # Разбиваем на слова
            words = text.split()
            
            # Фильтруем стоп-слова и короткие слова
            keywords = [
                word for word in words 
                if word not in stop_words and len(word) > 2
            ]
            
            # Считаем частоту и возвращаем топ-10
            word_freq = Counter(keywords)
            return [word for word, _ in word_freq.most_common(10)]
            
        except Exception as e:
            logger.error(f"Ошибка извлечения ключевых слов: {e}")
            return []
    
    def _build_context(self, documents: List[RAGDocument]) -> str:
        """Построение контекста из документов"""
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"Документ {i}: {doc.title}")
            context_parts.append(f"Источник: {doc.source}")
            context_parts.append(f"Содержание: {doc.content[:500]}...")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def _generate_response(
        self, 
        model_name: str, 
        prompt: str, 
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """Генерация ответа от модели"""
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await self.ollama_client.post(
                "/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("response", ""),
                    "model": model_name,
                    "tokens_used": data.get("eval_count", 0),
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "eval_count": data.get("eval_count", 0)
                }
            else:
                return {
                    "error": f"Ошибка генерации: {response.text}",
                    "response": "Извините, произошла ошибка при генерации ответа."
                }
                
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return {
                "error": str(e),
                "response": "Извините, произошла ошибка при генерации ответа."
            }
    
    async def update_document(self, doc_id: int, updates: Dict[str, Any]) -> Optional[RAGDocument]:
        """Обновление документа"""
        try:
            stmt = select(RAGDocument).where(RAGDocument.id == doc_id)
            result = await self.db.execute(stmt)
            document = result.scalar_one_or_none()
            
            if not document:
                return None
            
            # Обновляем поля
            for key, value in updates.items():
                if hasattr(document, key):
                    setattr(document, key, value)
            
            # Если изменился контент, обновляем эмбеддинги
            if "content" in updates:
                embeddings = await self._generate_embeddings(document.content)
                document.embeddings = json.dumps(embeddings)
                document.keywords = await self._extract_keywords(document.content)
                
                # Обновляем кэш
                self._vector_cache[f"doc_{document.id}"] = embeddings
            
            await self.db.commit()
            await self.db.refresh(document)
            
            return document
            
        except Exception as e:
            logger.error(f"Ошибка обновления документа: {e}")
            return None
    
    async def delete_document(self, doc_id: int) -> bool:
        """Удаление документа"""
        try:
            stmt = select(RAGDocument).where(RAGDocument.id == doc_id)
            result = await self.db.execute(stmt)
            document = result.scalar_one_or_none()
            
            if not document:
                return False
            
            # Удаляем из кэша
            cache_key = f"doc_{document.id}"
            if cache_key in self._vector_cache:
                del self._vector_cache[cache_key]
            
            # Помечаем как неактивный
            document.is_active = False
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления документа: {e}")
            return False
    
    async def get_documents_stats(self) -> Dict[str, Any]:
        """Получение статистики документов"""
        try:
            # Общее количество документов
            total_stmt = select(func.count(RAGDocument.id))
            total_result = await self.db.execute(total_stmt)
            total_docs = total_result.scalar()
            
            # Активные документы
            active_stmt = select(func.count(RAGDocument.id)).where(RAGDocument.is_active == True)
            active_result = await self.db.execute(active_stmt)
            active_docs = active_result.scalar()
            
            # Документы по типам
            type_stmt = select(
                RAGDocument.document_type,
                func.count(RAGDocument.id)
            ).group_by(RAGDocument.document_type)
            type_result = await self.db.execute(type_stmt)
            docs_by_type = dict(type_result.all())
            
            return {
                "total_documents": total_docs,
                "active_documents": active_docs,
                "documents_by_type": docs_by_type,
                "vector_cache_size": len(self._vector_cache)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики документов: {e}")
            return {}


class TuningService:
    """Сервис для динамического тюнинга моделей"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=settings.OLLAMA_TIMEOUT
        )
    
    async def create_tuning_session(self, session_data: Dict[str, Any]) -> TuningSession:
        """Создание сессии тюнинга"""
        session = TuningSession(**session_data)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def get_tuning_session(self, session_id: int) -> Optional[TuningSession]:
        """Получение сессии тюнинга"""
        stmt = select(TuningSession).where(TuningSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_tuning_session(self, session_id: int, updates: Dict[str, Any]) -> Optional[TuningSession]:
        """Обновление сессии тюнинга"""
        stmt = update(TuningSession).where(TuningSession.id == session_id).values(**updates)
        await self.db.execute(stmt)
        await self.db.commit()
        
        return await self.get_tuning_session(session_id)
    
    async def start_tuning(self, session_id: int) -> bool:
        """Запуск процесса тюнинга"""
        session = await self.get_tuning_session(session_id)
        if not session:
            return False
        
        try:
            # Обновляем статус
            await self.update_tuning_session(session_id, {
                "status": ModelStatus.TUNING,
                "started_at": datetime.now()
            })
            
            # Запускаем тюнинг в фоне
            asyncio.create_task(self._run_tuning(session_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при запуске тюнинга: {e}")
            await self.update_tuning_session(session_id, {
                "status": ModelStatus.FAILED,
                "error_message": str(e)
            })
            return False
    
    async def _run_tuning(self, session_id: int):
        """Выполнение процесса тюнинга модели"""
        session = await self.get_tuning_session(session_id)
        if not session:
            logger.error(f"Сессия тюнинга {session_id} не найдена")
            return
        
        try:
            logger.info(f"🚀 Начинаем тюнинг модели для сессии {session_id}")
            
            # Получаем данные модели
            model = await self._get_model_by_session(session_id)
            if not model:
                await self.update_tuning_session(session_id, {
                    "status": ModelStatus.FAILED,
                    "error_message": "Модель не найдена"
                })
                return
            
            # Обновляем статус на "в процессе"
            await self.update_tuning_session(session_id, {
                "status": ModelStatus.TUNING,
                "started_at": datetime.now()
            })
            
            # Этап 1: Подготовка данных (10%)
            logger.info("📊 Этап 1: Подготовка данных для тюнинга")
            await self.update_tuning_session(session_id, {"progress": 10})
            
            training_data = await self._prepare_training_data(session)
            if not training_data:
                await self.update_tuning_session(session_id, {
                    "status": ModelStatus.FAILED,
                    "error_message": "Не удалось подготовить данные для тюнинга"
                })
                return
            
            # Этап 2: Создание Modelfile (20%)
            logger.info("📝 Этап 2: Создание Modelfile")
            await self.update_tuning_session(session_id, {"progress": 20})
            
            modelfile = await self._create_modelfile(model, training_data, session)
            if not modelfile:
                await self.update_tuning_session(session_id, {
                    "status": ModelStatus.FAILED,
                    "error_message": "Не удалось создать Modelfile"
                })
                return
            
            # Этап 3: Загрузка базовой модели (40%)
            logger.info("⬇️ Этап 3: Загрузка базовой модели")
            await self.update_tuning_session(session_id, {"progress": 40})
            
            base_model_loaded = await self._ensure_base_model(model.base_model)
            if not base_model_loaded:
                await self.update_tuning_session(session_id, {
                    "status": ModelStatus.FAILED,
                    "error_message": "Не удалось загрузить базовую модель"
                })
                return
            
            # Этап 4: Создание тюнированной модели (70%)
            logger.info("🔧 Этап 4: Создание тюнированной модели")
            await self.update_tuning_session(session_id, {"progress": 70})
            
            tuned_model_name = f"{model.name}-tuned-{session_id}"
            model_created = await self._create_tuned_model(tuned_model_name, modelfile)
            if not model_created:
                await self.update_tuning_session(session_id, {
                    "status": ModelStatus.FAILED,
                    "error_message": "Не удалось создать тюнированную модель"
                })
                return
            
            # Этап 5: Валидация модели (90%)
            logger.info("✅ Этап 5: Валидация тюнированной модели")
            await self.update_tuning_session(session_id, {"progress": 90})
            
            validation_result = await self._validate_tuned_model(tuned_model_name, session)
            if not validation_result["success"]:
                await self.update_tuning_session(session_id, {
                    "status": ModelStatus.FAILED,
                    "error_message": f"Валидация не пройдена: {validation_result['error']}"
                })
                return
            
            # Этап 6: Завершение (100%)
            logger.info("🎉 Этап 6: Завершение тюнинга")
            await self.update_tuning_session(session_id, {
                "status": ModelStatus.READY,
                "progress": 100,
                "completed_at": datetime.now(),
                "tuned_model_name": tuned_model_name,
                "validation_metrics": validation_result["metrics"]
            })
            
            logger.info(f"✅ Тюнинг модели завершен успешно: {tuned_model_name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка в процессе тюнинга сессии {session_id}: {e}")
            await self.update_tuning_session(session_id, {
                "status": ModelStatus.FAILED,
                "error_message": str(e)
            })
    
    async def _get_model_by_session(self, session_id: int) -> Optional[LLMModel]:
        """Получение модели по ID сессии"""
        stmt = select(TuningSession).where(TuningSession.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        stmt = select(LLMModel).where(LLMModel.id == session.model_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _prepare_training_data(self, session: TuningSession) -> Optional[List[Dict[str, str]]]:
        """Подготовка данных для тюнинга"""
        try:
            # Получаем данные для тюнинга из сессии
            training_data = []
            
            # Примеры запросов и ответов для тюнинга
            if session.training_data:
                training_data = json.loads(session.training_data)
            else:
                # Используем стандартные примеры
                training_data = [
                    {
                        "instruction": "Объясни концепцию машинного обучения",
                        "input": "",
                        "output": "Машинное обучение - это подраздел искусственного интеллекта, который позволяет компьютерам учиться на данных без явного программирования."
                    },
                    {
                        "instruction": "Напиши код для сортировки массива",
                        "input": "массив [3, 1, 4, 1, 5]",
                        "output": "def sort_array(arr):\n    return sorted(arr)\n\n# Пример использования\narr = [3, 1, 4, 1, 5]\nsorted_arr = sort_array(arr)\nprint(sorted_arr)  # [1, 1, 3, 4, 5]"
                    }
                ]
            
            return training_data
            
        except Exception as e:
            logger.error(f"Ошибка подготовки данных для тюнинга: {e}")
            return None
    
    async def _create_modelfile(
        self, 
        model: LLMModel, 
        training_data: List[Dict[str, str]], 
        session: TuningSession
    ) -> Optional[str]:
        """Создание Modelfile для тюнинга"""
        try:
            modelfile_lines = [
                f"FROM {model.base_model}",
                "",
                "# Параметры модели",
                f"PARAMETER temperature {session.parameters.get('temperature', 0.7)}",
                f"PARAMETER top_p {session.parameters.get('top_p', 0.9)}",
                f"PARAMETER top_k {session.parameters.get('top_k', 40)}",
                f"PARAMETER repeat_penalty {session.parameters.get('repeat_penalty', 1.1)}",
                "",
                "# Системный промпт",
                f'SYSTEM """{session.system_prompt or "Ты полезный ассистент."}"""',
                "",
                "# Данные для тюнинга"
            ]
            
            # Добавляем примеры для тюнинга
            for i, example in enumerate(training_data):
                instruction = example.get("instruction", "")
                input_text = example.get("input", "")
                output = example.get("output", "")
                
                if input_text:
                    prompt = f"{instruction}\n\nВходные данные: {input_text}"
                else:
                    prompt = instruction
                
                modelfile_lines.extend([
                    f"# Пример {i+1}",
                    f'PROMPT """{prompt}"""',
                    f'RESPONSE """{output}"""',
                    ""
                ])
            
            modelfile = "\n".join(modelfile_lines)
            logger.info(f"Создан Modelfile для модели {model.name}")
            return modelfile
            
        except Exception as e:
            logger.error(f"Ошибка создания Modelfile: {e}")
            return None
    
    async def _ensure_base_model(self, base_model: str) -> bool:
        """Проверка и загрузка базовой модели"""
        try:
            # Проверяем, есть ли модель в Ollama
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model["name"] for model in models]
                    
                    if base_model in model_names:
                        logger.info(f"Базовая модель {base_model} уже загружена")
                        return True
            
            # Если модель не найдена, пытаемся загрузить
            logger.info(f"Загружаем базовую модель {base_model}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/pull",
                    json={"name": base_model}
                )
                
                if response.status_code == 200:
                    logger.info(f"Базовая модель {base_model} успешно загружена")
                    return True
                else:
                    logger.error(f"Ошибка загрузки базовой модели {base_model}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка проверки базовой модели: {e}")
            return False
    
    async def _create_tuned_model(self, model_name: str, modelfile: str) -> bool:
        """Создание тюнированной модели"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/create",
                    json={
                        "name": model_name,
                        "modelfile": modelfile
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Тюнированная модель {model_name} создана успешно")
                    return True
                else:
                    logger.error(f"Ошибка создания тюнированной модели: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка создания тюнированной модели: {e}")
            return False
    
    async def _validate_tuned_model(self, model_name: str, session: TuningSession) -> Dict[str, Any]:
        """Валидация тюнированной модели"""
        try:
            # Тестовые запросы для валидации
            test_queries = [
                "Привет, как дела?",
                "Объясни простыми словами, что такое API",
                "Напиши короткое стихотворение о программировании"
            ]
            
            results = []
            total_tokens = 0
            total_time = 0
            
            async with httpx.AsyncClient() as client:
                for query in test_queries:
                    start_time = time.time()
                    
                    response = await client.post(
                        f"{settings.OLLAMA_BASE_URL}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": query,
                            "stream": False
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        end_time = time.time()
                        
                        results.append({
                            "query": query,
                            "response": result.get("response", ""),
                            "tokens": result.get("eval_count", 0),
                            "time": end_time - start_time
                        })
                        
                        total_tokens += result.get("eval_count", 0)
                        total_time += end_time - start_time
                    else:
                        return {
                            "success": False,
                            "error": f"Ошибка валидации: {response.text}"
                        }
            
            # Вычисляем метрики
            avg_response_time = total_time / len(results) if results else 0
            avg_tokens = total_tokens / len(results) if results else 0
            
            # Проверяем качество ответов (простая проверка на длину)
            quality_score = sum(1 for r in results if len(r["response"]) > 10) / len(results)
            
            metrics = {
                "avg_response_time": avg_response_time,
                "avg_tokens": avg_tokens,
                "quality_score": quality_score,
                "test_queries_count": len(test_queries),
                "successful_responses": len(results)
            }
            
            # Критерии успешной валидации
            success = (
                avg_response_time < 5.0 and  # Время ответа менее 5 секунд
                quality_score > 0.8 and      # Качество ответов более 80%
                len(results) == len(test_queries)  # Все запросы обработаны
            )
            
            return {
                "success": success,
                "metrics": metrics,
                "error": None if success else "Модель не прошла валидацию"
            }
            
        except Exception as e:
            logger.error(f"Ошибка валидации модели: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class PerformanceMonitor:
    """Монитор производительности моделей"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def record_metrics(self, metrics_data: Dict[str, Any]) -> PerformanceMetrics:
        """Запись метрик производительности"""
        metrics = PerformanceMetrics(**metrics_data)
        self.db.add(metrics)
        await self.db.commit()
        await self.db.refresh(metrics)
        return metrics
    
    async def get_model_metrics(
        self, 
        model_id: int, 
        start_time: datetime = None, 
        end_time: datetime = None
    ) -> List[PerformanceMetrics]:
        """Получение метрик модели за период"""
        stmt = select(PerformanceMetrics).where(PerformanceMetrics.model_id == model_id)
        
        if start_time:
            stmt = stmt.where(PerformanceMetrics.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(PerformanceMetrics.timestamp <= end_time)
        
        stmt = stmt.order_by(PerformanceMetrics.timestamp.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_performance_summary(self, model_id: int) -> Dict[str, Any]:
        """Получение сводки производительности модели"""
        # Получаем метрики за последние 24 часа
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        metrics = await self.get_model_metrics(model_id, start_time, end_time)
        
        if not metrics:
            return {}
        
        # Вычисляем статистики
        response_times = [m.response_time for m in metrics if m.response_time]
        token_counts = [m.tokens_generated for m in metrics if m.tokens_generated]
        success_rates = [m.success_rate for m in metrics if m.success_rate]
        
        return {
            "total_requests": len(metrics),
            "avg_response_time": np.mean(response_times) if response_times else 0,
            "avg_tokens_generated": np.mean(token_counts) if token_counts else 0,
            "avg_success_rate": np.mean(success_rates) if success_rates else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
        }
    
    async def log_api_call(self, log_data: Dict[str, Any]) -> APILog:
        """Логирование API вызова"""
        log = APILog(**log_data)
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log


class OptimizationService:
    """Сервис для оптимизации моделей"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=settings.OLLAMA_TIMEOUT
        )
    
    async def optimize_model(self, model_id: int, optimization_params: Dict[str, Any]) -> Dict[str, Any]:
        """Оптимизация модели"""
        model = await self._get_model(model_id)
        if not model:
            return {"error": "Модель не найдена"}
        
        try:
            # Анализируем текущую производительность
            performance = await self._analyze_performance(model_id)
            
            # Определяем оптимальные параметры
            optimal_params = await self._calculate_optimal_params(performance, optimization_params)
            
            # Применяем оптимизацию
            result = await self._apply_optimization(model.name, optimal_params)
            
            return {
                "model_id": model_id,
                "optimization_applied": True,
                "new_params": optimal_params,
                "performance_improvement": result.get("improvement", 0)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при оптимизации модели: {e}")
            return {"error": str(e)}
    
    async def _get_model(self, model_id: int) -> Optional[LLMModel]:
        """Получение модели"""
        stmt = select(LLMModel).where(LLMModel.id == model_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _analyze_performance(self, model_id: int) -> Dict[str, Any]:
        """Анализ производительности модели"""
        # Получаем метрики за последний час
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        stmt = select(PerformanceMetrics).where(
            and_(
                PerformanceMetrics.model_id == model_id,
                PerformanceMetrics.timestamp >= start_time,
                PerformanceMetrics.timestamp <= end_time
            )
        )
        
        result = await self.db.execute(stmt)
        metrics = result.scalars().all()
        
        if not metrics:
            return {}
        
        # Вычисляем статистики
        response_times = [m.response_time for m in metrics if m.response_time]
        token_counts = [m.tokens_generated for m in metrics if m.tokens_generated]
        
        return {
            "avg_response_time": np.mean(response_times) if response_times else 0,
            "avg_tokens": np.mean(token_counts) if token_counts else 0,
            "total_requests": len(metrics),
            "success_rate": sum(1 for m in metrics if m.success_rate > 0.8) / len(metrics)
        }
    
    async def _calculate_optimal_params(
        self, 
        performance: Dict[str, Any], 
        optimization_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Расчет оптимальных параметров"""
        # Простая эвристика оптимизации
        target_response_time = optimization_params.get("target_response_time", 1.0)
        target_quality = optimization_params.get("target_quality", 0.8)
        
        current_response_time = performance.get("avg_response_time", 0)
        current_quality = performance.get("success_rate", 0)
        
        # Корректируем параметры
        temperature_adjustment = 0.1 if current_quality < target_quality else -0.05
        top_p_adjustment = 0.05 if current_quality < target_quality else -0.02
        
        return {
            "temperature": max(0.1, min(1.0, 0.7 + temperature_adjustment)),
            "top_p": max(0.1, min(1.0, 0.9 + top_p_adjustment)),
            "num_predict": optimization_params.get("num_predict", 1000),
            "repeat_penalty": optimization_params.get("repeat_penalty", 1.1)
        }
    
    async def _apply_optimization(self, model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Применение оптимизации к модели"""
        # В реальной системе здесь будет применение параметров к модели
        # Пока что возвращаем симуляцию
        
        return {
            "improvement": 0.15,  # 15% улучшение
            "applied_params": params
        }


class LLMTuningService:
    """Главный сервис для координации всех операций LLM Tuning"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.model_manager = ModelManager(db_session)
        self.route_manager = RouteManager(db_session)
        self.rag_service = RAGService(db_session)
        self.tuning_service = TuningService(db_session)
        self.performance_monitor = PerformanceMonitor(db_session)
        self.optimization_service = OptimizationService(db_session)
    
    async def process_request(
        self, 
        request_type: str, 
        content: str, 
        use_rag: bool = False,
        optimization_level: str = "balanced"
    ) -> Dict[str, Any]:
        """Обработка запроса с автоматической маршрутизацией"""
        start_time = time.time()
        
        try:
            # Определяем оптимальный маршрут
            route = await self.route_manager.get_route(request_type, content)
            if not route:
                return {"error": "Не найден подходящий маршрут"}
            
            # Получаем модель
            model = await self.model_manager.get_model(route.model_id)
            if not model:
                return {"error": "Модель не найдена"}
            
            # Обрабатываем запрос
            if use_rag:
                result = await self.rag_service.generate_with_rag(model.name, content)
            else:
                result = await self._generate_response(model.name, content, route.parameters)
            
            # Записываем метрики
            response_time = time.time() - start_time
            await self.performance_monitor.record_metrics({
                "model_id": model.id,
                "route_id": route.id,
                "request_type": request_type,
                "response_time": response_time,
                "tokens_generated": result.get("tokens_generated", 0),
                "success_rate": 1.0 if "response" in result else 0.0,
                "timestamp": datetime.now()
            })
            
            # Логируем API вызов
            await self.performance_monitor.log_api_call({
                "model_id": model.id,
                "route_id": route.id,
                "request_type": request_type,
                "request_content": content[:1000],  # Ограничиваем размер
                "response_time": response_time,
                "status_code": 200,
                "timestamp": datetime.now()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            return {"error": str(e)}
    
    async def _generate_response(
        self, 
        model_name: str, 
        content: str, 
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Генерация ответа от модели"""
        if not parameters:
            parameters = {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1000
            }
        
        response = await self.rag_service.ollama_client.post(
            f"/api/generate",
            json={
                "model": model_name,
                "prompt": content,
                "stream": False,
                "options": parameters
            }
        )
        
        return response.json()
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        try:
            # Получаем статистики
            models = await self.model_manager.list_models()
            active_routes = len([r for r in self.route_manager._route_cache.values() if r.is_active])
            
            # Получаем метрики производительности
            total_requests = 0
            avg_response_time = 0
            
            if models:
                for model in models:
                    summary = await self.performance_monitor.get_performance_summary(model.id)
                    total_requests += summary.get("total_requests", 0)
                    avg_response_time += summary.get("avg_response_time", 0)
                
                avg_response_time /= len(models)
            
            return {
                "status": "healthy",
                "models_count": len(models),
                "active_routes": active_routes,
                "total_requests_24h": total_requests,
                "avg_response_time": avg_response_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса системы: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 