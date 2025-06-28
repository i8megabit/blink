"""
Конкурентный менеджер для использования Ollama
"""

import asyncio
import aiohttp
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json

from .types import LLMRequest, LLMResponse, RequestStatus, PerformanceMetrics

logger = logging.getLogger(__name__)

@dataclass
class OllamaConfig:
    """Конфигурация Ollama для Apple M4"""
    base_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:7b"
    max_concurrent_requests: int = 2  # Apple M4 оптимизация
    request_timeout: float = 300.0  # 5 минут
    keep_alive: str = "2h"  # Оптимизация для Apple Silicon
    context_length: int = 4096
    batch_size: int = 512
    num_parallel: int = 2

class LoadMonitor:
    """Мониторинг нагрузки Ollama"""
    
    def __init__(self):
        self.request_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = time.time()
    
    def record_request(self, response_time: float, success: bool = True):
        """Запись метрик запроса"""
        self.request_times.append(response_time)
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        # Ограничиваем размер списка
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
    
    def get_avg_response_time(self) -> float:
        """Среднее время ответа"""
        if not self.request_times:
            return 0.0
        return sum(self.request_times) / len(self.request_times)
    
    def get_success_rate(self) -> float:
        """Процент успешных запросов"""
        total = self.success_count + self.error_count
        if total == 0:
            return 100.0
        return (self.success_count / total) * 100
    
    def get_uptime(self) -> float:
        """Время работы"""
        return time.time() - self.start_time

