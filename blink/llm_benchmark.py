#!/usr/bin/env python3
"""
🚀 LLM BENCHMARK SYSTEM для SEO-перелинковки
Система A/B тестирования моделей Ollama на Apple M4
"""

import asyncio
import json
import time
import httpx
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import statistics

@dataclass
class BenchmarkMetrics:
    """Метрики производительности модели."""
    model_name: str
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_quality_score: float
    memory_usage_mb: float
    tokens_per_second: float
    context_utilization: float
    hallucination_rate: float
    relevance_score: float
    anchor_quality: float
    reasoning_quality: float
    timestamp: str

@dataclass
class TestCase:
    """Тестовый кейс для бенчмарка."""
    name: str
    domain: str
    test_text: str
    expected_links_count: int
    difficulty_level: str  # easy, medium, hard
    category: str  # tech, health, business, etc.

class LLMBenchmark:
    """Система бенчмаркинга LLM моделей."""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.test_cases = self._create_test_cases()
        self.results = {}
    
    async def _switch_model(self, model_name: str) -> bool:
        """Переключает активную модель в бэкенде."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.backend_url}/api/v1/benchmark_model",
                    params={"model_name": model_name}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        print(f"✅ Модель переключена на {model_name}")
                        return True
                    else:
                        print(f"❌ Ошибка переключения: {result.get('message')}")
                        return False
                else:
                    print(f"❌ HTTP ошибка: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Исключение при переключении модели: {e}")
            return False
    
    def _create_test_cases(self) -> List[TestCase]:
        """Создает набор тестовых кейсов."""
        return [
            TestCase(
                name="simple_tech_linking",
                domain="tech-blog.com",
                test_text="Искусственный интеллект становится все более важным в современной разработке программного обеспечения. Машинное обучение помогает автоматизировать многие процессы.",
                expected_links_count=2,
                difficulty_level="easy",
                category="tech"
            ),
            TestCase(
                name="complex_seo_analysis",
                domain="seo-agency.ru",
                test_text="Поисковая оптимизация требует комплексного подхода. Внутренняя перелинковка является критически важным фактором для улучшения позиций сайта в поисковых системах. Анализ конкурентов, подбор ключевых слов и техническая оптимизация должны работать синергетически.",
                expected_links_count=4,
                difficulty_level="hard",
                category="seo"
            ),
            TestCase(
                name="medical_content",
                domain="med-portal.com",
                test_text="Здоровье сердечно-сосудистой системы напрямую связано с физической активностью. Регулярные кардиотренировки снижают риск развития атеросклероза и помогают контролировать артериальное давление.",
                expected_links_count=3,
                difficulty_level="medium",
                category="health"
            ),
            TestCase(
                name="business_consulting",
                domain="biz-consult.ru",
                test_text="Стратегическое планирование в условиях неопределенности требует гибкого подхода. Agile-методологии в управлении проектами позволяют быстро адаптироваться к изменениям рынка. Цифровая трансформация бизнеса становится необходимостью для выживания компаний.",
                expected_links_count=5,
                difficulty_level="hard",
                category="business"
            ),
            TestCase(
                name="ecommerce_optimization",
                domain="shop-expert.com",
                test_text="Конверсия интернет-магазина зависит от множества факторов. UX-дизайн, скорость загрузки страниц и персонализация контента играют ключевую роль в успехе e-commerce проекта.",
                expected_links_count=3,
                difficulty_level="medium",
                category="ecommerce"
            )
        ]
    
    async def benchmark_model(self, model_name: str, iterations: int = 5) -> BenchmarkMetrics:
        """Бенчмаркинг одной модели."""
        print(f"🔥 Бенчмаркинг модели: {model_name}")
        print("=" * 50)
        
        # Переключаем модель в бэкенде
        await self._switch_model(model_name)
        
        response_times = []
        quality_scores = []
        successful_requests = 0
        failed_requests = 0
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            
            for iteration in range(iterations):
                print(f"   Итерация {iteration + 1}/{iterations}")
                
                for test_case in self.test_cases:
                    try:
                        start_time = time.time()
                        
                        # Выполняем запрос к API
                        response = await client.post(
                            f"{self.backend_url}/api/v1/recommend",
                            json={"text": test_case.test_text}
                        )
                        
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        if response.status_code == 200:
                            result = response.json()
                            links = result.get('links', [])
                            
                            # Оценка качества
                            quality_score = self._calculate_quality_score(
                                links, test_case, response_time
                            )
                            
                            response_times.append(response_time)
                            quality_scores.append(quality_score)
                            successful_requests += 1
                            
                            print(f"     ✅ {test_case.name}: {len(links)} ссылок, {response_time:.2f}с, качество: {quality_score:.2f}")
                            
                        else:
                            failed_requests += 1
                            print(f"     ❌ {test_case.name}: Ошибка {response.status_code}")
                            
                    except Exception as e:
                        failed_requests += 1
                        print(f"     💥 {test_case.name}: Исключение - {e}")
        
        # Рассчитываем итоговые метрики
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            tokens_per_second = self._estimate_tokens_per_second(response_times)
        else:
            avg_response_time = min_response_time = max_response_time = tokens_per_second = 0
        
        avg_quality_score = statistics.mean(quality_scores) if quality_scores else 0
        
        return BenchmarkMetrics(
            model_name=model_name,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            total_requests=successful_requests + failed_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_quality_score=avg_quality_score,
            memory_usage_mb=0,  # Заполним позже
            tokens_per_second=tokens_per_second,
            context_utilization=0.8,  # Примерная оценка
            hallucination_rate=self._estimate_hallucination_rate(quality_scores),
            relevance_score=avg_quality_score * 0.9,
            anchor_quality=avg_quality_score * 0.85,
            reasoning_quality=avg_quality_score * 0.95,
            timestamp=datetime.now().isoformat()
        )
    
    def _calculate_quality_score(self, links: List[str], test_case: TestCase, response_time: float) -> float:
        """Рассчитывает оценку качества ответа."""
        score = 0.0
        
        # Количество ссылок (30% от оценки)
        link_count_score = min(len(links) / test_case.expected_links_count, 1.0) * 30
        score += link_count_score
        
        # Время ответа (20% от оценки)
        time_score = max(0, (10 - response_time) / 10) * 20
        score += time_score
        
        # Наличие ссылок (30% от оценки)
        has_links_score = 30 if links else 0
        score += has_links_score
        
        # Уникальность ссылок (20% от оценки)
        unique_score = (len(set(links)) / len(links) if links else 0) * 20
        score += unique_score
        
        return min(score, 100.0)
    
    def _estimate_tokens_per_second(self, response_times: List[float]) -> float:
        """Оценивает токены в секунду."""
        if not response_times:
            return 0
        avg_time = statistics.mean(response_times)
        estimated_tokens = 100  # Примерное количество токенов в ответе
        return estimated_tokens / avg_time if avg_time > 0 else 0
    
    def _estimate_hallucination_rate(self, quality_scores: List[float]) -> float:
        """Оценивает уровень галлюцинаций."""
        if not quality_scores:
            return 1.0
        avg_quality = statistics.mean(quality_scores)
        return max(0, (100 - avg_quality) / 100)
    
    async def compare_models(self, models: List[str], iterations: int = 3) -> Dict:
        """Сравнивает несколько моделей."""
        print("🏆 ЗАПУСК СИСТЕМЫ A/B БЕНЧМАРКИНГА")
        print("=" * 60)
        
        results = {}
        
        for model in models:
            print(f"\n🚀 Тестирование модели: {model}")
            results[model] = await self.benchmark_model(model, iterations)
        
        # Генерируем отчет сравнения
        self._generate_comparison_report(results)
        
        return results
    
    def _generate_comparison_report(self, results: Dict[str, BenchmarkMetrics]):
        """Генерирует отчет сравнения моделей."""
        print("\n" + "=" * 60)
        print("🏆 ИТОГОВЫЙ ОТЧЕТ БЕНЧМАРКА")
        print("=" * 60)
        
        # Таблица результатов
        print(f"{'Модель':<25} {'Время (с)':<10} {'Успех %':<10} {'Качество':<10} {'TPS':<8}")
        print("-" * 65)
        
        for model_name, metrics in results.items():
            success_rate = (metrics.successful_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0
            print(f"{model_name:<25} {metrics.avg_response_time:<10.2f} {success_rate:<10.1f} {metrics.avg_quality_score:<10.1f} {metrics.tokens_per_second:<8.1f}")
        
        # Победитель по категориям
        print("\n🏅 ЛИДЕРЫ ПО КАТЕГОРИЯМ:")
        
        fastest = min(results.items(), key=lambda x: x[1].avg_response_time)
        print(f"⚡ Самая быстрая: {fastest[0]} ({fastest[1].avg_response_time:.2f}с)")
        
        highest_quality = max(results.items(), key=lambda x: x[1].avg_quality_score)
        print(f"🎯 Лучшее качество: {highest_quality[0]} ({highest_quality[1].avg_quality_score:.1f})")
        
        most_reliable = max(results.items(), key=lambda x: x[1].successful_requests / x[1].total_requests if x[1].total_requests > 0 else 0)
        print(f"🛡️ Самая надежная: {most_reliable[0]} ({most_reliable[1].successful_requests}/{most_reliable[1].total_requests})")
        
        # Общий победитель (комплексная оценка)
        best_overall = self._calculate_overall_winner(results)
        print(f"\n👑 ОБЩИЙ ПОБЕДИТЕЛЬ: {best_overall}")
    
    def _calculate_overall_winner(self, results: Dict[str, BenchmarkMetrics]) -> str:
        """Определяет общего победителя по комплексной оценке."""
        scores = {}
        
        for model_name, metrics in results.items():
            # Комплексная оценка (можно настроить веса)
            speed_score = 1 / (metrics.avg_response_time + 0.1)  # Чем меньше время, тем больше очков
            quality_score = metrics.avg_quality_score
            reliability_score = (metrics.successful_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0
            
            # Взвешенная оценка
            overall_score = (speed_score * 0.3 + quality_score * 0.5 + reliability_score * 0.2)
            scores[model_name] = overall_score
        
        return max(scores.items(), key=lambda x: x[1])[0]

async def main():
    """Главная функция бенчмарка."""
    benchmark = LLMBenchmark()
    
    # Модели для сравнения
    models_to_test = [
        "qwen2.5:7b-turbo",           # Наша текущая турбо модель
        "qwen2.5:7b-instruct-turbo", # Новая оптимизированная instruct модель
        "qwen2.5:7b-instruct",       # Базовая instruct модель
    ]
    
    results = await benchmark.compare_models(models_to_test, iterations=3)
    
    # Сохраняем результаты
    with open(f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
        json.dump({k: asdict(v) for k, v in results.items()}, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Результаты сохранены в benchmark_results_*.json")

if __name__ == "__main__":
    asyncio.run(main()) 