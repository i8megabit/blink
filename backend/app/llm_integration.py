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
    
    async def initialize(self, redis_url: str = "redis://redis:6379"):
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
        llm_model: str = "qwen2.5:7b-instruct-turbo",
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
            llm_model=llm_model,
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
        llm_model: str = "qwen2.5:7b-instruct-turbo",
        max_tokens: int = 100,
        temperature: float = 0.7
    ) -> str:
        """Простая генерация ответа"""
        response = await self.process_llm_request(
            prompt=prompt,
            llm_model=llm_model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.response
    
    async def get_embedding(self, text: str, llm_model: str = "qwen2.5:7b-instruct-turbo") -> List[float]:
        """Получение эмбеддинга для текста"""
        if not self._initialized:
            raise RuntimeError("LLMIntegrationService не инициализирован")
        
        return await self.architecture.concurrent_manager.get_embedding(text, llm_model)
    
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
class SEOServiceIntegration:
    """Интеграция с SEO сервисом"""
    
    def __init__(self, llm_service: LLMIntegrationService):
        self.llm_service = llm_service
    
    async def analyze_domain_seo(self, domain: str, comprehensive: bool = True) -> Dict[str, Any]:
        """Анализ SEO домена с использованием LLM и RAG"""
        # Создаем промпт для анализа
        prompt = f"""
        Проведи комплексный SEO анализ домена {domain}.
        
        Если это сайт о садоводстве и огородничестве, проанализируй:
        1. Структуру контента и внутренние ссылки
        2. Семантическую кластеризацию статей
        3. Оптимизацию для поисковых запросов
        4. Пользовательский опыт и навигацию
        5. Технические аспекты SEO
        
        Предоставь конкретные рекомендации с приоритетами и метриками.
        """
        
        # Получаем LLM анализ
        llm_response = await self.llm_service.process_llm_request(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.7,
            use_rag=True,
            metadata={"domain": domain, "analysis_type": "seo_comprehensive"}
        )
        
        # Извлекаем метрики из ответа
        metrics = self._extract_seo_metrics(llm_response.response)
        
        return {
            "domain": domain,
            "analysis": llm_response.response,
            "metrics": metrics,
            "model_used": llm_response.used_model,
            "tokens_used": llm_response.tokens_used,
            "response_time": llm_response.response_time
        }
    
    async def generate_content_recommendations(self, domain: str, content_type: str = "articles") -> List[Dict[str, Any]]:
        """Генерация рекомендаций по контенту"""
        prompt = f"""
        Создай рекомендации по контенту для домена {domain}.
        
        Тип контента: {content_type}
        
        Включи:
        - Темы для новых статей
        - Структуру контента
        - Ключевые слова
        - Внутренние ссылки
        - Мета-описания
        
        Верни структурированный список рекомендаций.
        """
        
        llm_response = await self.llm_service.process_llm_request(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.8,
            use_rag=True
        )
        
        return self._parse_content_recommendations(llm_response.response)
    
    async def optimize_keywords(self, domain: str, current_keywords: List[str]) -> Dict[str, Any]:
        """Оптимизация ключевых слов"""
        keywords_text = ", ".join(current_keywords)
        
        prompt = f"""
        Оптимизируй ключевые слова для домена {domain}.
        
        Текущие ключевые слова: {keywords_text}
        
        Предложи:
        - Новые релевантные ключевые слова
        - Длиннохвостые запросы
        - Семантические варианты
        - Приоритеты для каждого ключевого слова
        
        Фокус на садоводстве и огородничестве.
        """
        
        llm_response = await self.llm_service.process_llm_request(
            prompt=prompt,
            max_tokens=800,
            temperature=0.6,
            use_rag=True
        )
        
        return {
            "domain": domain,
            "current_keywords": current_keywords,
            "optimized_keywords": self._parse_keywords(llm_response.response),
            "recommendations": llm_response.response
        }
    
    def _extract_seo_metrics(self, llm_response: str) -> Dict[str, Any]:
        """Извлечение SEO метрик из ответа LLM"""
        metrics = {
            "score": 75.0,  # Базовый скор
            "content_quality": 0.7,
            "internal_linking": 0.6,
            "keyword_optimization": 0.8,
            "technical_seo": 0.7,
            "user_experience": 0.75
        }
        
        # Простой анализ ответа для извлечения метрик
        response_lower = llm_response.lower()
        
        if "высокий" in response_lower or "отлично" in response_lower:
            metrics["score"] = 85.0
        elif "средний" in response_lower or "хорошо" in response_lower:
            metrics["score"] = 75.0
        elif "низкий" in response_lower or "плохо" in response_lower:
            metrics["score"] = 60.0
        
        return metrics
    
    def _parse_content_recommendations(self, llm_response: str) -> List[Dict[str, Any]]:
        """Парсинг рекомендаций по контенту"""
        recommendations = []
        
        # Простой парсинг по ключевым словам
        lines = llm_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in ['статья', 'контент', 'тема', 'ключевое слово']):
                recommendations.append({
                    "type": "content_suggestion",
                    "description": line,
                    "priority": "medium"
                })
        
        return recommendations[:10]  # Ограничиваем количество
    
    def _parse_keywords(self, llm_response: str) -> List[str]:
        """Парсинг ключевых слов из ответа LLM"""
        keywords = []
        
        # Простой извлечение ключевых слов
        lines = llm_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and len(line) < 50 and not line.startswith('-'):
                # Убираем лишние символы
                clean_keyword = line.replace('*', '').replace('-', '').strip()
                if clean_keyword and len(clean_keyword) > 2:
                    keywords.append(clean_keyword)
        
        return keywords[:20]  # Ограничиваем количество

class LLMIntegrationFactory:
    """Фабрика для создания интеграций с микросервисами"""
    
    def __init__(self, llm_service: LLMIntegrationService):
        self.llm_service = llm_service
    
    def get_testing_integration(self) -> TestingServiceIntegration:
        """Получение интеграции с сервисом тестирования"""
        return TestingServiceIntegration(self.llm_service)
    
    def get_diagram_integration(self) -> DiagramServiceIntegration:
        """Получение интеграции с сервисом диаграмм"""
        return DiagramServiceIntegration(self.llm_service)
    
    def get_monitoring_integration(self) -> MonitoringServiceIntegration:
        """Получение интеграции с сервисом мониторинга"""
        return MonitoringServiceIntegration(self.llm_service)
    
    def get_seo_integration(self) -> SEOServiceIntegration:
        """Получение интеграции с SEO сервисом"""
        return SEOServiceIntegration(self.llm_service)

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