class ConcurrentOllamaManager:
    """Менеджер конкурентного использования Ollama"""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Семафор для ограничения конкурентности
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        # Кэши для эмбеддингов и ответов
        self.embedding_cache: Dict[str, List[float]] = {}
        self.response_cache: Dict[str, LLMResponse] = {}
        
        # Мониторинг нагрузки
        self.load_monitor = LoadMonitor()
        
        # Активные запросы
        self.active_requests: Dict[str, asyncio.Task] = {}
        
        logger.info(f"ConcurrentOllamaManager инициализирован с лимитом {self.config.max_concurrent_requests} запросов")
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Завершение работы"""
        await self.stop()
    
    async def start(self):
        """Запуск менеджера"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("HTTP сессия для Ollama создана")
    
    async def stop(self):
        """Остановка менеджера"""
        # Отменяем все активные запросы
        for task in self.active_requests.values():
            task.cancel()
        
        # Ждем завершения всех задач
        if self.active_requests:
            await asyncio.gather(*self.active_requests.values(), return_exceptions=True)
        
        # Закрываем сессию
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("ConcurrentOllamaManager остановлен")
    
    async def process_request(self, request: LLMRequest) -> LLMResponse:
        """Обработка запроса к Ollama"""
        if self.session is None:
            await self.start()
        
        # Проверяем кэш ответов
        cache_key = self._generate_response_cache_key(request)
        if cache_key in self.response_cache:
            logger.info(f"Кэш-хит для запроса {request.id}")
            return self.response_cache[cache_key]
        
        # Получаем семафор для ограничения конкурентности
        async with self.semaphore:
            start_time = time.time()
            
            try:
                # Выполняем запрос к Ollama
                response_text = await self._call_ollama_api(request)
                
                # Создаем ответ
                response_time = time.time() - start_time
                response = LLMResponse(
                    request_id=request.id,
                    response=response_text,
                    model_used=request.model_name,
                    tokens_used=len(response_text.split()),  # Приблизительный подсчет
                    response_time=response_time,
                    rag_enhanced=False,
                    cache_hit=False
                )
                
                # Кэшируем ответ
                self.response_cache[cache_key] = response
                
                # Обновляем метрики
                self.load_monitor.record_request(response_time, success=True)
                
                logger.info(f"Запрос {request.id} обработан за {response_time:.2f}s")
                return response
                
            except Exception as e:
                response_time = time.time() - start_time
                self.load_monitor.record_request(response_time, success=False)
                logger.error(f"Ошибка обработки запроса {request.id}: {e}")
                raise
    
    async def generate_response(
        self, 
        prompt: str, 
        model_name: str = None, 
        max_tokens: int = 100, 
        temperature: float = 0.7
    ) -> str:
        """Генерация ответа от Ollama"""
        model_name = model_name or self.config.model_name
        
        request = LLMRequest(
            id=str(uuid.uuid4()),
            prompt=prompt,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        response = await self.process_request(request)
        return response.response
    
    async def get_embedding(self, text: str, model_name: str = "qwen2.5:7b") -> List[float]:
        """Получение эмбеддинга для текста"""
        # Проверяем кэш эмбеддингов
        cache_key = f"{model_name}:{hash(text)}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        if self.session is None:
            await self.start()
        
        async with self.semaphore:
            try:
                # Вызываем API эмбеддингов Ollama
                url = f"{self.config.base_url}/api/embeddings"
                payload = {
                    "model": model_name,
                    "prompt": text
                }
                
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        embedding = data.get("embedding", [])
                        
                        # Кэшируем эмбеддинг
                        self.embedding_cache[cache_key] = embedding
                        
                        logger.info(f"Эмбеддинг получен для текста длиной {len(text)}")
                        return embedding
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ошибка получения эмбеддинга: {response.status} - {error_text}")
            
            except Exception as e:
                logger.error(f"Ошибка получения эмбеддинга: {e}")
                raise
    
    async def get_response(self, request_id: str) -> Optional[LLMResponse]:
        """Получение ответа по ID запроса"""
        # Проверяем активные запросы
        if request_id in self.active_requests:
            task = self.active_requests[request_id]
            if not task.done():
                return None
            
            try:
                return await task
            except Exception as e:
                logger.error(f"Ошибка получения ответа для {request_id}: {e}")
                return None
            finally:
                del self.active_requests[request_id]
        
        # Проверяем кэш
        for response in self.response_cache.values():
            if response.request_id == request_id:
                return response
        
        return None
    
    async def _call_ollama_api(self, request: LLMRequest) -> str:
        """Вызов API Ollama"""
        url = f"{self.config.base_url}/api/generate"
        
        # Формируем payload с оптимизациями для Apple M4
        payload = {
            "model": request.model_name,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "num_predict": request.max_tokens,
                "temperature": request.temperature,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "seed": 42,
                "num_ctx": self.config.context_length,
                "num_batch": self.config.batch_size,
                "num_thread": self.config.num_parallel,
                "keep_alive": self.config.keep_alive
            }
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("response", "")
            else:
                error_text = await response.text()
                raise Exception(f"Ошибка API Ollama: {response.status} - {error_text}")
    
    def _generate_response_cache_key(self, request: LLMRequest) -> str:
        """Генерация ключа кэша для ответа"""
        import hashlib
        
        key_parts = [
            request.prompt,
            request.model_name,
            str(request.max_tokens),
            str(request.temperature)
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья Ollama"""
        try:
            if self.session is None:
                return {"status": "disconnected", "error": "Session not initialized"}
            
            # Проверяем доступность Ollama
            url = f"{self.config.base_url}/api/tags"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    
                    return {
                        "status": "healthy",
                        "available_models": [model["name"] for model in models],
                        "avg_response_time": self.load_monitor.get_avg_response_time(),
                        "success_rate": self.load_monitor.get_success_rate(),
                        "uptime": self.load_monitor.get_uptime(),
                        "active_requests": len(self.active_requests),
                        "cache_size": len(self.response_cache)
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status}",
                        "avg_response_time": self.load_monitor.get_avg_response_time(),
                        "success_rate": self.load_monitor.get_success_rate()
                    }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "avg_response_time": self.load_monitor.get_avg_response_time(),
                "success_rate": self.load_monitor.get_success_rate()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик менеджера"""
        return {
            "active_requests": len(self.active_requests),
            "response_cache_size": len(self.response_cache),
            "embedding_cache_size": len(self.embedding_cache),
            "avg_response_time": self.load_monitor.get_avg_response_time(),
            "success_rate": self.load_monitor.get_success_rate(),
            "uptime": self.load_monitor.get_uptime(),
            "total_requests": self.load_monitor.success_count + self.load_monitor.error_count
        }
    
    def clear_cache(self):
        """Очистка кэшей"""
        self.response_cache.clear()
        self.embedding_cache.clear()
        logger.info("Кэши очищены")
    
    async def list_models(self) -> List[str]:
        """Список доступных моделей"""
        try:
            if self.session is None:
                await self.start()
            
            url = f"{self.config.base_url}/api/tags"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["name"] for model in data.get("models", [])]
                else:
                    logger.error(f"Ошибка получения списка моделей: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Ошибка получения списка моделей: {e}")
            return [] 