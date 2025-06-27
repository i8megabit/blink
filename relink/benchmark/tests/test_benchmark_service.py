"""
🧪 ТЕСТЫ СЕРВИСОВ БЕНЧМАРК МИКРОСЕРВИСА
Тестирование основной бизнес-логики
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import List, Dict, Any

from app.services import OllamaService, MetricsCalculator, BenchmarkService
from app.models import BenchmarkRequest, BenchmarkType, BenchmarkStatus
from app.config import settings


class TestOllamaService:
    """Тесты сервиса Ollama."""
    
    @pytest.fixture
    def ollama_service(self):
        """Фикстура сервиса Ollama."""
        return OllamaService()
    
    @pytest.mark.asyncio
    async def test_check_model_availability_success(self, ollama_service):
        """Тест успешной проверки доступности модели."""
        with patch.object(ollama_service.client, 'list') as mock_list:
            mock_list.return_value = {
                'models': [
                    {'name': 'llama2'},
                    {'name': 'mistral'}
                ]
            }
            
            result = await ollama_service.check_model_availability('llama2')
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_model_availability_not_found(self, ollama_service):
        """Тест проверки недоступной модели."""
        with patch.object(ollama_service.client, 'list') as mock_list:
            mock_list.return_value = {
                'models': [
                    {'name': 'llama2'},
                    {'name': 'mistral'}
                ]
            }
            
            result = await ollama_service.check_model_availability('unknown_model')
            assert result is False
    
    @pytest.mark.asyncio
    async def test_check_model_availability_error(self, ollama_service):
        """Тест ошибки при проверке модели."""
        with patch.object(ollama_service.client, 'list') as mock_list:
            mock_list.side_effect = Exception("Connection error")
            
            result = await ollama_service.check_model_availability('llama2')
            assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, ollama_service):
        """Тест успешной генерации ответа."""
        with patch.object(ollama_service.client, 'generate') as mock_generate:
            mock_generate.return_value = {
                'response': 'Test response',
                'model': 'llama2'
            }
            
            response, response_time = await ollama_service.generate_response(
                'llama2', 'Test prompt'
            )
            
            assert response == 'Test response'
            assert response_time > 0
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_error(self, ollama_service):
        """Тест ошибки генерации ответа."""
        with patch.object(ollama_service.client, 'generate') as mock_generate:
            mock_generate.side_effect = Exception("Generation error")
            
            with pytest.raises(Exception):
                await ollama_service.generate_response('llama2', 'Test prompt')
    
    @pytest.mark.asyncio
    async def test_get_model_info_success(self, ollama_service):
        """Тест получения информации о модели."""
        with patch.object(ollama_service.client, 'list') as mock_list:
            mock_list.return_value = {
                'models': [
                    {
                        'name': 'llama2',
                        'size': 4096,
                        'modified_at': '2024-01-01T00:00:00Z',
                        'digest': 'abc123'
                    }
                ]
            }
            
            info = await ollama_service.get_model_info('llama2')
            
            assert info['name'] == 'llama2'
            assert info['size'] == 4096
            assert info['digest'] == 'abc123'
    
    @pytest.mark.asyncio
    async def test_get_model_info_not_found(self, ollama_service):
        """Тест получения информации о несуществующей модели."""
        with patch.object(ollama_service.client, 'list') as mock_list:
            mock_list.return_value = {
                'models': [
                    {'name': 'llama2'}
                ]
            }
            
            info = await ollama_service.get_model_info('unknown_model')
            assert info == {}


class TestMetricsCalculator:
    """Тесты калькулятора метрик."""
    
    @pytest.fixture
    def metrics_calculator(self):
        """Фикстура калькулятора метрик."""
        return MetricsCalculator()
    
    def test_calculate_performance_metrics(self, metrics_calculator):
        """Тест расчета метрик производительности."""
        response_times = [1.0, 1.5, 2.0, 1.2, 1.8]
        tokens_per_response = [100, 150, 200, 120, 180]
        
        metrics = metrics_calculator.calculate_performance_metrics(
            response_times, tokens_per_response
        )
        
        assert metrics.response_time_avg == pytest.approx(1.5, rel=1e-2)
        assert metrics.response_time_min == 1.0
        assert metrics.response_time_max == 2.0
        assert metrics.response_time_std > 0
        assert metrics.tokens_per_second > 0
        assert metrics.throughput > 0
        assert metrics.memory_usage_mb > 0
        assert 0 <= metrics.cpu_usage_percent <= 100
    
    def test_calculate_performance_metrics_empty_list(self, metrics_calculator):
        """Тест расчета метрик с пустым списком."""
        with pytest.raises(ValueError, match="не может быть пустым"):
            metrics_calculator.calculate_performance_metrics([], [])
    
    def test_calculate_quality_metrics(self, metrics_calculator):
        """Тест расчета метрик качества."""
        responses = [
            "This is a good response about artificial intelligence.",
            "AI is a technology that enables machines to learn.",
            "Artificial intelligence helps computers think like humans."
        ]
        expected_responses = [
            "AI explanation",
            "Machine learning description",
            "Computer intelligence overview"
        ]
        prompts = [
            "Explain artificial intelligence",
            "What is machine learning?",
            "Describe computer intelligence"
        ]
        
        metrics = metrics_calculator.calculate_quality_metrics(
            responses, expected_responses, prompts
        )
        
        assert 0 <= metrics.accuracy_score <= 1
        assert 0 <= metrics.relevance_score <= 1
        assert 0 <= metrics.coherence_score <= 1
        assert 0 <= metrics.fluency_score <= 1
        assert 0 <= metrics.semantic_similarity <= 1
        assert 0 <= metrics.hallucination_rate <= 1
        assert 0 <= metrics.factual_accuracy <= 1
    
    def test_calculate_seo_metrics(self, metrics_calculator):
        """Тест расчета SEO метрик."""
        responses = [
            "SEO optimization is important for website ranking.",
            "Use keywords and meta tags for better SEO.",
            "Internal linking strategy improves SEO performance."
        ]
        prompts = [
            "How to improve SEO?",
            "What are SEO best practices?",
            "Explain SEO strategy"
        ]
        
        metrics = metrics_calculator.calculate_seo_metrics(responses, prompts)
        
        assert 0 <= metrics.seo_understanding <= 1
        assert 0 <= metrics.anchor_optimization <= 1
        assert 0 <= metrics.semantic_relevance <= 1
        assert 0 <= metrics.internal_linking_strategy <= 1
        assert 0 <= metrics.keyword_density <= 1
        assert 0 <= metrics.content_quality <= 1
        assert 0 <= metrics.user_intent_alignment <= 1
    
    def test_calculate_reliability_metrics(self, metrics_calculator):
        """Тест расчета метрик надежности."""
        success_count = 8
        total_count = 10
        response_times = [1.0, 1.1, 1.2, 1.0, 1.1, 1.2, 1.0, 1.1, 1.2, 1.0]
        
        metrics = metrics_calculator.calculate_reliability_metrics(
            success_count, total_count, response_times
        )
        
        assert metrics.success_rate == 0.8
        assert metrics.error_rate == 0.2
        assert 0 <= metrics.timeout_rate <= 1
        assert 0 <= metrics.consistency_score <= 1
        assert 0 <= metrics.stability_score <= 1


class TestBenchmarkService:
    """Тесты основного сервиса бенчмарка."""
    
    @pytest.fixture
    async def benchmark_service(self):
        """Фикстура сервиса бенчмарка."""
        service = BenchmarkService()
        service.cache = AsyncMock()
        return service
    
    @pytest.fixture
    def benchmark_request(self):
        """Фикстура запроса бенчмарка."""
        return BenchmarkRequest(
            name="Test Benchmark",
            description="Test description",
            benchmark_type=BenchmarkType.SEO_BASIC,
            models=["llama2"],
            iterations=3,
            parameters={"temperature": 0.7}
        )
    
    @pytest.mark.asyncio
    async def test_initialize(self, benchmark_service):
        """Тест инициализации сервиса."""
        with patch('app.services.get_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_get_cache.return_value = mock_cache
            
            await benchmark_service.initialize()
            
            assert benchmark_service.cache is not None
            mock_get_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_benchmark_success(self, benchmark_service, benchmark_request):
        """Тест успешного запуска бенчмарка."""
        with patch.object(benchmark_service.ollama_service, 'check_model_availability') as mock_check:
            mock_check.return_value = True
            
            with patch.object(benchmark_service, '_run_single_benchmark') as mock_run:
                mock_result = Mock()
                mock_result.benchmark_id = "test-id"
                mock_result.dict.return_value = {"id": "test-id"}
                mock_run.return_value = mock_result
                
                results = await benchmark_service.run_benchmark(benchmark_request)
                
                assert len(results) == 1
                mock_check.assert_called_once_with("llama2")
                mock_run.assert_called_once_with(benchmark_request, "llama2")
    
    @pytest.mark.asyncio
    async def test_run_benchmark_model_unavailable(self, benchmark_service, benchmark_request):
        """Тест запуска бенчмарка с недоступной моделью."""
        with patch.object(benchmark_service.ollama_service, 'check_model_availability') as mock_check:
            mock_check.return_value = False
            
            results = await benchmark_service.run_benchmark(benchmark_request)
            
            assert len(results) == 0
            mock_check.assert_called_once_with("llama2")
    
    @pytest.mark.asyncio
    async def test_run_benchmark_error(self, benchmark_service, benchmark_request):
        """Тест ошибки при запуске бенчмарка."""
        with patch.object(benchmark_service.ollama_service, 'check_model_availability') as mock_check:
            mock_check.side_effect = Exception("Service error")
            
            with patch.object(benchmark_service, '_create_error_result') as mock_error:
                mock_error_result = Mock()
                mock_error.return_value = mock_error_result
                
                results = await benchmark_service.run_benchmark(benchmark_request)
                
                assert len(results) == 1
                mock_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_benchmark_history(self, benchmark_service):
        """Тест получения истории бенчмарков."""
        mock_cached_results = [
            {"benchmark_id": "1", "name": "Test 1"},
            {"benchmark_id": "2", "name": "Test 2"}
        ]
        benchmark_service.cache.get_benchmark_history.return_value = mock_cached_results
        
        results = await benchmark_service.get_benchmark_history(limit=10)
        
        assert len(results) == 2
        benchmark_service.cache.get_benchmark_history.assert_called_once_with(10)
    
    @pytest.mark.asyncio
    async def test_get_model_performance(self, benchmark_service):
        """Тест получения производительности модели."""
        mock_performance = {"model": "llama2", "score": 0.85}
        benchmark_service.cache.get_model_performance.return_value = mock_performance
        
        result = await benchmark_service.get_model_performance("llama2")
        
        assert result == mock_performance
        benchmark_service.cache.get_model_performance.assert_called_once_with("llama2")
    
    @pytest.mark.asyncio
    async def test_cancel_benchmark_success(self, benchmark_service):
        """Тест успешной отмены бенчмарка."""
        benchmark_id = "test-id"
        mock_task = AsyncMock()
        benchmark_service.active_benchmarks[benchmark_id] = mock_task
        
        result = await benchmark_service.cancel_benchmark(benchmark_id)
        
        assert result is True
        mock_task.cancel.assert_called_once()
        assert benchmark_id not in benchmark_service.active_benchmarks
    
    @pytest.mark.asyncio
    async def test_cancel_benchmark_not_found(self, benchmark_service):
        """Тест отмены несуществующего бенчмарка."""
        result = await benchmark_service.cancel_benchmark("unknown-id")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_test_data_seo_basic(self, benchmark_service):
        """Тест получения тестовых данных для SEO Basic."""
        test_data = await benchmark_service._get_test_data(BenchmarkType.SEO_BASIC)
        
        assert len(test_data) > 0
        for test in test_data:
            assert 'prompt' in test
            assert 'expected' in test
    
    @pytest.mark.asyncio
    async def test_get_test_data_performance(self, benchmark_service):
        """Тест получения тестовых данных для Performance."""
        test_data = await benchmark_service._get_test_data(BenchmarkType.PERFORMANCE)
        
        assert len(test_data) > 0
        for test in test_data:
            assert 'prompt' in test
            assert 'expected' in test
    
    @pytest.mark.asyncio
    async def test_create_error_result(self, benchmark_service, benchmark_request):
        """Тест создания результата с ошибкой."""
        error_message = "Test error"
        
        result = await benchmark_service._create_error_result(
            benchmark_request, "llama2", error_message
        )
        
        assert result.name == benchmark_request.name
        assert result.model_name == "llama2"
        assert result.status == BenchmarkStatus.FAILED
        assert result.error_message == error_message
        assert result.metrics.overall_score == 0


# Интеграционные тесты
class TestBenchmarkIntegration:
    """Интеграционные тесты бенчмарка."""
    
    @pytest.mark.asyncio
    async def test_full_benchmark_workflow(self):
        """Тест полного workflow бенчмарка."""
        # Создаем сервисы
        ollama_service = OllamaService()
        metrics_calculator = MetricsCalculator()
        benchmark_service = BenchmarkService()
        
        # Мокаем зависимости
        with patch.object(ollama_service, 'check_model_availability') as mock_check:
            mock_check.return_value = True
            
            with patch.object(ollama_service, 'generate_response') as mock_generate:
                mock_generate.return_value = ("Test response", 1.5)
                
                # Создаем запрос
                request = BenchmarkRequest(
                    name="Integration Test",
                    benchmark_type=BenchmarkType.PERFORMANCE,
                    models=["llama2"],
                    iterations=2
                )
                
                # Запускаем бенчмарк
                results = await benchmark_service.run_benchmark(request)
                
                # Проверяем результаты
                assert len(results) == 1
                result = results[0]
                assert result.name == "Integration Test"
                assert result.model_name == "llama2"
                assert result.status == BenchmarkStatus.COMPLETED
                assert result.metrics.overall_score > 0


# Тесты производительности
class TestBenchmarkPerformance:
    """Тесты производительности бенчмарка."""
    
    @pytest.mark.asyncio
    async def test_concurrent_benchmarks(self):
        """Тест конкурентных бенчмарков."""
        benchmark_service = BenchmarkService()
        
        # Создаем несколько запросов
        requests = [
            BenchmarkRequest(
                name=f"Concurrent Test {i}",
                benchmark_type=BenchmarkType.PERFORMANCE,
                models=["llama2"],
                iterations=1
            )
            for i in range(3)
        ]
        
        # Мокаем зависимости
        with patch.object(benchmark_service.ollama_service, 'check_model_availability') as mock_check:
            mock_check.return_value = True
            
            with patch.object(benchmark_service.ollama_service, 'generate_response') as mock_generate:
                mock_generate.return_value = ("Response", 1.0)
                
                # Запускаем конкурентно
                tasks = [
                    benchmark_service.run_benchmark(request)
                    for request in requests
                ]
                
                results = await asyncio.gather(*tasks)
                
                # Проверяем результаты
                assert len(results) == 3
                for result_list in results:
                    assert len(result_list) == 1
                    assert result_list[0].status == BenchmarkStatus.COMPLETED
    
    def test_metrics_calculation_performance(self):
        """Тест производительности расчета метрик."""
        metrics_calculator = MetricsCalculator()
        
        # Большой набор данных
        response_times = [1.0 + i * 0.1 for i in range(100)]
        tokens_per_response = [100 + i * 10 for i in range(100)]
        
        # Измеряем время
        import time
        start_time = time.time()
        
        metrics = metrics_calculator.calculate_performance_metrics(
            response_times, tokens_per_response
        )
        
        end_time = time.time()
        calculation_time = end_time - start_time
        
        # Проверяем, что расчет выполняется быстро
        assert calculation_time < 1.0  # Менее 1 секунды
        assert metrics.response_time_avg > 0
        assert metrics.tokens_per_second > 0 