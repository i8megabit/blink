"""
🧠 Единый LLM-маршрутизатор для всех микросервисов reLink

Обновлен для использования централизованной LLM архитектуры с конкурентным доступом к Ollama.
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
from .models import LLMRequest as DBLLMRequest, LLMResponse as DBLLMResponse, LLMEmbedding
from .cache import cache_manager
from .exceptions import LLMServiceError, OllamaConnectionError
from .monitoring import rag_monitor
from .llm_integration import get_llm_integration_service, LLMIntegrationService

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
                    "semaphore_limit": 2  # Оптимизировано для централизованной архитектуры
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
                    "semaphore_limit": 2
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
                    "semaphore_limit": 2
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
                    "semaphore_limit": 2
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
                    "semaphore_limit": 2
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
                    "semaphore_limit": 1
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
        
        try:
            # Проверка NVIDIA GPU
            result = subprocess.run(["nvidia-smi"], capture_output=True)
            if result.returncode == 0:
                gpu_available = True
                gpu_type = "nvidia"
            else:
                # Проверка AMD GPU
                result = subprocess.run(["rocm-smi"], capture_output=True)
                if result.returncode == 0:
                    gpu_available = True
                    gpu_type = "amd"
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
        
        logger.info(f"Система проанализирована: {self.specs}")
        return self.specs
    
    async def _get_llm_recommendation(self, specs: SystemSpecs, performance_data: List[Dict]) -> Dict[str, Any]:
        """Получение рекомендации от LLM для оптимизации конфигурации"""
        try:
            llm_service = await get_llm_integration_service()
            
            # Формируем промпт для LLM
            prompt = f"""
            Проанализируй системные характеристики и историю производительности для оптимизации конфигурации Ollama:
            
            Системные характеристики:
            - Платформа: {specs.platform}
            - Архитектура: {specs.architecture}
            - CPU ядер: {specs.cpu_count}
            - Память: {specs.memory_gb:.1f} GB
            - GPU доступен: {specs.gpu_available}
            - GPU тип: {specs.gpu_type}
            - Apple Silicon: {specs.apple_silicon}
            - M1/M2/M4: {specs.m1_m2_m4}
            
            История производительности (последние 10 записей):
            {performance_data[-10:] if performance_data else "Нет данных"}
            
            Предложи оптимальную конфигурацию для Ollama в формате JSON:
            {{
                "num_gpu": <количество GPU>,
                "num_thread": <количество потоков>,
                "batch_size": <размер батча>,
                "f16_kv": <использовать f16 для KV cache>,
                "context_length": <длина контекста>,
                "semaphore_limit": <лимит семафора>
            }}
            
            Учти, что используется централизованная архитектура с конкурентным доступом к одной модели Ollama.
            """
            
            response = await llm_service.generate_response(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )
            
            # Парсим JSON ответ
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
            
            # Возвращаем дефолтную конфигурацию если парсинг не удался
            return {
                "num_gpu": 1 if specs.gpu_available else 0,
                "num_thread": min(specs.cpu_count, 8),
                "batch_size": 512,
                "f16_kv": specs.gpu_available,
                "context_length": 4096,
                "semaphore_limit": 2
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения LLM рекомендации: {e}")
            # Возвращаем безопасную конфигурацию
            return {
                "num_gpu": 1 if specs.gpu_available else 0,
                "num_thread": min(specs.cpu_count, 4),
                "batch_size": 256,
                "f16_kv": specs.gpu_available,
                "context_length": 2048,
                "semaphore_limit": 2
            }
    
    async def _search_knowledge_base(self, specs: SystemSpecs) -> List[Dict[str, Any]]:
        """Поиск в базе знаний на основе характеристик системы"""
        relevant_configs = []
        
        # Определяем тип системы
        if specs.apple_silicon and specs.m1_m2_m4:
            system_type = "apple_silicon_m1_m2_m4"
        elif specs.apple_silicon:
            system_type = "apple_silicon_generic"
        elif specs.gpu_type == "nvidia":
            system_type = "nvidia_gpu"
        elif specs.gpu_type == "amd":
            system_type = "amd_gpu"
        elif specs.memory_gb >= 16:
            system_type = "cpu_only_high_memory"
        else:
            system_type = "cpu_only_low_memory"
        
        # Ищем соответствующие конфигурации
        for config in self.knowledge_base:
            if config["system_type"] == system_type:
                relevant_configs.append(config)
        
        return relevant_configs
    
    async def optimize_config(self) -> OptimizedConfig:
        """Оптимизация конфигурации на основе анализа системы"""
        if self.optimized_config:
            return self.optimized_config
        
        # Анализируем систему
        specs = await self.analyze_system()
        
        # Ищем в базе знаний
        knowledge_configs = await self._search_knowledge_base(specs)
        
        # Получаем рекомендацию от LLM
        llm_recommendation = await self._get_llm_recommendation(specs, self.performance_history)
        
        # Объединяем рекомендации
        optimal_config = {
            "model": "qwen2.5:7b-instruct-turbo",
            "num_gpu": llm_recommendation.get("num_gpu", 1 if specs.gpu_available else 0),
            "num_thread": llm_recommendation.get("num_thread", min(specs.cpu_count, 8)),
            "batch_size": llm_recommendation.get("batch_size", 512),
            "f16_kv": llm_recommendation.get("f16_kv", specs.gpu_available),
            "temperature": 0.7,
            "max_tokens": 2048,
            "context_length": llm_recommendation.get("context_length", 4096),
            "keep_alive": "2h",
            "request_timeout": 300,
            "semaphore_limit": llm_recommendation.get("semaphore_limit", 2),
            "cache_ttl": 3600
        }
        
        self.optimized_config = OptimizedConfig(**optimal_config)
        
        logger.info(f"Конфигурация оптимизирована: {self.optimized_config}")
        return self.optimized_config
    
    async def record_performance(self, response_time: float, success: bool, tokens_used: int):
        """Запись метрик производительности"""
        performance_record = {
            "timestamp": datetime.utcnow(),
            "response_time": response_time,
            "success": success,
            "tokens_used": tokens_used,
            "system_load": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent
        }
        
        self.performance_history.append(performance_record)
        
        # Ограничиваем размер истории
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
    
    async def _analyze_and_adapt(self):
        """Анализ производительности и адаптация конфигурации"""
        if len(self.performance_history) < 10:
            return
        
        # Анализируем последние метрики
        recent_performance = self.performance_history[-10:]
        avg_response_time = sum(p["response_time"] for p in recent_performance) / len(recent_performance)
        success_rate = sum(1 for p in recent_performance if p["success"]) / len(recent_performance)
        
        # Если производительность ухудшилась, пересматриваем конфигурацию
        if avg_response_time > 10.0 or success_rate < 0.9:
            logger.warning(f"Производительность ухудшилась: avg_time={avg_response_time:.2f}s, success_rate={success_rate:.2f}")
            self.optimized_config = None  # Сбрасываем для переоптимизации
    
    async def get_environment_variables(self) -> Dict[str, str]:
        """Получение переменных окружения для Ollama"""
        config = await self.optimize_config()
        
        env_vars = {
            "OLLAMA_HOST": "0.0.0.0:11434",
            "OLLAMA_MODELS": "/root/.ollama/models",
            "OLLAMA_KEEP_ALIVE": config.keep_alive,
            "OLLAMA_ORIGINS": "*",
            "OLLAMA_NUM_PARALLEL": str(config.semaphore_limit),
        }
        
        # Добавляем специфичные для GPU переменные
        if config.num_gpu > 0:
            if platform.system() == "Darwin":
                env_vars["OLLAMA_GPU_LAYERS"] = str(config.num_gpu)
            else:
                env_vars["CUDA_VISIBLE_DEVICES"] = "0"
        
        return env_vars
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Получение отчета об оптимизации"""
        config = await self.optimize_config()
        specs = await self.analyze_system()
        
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
                "avg_response_time": sum(p["response_time"] for p in self.performance_history) / len(self.performance_history) if self.performance_history else 0,
                "success_rate": sum(1 for p in self.performance_history if p["success"]) / len(self.performance_history) if self.performance_history else 1.0
            },
            "knowledge_base_size": len(self.knowledge_base)
        }

