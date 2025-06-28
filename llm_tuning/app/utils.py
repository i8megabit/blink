"""
🧠 Утилиты для LLM Tuning микросервиса
Оптимизированные функции для работы с Ollama, кэшированием, валидацией и метриками
"""

import asyncio
import aiohttp
import json
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from functools import wraps, lru_cache
from dataclasses import dataclass
from datetime import datetime, timedelta
import redis.asyncio as redis
from pydantic import BaseModel, validator
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Конфигурация для Ollama клиента"""
    base_url: str = "http://localhost:11434"
    timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Apple Silicon оптимизации
    metal_enabled: bool = True
    flash_attention: bool = True
    kv_cache_type: str = "q8_0"
    context_length: int = 4096
    batch_size: int = 512
    num_parallel: int = 2
    mem_fraction: float = 0.9


class OllamaClient:
    """Асинхронный клиент для работы с Ollama API"""
    
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._models_cache: Dict[str, Dict] = {}
        self._cache_ttl = 300  # 5 минут
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Выполнение HTTP запроса с повторными попытками"""
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.request(method, endpoint, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise ValueError(f"Endpoint not found: {endpoint}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
    
    async def list_models(self) -> List[Dict]:
        """Получение списка доступных моделей"""
        cache_key = f"models_list_{int(time.time() // self._cache_ttl)}"
        
        if cache_key in self._models_cache:
            return self._models_cache[cache_key]
        
        try:
            result = await self._make_request("GET", "/api/tags")
            models = result.get("models", [])
            self._models_cache[cache_key] = models
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def generate(self, model: str, prompt: str, **kwargs) -> Dict:
        """Генерация текста с помощью модели"""
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        # Apple Silicon оптимизации
        if self.config.metal_enabled:
            data["options"] = {
                "num_gpu": 1,
                "num_thread": self.config.num_parallel,
                "num_ctx": self.config.context_length,
                "batch_size": self.config.batch_size,
                "rope_freq_base": 10000,
                "rope_freq_scale": 0.5
            }
        
        return await self._make_request("POST", "/api/generate", data)
    
    async def chat(self, model: str, messages: List[Dict], **kwargs) -> Dict:
        """Чат с моделью"""
        data = {
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        # Apple Silicon оптимизации
        if self.config.metal_enabled:
            data["options"] = {
                "num_gpu": 1,
                "num_thread": self.config.num_parallel,
                "num_ctx": self.config.context_length,
                "batch_size": self.config.batch_size
            }
        
        return await self._make_request("POST", "/api/chat", data)
    
    async def create_model(self, name: str, modelfile: str) -> Dict:
        """Создание новой модели"""
        data = {
            "name": name,
            "modelfile": modelfile
        }
        return await self._make_request("POST", "/api/create", data)
    
    async def pull_model(self, name: str) -> Dict:
        """Загрузка модели из реестра"""
        data = {"name": name}
        return await self._make_request("POST", "/api/pull", data)
    
    async def delete_model(self, name: str) -> Dict:
        """Удаление модели"""
        data = {"name": name}
        return await self._make_request("DELETE", "/api/delete", data)
    
    async def get_model_info(self, name: str) -> Dict:
        """Получение информации о модели"""
        return await self._make_request("GET", f"/api/show", {"name": name})


class CacheManager:
    """Менеджер кэширования с Redis"""
    
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis_url = redis_url
        self.ttl = ttl
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Подключение к Redis"""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Генерация ключа кэша"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    async def get(self, prefix: str, *args) -> Optional[Any]:
        """Получение значения из кэша"""
        await self.connect()
        key = self._generate_key(prefix, *args)
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, prefix: str, value: Any, ttl: int = None, *args):
        """Установка значения в кэш"""
        await self.connect()
        key = self._generate_key(prefix, *args)
        try:
            await self.redis.setex(
                key, 
                ttl or self.ttl, 
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, prefix: str, *args):
        """Удаление значения из кэша"""
        await self.connect()
        key = self._generate_key(prefix, *args)
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def clear_pattern(self, pattern: str):
        """Очистка кэша по паттерну"""
        await self.connect()
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")


class SecurityUtils:
    """Утилиты безопасности"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Проверка пароля"""
        return SecurityUtils.hash_password(password) == hashed
    
    @staticmethod
    def generate_api_key() -> str:
        """Генерация API ключа"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Очистка входных данных"""
        import re
        # Удаление потенциально опасных символов
        sanitized = re.sub(r'[<>"\']', '', text)
        return sanitized.strip()
    
    @staticmethod
    def validate_rate_limit(user_id: str, limit: int, window: int) -> bool:
        """Валидация rate limit"""
        # Простая реализация - в продакшене использовать Redis
        return True


class ValidationUtils:
    """Утилиты валидации"""
    
    @staticmethod
    def validate_model_name(name: str) -> bool:
        """Валидация имени модели"""
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, name)) and len(name) <= 100
    
    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """Валидация промпта"""
        return len(prompt.strip()) > 0 and len(prompt) <= 10000
    
    @staticmethod
    def validate_temperature(temp: float) -> bool:
        """Валидация температуры"""
        return 0.0 <= temp <= 2.0
    
    @staticmethod
    def validate_max_tokens(tokens: int) -> bool:
        """Валидация максимального количества токенов"""
        return 1 <= tokens <= 8192
    
    @staticmethod
    def validate_context_length(length: int) -> bool:
        """Валидация длины контекста"""
        return 512 <= length <= 32768


class MetricsCollector:
    """Сборщик метрик производительности"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "response_times": [],
            "token_counts": [],
            "error_rates": [],
            "cache_hits": [],
            "cache_misses": []
        }
    
    def record_response_time(self, time_ms: float):
        """Запись времени ответа"""
        self.metrics["response_times"].append(time_ms)
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
    
    def record_token_count(self, count: int):
        """Запись количества токенов"""
        self.metrics["token_counts"].append(count)
        if len(self.metrics["token_counts"]) > 1000:
            self.metrics["token_counts"] = self.metrics["token_counts"][-1000:]
    
    def record_error(self):
        """Запись ошибки"""
        self.metrics["error_rates"].append(1.0)
        if len(self.metrics["error_rates"]) > 1000:
            self.metrics["error_rates"] = self.metrics["error_rates"][-1000:]
    
    def record_success(self):
        """Запись успешного запроса"""
        self.metrics["error_rates"].append(0.0)
        if len(self.metrics["error_rates"]) > 1000:
            self.metrics["error_rates"] = self.metrics["error_rates"][-1000:]
    
    def record_cache_hit(self):
        """Запись попадания в кэш"""
        self.metrics["cache_hits"].append(1.0)
        if len(self.metrics["cache_hits"]) > 1000:
            self.metrics["cache_hits"] = self.metrics["cache_hits"][-1000:]
    
    def record_cache_miss(self):
        """Запись промаха кэша"""
        self.metrics["cache_misses"].append(1.0)
        if len(self.metrics["cache_misses"]) > 1000:
            self.metrics["cache_misses"] = self.metrics["cache_misses"][-1000:]
    
    def get_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    "count": len(values),
                    "mean": np.mean(values),
                    "median": np.median(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values)
                }
            else:
                summary[metric_name] = {
                    "count": 0,
                    "mean": 0,
                    "median": 0,
                    "std": 0,
                    "min": 0,
                    "max": 0
                }
        
        return summary
    
    def reset(self):
        """Сброс метрик"""
        for key in self.metrics:
            self.metrics[key] = []


class EmbeddingManager:
    """Менеджер эмбеддингов для RAG"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.chroma_client: Optional[chromadb.Client] = None
    
    async def initialize(self):
        """Инициализация модели эмбеддингов"""
        try:
            self.model = SentenceTransformer(self.model_name)
            self.chroma_client = chromadb.Client(Settings(
                chroma_api_impl="rest",
                chroma_server_host="localhost",
                chroma_server_http_port=8000
            ))
            logger.info(f"Embedding model initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Генерация эмбеддингов для текстов"""
        if not self.model:
            raise ValueError("Embedding model not initialized")
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Вычисление косинусного сходства"""
        try:
            vec1_array = np.array(vec1)
            vec2_array = np.array(vec2)
            
            dot_product = np.dot(vec1_array, vec2_array)
            norm1 = np.linalg.norm(vec1_array)
            norm2 = np.linalg.norm(vec2_array)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error computing cosine similarity: {e}")
            return 0.0
    
    async def add_documents(self, collection_name: str, documents: List[str], 
                          metadatas: List[Dict] = None, ids: List[str] = None):
        """Добавление документов в векторную базу"""
        if not self.chroma_client:
            raise ValueError("ChromaDB client not initialized")
        
        try:
            collection = self.chroma_client.get_or_create_collection(collection_name)
            
            if not ids:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            if not metadatas:
                metadatas = [{"source": "unknown"} for _ in documents]
            
            embeddings = self.generate_embeddings(documents)
            
            collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection {collection_name}")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    async def search_similar(self, collection_name: str, query: str, 
                           n_results: int = 5, threshold: float = 0.7) -> List[Dict]:
        """Поиск похожих документов"""
        if not self.chroma_client:
            raise ValueError("ChromaDB client not initialized")
        
        try:
            collection = self.chroma_client.get_collection(collection_name)
            query_embedding = self.generate_embeddings([query])[0]
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Фильтрация по порогу сходства
            filtered_results = []
            for i, distance in enumerate(results['distances'][0]):
                similarity = 1 - distance  # ChromaDB возвращает расстояния
                if similarity >= threshold:
                    filtered_results.append({
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': similarity,
                        'id': results['ids'][0][i]
                    })
            
            return filtered_results
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []


# Декораторы для кэширования и мониторинга
def cache_result(prefix: str, ttl: int = 3600):
    """Декоратор для кэширования результатов функций"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Генерация ключа кэша
            cache_key = f"{prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Попытка получить из кэша
            cache_manager = CacheManager("redis://localhost:6379")
            cached_result = await cache_manager.get(prefix, cache_key)
            
            if cached_result is not None:
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Выполнение функции
            result = await func(*args, **kwargs)
            
            # Сохранение в кэш
            await cache_manager.set(prefix, result, ttl, cache_key)
            logger.info(f"Cache miss for {func.__name__}, stored result")
            
            return result
        return wrapper
    return decorator


def monitor_performance(metrics_collector: MetricsCollector):
    """Декоратор для мониторинга производительности"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                metrics_collector.record_success()
                return result
            except Exception as e:
                metrics_collector.record_error()
                raise
            finally:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # в миллисекундах
                metrics_collector.record_response_time(response_time)
        
        return wrapper
    return decorator


# Глобальные экземпляры
ollama_client = None
cache_manager = None
metrics_collector = MetricsCollector()
embedding_manager = None


async def initialize_utils(ollama_config: OllamaConfig, redis_url: str):
    """Инициализация всех утилит"""
    global ollama_client, cache_manager, embedding_manager
    
    # Инициализация Ollama клиента
    ollama_client = OllamaClient(ollama_config)
    
    # Инициализация кэш менеджера
    cache_manager = CacheManager(redis_url)
    
    # Инициализация менеджера эмбеддингов
    embedding_manager = EmbeddingManager()
    await embedding_manager.initialize()
    
    logger.info("Utils initialized successfully")


async def cleanup_utils():
    """Очистка ресурсов утилит"""
    global ollama_client, cache_manager
    
    if cache_manager:
        await cache_manager.disconnect()
    
    logger.info("Utils cleaned up successfully") 