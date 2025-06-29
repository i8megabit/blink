"""
Интеллектуальный роутер моделей для Ollama с автоматическим выбором оптимальной модели
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import psutil
import aiohttp
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Типы моделей для разных задач"""
    FAST_RESPONSE = "fast_response"      # Быстрые ответы
    HIGH_QUALITY = "high_quality"        # Высокое качество
    CODE_GENERATION = "code_generation"  # Генерация кода
    ANALYSIS = "analysis"                # Анализ и размышления
    CREATIVE = "creative"                # Креативные задачи


class TaskComplexity(Enum):
    """Уровни сложности задач"""
    SIMPLE = "simple"        # Простые запросы
    MEDIUM = "medium"        # Средняя сложность
    COMPLEX = "complex"      # Сложные задачи
    EXPERT = "expert"        # Экспертный уровень


@dataclass
class ModelConfig:
    """Конфигурация модели"""
    name: str
    type: ModelType
    max_tokens: int
    temperature: float
    top_p: float
    top_k: int
    repeat_penalty: float
    cpu_threads: int
    gpu_layers: int
    memory_usage: int  # MB
    response_time_target: float  # секунды
    quality_score: float  # 0-1


@dataclass
class SystemMetrics:
    """Метрики системы"""
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    available_memory: int
    load_average: float


@dataclass
class ModelPerformance:
    """Производительность модели"""
    model_name: str
    avg_response_time: float
    success_rate: float
    error_rate: float
    last_used: float
    usage_count: int