@dataclass
class LLMRequest:
    """Структура LLM-запроса"""
    service_type: LLMServiceType
    prompt: str
    context: Optional[Dict[str, Any]] = None
    llm_model: str = "qwen2.5:7b-instruct-turbo"  # Оптимизированная модель для Apple Silicon
    temperature: float = 0.7
    max_tokens: int = 2048
    use_rag: bool = True
    cache_ttl: int = 3600  # 1 час
    priority: str = "normal"  # critical, high, normal, low, background

@dataclass
class LLMResponse:
    """Структура LLM-ответа"""
    content: str
    service_type: LLMServiceType
    used_model: str
    tokens_used: int
    response_time: float
    cached: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class LLMRouter:
    """
    🚀 Обновленный LLM-маршрутизатор с централизованной архитектурой
    
    Использует централизованную LLM архитектуру для конкурентного доступа к Ollama.
    Обеспечивает RAG-обогащение, кэширование и мониторинг производительности.
    """
    
    def __init__(self):
        self.system_analyzer = SystemAnalyzer()
        self.llm_service: Optional[LLMIntegrationService] = None
        self.optimized_config: Optional[OptimizedConfig] = None
        self._initialized = False
        
        logger.info("LLMRouter инициализирован")
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Завершение работы"""
        await self.stop()
    
    async def start(self):
        """Запуск роутера"""
        if self._initialized:
            return
        
        try:
            # Инициализируем LLM сервис
            self.llm_service = await get_llm_integration_service()
            
            # Оптимизируем конфигурацию
            self.optimized_config = await self.system_analyzer.optimize_config()
            
            self._initialized = True
            logger.info("LLMRouter запущен с централизованной архитектурой")
            
        except Exception as e:
            logger.error(f"Ошибка запуска LLMRouter: {e}")
            raise
    
    async def stop(self):
        """Остановка роутера"""
        self._initialized = False
        logger.info("LLMRouter остановлен")
    
    def _generate_cache_key(self, request: LLMRequest) -> str:
        """Генерация ключа кэша"""
        key_parts = [
            request.service_type.value,
            request.prompt,
            request.llm_model,
            str(request.temperature),
            str(request.max_tokens),
            str(request.use_rag)
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _get_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """Получение кэшированного ответа"""
        try:
            cached_data = await cache_manager.get(f"llm_response:{cache_key}")
            if cached_data:
                return LLMResponse(**cached_data)
        except Exception as e:
            logger.error(f"Ошибка получения кэша: {e}")
        
        return None
    
    async def _cache_response(self, cache_key: str, response: LLMResponse, ttl: int):
        """Кэширование ответа"""
        try:
            response_data = {
                "content": response.content,
                "service_type": response.service_type.value,
                "used_model": response.used_model,
                "tokens_used": response.tokens_used,
                "response_time": response.response_time,
                "cached": True,
                "error": response.error,
                "metadata": response.metadata
            }
            
            await cache_manager.set(f"llm_response:{cache_key}", response_data, ttl)
            
        except Exception as e:
            logger.error(f"Ошибка кэширования: {e}")
    
    async def _generate_rag_context(self, request: LLMRequest) -> str:
        """Генерация RAG контекста"""
        try:
            if not request.use_rag:
                return ""
            
            # Получаем эмбеддинг для промпта
            embedding = await self.llm_service.get_embedding(request.prompt)
            
            # Ищем релевантные документы
            relevant_docs = await self.llm_service.search_knowledge_base(
                request.prompt, 
                limit=3
            )
            
            if relevant_docs:
                context = "\n".join(relevant_docs)
                logger.info(f"RAG контекст сгенерирован для {request.service_type.value}")
                return context
            
            return ""
            
        except Exception as e:
            logger.error(f"Ошибка генерации RAG контекста: {e}")
            return ""
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Получение эмбеддинга для текста"""
        try:
            return await self.llm_service.get_embedding(text)
        except Exception as e:
            logger.error(f"Ошибка получения эмбеддинга: {e}")
            return []
    
    async def _search_knowledge_base(
        self, 
        embedding: List[float], 
        service_type: LLMServiceType,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Поиск в базе знаний"""
        try:
            # Используем централизованную архитектуру для поиска
            query = f"service_type:{service_type.value}"
            relevant_docs = await self.llm_service.search_knowledge_base(query, limit)
            
            return [{"content": doc, "relevance": 0.8} for doc in relevant_docs]
            
        except Exception as e:
            logger.error(f"Ошибка поиска в базе знаний: {e}")
            return []
    
    async def _make_ollama_request(self, request: LLMRequest) -> LLMResponse:
        """Выполнение запроса к Ollama через централизованную архитектуру"""
        start_time = time.time()
        
        try:
            # Логируем входящий запрос
            logger.info(f"🤖 LLM ЗАПРОС [{request.service_type.value}]")
            logger.info(f"📝 Промпт: {request.prompt[:200]}{'...' if len(request.prompt) > 200 else ''}")
            logger.info(f"🔧 Параметры: модель={request.llm_model}, токены={request.max_tokens}, temp={request.temperature}")
            
            # Генерируем RAG контекст
            logger.info("🔍 Генерация RAG контекста...")
            rag_context = await self._generate_rag_context(request)
            
            if rag_context:
                logger.info(f"📚 RAG контекст найден: {len(rag_context)} символов")
                logger.info(f"📖 RAG контекст: {rag_context[:300]}{'...' if len(rag_context) > 300 else ''}")
                
                final_prompt = f"""
                Контекст для ответа:
                {rag_context}
                
                Запрос пользователя:
                {request.prompt}
                
                Ответь на основе предоставленного контекста:
                """
            else:
                logger.info("⚠️ RAG контекст не найден, используем прямой промпт")
                final_prompt = request.prompt
            
            logger.info(f"🚀 Отправка запроса к Ollama...")
            logger.info(f"📤 Финальный промпт: {final_prompt[:300]}{'...' if len(final_prompt) > 300 else ''}")
            
            # Отправляем запрос через централизованную архитектуру
            response = await self.llm_service.process_llm_request(
                prompt=final_prompt,
                llm_model=request.llm_model,
                priority=request.priority,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                use_rag=request.use_rag,
                metadata={
                    "service_type": request.service_type.value,
                    "context": request.context
                }
            )
            
            response_time = time.time() - start_time
            
            # Логируем ответ от Ollama
            logger.info(f"✅ OLLAMA ОТВЕТ [{request.service_type.value}]")
            logger.info(f"⏱️ Время ответа: {response_time:.2f}s")
            logger.info(f"🧠 Модель: {response.model_used}")
            logger.info(f"🔢 Токены: {response.tokens_used}")
            logger.info(f"📄 Ответ: {response.response[:500]}{'...' if len(response.response) > 500 else ''}")
            logger.info(f"🔍 RAG усилен: {response.rag_enhanced}")
            logger.info(f"💾 Кэш хит: {response.cache_hit}")
            
            # Записываем метрики производительности
            await self.system_analyzer.record_performance(
                response_time, 
                True, 
                response.tokens_used
            )
            
            # Создаем ответ в старом формате для совместимости
            llm_response = LLMResponse(
                content=response.response,
                service_type=request.service_type,
                used_model=response.model_used,
                tokens_used=response.tokens_used,
                response_time=response_time,
                cached=False,
                metadata={
                    "rag_enhanced": response.rag_enhanced,
                    "cache_hit": response.cache_hit,
                    "original_request_id": response.request_id
                }
            )
            
            logger.info(f"🎯 Запрос {request.service_type.value} успешно обработан за {response_time:.2f}s")
            return llm_response
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Логируем ошибку
            logger.error(f"❌ ОШИБКА LLM [{request.service_type.value}]")
            logger.error(f"⏱️ Время до ошибки: {response_time:.2f}s")
            logger.error(f"🚨 Ошибка: {str(e)}")
            logger.error(f"📝 Промпт: {request.prompt[:200]}{'...' if len(request.prompt) > 200 else ''}")
            
            # Записываем ошибку
            await self.system_analyzer.record_performance(response_time, False, 0)
            
            return LLMResponse(
                content="",
                service_type=request.service_type,
                used_model=request.llm_model,
                tokens_used=0,
                response_time=response_time,
                error=str(e)
            )
    
    async def process_request(self, request: LLMRequest) -> LLMResponse:
        """Обработка LLM запроса"""
        if not self._initialized:
            raise RuntimeError("LLMRouter не инициализирован")
        
        # Проверяем кэш
        cache_key = self._generate_cache_key(request)
        cached_response = await self._get_cached_response(cache_key)
        
        if cached_response:
            logger.info(f"Кэш-хит для {request.service_type.value}")
            return cached_response
        
        # Обрабатываем запрос
        response = await self._make_ollama_request(request)
        
        # Кэшируем успешный ответ
        if not response.error:
            await self._cache_response(cache_key, response, request.cache_ttl)
        
        return response
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики роутера"""
        if not self._initialized:
            return {"error": "LLMRouter не инициализирован"}
        
        # Получаем метрики централизованной архитектуры
        llm_metrics = await self.llm_service.get_metrics()
        
        # Получаем отчет об оптимизации
        optimization_report = await self.system_analyzer.get_optimization_report()
        
        return {
            "llm_metrics": llm_metrics,
            "optimization_report": optimization_report,
            "initialized": self._initialized
        }
    
    async def health_check(self) -> bool:
        """Проверка здоровья роутера"""
        if not self._initialized:
            return False
        
        try:
            health_status = await self.llm_service.health_check()
            return health_status.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья: {e}")
            return False

# Глобальные экземпляры для экспорта
system_analyzer = SystemAnalyzer()
_llm_router: Optional[LLMRouter] = None

async def get_llm_router() -> LLMRouter:
    """Получение глобального экземпляра LLM роутера"""
    global _llm_router
    
    if _llm_router is None:
        _llm_router = LLMRouter()
        await _llm_router.start()
    
    return _llm_router

# Инициализация llm_router для экспорта
llm_router = LLMRouter()

# Утилиты для быстрого доступа к функциям
async def generate_seo_recommendations(prompt: str, context: Optional[Dict] = None) -> str:
    """Генерация SEO рекомендаций"""
    router = await get_llm_router()
    
    request = LLMRequest(
        service_type=LLMServiceType.SEO_RECOMMENDATIONS,
        prompt=prompt,
        context=context,
        priority="high"
    )
    
    response = await router.process_request(request)
    
    if response.error:
        raise LLMServiceError(f"Ошибка генерации SEO рекомендаций: {response.error}")
    
    return response.content

async def generate_diagram(prompt: str, diagram_type: str = "architecture") -> str:
    """Генерация диаграммы"""
    router = await get_llm_router()
    
    request = LLMRequest(
        service_type=LLMServiceType.DIAGRAM_GENERATION,
        prompt=f"Создай {diagram_type} диаграмму: {prompt}",
        priority="normal"
    )
    
    response = await router.process_request(request)
    
    if response.error:
        raise LLMServiceError(f"Ошибка генерации диаграммы: {response.error}")
    
    return response.content

async def analyze_content(content: str, analysis_type: str = "general") -> str:
    """Анализ контента"""
    router = await get_llm_router()
    
    request = LLMRequest(
        service_type=LLMServiceType.CONTENT_ANALYSIS,
        prompt=f"Проанализируй контент ({analysis_type}): {content}",
        priority="normal"
    )
    
    response = await router.process_request(request)
    
    if response.error:
        raise LLMServiceError(f"Ошибка анализа контента: {response.error}")
    
    return response.content

async def run_benchmark(benchmark_type: str, parameters: Dict[str, Any]) -> str:
    """Запуск бенчмарка"""
    router = await get_llm_router()
    
    request = LLMRequest(
        service_type=LLMServiceType.BENCHMARK_SERVICE,
        prompt=f"Запусти {benchmark_type} бенчмарк с параметрами: {parameters}",
        priority="low"
    )
    
    response = await router.process_request(request)
    
    if response.error:
        raise LLMServiceError(f"Ошибка запуска бенчмарка: {response.error}")
    
    return response.content

async def tune_llm_model(model_config: Dict[str, Any], tuning_params: Dict[str, Any]) -> str:
    """Тюнинг LLM модели"""
    router = await get_llm_router()
    
    request = LLMRequest(
        service_type=LLMServiceType.LLM_TUNING,
        prompt=f"Настрой модель с конфигурацией {model_config} и параметрами {tuning_params}",
        priority="background"
    )
    
    response = await router.process_request(request)
    
    if response.error:
        raise LLMServiceError(f"Ошибка тюнинга модели: {response.error}")
    
    return response.content 