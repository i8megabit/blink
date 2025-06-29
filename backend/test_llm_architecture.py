"""
Тесты для централизованной LLM архитектуры reLink
"""

import asyncio
import pytest
import time
from typing import List

from app.llm.centralized_architecture import (
    CentralizedLLMArchitecture,
    LLMRequest,
    LLMResponse
)
from app.llm.concurrent_manager import ConcurrentOllamaManager, OllamaConfig
from app.llm.distributed_cache import DistributedRAGCache
from app.llm.request_prioritizer import RequestPrioritizer
from app.llm.rag_monitor import RAGMonitor
from app.llm_integration import LLMIntegrationService

class TestCentralizedLLMArchitecture:
    """Тесты централизованной LLM архитектуры"""
    
    @pytest.fixture
    async def architecture(self):
        """Фикстура для создания архитектуры"""
        arch = CentralizedLLMArchitecture()
        await arch.start()
        yield arch
        await arch.stop()
    
    @pytest.fixture
    async def llm_service(self):
        """Фикстура для создания LLM сервиса"""
        service = LLMIntegrationService()
        await service.initialize()
        yield service
        await service.shutdown()
    
    async def test_architecture_initialization(self, architecture):
        """Тест инициализации архитектуры"""
        assert architecture._running == True
        assert architecture.request_queue is not None
        assert architecture.semaphore is not None
        assert architecture.concurrent_manager is not None
        assert architecture.cache_manager is not None
        assert architecture.request_prioritizer is not None
        assert architecture.monitoring is not None
    
    async def test_request_submission(self, architecture):
        """Тест отправки запроса"""
        request = LLMRequest(
            id="test-1",
            prompt="Тестовый запрос",
            priority="normal"
        )
        
        request_id = await architecture.submit_request(request)
        assert request_id == "test-1"
        
        # Проверяем, что запрос добавлен в очередь
        assert architecture.request_queue.qsize() > 0
    
    async def test_priority_handling(self, architecture):
        """Тест обработки приоритетов"""
        # Создаем запросы с разными приоритетами
        requests = [
            LLMRequest(id="low-1", prompt="Низкий приоритет", priority="low"),
            LLMRequest(id="high-1", prompt="Высокий приоритет", priority="high"),
            LLMRequest(id="normal-1", prompt="Обычный приоритет", priority="normal"),
            LLMRequest(id="critical-1", prompt="Критический приоритет", priority="critical")
        ]
        
        # Отправляем запросы
        for request in requests:
            await architecture.submit_request(request)
        
        # Проверяем, что все запросы в очереди
        assert architecture.request_queue.qsize() == 4
    
    async def test_concurrent_manager(self):
        """Тест конкурентного менеджера"""
        config = OllamaConfig(
            max_concurrent_requests=2,
            request_timeout=30.0
        )
        
        manager = ConcurrentOllamaManager(config)
        await manager.start()
        
        # Проверяем инициализацию
        assert manager.session is not None
        assert manager.semaphore._value == 2
        
        await manager.stop()
        assert manager.session is None
    
    async def test_distributed_cache(self):
        """Тест распределенного кэша"""
        cache = DistributedRAGCache("redis://redis:6379")
        
        # Тестируем кэширование ответа
        response = LLMResponse(
            request_id="test-1",
            response="Тестовый ответ",
            model_used="qwen2.5:7b-instruct-turbo",
            tokens_used=10,
            response_time=1.0,
            rag_enhanced=False,
            cache_hit=False
        )
        
        # Кэшируем ответ
        success = await cache.cache_response("test-key", response)
        assert success == True
        
        # Получаем кэшированный ответ
        cached_response = await cache.get_response("test-key")
        assert cached_response is not None
        assert cached_response.response == "Тестовый ответ"
        assert cached_response.cache_hit == True
    
    async def test_request_prioritizer(self):
        """Тест приоритизатора запросов"""
        prioritizer = RequestPrioritizer()
        
        # Тестируем получение приоритетов
        critical_priority = prioritizer.get_priority("critical")
        high_priority = prioritizer.get_priority("high")
        normal_priority = prioritizer.get_priority("normal")
        low_priority = prioritizer.get_priority("low")
        
        # Проверяем, что приоритеты корректно упорядочены
        assert critical_priority > high_priority
        assert high_priority > normal_priority
        assert normal_priority > low_priority
    
    async def test_rag_monitor(self):
        """Тест мониторинга RAG"""
        monitor = RAGMonitor()
        
        # Тестируем запись метрик
        monitor.increment_metric("total_requests", 1)
        monitor.increment_metric("cache_hits", 1)
        monitor.record_response_time(1.5)
        
        # Проверяем метрики
        assert monitor.get_metric("total_requests") == 1
        assert monitor.get_metric("cache_hits") == 1
        assert monitor.get_metric("avg_response_time") == 1.5
    
    async def test_llm_integration_service(self, llm_service):
        """Тест сервиса интеграции"""
        # Тестируем простую генерацию ответа
        response = await llm_service.generate_response(
            prompt="Привет, как дела?",
            max_tokens=50
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    async def test_concurrent_requests(self, architecture):
        """Тест конкурентных запросов"""
        # Создаем несколько запросов одновременно
        requests = []
        for i in range(5):
            request = LLMRequest(
                id=f"concurrent-{i}",
                prompt=f"Запрос {i}",
                priority="normal"
            )
            requests.append(request)
        
        # Отправляем все запросы
        start_time = time.time()
        for request in requests:
            await architecture.submit_request(request)
        
        # Проверяем, что запросы обрабатываются конкурентно
        # (семафор ограничивает до 2 одновременных запросов)
        assert architecture.semaphore._value == 2
        
        # Получаем метрики
        metrics = architecture.get_metrics()
        assert metrics["total_requests"] >= 5
    
    async def test_error_handling(self, architecture):
        """Тест обработки ошибок"""
        # Создаем запрос с некорректными параметрами
        request = LLMRequest(
            id="error-test",
            prompt="",  # Пустой промпт
            priority="invalid"  # Некорректный приоритет
        )
        
        # Отправляем запрос (должен обработаться без ошибок)
        request_id = await architecture.submit_request(request)
        assert request_id == "error-test"
    
    async def test_health_check(self, architecture):
        """Тест проверки здоровья"""
        health = await architecture.health_check()
        
        assert "status" in health
        assert "queue_size" in health
        assert "concurrent_requests" in health
        assert health["status"] in ["healthy", "stopped"]

class TestPerformance:
    """Тесты производительности"""
    
    async def test_response_time(self, llm_service):
        """Тест времени ответа"""
        start_time = time.time()
        
        response = await llm_service.generate_response(
            prompt="Короткий тестовый запрос",
            max_tokens=20
        )
        
        response_time = time.time() - start_time
        
        # Проверяем, что ответ получен за разумное время
        assert response_time < 30.0  # Максимум 30 секунд
        assert len(response) > 0
    
    async def test_cache_performance(self):
        """Тест производительности кэша"""
        cache = DistributedRAGCache("redis://redis:6379")
        
        # Тестируем скорость кэширования
        response = LLMResponse(
            request_id="perf-test",
            response="Тест производительности",
            model_used="qwen2.5:7b-instruct-turbo",
            tokens_used=5,
            response_time=0.1,
            rag_enhanced=False,
            cache_hit=False
        )
        
        start_time = time.time()
        await cache.cache_response("perf-key", response)
        cache_time = time.time() - start_time
        
        # Кэширование должно быть быстрым
        assert cache_time < 1.0
        
        # Тестируем скорость чтения из кэша
        start_time = time.time()
        cached_response = await cache.get_response("perf-key")
        read_time = time.time() - start_time
        
        # Чтение из кэша должно быть очень быстрым
        assert read_time < 0.1
        assert cached_response is not None

class TestIntegration:
    """Интеграционные тесты"""
    
    async def test_full_pipeline(self, llm_service):
        """Тест полного пайплайна"""
        # 1. Генерация ответа
        response = await llm_service.generate_response(
            prompt="Объясни, что такое RAG",
            max_tokens=100
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # 2. Получение эмбеддинга
        embedding = await llm_service.get_embedding("Тестовый текст")
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        
        # 3. Поиск в базе знаний
        results = await llm_service.search_knowledge_base("RAG")
        
        assert isinstance(results, list)
        
        # 4. Получение метрик
        metrics = await llm_service.get_metrics()
        
        assert isinstance(metrics, dict)
        assert "total_requests" in metrics
    
    async def test_microservice_integration(self, llm_service):
        """Тест интеграции с микросервисами"""
        from app.llm_integration import LLMIntegrationFactory
        
        factory = LLMIntegrationFactory(llm_service)
        
        # Тестируем интеграцию с сервисом тестирования
        testing_integration = factory.get_testing_integration()
        test_case = await testing_integration.generate_test_case(
            "Функция сложения двух чисел",
            "unit"
        )
        
        assert isinstance(test_case, str)
        assert len(test_case) > 0
        
        # Тестируем интеграцию с сервисом диаграмм
        diagram_integration = factory.get_diagram_integration()
        diagram_desc = await diagram_integration.generate_diagram_description(
            {"nodes": ["A", "B", "C"], "edges": [("A", "B"), ("B", "C")]},
            "flowchart"
        )
        
        assert isinstance(diagram_desc, str)
        assert len(diagram_desc) > 0

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"]) 