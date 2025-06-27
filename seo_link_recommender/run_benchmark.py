#!/usr/bin/env python3
"""
🚀 ЗАПУСК LLM БЕНЧМАРКА
Автономный скрипт для сравнения производительности моделей
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в PATH для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_benchmark import LLMBenchmark, BenchmarkMetrics

async def main():
    """Главная функция запуска бенчмарка."""
    
    print("🏆 LLM ТУРБО-БЕНЧМАРК для Apple M4")
    print("🎯 Сравнение производительности на SEO задачах")
    print("=" * 60)
    
    # Создаем бенчмарк
    benchmark = LLMBenchmark("http://localhost:8000")
    
    # Модели для сравнения (лучшие по производительности)
    models_to_test = [
        "qwen2.5:7b-turbo",           # Базовая турбо модель (4.9с)
        "qwen2.5:7b-instruct-turbo", # ЧЕМПИОН! Instruct турбо модель (4.1с) 🏆
        "qwen2.5:7b-instruct",       # Базовая instruct модель (для сравнения)
    ]
    
    print(f"📋 Модели для тестирования: {models_to_test}")
    print(f"🧪 Тестовых кейсов: {len(benchmark.test_cases)}")
    print(f"🔄 Итераций на модель: 3")
    print()
    
    # Запускаем бенчмарк
    try:
        results = await benchmark.compare_models(models_to_test, iterations=3)
        
        print("\n" + "🎉" * 20)
        print("БЕНЧМАРК ЗАВЕРШЕН УСПЕШНО!")
        print("🎉" * 20)
        
        # Показываем краткую сводку
        print("\n📊 КРАТКАЯ СВОДКА:")
        for model_name, metrics in results.items():
            print(f"• {model_name}: {metrics.avg_response_time:.2f}с, качество {metrics.avg_quality_score:.1f}")
        
        return results
        
    except KeyboardInterrupt:
        print("\n⏹️ Бенчмарк остановлен пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка бенчмарка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Проверяем доступность бэкенда
    import httpx
    
    async def check_backend():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:8000/api/v1/health")
                if response.status_code == 200:
                    print("✅ Бэкенд доступен")
                    return True
                else:
                    print(f"❌ Бэкенд недоступен: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Не удается подключиться к бэкенду: {e}")
            print("💡 Убедитесь, что запущен: docker-compose up -d")
            return False
    
    async def run_full_benchmark():
        if await check_backend():
            await main()
        else:
            sys.exit(1)
    
    asyncio.run(run_full_benchmark()) 