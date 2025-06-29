"""
Централизованная архитектура LLM для reLink
Обеспечивает единую точку доступа к Ollama с приоритизацией и кэшированием
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from .types import LLMRequest, LLMResponse, RequestPriority, RequestStatus, PerformanceMetrics
from .concurrent_manager import ConcurrentOllamaManager
from .distributed_cache import DistributedCache
from .request_prioritizer import RequestPrioritizer
from .rag_monitor import RAGMonitor

logger = logging.getLogger(__name__)

@dataclass
class LLMRequest:
    """Запрос к LLM"""
    id: str
    prompt: str
    llm_model: str = "qwen2.5:7b-instruct-turbo"
    priority: str = "normal"
    max_tokens: int = 100
    temperature: float = 0.7
    use_rag: bool = True
    user_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class LLMResponse:
    """Ответ от LLM"""
    request_id: str
    response: str
    used_model: str
    tokens_used: int
    response_time: float
    rag_enhanced: bool
    cache_hit: bool
    created_at: datetime = field(default_factory=datetime.utcnow)

class CentralizedLLMArchitecture:
    """Централизованная архитектура для конкурентного использования Ollama"""
    
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.concurrent_manager = ConcurrentOllamaManager()
        self.cache_manager = DistributedCache(redis_url)
        self.request_prioritizer = RequestPrioritizer()
        self.monitoring = RAGMonitor()
        
        # Очередь запросов с приоритетами
        self.request_queue = asyncio.PriorityQueue()
        
        # Семафор для ограничения конкурентности (Apple M4 оптимизация)
        self.semaphore = asyncio.Semaphore(2)
        
        # Флаг для остановки обработки
        self._running = False
        self._processor_task = None
        
        logger.info("Централизованная LLM архитектура инициализирована")
    
    async def start(self):
        """Запуск архитектуры"""
        if self._running:
            logger.warning("Архитектура уже запущена")
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_queue())
        logger.info("Централизованная LLM архитектура запущена")
    
    async def stop(self):
        """Остановка архитектуры"""
        if not self._running:
            return
        
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Централизованная LLM архитектура остановлена")
    
    async def submit_request(self, request: LLMRequest) -> str:
        """Отправка запроса в очередь"""
        if not self._running:
            raise RuntimeError("Архитектура не запущена")
        
        # Определяем приоритет
        priority = self.request_prioritizer.get_priority(request.priority)
        
        # Добавляем в очередь
        await self.request_queue.put((priority, request))
        
        # Обновляем метрики
        self.monitoring.increment_metric("queue_size", 1)
        self.monitoring.increment_metric("total_requests", 1)
        
        logger.info(f"Запрос {request.id} добавлен в очередь с приоритетом {request.priority}")
        return request.id
    
    async def get_response(self, request_id: str, timeout: float = 30.0) -> Optional[LLMResponse]:
        """Получение ответа по ID запроса"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Проверяем кэш
            cached_response = await self.cache_manager.get_response(request_id)
            if cached_response:
                logger.info(f"Ответ для запроса {request_id} найден в кэше")
                return cached_response
            
            # Проверяем завершенные запросы
            response = await self.concurrent_manager.get_response(request_id)
            if response:
                # Кэшируем ответ
                await self.cache_manager.cache_response(request_id, response)
                logger.info(f"Ответ для запроса {request_id} получен")
                return response
            
            await asyncio.sleep(0.1)
        
        logger.warning(f"Таймаут ожидания ответа для запроса {request_id}")
        return None
    
    async def _process_queue(self):
        """Обработка очереди запросов"""
        logger.info("Начата обработка очереди запросов")
        
        while self._running:
            try:
                # Получаем запрос из очереди
                priority, request = await asyncio.wait_for(
                    self.request_queue.get(), 
                    timeout=1.0
                )
                
                # Обрабатываем запрос
                asyncio.create_task(self._process_request(request))
                
                # Обновляем метрики
                self.monitoring.increment_metric("queue_size", -1)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Ошибка обработки очереди: {e}")
                continue
        
        logger.info("Обработка очереди запросов остановлена")
    
    async def _process_request(self, request: LLMRequest):
        """Обработка отдельного запроса"""
        start_time = time.time()
        
        try:
            # Проверяем кэш
            cache_key = self._generate_cache_key(request)
            cached_response = await self.cache_manager.get_response(cache_key)
            
            if cached_response:
                logger.info(f"Кэш-хит для запроса {request.id}")
                self.monitoring.increment_metric("cache_hits", 1)
                return cached_response
            
            # Получаем семафор для ограничения конкурентности
            async with self.semaphore:
                self.monitoring.increment_metric("concurrent_requests", 1)
                
                try:
                    # Обрабатываем запрос через конкурентный менеджер
                    response = await self.concurrent_manager.process_request(request)
                    
                    # Обогащаем RAG контекстом если нужно
                    if request.use_rag:
                        response = await self._enhance_with_rag(request, response)
                        self.monitoring.increment_metric("rag_enhancements", 1)
                    
                    # Кэшируем результат
                    await self.cache_manager.cache_response(cache_key, response)
                    
                    # Обновляем метрики
                    response_time = time.time() - start_time
                    self.monitoring.update_metric("avg_response_time", response_time)
                    
                    logger.info(f"Запрос {request.id} обработан за {response_time:.2f}s")
                    return response
                    
                finally:
                    self.monitoring.increment_metric("concurrent_requests", -1)
        
        except Exception as e:
            logger.error(f"Ошибка обработки запроса {request.id}: {e}")
            self.monitoring.increment_metric("errors", 1)
            raise
    
    async def _enhance_with_rag(self, request: LLMRequest, response: LLMResponse) -> LLMResponse:
        """Обогащение ответа RAG контекстом"""
        try:
            # Получаем релевантные документы
            relevant_docs = await self.cache_manager.search_knowledge_base(
                request.prompt, 
                limit=3
            )
            
            if relevant_docs:
                # Обогащаем промпт контекстом
                enhanced_prompt = self._build_enhanced_prompt(request.prompt, relevant_docs)
                
                # Перегенерируем ответ с контекстом
                enhanced_response = await self.concurrent_manager.generate_response(
                    enhanced_prompt,
                    request.llm_model,
                    request.max_tokens,
                    request.temperature
                )
                
                # Обновляем ответ
                response.response = enhanced_response
                response.rag_enhanced = True
                
                logger.info(f"Ответ для запроса {request.id} обогащен RAG контекстом")
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка RAG обогащения для запроса {request.id}: {e}")
            return response
    
    def _build_enhanced_prompt(self, original_prompt: str, relevant_docs: List[str]) -> str:
        """Построение обогащенного промпта"""
        context = "\n".join(relevant_docs)
        
        enhanced_prompt = f"""
        Контекст для ответа:
        {context}
        
        Вопрос пользователя:
        {original_prompt}
        
        Ответь на основе предоставленного контекста:
        """
        
        return enhanced_prompt
    
    def _generate_cache_key(self, request: LLMRequest) -> str:
        """Генерация ключа кэша для запроса"""
        # Создаем хеш на основе параметров запроса
        key_parts = [
            request.prompt,
            request.llm_model,
            str(request.max_tokens),
            str(request.temperature),
            str(request.use_rag)
        ]
        
        import hashlib
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик архитектуры"""
        return {
            "queue_size": self.request_queue.qsize(),
            "concurrent_requests": self.monitoring.get_metric("concurrent_requests"),
            "total_requests": self.monitoring.get_metric("total_requests"),
            "cache_hits": self.monitoring.get_metric("cache_hits"),
            "rag_enhancements": self.monitoring.get_metric("rag_enhancements"),
            "avg_response_time": self.monitoring.get_metric("avg_response_time"),
            "errors": self.monitoring.get_metric("errors"),
            "uptime": time.time() - self.monitoring.start_time
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья архитектуры"""
        return {
            "status": "healthy" if self._running else "stopped",
            "queue_size": self.request_queue.qsize(),
            "concurrent_requests": self.monitoring.get_metric("concurrent_requests"),
            "cache_status": await self.cache_manager.health_check(),
            "ollama_status": await self.concurrent_manager.health_check()
        }

# Глобальный экземпляр архитектуры
_global_architecture: Optional[CentralizedLLMArchitecture] = None

async def get_architecture() -> CentralizedLLMArchitecture:
    """Получение глобального экземпляра архитектуры"""
    global _global_architecture
    
    if _global_architecture is None:
        _global_architecture = CentralizedLLMArchitecture()
        await _global_architecture.start()
    
    return _global_architecture

async def shutdown_architecture():
    """Завершение работы архитектуры"""
    global _global_architecture
    
    if _global_architecture:
        await _global_architecture.stop()
        _global_architecture = None 