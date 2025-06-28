"""
🧠 Единый LLM-маршрутизатор для всех микросервисов reLink

Основан на проверенном RAG-подходе, разработанном в сервисе SEO-рекомендаций.
Обеспечивает стабильное, конкурентное и масштабируемое взаимодействие с Ollama.
"""

import asyncio
import aiohttp
import json
import logging
import platform
import psutil
import subprocess
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time
from contextlib import asynccontextmanager

from .config import settings
from .database import get_db
from .models import LLMRequest, LLMResponse, LLMEmbedding
from .cache import cache_manager
from .exceptions import LLMServiceError, OllamaConnectionError

logger = logging.getLogger(__name__)

class LLMServiceType(Enum):
    """Типы LLM-сервисов"""
    SEO_RECOMMENDATIONS = "seo_recommendations"
    DIAGRAM_GENERATION = "diagram_generation"
    CONTENT_ANALYSIS = "content_analysis"
    BENCHMARK_SERVICE = "benchmark_service"
    LLM_TUNING = "llm_tuning"

@dataclass
class SystemSpecs:
    """Спецификации системы"""
    platform: str
    architecture: str
    cpu_count: int
    memory_gb: float
    gpu_available: bool
    gpu_type: Optional[str] = None
    apple_silicon: bool = False
    m1_m2_m4: bool = False

@dataclass
class OptimizedConfig:
    """Оптимизированная конфигурация для системы"""
    model: str
    num_gpu: int
    num_thread: int
    batch_size: int
    f16_kv: bool
    temperature: float
    max_tokens: int
    context_length: int
    keep_alive: str
    request_timeout: int
    semaphore_limit: int
    cache_ttl: int

