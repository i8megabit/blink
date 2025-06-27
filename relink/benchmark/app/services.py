"""
🚀 СЕРВИСЫ БЕНЧМАРК МИКРОСЕРВИСА
Основная бизнес-логика для тестирования производительности LLM моделей
"""

import asyncio
import time
import statistics
import psutil
import httpx
import ollama
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import structlog
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import textstat

from .config import settings, BENCHMARK_TYPES, MODEL_CONFIGS
from .models import (
    BenchmarkRequest, BenchmarkResult, BenchmarkMetrics, PerformanceMetrics,
    QualityMetrics, SEOMetrics, ReliabilityMetrics, BenchmarkStatus, BenchmarkType
)
from .cache import get_cache

logger = structlog.get_logger(__name__)

# Загрузка NLTK данных
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class OllamaService:
    """Сервис для работы с Ollama."""
    
    def __init__(self):
        self.client = ollama.Client(host=settings.ollama_url)
        self.timeout = settings.ollama_timeout
    
    async def check_model_availability(self, model_name: str) -> bool:
        """Проверка доступности модели."""
        try:
            models = await asyncio.to_thread(self.client.list)
            return any(model['name'] == model_name for model in models['models'])
        except Exception as e:
            logger.error(f"Ошибка проверки модели {model_name}: {e}")
            return False
    
    async def generate_response(
        self, 
        model_name: str, 
        prompt: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float]:
        """Генерация ответа с измерением времени."""
        start_time = time.time()
        
        try:
            # Получаем параметры модели
            model_params = MODEL_CONFIGS.get(model_name, {}).get('benchmark_params', {})
            if parameters:
                model_params.update(parameters)
            
            # Генерируем ответ
            response = await asyncio.to_thread(
                self.client.generate,
                model=model_name,
                prompt=prompt,
                **model_params
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return response['response'], response_time
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа для модели {model_name}: {e}")
            raise
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Получение информации о модели."""
        try:
            models = await asyncio.to_thread(self.client.list)
            for model in models['models']:
                if model['name'] == model_name:
                    return {
                        'name': model['name'],
                        'size': model.get('size', 0),
                        'modified_at': model.get('modified_at'),
                        'digest': model.get('digest', '')
                    }
            return {}
        except Exception as e:
            logger.error(f"Ошибка получения информации о модели {model_name}: {e}")
            return {}


class MetricsCalculator:
    """Калькулятор метрик."""
    
    @staticmethod
    def calculate_performance_metrics(response_times: List[float], tokens_per_response: List[int]) -> PerformanceMetrics:
        """Расчет метрик производительности."""
        if not response_times:
            raise ValueError("Список времен ответа не может быть пустым")
        
        # Базовые метрики времени ответа
        response_time_avg = statistics.mean(response_times)
        response_time_min = min(response_times)
        response_time_max = max(response_times)
        response_time_std = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        # Метрики токенов
        total_tokens = sum(tokens_per_response)
        total_time = sum(response_times)
        tokens_per_second = total_tokens / total_time if total_time > 0 else 0
        
        # Пропускная способность
        throughput = len(response_times) / total_time if total_time > 0 else 0
        
        # Использование ресурсов
        memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
        cpu_usage_percent = psutil.cpu_percent(interval=1)
        
        return PerformanceMetrics(
            response_time_avg=response_time_avg,
            response_time_min=response_time_min,
            response_time_max=response_time_max,
            response_time_std=response_time_std,
            tokens_per_second=tokens_per_second,
            throughput=throughput,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent
        )
    
    @staticmethod
    def calculate_quality_metrics(
        responses: List[str], 
        expected_responses: List[str],
        prompts: List[str]
    ) -> QualityMetrics:
        """Расчет метрик качества."""
        if not responses:
            raise ValueError("Список ответов не может быть пустым")
        
        # Векторизация текстов для семантического анализа
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        
        try:
            # Объединяем все тексты для векторизации
            all_texts = responses + expected_responses + prompts
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Семантическое сходство
            response_vectors = tfidf_matrix[:len(responses)]
            expected_vectors = tfidf_matrix[len(responses):len(responses) + len(expected_responses)]
            
            similarities = []
            for resp_vec, exp_vec in zip(response_vectors, expected_vectors):
                similarity = cosine_similarity(resp_vec, exp_vec)[0][0]
                similarities.append(similarity)
            
            semantic_similarity = statistics.mean(similarities) if similarities else 0
        except Exception as e:
            logger.warning(f"Ошибка расчета семантического сходства: {e}")
            semantic_similarity = 0
        
        # Анализ текста
        accuracy_scores = []
        relevance_scores = []
        coherence_scores = []
        fluency_scores = []
        
        for response in responses:
            # Оценка точности (простота реализации)
            accuracy_score = min(1.0, len(response.split()) / 50)  # Чем больше слов, тем лучше
            accuracy_scores.append(accuracy_score)
            
            # Оценка релевантности
            relevance_score = min(1.0, len(set(response.lower().split()) & set(prompts[0].lower().split())) / 10)
            relevance_scores.append(relevance_score)
            
            # Оценка связности (количество предложений)
            sentences = sent_tokenize(response)
            coherence_score = min(1.0, len(sentences) / 5)
            coherence_scores.append(coherence_score)
            
            # Оценка беглости (читаемость)
            try:
                flesch_score = textstat.flesch_reading_ease(response)
                fluency_score = max(0, min(1, flesch_score / 100))
            except:
                fluency_score = 0.5
            fluency_scores.append(fluency_score)
        
        # Расчет средних значений
        accuracy_score = statistics.mean(accuracy_scores)
        relevance_score = statistics.mean(relevance_scores)
        coherence_score = statistics.mean(coherence_scores)
        fluency_score = statistics.mean(fluency_scores)
        
        # Оценка галлюцинаций (простая реализация)
        hallucination_rate = 0.1  # Заглушка
        
        # Фактическая точность
        factual_accuracy = 0.8  # Заглушка
        
        return QualityMetrics(
            accuracy_score=accuracy_score,
            relevance_score=relevance_score,
            coherence_score=coherence_score,
            fluency_score=fluency_score,
            semantic_similarity=semantic_similarity,
            hallucination_rate=hallucination_rate,
            factual_accuracy=factual_accuracy
        )
    
    @staticmethod
    def calculate_seo_metrics(responses: List[str], prompts: List[str]) -> SEOMetrics:
        """Расчет SEO-специфичных метрик."""
        if not responses:
            raise ValueError("Список ответов не может быть пустым")
        
        seo_scores = []
        anchor_scores = []
        semantic_scores = []
        linking_scores = []
        keyword_scores = []
        content_scores = []
        intent_scores = []
        
        for response in responses:
            # Понимание SEO (наличие SEO-терминов)
            seo_terms = ['seo', 'search', 'optimization', 'ranking', 'keywords', 'meta', 'title']
            seo_count = sum(1 for term in seo_terms if term in response.lower())
            seo_score = min(1.0, seo_count / len(seo_terms))
            seo_scores.append(seo_score)
            
            # Оптимизация анкоров (наличие ссылок)
            anchor_count = response.lower().count('href=') + response.lower().count('link')
            anchor_score = min(1.0, anchor_count / 5)
            anchor_scores.append(anchor_score)
            
            # Семантическая релевантность
            response_words = set(response.lower().split())
            prompt_words = set(prompts[0].lower().split())
            semantic_score = len(response_words & prompt_words) / len(prompt_words) if prompt_words else 0
            semantic_scores.append(semantic_score)
            
            # Стратегия внутренних ссылок
            internal_links = response.lower().count('internal') + response.lower().count('linking')
            linking_score = min(1.0, internal_links / 3)
            linking_scores.append(linking_score)
            
            # Плотность ключевых слов
            words = response.lower().split()
            keyword_density = len([w for w in words if w in prompt_words]) / len(words) if words else 0
            keyword_scores.append(min(1.0, keyword_density * 10))
            
            # Качество контента (длина и структура)
            content_score = min(1.0, len(response) / 1000)
            content_scores.append(content_score)
            
            # Соответствие намерению пользователя
            intent_score = 0.8  # Заглушка
            intent_scores.append(intent_score)
        
        return SEOMetrics(
            seo_understanding=statistics.mean(seo_scores),
            anchor_optimization=statistics.mean(anchor_scores),
            semantic_relevance=statistics.mean(semantic_scores),
            internal_linking_strategy=statistics.mean(linking_scores),
            keyword_density=statistics.mean(keyword_scores),
            content_quality=statistics.mean(content_scores),
            user_intent_alignment=statistics.mean(intent_scores)
        )
    
    @staticmethod
    def calculate_reliability_metrics(
        success_count: int, 
        total_count: int, 
        response_times: List[float]
    ) -> ReliabilityMetrics:
        """Расчет метрик надежности."""
        success_rate = success_count / total_count if total_count > 0 else 0
        error_rate = 1 - success_rate
        timeout_rate = 0.05  # Заглушка
        
        # Оценка консистентности (стабильность времени ответа)
        if len(response_times) > 1:
            consistency_score = 1 - (statistics.stdev(response_times) / statistics.mean(response_times))
            consistency_score = max(0, min(1, consistency_score))
        else:
            consistency_score = 1.0
        
        # Оценка стабильности
        stability_score = 0.9  # Заглушка
        
        return ReliabilityMetrics(
            success_rate=success_rate,
            error_rate=error_rate,
            timeout_rate=timeout_rate,
            consistency_score=consistency_score,
            stability_score=stability_score
        )


class BenchmarkService:
    """Основной сервис бенчмарка."""
    
    def __init__(self):
        self.ollama_service = OllamaService()
        self.metrics_calculator = MetricsCalculator()
        self.cache = None
        self.active_benchmarks: Dict[str, asyncio.Task] = {}
    
    async def initialize(self):
        """Инициализация сервиса."""
        self.cache = await get_cache()
        logger.info("BenchmarkService инициализирован")
    
    async def run_benchmark(self, request: BenchmarkRequest) -> List[BenchmarkResult]:
        """Запуск бенчмарка для всех моделей."""
        results = []
        
        for model_name in request.models:
            try:
                # Проверяем доступность модели
                if not await self.ollama_service.check_model_availability(model_name):
                    logger.warning(f"Модель {model_name} недоступна")
                    continue
                
                # Запускаем бенчмарк для модели
                result = await self._run_single_benchmark(request, model_name)
                results.append(result)
                
                # Кэшируем результат
                if self.cache:
                    await self.cache.set_benchmark_result(
                        str(result.benchmark_id), 
                        result.dict(),
                        ttl=settings.cache_ttl
                    )
                
            except Exception as e:
                logger.error(f"Ошибка бенчмарка для модели {model_name}: {e}")
                # Создаем результат с ошибкой
                error_result = await self._create_error_result(request, model_name, str(e))
                results.append(error_result)
        
        return results
    
    async def _run_single_benchmark(
        self, 
        request: BenchmarkRequest, 
        model_name: str
    ) -> BenchmarkResult:
        """Запуск бенчмарка для одной модели."""
        benchmark_id = uuid.uuid4()
        started_at = datetime.utcnow()
        
        logger.info(f"Запуск бенчмарка {benchmark_id} для модели {model_name}")
        
        # Получаем тестовые данные
        test_data = await self._get_test_data(request.benchmark_type)
        
        # Выполняем итерации
        response_times = []
        responses = []
        tokens_per_response = []
        success_count = 0
        
        for i in range(request.iterations):
            try:
                # Выбираем случайный тест
                test = test_data[i % len(test_data)]
                prompt = test['prompt']
                expected = test.get('expected', '')
                
                # Генерируем ответ
                response, response_time = await self.ollama_service.generate_response(
                    model_name, 
                    prompt, 
                    request.parameters
                )
                
                response_times.append(response_time)
                responses.append(response)
                tokens_per_response.append(len(response.split()))
                success_count += 1
                
                logger.debug(f"Итерация {i+1}/{request.iterations} завершена за {response_time:.2f}с")
                
            except Exception as e:
                logger.error(f"Ошибка в итерации {i+1}: {e}")
                response_times.append(30.0)  # Таймаут
                responses.append("")
                tokens_per_response.append(0)
        
        # Рассчитываем метрики
        performance_metrics = self.metrics_calculator.calculate_performance_metrics(
            response_times, tokens_per_response
        )
        
        quality_metrics = self.metrics_calculator.calculate_quality_metrics(
            responses, [test.get('expected', '') for test in test_data[:len(responses)]], 
            [test['prompt'] for test in test_data[:len(responses)]]
        )
        
        reliability_metrics = self.metrics_calculator.calculate_reliability_metrics(
            success_count, request.iterations, response_times
        )
        
        # SEO метрики только для SEO бенчмарков
        seo_metrics = None
        if request.benchmark_type in [BenchmarkType.SEO_BASIC, BenchmarkType.SEO_ADVANCED]:
            seo_metrics = self.metrics_calculator.calculate_seo_metrics(responses, [test['prompt'] for test in test_data[:len(responses)]])
        
        # Создаем комплексные метрики
        benchmark_metrics = BenchmarkMetrics(
            performance=performance_metrics,
            quality=quality_metrics,
            seo=seo_metrics,
            reliability=reliability_metrics
        )
        
        completed_at = datetime.utcnow()
        
        return BenchmarkResult(
            benchmark_id=benchmark_id,
            name=request.name,
            description=request.description,
            benchmark_type=request.benchmark_type,
            model_name=model_name,
            status=BenchmarkStatus.COMPLETED,
            metrics=benchmark_metrics,
            iterations=request.iterations,
            parameters=request.parameters,
            started_at=started_at,
            completed_at=completed_at,
            raw_data={
                'responses': responses,
                'response_times': response_times,
                'tokens_per_response': tokens_per_response
            }
        )
    
    async def _create_error_result(
        self, 
        request: BenchmarkRequest, 
        model_name: str, 
        error_message: str
    ) -> BenchmarkResult:
        """Создание результата с ошибкой."""
        return BenchmarkResult(
            name=request.name,
            description=request.description,
            benchmark_type=request.benchmark_type,
            model_name=model_name,
            status=BenchmarkStatus.FAILED,
            metrics=BenchmarkMetrics(
                performance=PerformanceMetrics(
                    response_time_avg=0, response_time_min=0, response_time_max=0,
                    response_time_std=0, tokens_per_second=0, throughput=0,
                    memory_usage_mb=0, cpu_usage_percent=0
                ),
                quality=QualityMetrics(
                    accuracy_score=0, relevance_score=0, coherence_score=0,
                    fluency_score=0, semantic_similarity=0, hallucination_rate=0,
                    factual_accuracy=0
                ),
                reliability=ReliabilityMetrics(
                    success_rate=0, error_rate=1, timeout_rate=0,
                    consistency_score=0, stability_score=0
                )
            ),
            iterations=request.iterations,
            parameters=request.parameters,
            started_at=datetime.utcnow(),
            error_message=error_message
        )
    
    async def _get_test_data(self, benchmark_type: BenchmarkType) -> List[Dict[str, str]]:
        """Получение тестовых данных для бенчмарка."""
        if benchmark_type == BenchmarkType.SEO_BASIC:
            return [
                {
                    'prompt': 'Проанализируй SEO-оптимизацию для сайта о ресторанах в Москве',
                    'expected': 'SEO анализ должен включать ключевые слова, мета-теги, структуру URL'
                },
                {
                    'prompt': 'Создай заголовок H1 для страницы о доставке пиццы',
                    'expected': 'Заголовок должен быть привлекательным и содержать ключевые слова'
                },
                {
                    'prompt': 'Напиши meta description для интернет-магазина одежды',
                    'expected': 'Meta description должен быть информативным и привлекательным'
                }
            ]
        elif benchmark_type == BenchmarkType.SEO_ADVANCED:
            return [
                {
                    'prompt': 'Разработай стратегию внутренних ссылок для блога о путешествиях',
                    'expected': 'Стратегия должна включать структуру сайта, анкоры, распределение веса'
                },
                {
                    'prompt': 'Создай контент-план для сайта о фитнесе с учетом семантического ядра',
                    'expected': 'План должен включать темы, ключевые слова, структуру контента'
                },
                {
                    'prompt': 'Проанализируй конкурентов в нише онлайн-образования',
                    'expected': 'Анализ должен включать ключевые слова, контент, технические аспекты'
                }
            ]
        elif benchmark_type == BenchmarkType.PERFORMANCE:
            return [
                {
                    'prompt': 'Напиши короткий ответ на вопрос: "Что такое искусственный интеллект?"',
                    'expected': 'Краткое определение ИИ'
                },
                {
                    'prompt': 'Переведи на английский: "Привет, как дела?"',
                    'expected': 'Hello, how are you?'
                },
                {
                    'prompt': 'Посчитай: 2 + 2 = ?',
                    'expected': '4'
                }
            ]
        else:
            return [
                {
                    'prompt': 'Объясни простыми словами, что такое блокчейн',
                    'expected': 'Простое объяснение блокчейна'
                },
                {
                    'prompt': 'Напиши краткое резюме статьи о климатических изменениях',
                    'expected': 'Краткое резюме'
                }
            ]
    
    async def get_benchmark_history(self, limit: int = 50) -> List[BenchmarkResult]:
        """Получение истории бенчмарков."""
        if self.cache:
            cached_results = await self.cache.get_benchmark_history(limit)
            return [BenchmarkResult(**result) for result in cached_results]
        return []
    
    async def get_model_performance(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Получение производительности модели."""
        if self.cache:
            return await self.cache.get_model_performance(model_name)
        return None
    
    async def cancel_benchmark(self, benchmark_id: str) -> bool:
        """Отмена бенчмарка."""
        if benchmark_id in self.active_benchmarks:
            task = self.active_benchmarks[benchmark_id]
            task.cancel()
            del self.active_benchmarks[benchmark_id]
            logger.info(f"Бенчмарк {benchmark_id} отменен")
            return True
        return False


# Глобальный экземпляр сервиса
benchmark_service = BenchmarkService()


async def get_benchmark_service() -> BenchmarkService:
    """Получение экземпляра сервиса бенчмарка."""
    if benchmark_service.cache is None:
        await benchmark_service.initialize()
    return benchmark_service 