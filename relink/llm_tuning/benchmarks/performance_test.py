#!/usr/bin/env python3
"""
Бенчмарки производительности для LLM Tuning Microservice

Этот файл содержит тесты производительности для всех API эндпоинтов:
- A/B тестирование
- Автоматическая оптимизация
- Оценка качества
- Мониторинг здоровья системы
- Расширенная статистика
"""

import asyncio
import time
import statistics
import psutil
import aiohttp
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np


class PerformanceBenchmark:
    """Класс для проведения бенчмарков производительности"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.results = {}
        self.memory_usage = []
        self.cpu_usage = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_system_metrics(self):
        """Получение системных метрик"""
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent()
        
        self.memory_usage.append(memory_info.rss / 1024 / 1024)  # MB
        self.cpu_usage.append(cpu_percent)
        
        return {
            "memory_mb": memory_info.rss / 1024 / 1024,
            "cpu_percent": cpu_percent,
            "timestamp": datetime.utcnow()
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Выполнение HTTP запроса с измерением времени"""
        start_time = time.time()
        start_metrics = self._get_system_metrics()
        
        try:
            if method.upper() == "GET":
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    result = await response.json()
            elif method.upper() == "POST":
                async with self.session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    result = await response.json()
            elif method.upper() == "PUT":
                async with self.session.put(f"{self.base_url}{endpoint}", json=data) as response:
                    result = await response.json()
            
            end_time = time.time()
            end_metrics = self._get_system_metrics()
            
            return {
                "success": True,
                "response_time": end_time - start_time,
                "status_code": response.status,
                "start_metrics": start_metrics,
                "end_metrics": end_metrics,
                "result": result
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response_time": end_time - start_time,
                "error": str(e)
            }
    
    async def benchmark_ab_testing(self, num_requests: int = 100) -> Dict:
        """Бенчмарк A/B тестирования"""
        print(f"🧪 Бенчмарк A/B тестирования ({num_requests} запросов)...")
        
        # Тестовые данные
        test_data = {
            "name": f"Benchmark Test {datetime.utcnow().timestamp()}",
            "description": "Performance benchmark test",
            "model_id": 1,
            "variant_a": "llama2:7b",
            "variant_b": "llama2:13b",
            "traffic_split": 0.5,
            "test_duration_days": 1,
            "success_metrics": ["response_time", "quality_score"],
            "minimum_sample_size": 10
        }
        
        results = []
        
        # Создание A/B теста
        create_result = await self._make_request("POST", "/api/v1/ab-tests", test_data)
        if create_result["success"]:
            test_id = create_result["result"]["id"]
            results.append(("create_ab_test", create_result))
            
            # Выбор модели для A/B теста
            select_data = {
                "request_type": "benchmark_test",
                "user_id": "benchmark_user"
            }
            
            for i in range(num_requests):
                select_result = await self._make_request(
                    "POST", f"/api/v1/ab-tests/{test_id}/select-model", select_data
                )
                results.append((f"select_model_{i}", select_result))
                
                # Запись результатов
                record_data = {
                    "model_variant": "llama2:13b",
                    "metrics": {
                        "response_time": 2.0 + (i % 3) * 0.5,
                        "quality_score": 8.0 + (i % 5) * 0.2,
                        "success": True
                    }
                }
                
                record_result = await self._make_request(
                    "POST", f"/api/v1/ab-tests/{test_id}/record-result", record_data
                )
                results.append((f"record_result_{i}", record_result))
        
        return self._analyze_results("ab_testing", results)
    
    async def benchmark_optimization(self, num_requests: int = 50) -> Dict:
        """Бенчмарк автоматической оптимизации"""
        print(f"⚡ Бенчмарк оптимизации ({num_requests} запросов)...")
        
        results = []
        
        for i in range(num_requests):
            optimization_data = {
                "model_id": 1,
                "optimization_type": "performance",
                "target_metrics": {
                    "response_time": 1.5 + (i % 3) * 0.2,
                    "quality_score": 8.0 + (i % 5) * 0.1
                },
                "optimization_strategies": ["quantization", "pruning"]
            }
            
            result = await self._make_request("POST", "/api/v1/optimization", optimization_data)
            results.append((f"optimize_model_{i}", result))
            
            if result["success"] and "id" in result["result"]:
                # Получение статуса оптимизации
                status_result = await self._make_request(
                    "GET", f"/api/v1/optimization/{result['result']['id']}"
                )
                results.append((f"get_optimization_{i}", status_result))
        
        return self._analyze_results("optimization", results)
    
    async def benchmark_quality_assessment(self, num_requests: int = 100) -> Dict:
        """Бенчмарк оценки качества"""
        print(f"🎯 Бенчмарк оценки качества ({num_requests} запросов)...")
        
        results = []
        
        for i in range(num_requests):
            assessment_data = {
                "model_id": 1,
                "request_text": f"Benchmark request {i}: Create SEO content about AI",
                "response_text": f"AI (Artificial Intelligence) is a field of computer science that focuses on creating systems capable of performing tasks that typically require human intelligence. This includes learning, reasoning, problem-solving, perception, and language understanding. AI has applications in various industries including healthcare, finance, transportation, and entertainment. Machine learning, a subset of AI, enables computers to learn and improve from experience without being explicitly programmed. Deep learning, a type of machine learning, uses neural networks with multiple layers to analyze various factors of data. The field continues to evolve rapidly, with new breakthroughs and applications emerging regularly.",
                "context_documents": [
                    "AI is transforming industries worldwide",
                    "Machine learning is a key component of AI",
                    "Deep learning enables complex pattern recognition"
                ],
                "assessment_criteria": ["relevance", "accuracy", "completeness", "seo_optimization"]
            }
            
            result = await self._make_request("POST", "/api/v1/quality/assess", assessment_data)
            results.append((f"assess_quality_{i}", result))
        
        return self._analyze_results("quality_assessment", results)
    
    async def benchmark_system_health(self, num_requests: int = 200) -> Dict:
        """Бенчмарк мониторинга здоровья системы"""
        print(f"🏥 Бенчмарк мониторинга здоровья ({num_requests} запросов)...")
        
        results = []
        
        for i in range(num_requests):
            # Получение состояния здоровья
            health_result = await self._make_request("GET", "/api/v1/health/system")
            results.append((f"get_health_{i}", health_result))
            
            # Получение истории здоровья (каждый 10-й запрос)
            if i % 10 == 0:
                history_result = await self._make_request(
                    "GET", "/api/v1/health/system/history?hours=1"
                )
                results.append((f"get_history_{i}", history_result))
        
        return self._analyze_results("system_health", results)
    
    async def benchmark_extended_stats(self, num_requests: int = 100) -> Dict:
        """Бенчмарк расширенной статистики"""
        print(f"📊 Бенчмарк расширенной статистики ({num_requests} запросов)...")
        
        results = []
        
        for i in range(num_requests):
            # Статистика модели
            model_stats_result = await self._make_request(
                "GET", f"/api/v1/stats/models/1?days={1 + (i % 30)}"
            )
            results.append((f"model_stats_{i}", model_stats_result))
            
            # Общая статистика системы (каждый 5-й запрос)
            if i % 5 == 0:
                system_stats_result = await self._make_request("GET", "/api/v1/stats/system")
                results.append((f"system_stats_{i}", system_stats_result))
        
        return self._analyze_results("extended_stats", results)
    
    def _analyze_results(self, test_name: str, results: List[tuple]) -> Dict:
        """Анализ результатов бенчмарка"""
        response_times = []
        success_count = 0
        error_count = 0
        
        for name, result in results:
            if result["success"]:
                success_count += 1
                response_times.append(result["response_time"])
            else:
                error_count += 1
        
        if response_times:
            analysis = {
                "test_name": test_name,
                "total_requests": len(results),
                "successful_requests": success_count,
                "failed_requests": error_count,
                "success_rate": success_count / len(results),
                "avg_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "std_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "requests_per_second": len(response_times) / sum(response_times) if sum(response_times) > 0 else 0
            }
        else:
            analysis = {
                "test_name": test_name,
                "total_requests": len(results),
                "successful_requests": 0,
                "failed_requests": len(results),
                "success_rate": 0,
                "avg_response_time": 0,
                "median_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "std_response_time": 0,
                "requests_per_second": 0
            }
        
        self.results[test_name] = analysis
        return analysis
    
    def generate_report(self) -> str:
        """Генерация отчета о производительности"""
        report = []
        report.append("🚀 ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ LLM TUNING MICROSERVICE")
        report.append("=" * 60)
        report.append(f"📅 Дата: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("")
        
        # Системные метрики
        if self.memory_usage:
            report.append("💾 СИСТЕМНЫЕ МЕТРИКИ:")
            report.append(f"   Среднее использование памяти: {statistics.mean(self.memory_usage):.2f} MB")
            report.append(f"   Максимальное использование памяти: {max(self.memory_usage):.2f} MB")
            report.append(f"   Среднее использование CPU: {statistics.mean(self.cpu_usage):.2f}%")
            report.append(f"   Максимальное использование CPU: {max(self.cpu_usage):.2f}%")
            report.append("")
        
        # Результаты тестов
        for test_name, result in self.results.items():
            report.append(f"📈 {test_name.upper()}:")
            report.append(f"   Всего запросов: {result['total_requests']}")
            report.append(f"   Успешных: {result['successful_requests']}")
            report.append(f"   Неудачных: {result['failed_requests']}")
            report.append(f"   Процент успеха: {result['success_rate']:.2%}")
            report.append(f"   Среднее время ответа: {result['avg_response_time']:.3f}с")
            report.append(f"   Медианное время ответа: {result['median_response_time']:.3f}с")
            report.append(f"   Минимальное время: {result['min_response_time']:.3f}с")
            report.append(f"   Максимальное время: {result['max_response_time']:.3f}с")
            report.append(f"   Стандартное отклонение: {result['std_response_time']:.3f}с")
            report.append(f"   Запросов в секунду: {result['requests_per_second']:.2f}")
            report.append("")
        
        # Общие выводы
        report.append("🎯 ОБЩИЕ ВЫВОДЫ:")
        
        total_requests = sum(r['total_requests'] for r in self.results.values())
        total_success = sum(r['successful_requests'] for r in self.results.values())
        overall_success_rate = total_success / total_requests if total_requests > 0 else 0
        
        avg_response_times = [r['avg_response_time'] for r in self.results.values() if r['avg_response_time'] > 0]
        overall_avg_response_time = statistics.mean(avg_response_times) if avg_response_times else 0
        
        report.append(f"   Общий процент успеха: {overall_success_rate:.2%}")
        report.append(f"   Общее среднее время ответа: {overall_avg_response_time:.3f}с")
        
        if overall_avg_response_time < 1.0:
            report.append("   ✅ Отличная производительность!")
        elif overall_avg_response_time < 3.0:
            report.append("   ⚠️ Хорошая производительность")
        else:
            report.append("   ❌ Требуется оптимизация")
        
        return "\n".join(report)
    
    def plot_results(self, save_path: str = "benchmark_results.png"):
        """Создание графиков результатов"""
        if not self.results:
            print("Нет данных для построения графиков")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # График 1: Время ответа
        test_names = list(self.results.keys())
        avg_times = [self.results[name]['avg_response_time'] for name in test_names]
        
        ax1.bar(test_names, avg_times, color='skyblue')
        ax1.set_title('Среднее время ответа по тестам')
        ax1.set_ylabel('Время (секунды)')
        ax1.tick_params(axis='x', rotation=45)
        
        # График 2: Процент успеха
        success_rates = [self.results[name]['success_rate'] * 100 for name in test_names]
        
        ax2.bar(test_names, success_rates, color='lightgreen')
        ax2.set_title('Процент успешных запросов')
        ax2.set_ylabel('Процент (%)')
        ax2.tick_params(axis='x', rotation=45)
        
        # График 3: Запросов в секунду
        rps = [self.results[name]['requests_per_second'] for name in test_names]
        
        ax3.bar(test_names, rps, color='orange')
        ax3.set_title('Запросов в секунду')
        ax3.set_ylabel('RPS')
        ax3.tick_params(axis='x', rotation=45)
        
        # График 4: Использование памяти
        if self.memory_usage:
            ax4.plot(self.memory_usage, color='red')
            ax4.set_title('Использование памяти во время тестов')
            ax4.set_xlabel('Запрос')
            ax4.set_ylabel('Память (MB)')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Графики сохранены в {save_path}")


async def run_full_benchmark():
    """Запуск полного бенчмарка"""
    print("🚀 Запуск полного бенчмарка производительности LLM Tuning Microservice")
    print("=" * 70)
    
    async with PerformanceBenchmark() as benchmark:
        # Запуск всех бенчмарков
        await benchmark.benchmark_ab_testing(50)
        await benchmark.benchmark_optimization(20)
        await benchmark.benchmark_quality_assessment(100)
        await benchmark.benchmark_system_health(150)
        await benchmark.benchmark_extended_stats(80)
        
        # Генерация отчета
        report = benchmark.generate_report()
        print(report)
        
        # Сохранение отчета
        with open("benchmark_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        # Создание графиков
        benchmark.plot_results()
        
        print("\n✅ Бенчмарк завершен!")
        print("📄 Отчет сохранен в benchmark_report.txt")
        print("📊 Графики сохранены в benchmark_results.png")


async def run_specific_benchmark(benchmark_name: str, num_requests: int = 100):
    """Запуск конкретного бенчмарка"""
    print(f"🎯 Запуск бенчмарка: {benchmark_name}")
    
    async with PerformanceBenchmark() as benchmark:
        if benchmark_name == "ab_testing":
            result = await benchmark.benchmark_ab_testing(num_requests)
        elif benchmark_name == "optimization":
            result = await benchmark.benchmark_optimization(num_requests)
        elif benchmark_name == "quality_assessment":
            result = await benchmark.benchmark_quality_assessment(num_requests)
        elif benchmark_name == "system_health":
            result = await benchmark.benchmark_system_health(num_requests)
        elif benchmark_name == "extended_stats":
            result = await benchmark.benchmark_extended_stats(num_requests)
        else:
            print(f"❌ Неизвестный бенчмарк: {benchmark_name}")
            return
        
        print(f"📊 Результаты {benchmark_name}:")
        for key, value in result.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.3f}")
            else:
                print(f"   {key}: {value}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Запуск конкретного бенчмарка
        benchmark_name = sys.argv[1]
        num_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        asyncio.run(run_specific_benchmark(benchmark_name, num_requests))
    else:
        # Запуск полного бенчмарка
        asyncio.run(run_full_benchmark()) 