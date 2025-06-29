"""
Менеджер оптимизаций для объединения всех компонентов оптимизации
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import psutil
import aiohttp
from concurrent.futures import ThreadPoolExecutor

from .intelligent_model_router import IntelligentModelRouter, ModelType, TaskComplexity
from .advanced_chromadb_service import AdvancedChromaDBService

logger = logging.getLogger(__name__)


class OptimizationLevel(Enum):
    """Уровни оптимизации"""
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class SystemHealth:
    """Состояние здоровья системы"""
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    available_memory: int
    disk_usage: float
    load_average: float
    ollama_status: str
    chromadb_status: str
    redis_status: str


@dataclass
class OptimizationMetrics:
    """Метрики оптимизации"""
    total_requests: int
    avg_response_time: float
    cache_hit_rate: float
    model_utilization: Dict[str, float]
    memory_efficiency: float
    cpu_efficiency: float
    optimization_score: float


class OptimizationManager:
    """
    Центральный менеджер оптимизаций для reLink
    """
    
    def __init__(
        self,
        optimization_level: OptimizationLevel = OptimizationLevel.ADVANCED,
        auto_optimize: bool = True,
        optimization_interval: int = 300  # 5 минут
    ):
        self.optimization_level = optimization_level
        self.auto_optimize = auto_optimize
        self.optimization_interval = optimization_interval
        
        # Инициализация компонентов
        self.model_router = IntelligentModelRouter()
        self.chromadb_service = AdvancedChromaDBService()
        
        # Thread pool для фоновых задач
        self.executor = ThreadPoolExecutor(max_workers=8)
        
        # Статистика оптимизации
        self.optimization_stats = {
            "total_optimizations": 0,
            "last_optimization": 0,
            "optimization_duration": 0,
            "performance_improvements": {}
        }
        
        # Флаг работы фоновой оптимизации
        self.background_task_running = False
        
        logger.info(f"OptimizationManager инициализирован с уровнем {optimization_level.value}")
    
    async def start(self):
        """Запуск менеджера оптимизаций"""
        
        try:
            # Предзагрузка моделей
            await self._preload_models()
            
            # Инициализация ChromaDB
            await self._initialize_chromadb()
            
            # Запуск фоновой оптимизации
            if self.auto_optimize:
                asyncio.create_task(self._background_optimization_loop())
            
            logger.info("OptimizationManager запущен успешно")
            
        except Exception as e:
            logger.error(f"Ошибка запуска OptimizationManager: {e}")
            raise
    
    async def _preload_models(self):
        """Предзагрузка часто используемых моделей"""
        
        # Определение моделей для предзагрузки в зависимости от уровня оптимизации
        if self.optimization_level == OptimizationLevel.BASIC:
            models_to_preload = ["qwen2.5:0.5b"]
        elif self.optimization_level == OptimizationLevel.STANDARD:
            models_to_preload = ["qwen2.5:0.5b", "qwen2.5:1.5b"]
        elif self.optimization_level == OptimizationLevel.ADVANCED:
            models_to_preload = ["qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b"]
        else:  # EXPERT
            models_to_preload = ["qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b"]
        
        logger.info(f"Предзагрузка моделей: {models_to_preload}")
        await self.model_router.preload_models(models_to_preload)
    
    async def _initialize_chromadb(self):
        """Инициализация ChromaDB с оптимизациями"""
        
        try:
            # Проверка здоровья ChromaDB
            health_status = await self.chromadb_service.health_check()
            
            if health_status["status"] == "healthy":
                logger.info("ChromaDB инициализирован успешно")
                
                # Оптимизация коллекций если необходимо
                if self.optimization_level in [OptimizationLevel.ADVANCED, OptimizationLevel.EXPERT]:
                    await self.chromadb_service.optimize_collections()
            else:
                logger.warning(f"ChromaDB имеет проблемы: {health_status}")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации ChromaDB: {e}")
    
    async def _background_optimization_loop(self):
        """Фоновая оптимизация системы"""
        
        self.background_task_running = True
        
        while self.background_task_running:
            try:
                await asyncio.sleep(self.optimization_interval)
                
                # Проверка необходимости оптимизации
                if await self._should_optimize():
                    await self.optimize_system()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в фоновой оптимизации: {e}")
                await asyncio.sleep(60)  # Пауза перед повторной попыткой
    
    async def _should_optimize(self) -> bool:
        """Определение необходимости оптимизации"""
        
        # Проверка метрик системы
        system_health = await self.get_system_health()
        
        # Оптимизация при высоком использовании ресурсов
        if system_health.cpu_usage > 80 or system_health.memory_usage > 85:
            return True
        
        # Оптимизация при низкой производительности
        router_stats = self.model_router.get_router_stats()
        if router_stats["usage_stats"]["total_requests"] > 0:
            error_rate = router_stats["usage_stats"]["errors"] / router_stats["usage_stats"]["total_requests"]
            if error_rate > 0.1:  # Более 10% ошибок
                return True
        
        # Периодическая оптимизация
        time_since_last = time.time() - self.optimization_stats["last_optimization"]
        if time_since_last > 3600:  # Каждый час
            return True
        
        return False
    
    async def optimize_system(self):
        """Комплексная оптимизация системы"""
        
        start_time = time.time()
        logger.info("Начинается комплексная оптимизация системы")
        
        try:
            # 1. Оптимизация ChromaDB
            await self._optimize_chromadb()
            
            # 2. Оптимизация роутера моделей
            await self._optimize_model_router()
            
            # 3. Оптимизация ресурсов
            await self._optimize_resources()
            
            # 4. Анализ производительности
            await self._analyze_performance()
            
            # Обновление статистики
            optimization_duration = time.time() - start_time
            self.optimization_stats["total_optimizations"] += 1
            self.optimization_stats["last_optimization"] = time.time()
            self.optimization_stats["optimization_duration"] = optimization_duration
            
            logger.info(f"Оптимизация завершена за {optimization_duration:.2f} секунд")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации системы: {e}")
    
    async def _optimize_chromadb(self):
        """Оптимизация ChromaDB"""
        
        try:
            # Оптимизация коллекций
            await self.chromadb_service.optimize_collections()
            
            # Очистка кеша
            await self.chromadb_service._cleanup_cache()
            
            logger.info("ChromaDB оптимизирован")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации ChromaDB: {e}")
    
    async def _optimize_model_router(self):
        """Оптимизация роутера моделей"""
        
        try:
            # Анализ производительности моделей
            router_stats = self.model_router.get_router_stats()
            
            # Удаление плохо работающих моделей из кеша
            for model_name, perf in router_stats["model_performance"].items():
                if perf["error_rate"] > 0.3:  # Более 30% ошибок
                    logger.warning(f"Модель {model_name} имеет высокий уровень ошибок: {perf['error_rate']}")
            
            # Предзагрузка популярных моделей
            popular_models = sorted(
                router_stats["model_performance"].items(),
                key=lambda x: x[1]["usage_count"],
                reverse=True
            )[:3]
            
            if popular_models:
                model_names = [model[0] for model in popular_models]
                await self.model_router.preload_models(model_names)
            
            logger.info("Роутер моделей оптимизирован")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации роутера моделей: {e}")
    
    async def _optimize_resources(self):
        """Оптимизация ресурсов системы"""
        
        try:
            # Проверка использования памяти
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                logger.warning("Высокое использование памяти, запуск очистки")
                
                # Принудительная очистка кешей
                self.model_router.local_cache.clear()
                await self.chromadb_service._cleanup_cache()
                
                # Сборка мусора
                import gc
                gc.collect()
            
            # Проверка дискового пространства
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > 90:
                logger.warning("Критически мало места на диске")
            
            logger.info("Ресурсы оптимизированы")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации ресурсов: {e}")
    
    async def _analyze_performance(self):
        """Анализ производительности системы"""
        
        try:
            # Сбор метрик
            router_stats = self.model_router.get_router_stats()
            chromadb_stats = self.chromadb_service.get_performance_stats()
            system_health = await self.get_system_health()
            
            # Расчет общего скора производительности
            performance_score = self._calculate_performance_score(
                router_stats, chromadb_stats, system_health
            )
            
            self.optimization_stats["performance_improvements"] = {
                "performance_score": performance_score,
                "router_stats": router_stats,
                "chromadb_stats": chromadb_stats,
                "system_health": system_health
            }
            
            logger.info(f"Скор производительности: {performance_score:.2f}")
            
        except Exception as e:
            logger.error(f"Ошибка анализа производительности: {e}")
    
    def _calculate_performance_score(
        self,
        router_stats: Dict[str, Any],
        chromadb_stats: Dict[str, Any],
        system_health: SystemHealth
    ) -> float:
        """Расчет общего скора производительности"""
        
        score = 0.0
        
        # Скор роутера моделей (40%)
        if router_stats["usage_stats"]["total_requests"] > 0:
            success_rate = router_stats["usage_stats"]["successful_routes"] / router_stats["usage_stats"]["total_requests"]
            avg_response_time = sum(
                perf["avg_response_time"] for perf in router_stats["model_performance"].values()
            ) / len(router_stats["model_performance"]) if router_stats["model_performance"] else 0
            
            router_score = success_rate * (1 - min(avg_response_time / 10, 1))  # Нормализация
            score += router_score * 0.4
        
        # Скор ChromaDB (30%)
        if chromadb_stats["total_queries"] > 0:
            cache_hit_rate = chromadb_stats["cache_hit_rate"]
            avg_query_time = chromadb_stats["avg_query_time"]
            
            chromadb_score = cache_hit_rate * (1 - min(avg_query_time / 5, 1))
            score += chromadb_score * 0.3
        
        # Скор системы (30%)
        cpu_score = 1 - (system_health.cpu_usage / 100)
        memory_score = 1 - (system_health.memory_usage / 100)
        
        system_score = (cpu_score + memory_score) / 2
        score += system_score * 0.3
        
        return min(score, 1.0)  # Нормализация до 0-1
    
    async def process_request(
        self,
        prompt: str,
        context: str = "",
        collection_name: Optional[str] = None,
        query_texts: Optional[List[str]] = None,
        n_results: int = 10,
        preferred_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Обработка запроса с интеллектуальной оптимизацией"""
        
        start_time = time.time()
        
        try:
            # 1. Поиск в ChromaDB если указана коллекция
            chromadb_results = None
            if collection_name and query_texts:
                chromadb_results = await self.chromadb_service.query(
                    collection_name=collection_name,
                    query_texts=query_texts,
                    n_results=n_results
                )
                
                # Обогащение контекста результатами поиска
                if chromadb_results and chromadb_results.get("documents"):
                    enriched_context = context + "\n\n".join(chromadb_results["documents"])
                else:
                    enriched_context = context
            else:
                enriched_context = context
            
            # 2. Генерация ответа через роутер моделей
            llm_response = await self.model_router.route_request(
                prompt=prompt,
                context=enriched_context,
                preferred_model=preferred_model
            )
            
            # 3. Формирование итогового ответа
            total_time = time.time() - start_time
            
            response = {
                "llm_response": llm_response,
                "chromadb_results": chromadb_results,
                "total_processing_time": total_time,
                "optimization_level": self.optimization_level.value,
                "system_metrics": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            raise
    
    async def get_system_health(self) -> SystemHealth:
        """Получение состояния здоровья системы"""
        
        try:
            # Системные метрики
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            
            # GPU метрики (если доступно)
            gpu_usage = None
            try:
                # Здесь можно добавить интеграцию с GPU мониторами
                pass
            except:
                pass
            
            # Дисковое использование
            disk_usage = psutil.disk_usage('/').percent
            
            # Статус сервисов
            ollama_status = await self._check_ollama_status()
            chromadb_status = await self._check_chromadb_status()
            redis_status = await self._check_redis_status()
            
            return SystemHealth(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                gpu_usage=gpu_usage,
                available_memory=memory.available // (1024 * 1024),  # MB
                disk_usage=disk_usage,
                load_average=load_avg,
                ollama_status=ollama_status,
                chromadb_status=chromadb_status,
                redis_status=redis_status
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения состояния системы: {e}")
            return SystemHealth(0, 0, None, 0, 0, 0, "unknown", "unknown", "unknown")
    
    async def _check_ollama_status(self) -> str:
        """Проверка статуса Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags", timeout=5) as response:
                    return "healthy" if response.status == 200 else "unhealthy"
        except Exception:
            return "unavailable"
    
    async def _check_chromadb_status(self) -> str:
        """Проверка статуса ChromaDB"""
        try:
            health = await self.chromadb_service.health_check()
            return health["status"]
        except Exception:
            return "unavailable"
    
    async def _check_redis_status(self) -> str:
        """Проверка статуса Redis"""
        try:
            if self.chromadb_service.redis_available:
                self.chromadb_service.redis_client.ping()
                return "healthy"
            else:
                return "not_configured"
        except Exception:
            return "unavailable"
    
    def get_optimization_metrics(self) -> OptimizationMetrics:
        """Получение метрик оптимизации"""
        
        router_stats = self.model_router.get_router_stats()
        chromadb_stats = self.chromadb_service.get_performance_stats()
        
        # Расчет метрик
        total_requests = router_stats["usage_stats"]["total_requests"]
        avg_response_time = router_stats["usage_stats"]["successful_routes"] / total_requests if total_requests > 0 else 0
        cache_hit_rate = chromadb_stats["cache_hit_rate"]
        
        # Утилизация моделей
        model_utilization = {}
        for model_name, perf in router_stats["model_performance"].items():
            model_utilization[model_name] = perf["usage_count"] / total_requests if total_requests > 0 else 0
        
        # Эффективность ресурсов
        memory = psutil.virtual_memory()
        cpu_usage = psutil.cpu_percent()
        
        memory_efficiency = 1 - (memory.percent / 100)
        cpu_efficiency = 1 - (cpu_usage / 100)
        
        # Общий скор оптимизации
        optimization_score = (
            cache_hit_rate * 0.3 +
            memory_efficiency * 0.25 +
            cpu_efficiency * 0.25 +
            (1 - avg_response_time / 10) * 0.2  # Нормализация времени ответа
        )
        
        return OptimizationMetrics(
            total_requests=total_requests,
            avg_response_time=avg_response_time,
            cache_hit_rate=cache_hit_rate,
            model_utilization=model_utilization,
            memory_efficiency=memory_efficiency,
            cpu_efficiency=cpu_efficiency,
            optimization_score=optimization_score
        )
    
    async def stop(self):
        """Остановка менеджера оптимизаций"""
        
        self.background_task_running = False
        
        # Ожидание завершения фоновых задач
        await asyncio.sleep(1)
        
        # Закрытие thread pool
        self.executor.shutdown(wait=True)
        
        logger.info("OptimizationManager остановлен")


# Глобальный экземпляр менеджера
optimization_manager = OptimizationManager() 