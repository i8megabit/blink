#!/usr/bin/env python3
"""
Примеры использования API эндпоинтов LLM Tuning Microservice

Этот файл содержит примеры использования всех новых API эндпоинтов:
- A/B тестирование
- Автоматическая оптимизация
- Оценка качества
- Мониторинг здоровья системы
- Расширенная статистика
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta


class LLMTuningAPIExamples:
    """Примеры использования API LLM Tuning Microservice"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Выполнение HTTP запроса"""
        url = f"{self.base_url}{endpoint}"
        
        if method.upper() == "GET":
            async with self.session.get(url) as response:
                return await response.json()
        elif method.upper() == "POST":
            async with self.session.post(url, json=data) as response:
                return await response.json()
        elif method.upper() == "PUT":
            async with self.session.put(url, json=data) as response:
                return await response.json()
        elif method.upper() == "DELETE":
            async with self.session.delete(url) as response:
                return await response.json()
    
    # A/B Тестирование
    async def create_ab_test_example(self):
        """Пример создания A/B теста"""
        print("🧪 Создание A/B теста...")
        
        test_data = {
            "name": "SEO Content Quality Test",
            "description": "Тестирование качества SEO контента между разными моделями",
            "model_id": 1,
            "variant_a": "llama2:7b",
            "variant_b": "llama2:13b",
            "traffic_split": 0.5,
            "test_duration_days": 7,
            "success_metrics": ["response_time", "quality_score", "user_satisfaction"],
            "minimum_sample_size": 1000
        }
        
        result = await self._make_request("POST", "/api/v1/ab-tests", test_data)
        print(f"✅ A/B тест создан: {result}")
        return result
    
    async def list_ab_tests_example(self):
        """Пример получения списка A/B тестов"""
        print("📋 Получение списка A/B тестов...")
        
        result = await self._make_request("GET", "/api/v1/ab-tests")
        print(f"✅ Найдено A/B тестов: {len(result)}")
        for test in result:
            print(f"  - {test['name']} (статус: {test['status']})")
        return result
    
    async def select_model_for_ab_test_example(self, test_id: int):
        """Пример выбора модели для A/B теста"""
        print(f"🎯 Выбор модели для A/B теста {test_id}...")
        
        data = {
            "request_type": "seo_content_generation",
            "user_id": "user_123"
        }
        
        result = await self._make_request("POST", f"/api/v1/ab-tests/{test_id}/select-model", data)
        print(f"✅ Выбрана модель: {result['model_name']} (вариант: {result['variant']})")
        return result
    
    async def record_ab_test_result_example(self, test_id: int):
        """Пример записи результатов A/B теста"""
        print(f"📊 Запись результатов A/B теста {test_id}...")
        
        metrics = {
            "response_time": 2.5,
            "quality_score": 8.5,
            "user_satisfaction": 4.2,
            "tokens_generated": 150,
            "tokens_processed": 50,
            "success": True
        }
        
        data = {
            "model_variant": "llama2:13b",
            "metrics": metrics
        }
        
        result = await self._make_request("POST", f"/api/v1/ab-tests/{test_id}/record-result", data)
        print(f"✅ Результаты записаны: {result}")
        return result
    
    # Автоматическая оптимизация
    async def optimize_model_example(self):
        """Пример запуска автоматической оптимизации"""
        print("⚡ Запуск автоматической оптимизации...")
        
        optimization_data = {
            "model_id": 1,
            "optimization_type": "performance",
            "target_metrics": {
                "response_time": 1.5,
                "quality_score": 8.0,
                "error_rate": 0.01
            },
            "optimization_strategies": [
                "quantization",
                "pruning",
                "hyperparameter_tuning"
            ]
        }
        
        result = await self._make_request("POST", "/api/v1/optimization", optimization_data)
        print(f"✅ Оптимизация запущена: {result}")
        return result
    
    async def get_optimization_status_example(self, optimization_id: int):
        """Пример получения статуса оптимизации"""
        print(f"📈 Получение статуса оптимизации {optimization_id}...")
        
        result = await self._make_request("GET", f"/api/v1/optimization/{optimization_id}")
        print(f"✅ Статус оптимизации: {result['status']}")
        print(f"   Прогресс: {result['progress']}%")
        print(f"   Улучшения: {result['improvements']}")
        return result
    
    # Оценка качества
    async def assess_quality_example(self):
        """Пример оценки качества ответа"""
        print("🎯 Оценка качества ответа...")
        
        assessment_data = {
            "model_id": 1,
            "request_text": "Создай SEO-оптимизированную статью о машинном обучении",
            "response_text": "Машинное обучение - это подраздел искусственного интеллекта...",
            "context_documents": [
                "Машинное обучение использует алгоритмы для анализа данных...",
                "Основные типы ML: supervised, unsupervised, reinforcement learning..."
            ],
            "assessment_criteria": [
                "relevance",
                "accuracy",
                "completeness",
                "seo_optimization"
            ]
        }
        
        result = await self._make_request("POST", "/api/v1/quality/assess", assessment_data)
        print(f"✅ Оценка качества: {result['overall_score']}/10")
        print(f"   Детали: {result['detailed_scores']}")
        return result
    
    async def get_quality_stats_example(self, model_id: int):
        """Пример получения статистики качества"""
        print(f"📊 Получение статистики качества модели {model_id}...")
        
        result = await self._make_request("GET", f"/api/v1/quality/stats/{model_id}?days=30")
        print(f"✅ Статистика качества:")
        print(f"   Средний балл: {result['avg_score']}")
        print(f"   Количество оценок: {result['total_assessments']}")
        print(f"   Тренд: {result['trend']}")
        return result
    
    # Мониторинг здоровья системы
    async def get_system_health_example(self):
        """Пример получения состояния здоровья системы"""
        print("🏥 Получение состояния здоровья системы...")
        
        result = await self._make_request("GET", "/api/v1/health/system")
        print(f"✅ Состояние здоровья:")
        print(f"   CPU: {result['cpu_usage']}%")
        print(f"   Память: {result['memory_usage']}%")
        print(f"   Диск: {result['disk_usage']}%")
        print(f"   Ollama: {result['ollama_status']}")
        print(f"   RAG: {result['rag_status']}")
        print(f"   Среднее время ответа: {result['response_time_avg']}с")
        print(f"   Ошибки: {result['error_rate']}%")
        return result
    
    async def get_system_health_history_example(self):
        """Пример получения истории здоровья системы"""
        print("📈 Получение истории здоровья системы...")
        
        result = await self._make_request("GET", "/api/v1/health/system/history?hours=24")
        print(f"✅ История здоровья (за 24 часа):")
        print(f"   Записей: {len(result['records'])}")
        
        if result['records']:
            latest = result['records'][0]
            print(f"   Последняя запись: {latest['timestamp']}")
            print(f"   CPU: {latest['cpu_usage']}%")
            print(f"   Память: {latest['memory_usage']}%")
        
        return result
    
    # Расширенная статистика
    async def get_model_stats_example(self, model_id: int):
        """Пример получения статистики модели"""
        print(f"📊 Получение статистики модели {model_id}...")
        
        result = await self._make_request("GET", f"/api/v1/stats/models/{model_id}?days=30")
        print(f"✅ Статистика модели {result['model_name']}:")
        print(f"   Всего запросов: {result['total_requests']}")
        print(f"   Успешных: {result['successful_requests']}")
        print(f"   Неудачных: {result['failed_requests']}")
        print(f"   Среднее время ответа: {result['avg_response_time']}с")
        print(f"   Средний балл качества: {result['avg_quality_score']}")
        print(f"   Токенов сгенерировано: {result['total_tokens_generated']}")
        print(f"   Токенов обработано: {result['total_tokens_processed']}")
        print(f"   Процент ошибок: {result['error_rate']}%")
        return result
    
    async def get_system_stats_example(self):
        """Пример получения общей статистики системы"""
        print("📈 Получение общей статистики системы...")
        
        result = await self._make_request("GET", "/api/v1/stats/system")
        print(f"✅ Общая статистика:")
        print(f"   Всего моделей: {result['total_models']}")
        print(f"   Активных моделей: {result['active_models']}")
        print(f"   Всего маршрутов: {result['total_routes']}")
        print(f"   Активных маршрутов: {result['active_routes']}")
        print(f"   Документов в RAG: {result['total_documents']}")
        print(f"   Запросов сегодня: {result['total_requests_today']}")
        print(f"   Среднее время ответа: {result['avg_response_time']}с")
        print(f"   Процент ошибок: {result['error_rate']}%")
        return result
    
    # Комплексный пример
    async def run_comprehensive_example(self):
        """Комплексный пример использования всех API"""
        print("🚀 Запуск комплексного примера...")
        
        try:
            # 1. Создание A/B теста
            ab_test = await self.create_ab_test_example()
            test_id = ab_test['id']
            
            # 2. Получение списка тестов
            await self.list_ab_tests_example()
            
            # 3. Выбор модели для теста
            await self.select_model_for_ab_test_example(test_id)
            
            # 4. Запись результатов
            await self.record_ab_test_result_example(test_id)
            
            # 5. Запуск оптимизации
            optimization = await self.optimize_model_example()
            optimization_id = optimization['id']
            
            # 6. Получение статуса оптимизации
            await self.get_optimization_status_example(optimization_id)
            
            # 7. Оценка качества
            await self.assess_quality_example()
            
            # 8. Получение статистики качества
            await self.get_quality_stats_example(1)
            
            # 9. Мониторинг здоровья
            await self.get_system_health_example()
            await self.get_system_health_history_example()
            
            # 10. Расширенная статистика
            await self.get_model_stats_example(1)
            await self.get_system_stats_example()
            
            print("✅ Комплексный пример завершен успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка в комплексном примере: {e}")


async def main():
    """Основная функция для запуска примеров"""
    print("🎯 Примеры использования API LLM Tuning Microservice")
    print("=" * 60)
    
    async with LLMTuningAPIExamples() as api:
        # Запуск комплексного примера
        await api.run_comprehensive_example()


if __name__ == "__main__":
    asyncio.run(main()) 