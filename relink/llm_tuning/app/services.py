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
    
    async def add_document(self, document_data: Dict[str, Any]) -> RAGDocument:
        """Добавление документа в RAG систему"""
        document = RAGDocument(**document_data)
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document
    
    async def search_documents(self, query: str, limit: int = 5) -> List[RAGDocument]:
        """Поиск релевантных документов"""
        # Простой поиск по ключевым словам
        # В реальной системе здесь будет векторный поиск
        stmt = select(RAGDocument).where(
            or_(
                RAGDocument.content.contains(query),
                RAGDocument.metadata.contains({"keywords": query})
            )
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def generate_with_rag(
        self, 
        model_name: str, 
        query: str, 
        context_documents: List[RAGDocument] = None
    ) -> Dict[str, Any]:
        """Генерация ответа с использованием RAG"""
        if not context_documents:
            context_documents = await self.search_documents(query)
        
        # Формируем контекст
        context = "\n\n".join([doc.content for doc in context_documents])
        
        # Создаем промпт с контекстом
        prompt = f"""Используй следующий контекст для ответа на вопрос:

Контекст:
{context}

Вопрос: {query}

Ответ:"""
        
        # Отправляем запрос к модели
        response = await self.ollama_client.post(
            f"/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            }
        )
        
        return response.json()


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
        """Выполнение процесса тюнинга"""
        session = await self.get_tuning_session(session_id)
        if not session:
            return
        
        try:
            # Здесь будет логика тюнинга модели
            # Пока что симулируем процесс
            
            # Обновляем прогресс
            for progress in range(0, 101, 10):
                await self.update_tuning_session(session_id, {
                    "progress": progress
                })
                await asyncio.sleep(1)  # Симуляция работы
            
            # Завершаем тюнинг
            await self.update_tuning_session(session_id, {
                "status": ModelStatus.READY,
                "completed_at": datetime.now(),
                "progress": 100
            })
            
        except Exception as e:
            logger.error(f"Ошибка в процессе тюнинга: {e}")
            await self.update_tuning_session(session_id, {
                "status": ModelStatus.FAILED,
                "error_message": str(e)
            })


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