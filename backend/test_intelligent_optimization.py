#!/usr/bin/env python3
"""
🧠 Тестовый скрипт для демонстрации интеллектуальной системы оптимизации

Демонстрирует:
- Автоопределение системных характеристик
- LLM-рекомендации для оптимизации
- Адаптивную оптимизацию на основе производительности
- RAG-подход к принятию решений
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.llm_router import system_analyzer, llm_router, LLMRequest, LLMServiceType

async def test_system_analysis():
    """Тест анализа системы"""
    print("🔍 Тестирование анализа системы...")
    
    specs = await system_analyzer.analyze_system()
    print(f"✅ Системные характеристики определены:")
    print(f"   Платформа: {specs.platform}")
    print(f"   Архитектура: {specs.architecture}")
    print(f"   CPU ядер: {specs.cpu_count}")
    print(f"   Память: {specs.memory_gb:.1f} GB")
    print(f"   GPU доступен: {specs.gpu_available}")
    print(f"   Тип GPU: {specs.gpu_type}")
    print(f"   Apple Silicon: {specs.apple_silicon}")
    print(f"   M1/M2/M4: {specs.m1_m2_m4}")
    print()

async def test_optimization():
    """Тест оптимизации конфигурации"""
    print("⚙️ Тестирование интеллектуальной оптимизации...")
    
    config = await system_analyzer.optimize_config()
    print(f"✅ Оптимизированная конфигурация:")
    print(f"   Модель: {config.model}")
    print(f"   GPU: {config.num_gpu}")
    print(f"   Потоки: {config.num_thread}")
    print(f"   Размер батча: {config.batch_size}")
    print(f"   F16 KV: {config.f16_kv}")
    print(f"   Размер контекста: {config.context_length}")
    print(f"   Лимит семафора: {config.semaphore_limit}")
    print(f"   Температура: {config.temperature}")
    print(f"   Максимум токенов: {config.max_tokens}")
    print()

async def test_llm_router():
    """Тест LLM роутера с интеллектуальной оптимизацией"""
    print("🧠 Тестирование LLM роутера...")
    
    try:
        await llm_router.start()
        
        # Тестовый запрос
        request = LLMRequest(
            service_type=LLMServiceType.SEO_RECOMMENDATIONS,
            prompt="Проанализируй SEO оптимизацию для сайта о технологиях",
            context={"domain": "tech-example.com"},
            temperature=0.7,
            max_tokens=512
        )
        
        print("📤 Отправка тестового запроса...")
        response = await llm_router.process_request(request)
        
        print(f"✅ Ответ получен за {response.response_time:.2f} секунд")
        print(f"   Использовано токенов: {response.tokens_used}")
        print(f"   Модель: {response.model_used}")
        print(f"   Кэширован: {response.cached}")
        print(f"   Метаданные: {response.metadata}")
        print()
        
        await llm_router.stop()
        
    except Exception as e:
        print(f"❌ Ошибка тестирования LLM роутера: {e}")
        print()

async def test_performance_monitoring():
    """Тест мониторинга производительности"""
    print("📊 Тестирование мониторинга производительности...")
    
    # Симуляция нескольких запросов
    for i in range(5):
        await system_analyzer.record_performance(
            response_time=1.5 + (i * 0.1),
            success=True,
            tokens_used=100 + (i * 10)
        )
        print(f"   Запись производительности {i+1}/5")
    
    # Получение отчета
    report = await system_analyzer.get_optimization_report()
    print(f"✅ Отчет о производительности:")
    print(f"   Всего записей: {report['performance_history']['total_records']}")
    print(f"   Среднее время ответа: {report['performance_history']['recent_avg_response_time']:.2f}s")
    print(f"   Процент успеха: {report['performance_history']['recent_success_rate']:.1%}")
    print()

async def test_environment_variables():
    """Тест переменных окружения"""
    print("🔧 Тестирование переменных окружения...")
    
    env_vars = await system_analyzer.get_environment_variables()
    print(f"✅ Оптимизированные переменные окружения:")
    for key, value in env_vars.items():
        print(f"   {key}: {value}")
    print()

async def test_adaptive_optimization():
    """Тест адаптивной оптимизации"""
    print("🔄 Тестирование адаптивной оптимизации...")
    
    # Симуляция ухудшения производительности
    print("   Симуляция ухудшения производительности...")
    for i in range(10):
        await system_analyzer.record_performance(
            response_time=6.0 + (i * 0.5),  # Высокое время ответа
            success=i < 7,  # Некоторые неудачи
            tokens_used=200
        )
    
    # Проверка, что система адаптировалась
    print("   Проверка адаптации...")
    new_config = await system_analyzer.optimize_config()
    print(f"   Новая конфигурация после адаптации:")
    print(f"     Размер батча: {new_config.batch_size}")
    print(f"     Лимит семафора: {new_config.semaphore_limit}")
    print()

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования интеллектуальной системы оптимизации")
    print("=" * 60)
    
    try:
        await test_system_analysis()
        await test_optimization()
        await test_llm_router()
        await test_performance_monitoring()
        await test_environment_variables()
        await test_adaptive_optimization()
        
        print("🎉 Все тесты завершены успешно!")
        print("=" * 60)
        
        # Финальный отчет
        print("📋 ФИНАЛЬНЫЙ ОТЧЕТ:")
        final_report = await system_analyzer.get_optimization_report()
        print(json.dumps(final_report, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 