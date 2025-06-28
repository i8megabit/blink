"""
Интеграция централизованной LLM архитектуры с микросервисами reLink
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .config import settings
from .llm.centralized_architecture import (
    CentralizedLLMArchitecture, 
    LLMRequest, 
    LLMResponse,
    get_architecture,
    shutdown_architecture
)
from .llm.concurrent_manager import ConcurrentOllamaManager
from .llm.distributed_cache import DistributedCache
from .llm.request_prioritizer import RequestPrioritizer
from .llm.rag_monitor import RAGMonitor

logger = logging.getLogger(__name__)

class LLMIntegrationService:
    """Сервис интеграции LLM с микросервисами"""
    
    def __init__(self):
        self.architecture: Optional[CentralizedLLMArchitecture] = None
        self._initialized = False
        
        logger.info("LLMIntegrationService инициализирован")
    
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Инициализация централизованной архитектуры"""
        if self._initialized:
            logger.warning("LLMIntegrationService уже инициализирован")
            return
        
        try:
            # Получаем глобальный экземпляр архитектуры
            self.architecture = await get_architecture()
            self._initialized = True
            
            logger.info("LLMIntegrationService успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации LLMIntegrationService: {e}")
            raise
    
    async def shutdown(self):
        """Завершение работы сервиса"""
        if not self._initialized:
            return
        
        try:
            await shutdown_architecture()
            self._initialized = False
            logger.info("LLMIntegrationService завершен")
            
        except Exception as e:
            logger.error(f"Ошибка завершения LLMIntegrationService: {e}")
    
    async def process_llm_request(
        self,
        prompt: str,
        model_name: str = "qwen2.5:7b",
        priority: str = "normal",
        max_tokens: int = 100,
        temperature: float = 0.7,
        use_rag: bool = True,
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Обработка LLM запроса через централизованную архитектуру"""
        if not self._initialized:
            raise RuntimeError("LLMIntegrationService не инициализирован")
        
        # Создаем запрос
        request = LLMRequest(
            id=str(uuid.uuid4()),
            prompt=prompt,
            model_name=model_name,
            priority=priority,
            max_tokens=max_tokens,
            temperature=temperature,
            use_rag=use_rag,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Отправляем запрос в архитектуру
        request_id = await self.architecture.submit_request(request)
        
        # Получаем ответ
        response = await self.architecture.get_response(request_id)
        
        if response is None:
            raise TimeoutError(f"Таймаут ожидания ответа для запроса {request_id}")
        
        return response
    
    async def generate_response(
        self,
        prompt: str,
        model_name: str = "qwen2.5:7b",
        max_tokens: int = 100,
        temperature: float = 0.7
    ) -> str:
        """Простая генерация ответа"""
        response = await self.process_llm_request(
            prompt=prompt,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.response
    
    async def get_embedding(self, text: str, model_name: str = "qwen2.5:7b") -> List[float]:
        """Получение эмбеддинга для текста"""
        if not self._initialized:
            raise RuntimeError("LLMIntegrationService не инициализирован")
        
        return await self.architecture.concurrent_manager.get_embedding(text, model_name)
    
    async def search_knowledge_base(self, query: str, limit: int = 5) -> List[str]:
        """Поиск в базе знаний"""
        if not self._initialized:
            raise RuntimeError("LLMIntegrationService не инициализирован")
        
        return await self.architecture.cache_manager.search_knowledge_base(query, limit)
    
    async def add_to_knowledge_base(self, documents: List[Dict[str, Any]]) -> bool:
        """Добавление документов в базу знаний"""
        if not self._initialized:
            raise RuntimeError("LLMIntegrationService не инициализирован")
        
        return await self.architecture.cache_manager.add_to_knowledge_base(documents)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик архитектуры"""
        if not self._initialized:
            return {"error": "LLMIntegrationService не инициализирован"}
        
        return self.architecture.get_metrics()
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья архитектуры"""
        if not self._initialized:
            return {"status": "not_initialized"}
        
        return await self.architecture.health_check()

# Глобальный экземпляр сервиса интеграции
_llm_integration_service: Optional[LLMIntegrationService] = None

async def get_llm_integration_service() -> LLMIntegrationService:
    """Получение глобального экземпляра сервиса интеграции"""
    global _llm_integration_service
    
    if _llm_integration_service is None:
        _llm_integration_service = LLMIntegrationService()
        await _llm_integration_service.initialize()
    
    return _llm_integration_service

async def shutdown_llm_integration():
    """Завершение работы сервиса интеграции"""
    global _llm_integration_service
    
    if _llm_integration_service:
        await _llm_integration_service.shutdown()
        _llm_integration_service = None

# Интеграция с существующими микросервисами

class TestingServiceIntegration:
    """Интеграция с сервисом тестирования"""
    
    def __init__(self, llm_service: LLMIntegrationService):
        self.llm_service = llm_service
    
    async def generate_test_case(self, description: str, test_type: str = "unit") -> str:
        """Генерация тест-кейса"""
        prompt = f"""
        Создай {test_type} тест для следующего описания:
        {description}
        
        Верни только код теста без дополнительных комментариев.
        """
        
        return await self.llm_service.generate_response(
            prompt=prompt,
            max_tokens=500,
            temperature=0.3
        )
    
    async def analyze_test_results(self, test_output: str) -> str:
        """Анализ результатов тестирования"""
        prompt = f"""
        Проанализируй результаты тестирования и дай рекомендации:
        
        {test_output}
        
        Предложи улучшения и исправления.
        """
        
        return await self.llm_service.generate_response(
            prompt=prompt,
            max_tokens=300,
            temperature=0.5
        )

class DiagramServiceIntegration:
    """Интеграция с сервисом диаграмм"""
    
    def __init__(self, llm_service: LLMIntegrationService):
        self.llm_service = llm_service
    
    async def generate_diagram_description(self, data: Dict[str, Any], diagram_type: str = "flowchart") -> str:
        """Генерация описания диаграммы"""
        prompt = f"""
        Создай описание {diagram_type} диаграммы на основе данных:
        
        {data}
        
        Верни описание в формате, подходящем для генерации SVG диаграммы.
        """
        
        return await self.llm_service.generate_response(
            prompt=prompt,
            max_tokens=400,
            temperature=0.4
        )
    
    async def optimize_diagram_layout(self, current_layout: str, feedback: str) -> str:
        """Оптимизация макета диаграммы"""
        prompt = f"""
        Оптимизируй макет диаграммы на основе обратной связи:
        
        Текущий макет:
        {current_layout}
        
        Обратная связь:
        {feedback}
        
        Предложи улучшенный макет.
        """
        
        return await self.llm_service.generate_response(
            prompt=prompt,
            max_tokens=300,
            temperature=0.6
        )

class MonitoringServiceIntegration:
    """Интеграция с сервисом мониторинга"""
    
    def __init__(self, llm_service: LLMIntegrationService):
        self.llm_service = llm_service
    
    async def analyze_performance_data(self, metrics: Dict[str, Any]) -> str:
        """Анализ данных производительности"""
        prompt = f"""
        Проанализируй метрики производительности и дай рекомендации:
        
        {metrics}
        
        Определи узкие места и предложи оптимизации.
        """
        
        return await self.llm_service.generate_response(
            prompt=prompt,
            max_tokens=400,
            temperature=0.3
        )
    
    async def generate_alert_description(self, alert_data: Dict[str, Any]) -> str:
        """Генерация описания алерта"""
        prompt = f"""
        Создай понятное описание алерта на основе данных:
        
        {alert_data}
        
        Сделай описание понятным для разработчиков и операторов.
        """
        
        return await self.llm_service.generate_response(
            prompt=prompt,
            max_tokens=200,
            temperature=0.5
        )

# Фабрика интеграций для микросервисов
class LLMIntegrationFactory:
    """Фабрика для создания интеграций с микросервисами"""
    
    def __init__(self, llm_service: LLMIntegrationService):
        self.llm_service = llm_service
        self._integrations: Dict[str, Any] = {}
    
    def get_testing_integration(self) -> TestingServiceIntegration:
        """Получение интеграции для сервиса тестирования"""
        if "testing" not in self._integrations:
            self._integrations["testing"] = TestingServiceIntegration(self.llm_service)
        return self._integrations["testing"]
    
    def get_diagram_integration(self) -> DiagramServiceIntegration:
        """Получение интеграции для сервиса диаграмм"""
        if "diagram" not in self._integrations:
            self._integrations["diagram"] = DiagramServiceIntegration(self.llm_service)
        return self._integrations["diagram"]
    
    def get_monitoring_integration(self) -> MonitoringServiceIntegration:
        """Получение интеграции для сервиса мониторинга"""
        if "monitoring" not in self._integrations:
            self._integrations["monitoring"] = MonitoringServiceIntegration(self.llm_service)
        return self._integrations["monitoring"]

# Утилиты для быстрой интеграции
async def quick_llm_response(prompt: str, **kwargs) -> str:
    """Быстрый LLM ответ для простых случаев"""
    service = await get_llm_integration_service()
    return await service.generate_response(prompt, **kwargs)

async def quick_embedding(text: str, **kwargs) -> List[float]:
    """Быстрое получение эмбеддинга"""
    service = await get_llm_integration_service()
    return await service.get_embedding(text, **kwargs)

async def quick_knowledge_search(query: str, **kwargs) -> List[str]:
    """Быстрый поиск в базе знаний"""
    service = await get_llm_integration_service()
    return await service.search_knowledge_base(query, **kwargs) 