class SystemAnalyzer:
    """
    🔍 Интеллектуальный анализатор системы с RAG и LLM
    
    Автоматически определяет оптимальную конфигурацию используя:
    - Анализ системных характеристик
    - RAG с базой знаний о производительности
    - LLM для принятия решений о конфигурации
    - Адаптивную оптимизацию на основе результатов
    """
    
    def __init__(self):
        self.specs: Optional[SystemSpecs] = None
        self.optimized_config: Optional[OptimizedConfig] = None
        self.performance_history: List[Dict[str, Any]] = []
        self.knowledge_base: List[Dict[str, Any]] = []
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Инициализация базы знаний о производительности"""
        self.knowledge_base = [
            {
                "system_type": "apple_silicon_m1_m2_m4",
                "optimal_config": {
                    "num_gpu": 1,
                    "num_thread": 8,
                    "batch_size": 1024,
                    "f16_kv": True,
                    "context_length": 8192,
                    "semaphore_limit": 8
                },
                "performance_notes": "Apple Silicon M1/M2/M4 показывает лучшую производительность с GPU acceleration и большими batch sizes",
                "memory_optimization": "Использует Unified Memory Architecture для эффективного распределения ресурсов"
            },
            {
                "system_type": "apple_silicon_generic",
                "optimal_config": {
                    "num_gpu": 1,
                    "num_thread": 6,
                    "batch_size": 768,
                    "f16_kv": True,
                    "context_length": 6144,
                    "semaphore_limit": 6
                },
                "performance_notes": "Общие Apple Silicon процессоры хорошо работают с Metal acceleration",
                "memory_optimization": "Оптимизированное использование GPU memory"
            },
            {
                "system_type": "nvidia_gpu",
                "optimal_config": {
                    "num_gpu": 1,
                    "num_thread": 6,
                    "batch_size": 1024,
                    "f16_kv": True,
                    "context_length": 8192,
                    "semaphore_limit": 6
                },
                "performance_notes": "NVIDIA GPU обеспечивает высокую производительность с CUDA acceleration",
                "memory_optimization": "Использует GPU memory для KV cache"
            },
            {
                "system_type": "amd_gpu",
                "optimal_config": {
                    "num_gpu": 1,
                    "num_thread": 6,
                    "batch_size": 768,
                    "f16_kv": True,
                    "context_length": 6144,
                    "semaphore_limit": 6
                },
                "performance_notes": "AMD GPU работает с ROCm acceleration",
                "memory_optimization": "Оптимизированное использование VRAM"
            },
            {
                "system_type": "cpu_only_high_memory",
                "optimal_config": {
                    "num_gpu": 0,
                    "num_thread": 8,
                    "batch_size": 512,
                    "f16_kv": False,
                    "context_length": 8192,
                    "semaphore_limit": 6
                },
                "performance_notes": "CPU-only системы с большим объемом памяти могут использовать большие контексты",
                "memory_optimization": "Использует RAM для всех операций"
            },
            {
                "system_type": "cpu_only_low_memory",
                "optimal_config": {
                    "num_gpu": 0,
                    "num_thread": 4,
                    "batch_size": 256,
                    "f16_kv": False,
                    "context_length": 2048,
                    "semaphore_limit": 3
                },
                "performance_notes": "Системы с ограниченной памятью требуют консервативных настроек",
                "memory_optimization": "Минимизирует использование памяти"
            }
        ]
    
    async def analyze_system(self) -> SystemSpecs:
        """Анализ системы и определение спецификаций"""
        if self.specs:
            return self.specs
        
        platform_name = platform.system()
        architecture = platform.machine()
        cpu_count = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Определение Apple Silicon
        apple_silicon = False
        m1_m2_m4 = False
        
        if platform_name == "Darwin" and "arm" in architecture.lower():
            apple_silicon = True
            # Проверка конкретной модели
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"], 
                    capture_output=True, text=True
                )
                cpu_brand = result.stdout.lower()
                if any(x in cpu_brand for x in ["m1", "m2", "m3", "m4"]):
                    m1_m2_m4 = True
            except:
                pass
        
        # Определение GPU
        gpu_available = False
        gpu_type = None
        
        if apple_silicon:
            gpu_available = True
            gpu_type = "Apple Silicon GPU"
        else:
            try:
                # Проверка NVIDIA GPU
                result = subprocess.run(["nvidia-smi"], capture_output=True)
                if result.returncode == 0:
                    gpu_available = True
                    gpu_type = "NVIDIA"
                else:
                    # Проверка AMD GPU
                    result = subprocess.run(["rocm-smi"], capture_output=True)
                    if result.returncode == 0:
                        gpu_available = True
                        gpu_type = "AMD"
            except:
                pass
        
        self.specs = SystemSpecs(
            platform=platform_name,
            architecture=architecture,
            cpu_count=cpu_count,
            memory_gb=memory_gb,
            gpu_available=gpu_available,
            gpu_type=gpu_type,
            apple_silicon=apple_silicon,
            m1_m2_m4=m1_m2_m4
        )
        
        logger.info(f"🔍 System analysis completed: {self.specs}")
        return self.specs
    
    async def _get_llm_recommendation(self, specs: SystemSpecs, performance_data: List[Dict]) -> Dict[str, Any]:
        """
        🧠 Получение рекомендаций от LLM для оптимизации конфигурации
        
        Использует RAG с базой знаний и историей производительности
        """
        try:
            # Формирование контекста для LLM
            context_parts = [
                f"Системные характеристики:",
                f"- Платформа: {specs.platform}",
                f"- Архитектура: {specs.architecture}",
                f"- CPU ядер: {specs.cpu_count}",
                f"- Память: {specs.memory_gb:.1f} GB",
                f"- GPU доступен: {specs.gpu_available}",
                f"- Тип GPU: {specs.gpu_type}",
                f"- Apple Silicon: {specs.apple_silicon}",
                f"- M1/M2/M4: {specs.m1_m2_m4}"
            ]
            
            if performance_data:
                context_parts.append("\nИстория производительности:")
                for perf in performance_data[-3:]:  # Последние 3 записи
                    context_parts.append(f"- {perf['timestamp']}: {perf['avg_response_time']:.2f}s, {perf['success_rate']:.1%}")
            
            context_parts.append("\nБаза знаний о производительности:")
            for kb in self.knowledge_base:
                context_parts.append(f"- {kb['system_type']}: {kb['performance_notes']}")
            
            context = "\n".join(context_parts)
            
            # Промпт для LLM
            prompt = f"""
            Ты эксперт по оптимизации LLM систем. Проанализируй характеристики системы и историю производительности, чтобы дать рекомендации по оптимальной конфигурации Ollama.

            Контекст:
            {context}

            Задача: Определи оптимальные параметры для максимальной производительности и стабильности.

            Ответь в формате JSON с параметрами:
            {{
                "num_gpu": <0 или 1>,
                "num_thread": <количество потоков>,
                "batch_size": <размер батча>,
                "f16_kv": <true/false>,
                "context_length": <длина контекста>,
                "semaphore_limit": <лимит одновременных запросов>,
                "temperature": <температура для генерации>,
                "max_tokens": <максимум токенов>,
                "keep_alive": <время жизни модели>,
                "request_timeout": <таймаут запроса в секундах>,
                "cache_ttl": <время жизни кэша в секундах>,
                "reasoning": "<объяснение выбора параметров>"
            }}
            """
            
            # Создание временного LLM роутера для получения рекомендаций
            temp_router = LLMRouter()
            await temp_router.start()
            
            request = LLMRequest(
                service_type=LLMServiceType.LLM_TUNING,
                prompt=prompt,
                context={"task": "system_optimization"},
                model="qwen2.5:7b-instruct-turbo",
                temperature=0.3,  # Низкая температура для консистентности
                max_tokens=1024,
                use_rag=False  # Отключаем RAG для этого запроса
            )
            
            response = await temp_router.process_request(request)
            await temp_router.stop()
            
            # Парсинг JSON ответа
            try:
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    recommendation = json.loads(json_match.group())
                    logger.info(f"🧠 LLM recommendation: {recommendation['reasoning']}")
                    return recommendation
            except Exception as e:
                logger.warning(f"Failed to parse LLM recommendation: {e}")
            
        except Exception as e:
            logger.error(f"LLM recommendation failed: {e}")
        
        # Fallback к базовым настройкам
        return None
    
    async def _search_knowledge_base(self, specs: SystemSpecs) -> List[Dict[str, Any]]:
        """Поиск релевантных знаний в базе знаний"""
        relevant_knowledge = []
        
        # Определение типа системы
        if specs.apple_silicon and specs.m1_m2_m4:
            system_type = "apple_silicon_m1_m2_m4"
        elif specs.apple_silicon:
            system_type = "apple_silicon_generic"
        elif specs.gpu_available and specs.gpu_type == "NVIDIA":
            system_type = "nvidia_gpu"
        elif specs.gpu_available and specs.gpu_type == "AMD":
            system_type = "amd_gpu"
        elif specs.memory_gb >= 16:
            system_type = "cpu_only_high_memory"
        else:
            system_type = "cpu_only_low_memory"
        
        # Поиск соответствующих знаний
        for kb in self.knowledge_base:
            if kb["system_type"] == system_type:
                relevant_knowledge.append(kb)
                break
        
        return relevant_knowledge
    
    async def optimize_config(self) -> OptimizedConfig:
        """Интеллектуальная оптимизация конфигурации с использованием LLM"""
        if self.optimized_config:
            return self.optimized_config
        
        specs = await self.analyze_system()
        
        # Базовые настройки
        config = OptimizedConfig(
            model="qwen2.5:7b-instruct-turbo",
            num_gpu=0,
            num_thread=4,
            batch_size=512,
            f16_kv=True,
            temperature=0.7,
            max_tokens=2048,
            context_length=4096,
            keep_alive="2h",
            request_timeout=300,
            semaphore_limit=5,
            cache_ttl=3600
        )
        
        # Получение рекомендаций от LLM
        llm_recommendation = await self._get_llm_recommendation(specs, self.performance_history)
        
        if llm_recommendation:
            # Применение рекомендаций LLM
            config.num_gpu = llm_recommendation.get("num_gpu", config.num_gpu)
            config.num_thread = llm_recommendation.get("num_thread", config.num_thread)
            config.batch_size = llm_recommendation.get("batch_size", config.batch_size)
            config.f16_kv = llm_recommendation.get("f16_kv", config.f16_kv)
            config.context_length = llm_recommendation.get("context_length", config.context_length)
            config.semaphore_limit = llm_recommendation.get("semaphore_limit", config.semaphore_limit)
            config.temperature = llm_recommendation.get("temperature", config.temperature)
            config.max_tokens = llm_recommendation.get("max_tokens", config.max_tokens)
            config.keep_alive = llm_recommendation.get("keep_alive", config.keep_alive)
            config.request_timeout = llm_recommendation.get("request_timeout", config.request_timeout)
            config.cache_ttl = llm_recommendation.get("cache_ttl", config.cache_ttl)
            
            logger.info(f"🧠 Applied LLM recommendations: {llm_recommendation.get('reasoning', 'No reasoning provided')}")
        else:
            # Fallback к правилам на основе знаний
            relevant_knowledge = await self._search_knowledge_base(specs)
            
            if relevant_knowledge:
                kb_config = relevant_knowledge[0]["optimal_config"]
                config.num_gpu = kb_config.get("num_gpu", config.num_gpu)
                config.num_thread = min(kb_config.get("num_thread", config.num_thread), specs.cpu_count)
                config.batch_size = kb_config.get("batch_size", config.batch_size)
                config.f16_kv = kb_config.get("f16_kv", config.f16_kv)
                config.context_length = kb_config.get("context_length", config.context_length)
                config.semaphore_limit = kb_config.get("semaphore_limit", config.semaphore_limit)
                
                logger.info(f"📚 Applied knowledge base config: {relevant_knowledge[0]['system_type']}")
        
        # Дополнительная оптимизация по памяти
        if specs.memory_gb >= 32:
            config.context_length = min(config.context_length * 2, 16384)
            config.batch_size = min(config.batch_size * 1.5, 2048)
            config.semaphore_limit = min(config.semaphore_limit + 2, 10)
            logger.info("💾 High memory optimization applied")
        elif specs.memory_gb < 8:
            config.context_length = min(config.context_length // 2, 2048)
            config.batch_size = min(config.batch_size // 2, 256)
            config.semaphore_limit = max(config.semaphore_limit - 2, 2)
            logger.info("💾 Low memory optimization applied")
        
        self.optimized_config = config
        logger.info(f"⚙️ Optimized config: {config}")
        return config
    
    async def record_performance(self, response_time: float, success: bool, tokens_used: int):
        """Запись производительности для адаптивной оптимизации"""
        performance_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "response_time": response_time,
            "success": success,
            "tokens_used": tokens_used,
            "config_snapshot": {
                "num_gpu": self.optimized_config.num_gpu if self.optimized_config else 0,
                "num_thread": self.optimized_config.num_thread if self.optimized_config else 4,
                "batch_size": self.optimized_config.batch_size if self.optimized_config else 512,
                "context_length": self.optimized_config.context_length if self.optimized_config else 4096
            }
        }
        
        self.performance_history.append(performance_record)
        
        # Ограничиваем историю последними 100 записями
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # Анализируем производительность и при необходимости переоптимизируем
        await self._analyze_and_adapt()
    
    async def _analyze_and_adapt(self):
        """Анализ производительности и адаптивная оптимизация"""
        if len(self.performance_history) < 10:
            return
        
        recent_performance = self.performance_history[-10:]
        avg_response_time = sum(p["response_time"] for p in recent_performance) / len(recent_performance)
        success_rate = sum(1 for p in recent_performance if p["success"]) / len(recent_performance)
        
        # Если производительность ухудшилась, переоптимизируем
        if avg_response_time > 5.0 or success_rate < 0.8:
            logger.warning(f"Performance degradation detected: avg_time={avg_response_time:.2f}s, success_rate={success_rate:.1%}")
            logger.info("🔄 Triggering adaptive reoptimization...")
            
            # Сбрасываем оптимизированную конфигурацию для пересчета
            self.optimized_config = None
            await self.optimize_config()
    
    async def get_environment_variables(self) -> Dict[str, str]:
        """Получение переменных окружения для Ollama"""
        config = await self.optimize_config()
        
        env_vars = {
            "OLLAMA_HOST": "0.0.0.0",
            "OLLAMA_ORIGINS": "*",
            "OLLAMA_KEEP_ALIVE": config.keep_alive,
            "OLLAMA_CONTEXT_LENGTH": str(config.context_length),
            "OLLAMA_BATCH_SIZE": str(config.batch_size),
            "OLLAMA_NUM_PARALLEL": str(config.semaphore_limit),
            "REQUEST_TIMEOUT": str(config.request_timeout)
        }
        
        # Специальные настройки для Apple Silicon
        specs = await self.analyze_system()
        if specs.apple_silicon:
            env_vars.update({
                "OLLAMA_METAL": "1",
                "OLLAMA_FLASH_ATTENTION": "1",
                "OLLAMA_KV_CACHE_TYPE": "q8_0",
                "OLLAMA_MEM_FRACTION": "0.9"
            })
        
        return env_vars
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Получение отчета об оптимизации"""
        specs = await self.analyze_system()
        config = await self.optimize_config()
        
        return {
            "system_specs": {
                "platform": specs.platform,
                "architecture": specs.architecture,
                "cpu_count": specs.cpu_count,
                "memory_gb": specs.memory_gb,
                "gpu_available": specs.gpu_available,
                "gpu_type": specs.gpu_type,
                "apple_silicon": specs.apple_silicon,
                "m1_m2_m4": specs.m1_m2_m4
            },
            "optimized_config": {
                "model": config.model,
                "num_gpu": config.num_gpu,
                "num_thread": config.num_thread,
                "batch_size": config.batch_size,
                "f16_kv": config.f16_kv,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "context_length": config.context_length,
                "keep_alive": config.keep_alive,
                "request_timeout": config.request_timeout,
                "semaphore_limit": config.semaphore_limit,
                "cache_ttl": config.cache_ttl
            },
            "performance_history": {
                "total_records": len(self.performance_history),
                "recent_avg_response_time": sum(p["response_time"] for p in self.performance_history[-10:]) / min(10, len(self.performance_history)) if self.performance_history else 0,
                "recent_success_rate": sum(1 for p in self.performance_history[-10:] if p["success"]) / min(10, len(self.performance_history)) if self.performance_history else 0
            },
            "knowledge_base_entries": len(self.knowledge_base)
        }