class IntelligentModelRouter:
    """
    Интеллектуальный роутер для автоматического выбора оптимальной модели
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Конфигурации моделей для Apple Silicon
        self.model_configs = {
            "qwen2.5:0.5b": ModelConfig(
                name="qwen2.5:0.5b",
                type=ModelType.FAST_RESPONSE,
                max_tokens=2048,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                cpu_threads=8,
                gpu_layers=35,
                memory_usage=1024,
                response_time_target=2.0,
                quality_score=0.6
            ),
            "qwen2.5:1.5b": ModelConfig(
                name="qwen2.5:1.5b", 
                type=ModelType.HIGH_QUALITY,
                max_tokens=4096,
                temperature=0.8,
                top_p=0.95,
                top_k=50,
                repeat_penalty=1.15,
                cpu_threads=12,
                gpu_layers=35,
                memory_usage=2048,
                response_time_target=5.0,
                quality_score=0.8
            ),
            "qwen2.5:3b": ModelConfig(
                name="qwen2.5:3b",
                type=ModelType.CODE_GENERATION,
                max_tokens=8192,
                temperature=0.3,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                cpu_threads=16,
                gpu_layers=35,
                memory_usage=4096,
                response_time_target=8.0,
                quality_score=0.9
            ),
            "qwen2.5:7b": ModelConfig(
                name="qwen2.5:7b",
                type=ModelType.ANALYSIS,
                max_tokens=16384,
                temperature=0.7,
                top_p=0.95,
                top_k=50,
                repeat_penalty=1.2,
                cpu_threads=20,
                gpu_layers=35,
                memory_usage=8192,
                response_time_target=15.0,
                quality_score=0.95
            ),
            "qwen2.5:14b": ModelConfig(
                name="qwen2.5:14b",
                type=ModelType.EXPERT,
                max_tokens=32768,
                temperature=0.8,
                top_p=0.98,
                top_k=60,
                repeat_penalty=1.25,
                cpu_threads=24,
                gpu_layers=35,
                memory_usage=16384,
                response_time_target=30.0,
                quality_score=0.98
            )
        }
        
        # Кэш производительности моделей
        self.model_performance: Dict[str, ModelPerformance] = {}
        
        # Статистика использования
        self.usage_stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "fallback_routes": 0,
            "errors": 0
        }
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Получение метрик системы"""
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            
            # Попытка получить GPU метрики (если доступно)
            gpu_usage = None
            try:
                # Здесь можно добавить интеграцию с nvidia-ml-py или другими GPU мониторами
                pass
            except:
                pass
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                gpu_usage=gpu_usage,
                available_memory=memory.available // (1024 * 1024),  # MB
                load_average=load_avg
            )
        except Exception as e:
            logger.error(f"Ошибка получения метрик системы: {e}")
            return SystemMetrics(0, 0, None, 8192, 0)
    
    async def check_model_availability(self, model_name: str) -> bool:
        """Проверка доступности модели"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_base_url}/api/tags") as response:
                    if response.status == 200:
                        models = await response.json()
                        return any(model['name'] == model_name for model in models.get('models', []))
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки доступности модели {model_name}: {e}")
            return False
    
    def analyze_task_complexity(self, prompt: str, context_length: int = 0) -> TaskComplexity:
        """Анализ сложности задачи на основе промпта"""
        # Простые эвристики для определения сложности
        word_count = len(prompt.split())
        
        # Ключевые слова для определения типа задачи
        code_keywords = ['код', 'функция', 'класс', 'алгоритм', 'программа', 'script', 'function', 'class']
        analysis_keywords = ['анализ', 'сравни', 'объясни', 'почему', 'как работает', 'analyze', 'explain']
        creative_keywords = ['создай', 'придумай', 'вообрази', 'креатив', 'creative', 'imagine', 'create']
        
        code_score = sum(1 for keyword in code_keywords if keyword.lower() in prompt.lower())
        analysis_score = sum(1 for keyword in analysis_keywords if keyword.lower() in prompt.lower())
        creative_score = sum(1 for keyword in creative_keywords if keyword.lower() in prompt.lower())
        
        # Определение сложности
        if word_count < 20 and context_length < 1000:
            return TaskComplexity.SIMPLE
        elif word_count < 100 and context_length < 5000:
            return TaskComplexity.MEDIUM
        elif word_count < 300 and context_length < 15000:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.EXPERT
    
    def select_optimal_model(
        self, 
        task_complexity: TaskComplexity,
        system_metrics: SystemMetrics,
        preferred_type: Optional[ModelType] = None
    ) -> Tuple[str, ModelConfig]:
        """Выбор оптимальной модели на основе метрик"""
        
        available_models = []
        
        # Фильтрация доступных моделей по ресурсам
        for model_name, config in self.model_configs.items():
            # Проверка доступности памяти
            if config.memory_usage > system_metrics.available_memory * 0.8:
                continue
                
            # Проверка нагрузки CPU
            if system_metrics.cpu_usage > 90:
                continue
                
            # Проверка предпочтительного типа
            if preferred_type and config.type != preferred_type:
                continue
                
            available_models.append((model_name, config))
        
        if not available_models:
            # Fallback к самой легкой модели
            return "qwen2.5:0.5b", self.model_configs["qwen2.5:0.5b"]
        
        # Сортировка по приоритету
        def model_score(model_tuple):
            name, config = model_tuple
            
            # Базовый скор качества
            score = config.quality_score
            
            # Корректировка по сложности задачи
            if task_complexity == TaskComplexity.SIMPLE:
                score *= 1.2 if config.type == ModelType.FAST_RESPONSE else 0.8
            elif task_complexity == TaskComplexity.MEDIUM:
                score *= 1.1 if config.type == ModelType.HIGH_QUALITY else 0.9
            elif task_complexity == TaskComplexity.COMPLEX:
                score *= 1.1 if config.type == ModelType.CODE_GENERATION else 0.9
            elif task_complexity == TaskComplexity.EXPERT:
                score *= 1.2 if config.type == ModelType.ANALYSIS else 0.8
            
            # Корректировка по производительности
            if name in self.model_performance:
                perf = self.model_performance[name]
                score *= perf.success_rate
                score *= (1 - perf.error_rate)
            
            # Корректировка по ресурсам
            memory_factor = 1 - (config.memory_usage / system_metrics.available_memory)
            score *= memory_factor
            
            return score
        
        # Выбор модели с наивысшим скором
        best_model = max(available_models, key=model_score)
        return best_model
    
    async def route_request(
        self, 
        prompt: str, 
        context: str = "",
        preferred_model: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Маршрутизация запроса к оптимальной модели"""
        
        start_time = time.time()
        self.usage_stats["total_requests"] += 1
        
        try:
            # Анализ задачи
            task_complexity = self.analyze_task_complexity(prompt, len(context))
            
            # Получение метрик системы
            system_metrics = await self.get_system_metrics()
            
            # Выбор модели
            if preferred_model and preferred_model in self.model_configs:
                model_name = preferred_model
                model_config = self.model_configs[preferred_model]
            else:
                model_name, model_config = self.select_optimal_model(
                    task_complexity, 
                    system_metrics
                )
            
            # Проверка доступности модели
            if not await self.check_model_availability(model_name):
                logger.warning(f"Модель {model_name} недоступна, поиск альтернативы")
                # Поиск альтернативной модели
                for alt_name, alt_config in self.model_configs.items():
                    if alt_name != model_name and await self.check_model_availability(alt_name):
                        model_name = alt_name
                        model_config = alt_config
                        break
                else:
                    raise Exception("Нет доступных моделей")
            
            # Подготовка параметров
            params = {
                "model": model_name,
                "prompt": prompt,
                "context": context,
                "stream": False,
                "options": {
                    "num_predict": max_tokens or model_config.max_tokens,
                    "temperature": model_config.temperature,
                    "top_p": model_config.top_p,
                    "top_k": model_config.top_k,
                    "repeat_penalty": model_config.repeat_penalty,
                    "num_ctx": model_config.max_tokens,
                    "num_thread": model_config.cpu_threads,
                    "num_gpu": model_config.gpu_layers
                }
            }
            
            # Выполнение запроса
            response = await self._make_ollama_request(params)
            
            # Обновление статистики
            response_time = time.time() - start_time
            self._update_model_performance(model_name, response_time, True)
            self.usage_stats["successful_routes"] += 1
            
            return {
                "model_used": model_name,
                "response": response,
                "response_time": response_time,
                "task_complexity": task_complexity.value,
                "system_metrics": {
                    "cpu_usage": system_metrics.cpu_usage,
                    "memory_usage": system_metrics.memory_usage,
                    "available_memory": system_metrics.available_memory
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка маршрутизации запроса: {e}")
            self.usage_stats["errors"] += 1
            
            # Fallback к самой легкой модели
            try:
                fallback_response = await self._make_ollama_request({
                    "model": "qwen2.5:0.5b",
                    "prompt": prompt,
                    "context": context,
                    "stream": False,
                    "options": {
                        "num_predict": 1024,
                        "temperature": 0.7,
                        "num_thread": 4
                    }
                })
                
                self.usage_stats["fallback_routes"] += 1
                return {
                    "model_used": "qwen2.5:0.5b (fallback)",
                    "response": fallback_response,
                    "error": str(e),
                    "fallback": True
                }
            except Exception as fallback_error:
                logger.error(f"Fallback также не удался: {fallback_error}")
                raise
    
    async def _make_ollama_request(self, params: Dict[str, Any]) -> str:
        """Выполнение запроса к Ollama"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_base_url}/api/generate",
                json=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {response.status} - {error_text}")
    
    def _update_model_performance(self, model_name: str, response_time: float, success: bool):
        """Обновление статистики производительности модели"""
        if model_name not in self.model_performance:
            self.model_performance[model_name] = ModelPerformance(
                model_name=model_name,
                avg_response_time=response_time,
                success_rate=1.0 if success else 0.0,
                error_rate=0.0 if success else 1.0,
                last_used=time.time(),
                usage_count=1
            )
        else:
            perf = self.model_performance[model_name]
            # Экспоненциальное скользящее среднее
            alpha = 0.1
            perf.avg_response_time = alpha * response_time + (1 - alpha) * perf.avg_response_time
            perf.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * perf.success_rate
            perf.error_rate = alpha * (0.0 if success else 1.0) + (1 - alpha) * perf.error_rate
            perf.last_used = time.time()
            perf.usage_count += 1
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Получение статистики роутера"""
        return {
            "usage_stats": self.usage_stats,
            "model_performance": {
                name: {
                    "avg_response_time": perf.avg_response_time,
                    "success_rate": perf.success_rate,
                    "error_rate": perf.error_rate,
                    "usage_count": perf.usage_count,
                    "last_used": perf.last_used
                }
                for name, perf in self.model_performance.items()
            },
            "available_models": list(self.model_configs.keys())
        }
    
    async def preload_models(self, model_names: List[str] = None):
        """Предзагрузка моделей для ускорения работы"""
        if model_names is None:
            model_names = ["qwen2.5:0.5b", "qwen2.5:1.5b"]
        
        for model_name in model_names:
            if model_name in self.model_configs:
                try:
                    # Отправляем тестовый запрос для загрузки модели
                    await self._make_ollama_request({
                        "model": model_name,
                        "prompt": "test",
                        "stream": False,
                        "options": {"num_predict": 1}
                    })
                    logger.info(f"Модель {model_name} предзагружена")
                except Exception as e:
                    logger.warning(f"Не удалось предзагрузить модель {model_name}: {e}")


# Глобальный экземпляр роутера
model_router = IntelligentModelRouter() 