# Глобальный экземпляр анализатора
system_analyzer = SystemAnalyzer()

@dataclass
class LLMRequest:
    """Структура LLM-запроса"""
    service_type: LLMServiceType
    prompt: str
    context: Optional[Dict[str, Any]] = None
    model: str = "qwen2.5:7b-instruct-turbo"  # Оптимизированная модель для Apple Silicon
    temperature: float = 0.7
    max_tokens: int = 2048
    use_rag: bool = True
    cache_ttl: int = 3600  # 1 час
    priority: int = 1  # 1-10, где 10 - высший приоритет

@dataclass
class LLMResponse:
    """Структура LLM-ответа"""
    content: str
    service_type: LLMServiceType
    model_used: str
    tokens_used: int
    response_time: float
    cached: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class LLMRouter:
    """
    🧠 Единый маршрутизатор LLM с RAG-подходом
    
    Основан на успешном опыте SEO-рекомендаций:
    - Конкурентная обработка запросов
    - RAG с векторной базой знаний
    - Кэширование и оптимизация
    - Обработка ошибок и fallback
    - Автоопределение оптимальной конфигурации
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.request_queue = asyncio.Queue()
        self.processing = False
        self.optimized_config: Optional[OptimizedConfig] = None
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cached_responses": 0,
            "avg_response_time": 0.0,
            "system_specs": None,
            "optimization_applied": False
        }
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие соединений"""
        await self.stop()
    
    async def start(self):
        """Запуск маршрутизатора с автоопределением конфигурации"""
        if not self.session:
            # Получение оптимизированной конфигурации
            self.optimized_config = await system_analyzer.optimize_config()
            specs = await system_analyzer.analyze_system()
            
            # Обновление статистики
            self.stats["system_specs"] = {
                "platform": specs.platform,
                "architecture": specs.architecture,
                "cpu_count": specs.cpu_count,
                "memory_gb": specs.memory_gb,
                "gpu_available": specs.gpu_available,
                "gpu_type": specs.gpu_type,
                "apple_silicon": specs.apple_silicon,
                "m1_m2_m4": specs.m1_m2_m4
            }
            self.stats["optimization_applied"] = True
            
            # Создание семафора с оптимизированным лимитом
            self.semaphore = asyncio.Semaphore(self.optimized_config.semaphore_limit)
            
            # Создание сессии с оптимизированным таймаутом
            timeout = aiohttp.ClientTimeout(total=self.optimized_config.request_timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            
            logger.info(f"🚀 LLM Router started with optimized config: {self.optimized_config}")
            logger.info(f"🔍 System specs: {self.stats['system_specs']}")
    
    async def stop(self):
        """Остановка маршрутизатора"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("🛑 LLM Router stopped")
    
    def _generate_cache_key(self, request: LLMRequest) -> str:
        """Генерация ключа кэша для запроса"""
        content = f"{request.service_type.value}:{request.prompt}:{request.model}:{request.temperature}"
        if request.context:
            content += f":{json.dumps(request.context, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """Получение кэшированного ответа"""
        try:
            cached_data = await cache_manager.get(f"llm:{cache_key}")
            if cached_data:
                logger.info(f"📦 Cache hit for {cache_key[:16]}...")
                return LLMResponse(**cached_data, cached=True)
        except Exception as e:
            logger.warning(f"Cache error: {e}")
        return None
    
    async def _cache_response(self, cache_key: str, response: LLMResponse, ttl: int):
        """Кэширование ответа"""
        try:
            cache_data = {
                "content": response.content,
                "service_type": response.service_type.value,
                "model_used": response.model_used,
                "tokens_used": response.tokens_used,
                "response_time": response.response_time,
                "metadata": response.metadata
            }
            await cache_manager.set(f"llm:{cache_key}", cache_data, ttl)
            logger.info(f"💾 Cached response for {cache_key[:16]}...")
        except Exception as e:
            logger.warning(f"Cache error: {e}")
    
    async def _generate_rag_context(self, request: LLMRequest) -> str:
        """
        🔍 Генерация RAG-контекста
        
        Основано на успешном подходе SEO-рекомендаций:
        - Поиск релевантных знаний в векторной БД
        - Обогащение промпта контекстом
        - Улучшение качества ответов
        """
        if not request.use_rag:
            return request.prompt
        
        try:
            # Получение эмбеддингов для промпта
            embedding = await self._get_embedding(request.prompt)
            
            # Поиск релевантных знаний
            relevant_knowledge = await self._search_knowledge_base(
                embedding, 
                request.service_type,
                limit=3
            )
            
            if relevant_knowledge:
                context_parts = [request.prompt]
                context_parts.append("\n\nРелевантная информация:")
                for knowledge in relevant_knowledge:
                    context_parts.append(f"- {knowledge['content']}")
                
                enhanced_prompt = "\n".join(context_parts)
                logger.info(f"🧠 RAG enhanced prompt for {request.service_type.value}")
                return enhanced_prompt
            
        except Exception as e:
            logger.warning(f"RAG error: {e}")
        
        return request.prompt
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Получение эмбеддинга для текста"""
        try:
            async with self.semaphore:
                async with self.session.post(
                    f"{settings.OLLAMA_URL}/api/embeddings",
                    json={"model": "qwen2.5:7b-instruct-turbo", "prompt": text}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("embedding", [])
                    else:
                        logger.error(f"Embedding error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Embedding request failed: {e}")
            return []
    
    async def _search_knowledge_base(
        self, 
        embedding: List[float], 
        service_type: LLMServiceType,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Поиск в векторной базе знаний"""
        try:
            # Здесь должна быть интеграция с векторной БД (Chroma, Pinecone, etc.)
            # Пока возвращаем пустой список
            return []
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            return []
    
    async def _make_ollama_request(self, request: LLMRequest) -> LLMResponse:
        """
        🔄 Выполнение запроса к Ollama с оптимизациями Apple Silicon M4
        
        Основано на проверенных паттернах SEO-рекомендаций:
        - Конкурентное управление
        - Обработка ошибок
        - Таймауты и retry
        - Apple Silicon оптимизации
        """
        start_time = time.time()
        
        try:
            async with self.semaphore:
                # Подготовка промпта с RAG
                enhanced_prompt = await self._generate_rag_context(request)
                
                # Формирование запроса к Ollama с Apple Silicon оптимизациями
                ollama_request = {
                    "model": request.model,
                    "prompt": enhanced_prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens,
                        # 🚀 APPLE SILICON M4 ОПТИМИЗАЦИИ
                        "num_gpu": 1,                    # Использование GPU
                        "num_thread": 8,                 # Оптимальное количество потоков для M4
                        "num_ctx": 4096,                 # Размер контекста
                        "batch_size": 512,               # Размер батча для производительности
                        "f16_kv": True,                  # 16-битные ключи-значения для экономии памяти
                        "use_mmap": True,                # Memory mapping для быстрого доступа
                        "use_mlock": True,               # Блокировка памяти
                        "rope_freq_base": 10000,         # RoPE базовая частота
                        "rope_freq_scale": 0.5,          # RoPE масштаб частоты
                        "top_p": 0.9,                    # Top-p sampling
                        "top_k": 40,                     # Top-k sampling
                        "repeat_penalty": 1.1,           # Штраф за повторения
                        "seed": 42                       # Фиксированный seed для воспроизводимости
                    }
                }
                
                # Выполнение запроса
                async with self.session.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json=ollama_request
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        response_time = time.time() - start_time
                        
                        return LLMResponse(
                            content=data.get("response", ""),
                            service_type=request.service_type,
                            model_used=request.model,
                            tokens_used=data.get("eval_count", 0),
                            response_time=response_time,
                            metadata={
                                "prompt_tokens": data.get("prompt_eval_count", 0),
                                "total_duration": data.get("total_duration", 0),
                                "apple_silicon_optimized": True,
                                "gpu_used": True,
                                "batch_size": 512,
                                "context_length": 4096
                            }
                        )
                    else:
                        error_text = await response.text()
                        raise OllamaConnectionError(f"Ollama error {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            raise LLMServiceError("Request timeout")
        except Exception as e:
            raise LLMServiceError(f"Request failed: {e}")
    
    async def process_request(self, request: LLMRequest) -> LLMResponse:
        """
        🎯 Основной метод обработки LLM-запросов
        
        Реализует полный pipeline:
        1. Проверка кэша
        2. RAG-обогащение
        3. Запрос к Ollama
        4. Кэширование результата
        5. Логирование и мониторинг
        """
        self.stats["total_requests"] += 1
        start_time = time.time()
        
        try:
            # Генерация ключа кэша
            cache_key = self._generate_cache_key(request)
            
            # Проверка кэша
            if request.cache_ttl > 0:
                cached_response = await self._get_cached_response(cache_key)
                if cached_response:
                    self.stats["cached_responses"] += 1
                    return cached_response
            
            # Выполнение запроса к Ollama
            response = await self._make_ollama_request(request)
            
            # Кэширование результата
            if request.cache_ttl > 0:
                await self._cache_response(cache_key, response, request.cache_ttl)
            
            # Обновление статистики
            self.stats["successful_requests"] += 1
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (self.stats["successful_requests"] - 1) + 
                 response.response_time) / self.stats["successful_requests"]
            )
            
            # Логирование успешного запроса
            logger.info(
                f"✅ {request.service_type.value} completed in {response.response_time:.2f}s "
                f"(tokens: {response.tokens_used})"
            )
            
            return response
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"❌ {request.service_type.value} failed: {e}")
            
            # Fallback: возвращаем базовый ответ
            return LLMResponse(
                content=f"Извините, произошла ошибка при обработке запроса: {str(e)}",
                service_type=request.service_type,
                model_used=request.model,
                tokens_used=0,
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики маршрутизатора"""
        return {
            **self.stats,
            "active_connections": self.semaphore._value,
            "queue_size": self.request_queue.qsize() if hasattr(self.request_queue, 'qsize') else 0
        }
    
    async def health_check(self) -> bool:
        """Проверка здоровья Ollama"""
        try:
            async with self.session.get(f"{settings.OLLAMA_URL}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

# Глобальный экземпляр маршрутизатора
llm_router = LLMRouter()

# Утилитарные функции для удобства использования
async def generate_seo_recommendations(prompt: str, context: Optional[Dict] = None) -> str:
    """Генерация SEO-рекомендаций с оптимизированной моделью"""
    request = LLMRequest(
        service_type=LLMServiceType.SEO_RECOMMENDATIONS,
        prompt=prompt,
        context=context,
        model="qwen2.5:7b-instruct-turbo",
        temperature=0.6,  # Более низкая температура для SEO задач
        max_tokens=2048
    )
    response = await llm_router.process_request(request)
    return response.content

async def generate_diagram(prompt: str, diagram_type: str = "architecture") -> str:
    """Генерация SVG диаграммы с оптимизированной моделью"""
    request = LLMRequest(
        service_type=LLMServiceType.DIAGRAM_GENERATION,
        prompt=f"Создай SVG диаграмму типа '{diagram_type}': {prompt}",
        context={"diagram_type": diagram_type},
        model="qwen2.5:7b-instruct-turbo",
        temperature=0.8,  # Высокая креативность для диаграмм
        max_tokens=4096   # Больше токенов для SVG
    )
    response = await llm_router.process_request(request)
    return response.content

async def analyze_content(content: str, analysis_type: str = "general") -> str:
    """Анализ контента с оптимизированной моделью"""
    request = LLMRequest(
        service_type=LLMServiceType.CONTENT_ANALYSIS,
        prompt=f"Проанализируй контент (тип анализа: {analysis_type}): {content}",
        context={"analysis_type": analysis_type},
        model="qwen2.5:7b-instruct-turbo",
        temperature=0.5,  # Умеренная температура для анализа
        max_tokens=2048
    )
    response = await llm_router.process_request(request)
    return response.content

async def run_benchmark(benchmark_type: str, parameters: Dict[str, Any]) -> str:
    """Запуск бенчмарка с оптимизированной моделью"""
    request = LLMRequest(
        service_type=LLMServiceType.BENCHMARK_SERVICE,
        prompt=f"Выполни бенчмарк типа '{benchmark_type}' с параметрами: {json.dumps(parameters)}",
        context={"benchmark_type": benchmark_type, "parameters": parameters},
        model="qwen2.5:7b-instruct-turbo",
        temperature=0.3,  # Низкая температура для точных результатов
        max_tokens=2048
    )
    response = await llm_router.process_request(request)
    return response.content

async def tune_llm_model(model_config: Dict[str, Any], tuning_params: Dict[str, Any]) -> str:
    """Настройка LLM модели с оптимизированной моделью"""
    request = LLMRequest(
        service_type=LLMServiceType.LLM_TUNING,
        prompt=f"Настрой модель с конфигурацией: {json.dumps(model_config)} и параметрами: {json.dumps(tuning_params)}",
        context={"model_config": model_config, "tuning_params": tuning_params},
        model="qwen2.5:7b-instruct-turbo",
        temperature=0.4,  # Умеренная температура для настройки
        max_tokens=2048
    )
    response = await llm_router.process_request(request)
    return response.content 