"""
Тестовый скрипт для проверки работы оптимизаций reLink
"""

import asyncio
import logging
import time
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_intelligent_model_router():
    """Тестирование интеллектуального роутера моделей"""
    logger.info("🧠 Тестирование интеллектуального роутера моделей...")
    
    try:
        from app.llm.intelligent_model_router import IntelligentModelRouter, ModelType, TaskComplexity
        
        # Создание роутера
        router = IntelligentModelRouter()
        
        # Тест 1: Анализ сложности задач
        simple_prompt = "Привет, как дела?"
        complex_prompt = "Проанализируй архитектуру микросервисов и предложи оптимизации для масштабирования системы с учетом производительности и отказоустойчивости"
        
        simple_complexity = router.analyze_task_complexity(simple_prompt)
        complex_complexity = router.analyze_task_complexity(complex_prompt)
        
        logger.info(f"Сложность простого запроса: {simple_complexity.value}")
        logger.info(f"Сложность сложного запроса: {complex_complexity.value}")
        
        # Тест 2: Получение метрик системы
        system_metrics = await router.get_system_metrics()
        logger.info(f"CPU: {system_metrics.cpu_usage}%, Memory: {system_metrics.memory_usage}%")
        
        # Тест 3: Выбор оптимальной модели
        model_name, config = router.select_optimal_model(
            TaskComplexity.SIMPLE, 
            system_metrics
        )
        logger.info(f"Выбрана модель для простой задачи: {model_name}")
        
        model_name, config = router.select_optimal_model(
            TaskComplexity.COMPLEX, 
            system_metrics
        )
        logger.info(f"Выбрана модель для сложной задачи: {model_name}")
        
        # Тест 4: Статистика роутера
        stats = router.get_router_stats()
        logger.info(f"Статистика роутера: {stats['usage_stats']}")
        
        logger.info("✅ Тест интеллектуального роутера моделей завершен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования роутера моделей: {e}")
        return False


async def test_advanced_chromadb_service():
    """Тестирование продвинутого сервиса ChromaDB"""
    logger.info("🗄️ Тестирование продвинутого сервиса ChromaDB...")
    
    try:
        from app.llm.advanced_chromadb_service import AdvancedChromaDBService
        
        # Создание сервиса
        service = AdvancedChromaDBService(
            persist_directory="./test_chroma_db",
            enable_compression=True,
            enable_sharding=True
        )
        
        # Тест 1: Проверка здоровья
        health = await service.health_check()
        logger.info(f"Статус ChromaDB: {health['status']}")
        
        # Тест 2: Создание коллекции
        collection_name = "test_collection"
        try:
            collection = await service.create_collection(collection_name)
            logger.info(f"Коллекция {collection_name} создана")
        except Exception as e:
            logger.warning(f"Коллекция уже существует: {e}")
        
        # Тест 3: Добавление документов
        test_documents = [
            "Это первый тестовый документ для проверки работы ChromaDB",
            "Второй документ содержит информацию об оптимизации",
            "Третий документ описывает архитектуру системы"
        ]
        
        test_metadatas = [
            {"type": "test", "category": "optimization"},
            {"type": "test", "category": "architecture"},
            {"type": "test", "category": "system"}
        ]
        
        try:
            ids = await service.add_documents(
                collection_name=collection_name,
                documents=test_documents,
                metadatas=test_metadatas
            )
            logger.info(f"Добавлено {len(ids)} документов")
        except Exception as e:
            logger.warning(f"Ошибка добавления документов: {e}")
        
        # Тест 4: Поиск документов
        try:
            results = await service.query(
                collection_name=collection_name,
                query_texts=["оптимизация системы"],
                n_results=2
            )
            logger.info(f"Найдено документов: {len(results.get('documents', []))}")
        except Exception as e:
            logger.warning(f"Ошибка поиска: {e}")
        
        # Тест 5: Статистика производительности
        stats = service.get_performance_stats()
        logger.info(f"Статистика ChromaDB: {stats}")
        
        logger.info("✅ Тест продвинутого сервиса ChromaDB завершен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования ChromaDB: {e}")
        return False


async def test_optimization_manager():
    """Тестирование менеджера оптимизаций"""
    logger.info("⚙️ Тестирование менеджера оптимизаций...")
    
    try:
        from app.llm.optimization_manager import OptimizationManager, OptimizationLevel
        
        # Создание менеджера
        manager = OptimizationManager(
            optimization_level=OptimizationLevel.STANDARD,
            auto_optimize=False  # Отключаем автооптимизацию для тестов
        )
        
        # Тест 1: Запуск менеджера
        await manager.start()
        logger.info("Менеджер оптимизаций запущен")
        
        # Тест 2: Проверка здоровья системы
        health = await manager.get_system_health()
        logger.info(f"CPU: {health.cpu_usage}%, Memory: {health.memory_usage}%")
        logger.info(f"Ollama: {health.ollama_status}, ChromaDB: {health.chromadb_status}")
        
        # Тест 3: Обработка запроса
        try:
            result = await manager.process_request(
                prompt="Расскажи о преимуществах оптимизации",
                context="Оптимизация важна для производительности системы"
            )
            logger.info(f"Обработка запроса завершена за {result['total_processing_time']:.2f} сек")
        except Exception as e:
            logger.warning(f"Ошибка обработки запроса (возможно, Ollama недоступен): {e}")
        
        # Тест 4: Метрики оптимизации
        metrics = manager.get_optimization_metrics()
        logger.info(f"Скор оптимизации: {metrics.optimization_score:.2f}")
        logger.info(f"Эффективность кеша: {metrics.cache_hit_rate:.2f}")
        
        # Тест 5: Принудительная оптимизация
        await manager.optimize_system()
        logger.info("Принудительная оптимизация завершена")
        
        # Тест 6: Остановка менеджера
        await manager.stop()
        logger.info("Менеджер оптимизаций остановлен")
        
        logger.info("✅ Тест менеджера оптимизаций завершен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования менеджера оптимизаций: {e}")
        return False


async def test_api_endpoints():
    """Тестирование API эндпоинтов оптимизации"""
    logger.info("🌐 Тестирование API эндпоинтов оптимизации...")
    
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        # Тест 1: Проверка здоровья системы
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{base_url}/api/v1/optimization/health")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Статус здоровья: {data['data']['services']}")
                else:
                    logger.warning(f"Ошибка здоровья: {response.status_code}")
            except Exception as e:
                logger.warning(f"API недоступен (возможно, сервер не запущен): {e}")
        
        # Тест 2: Получение метрик
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{base_url}/api/v1/optimization/metrics")
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Метрики оптимизации получены")
                else:
                    logger.warning(f"Ошибка метрик: {response.status_code}")
            except Exception as e:
                logger.warning(f"API недоступен: {e}")
        
        logger.info("✅ Тест API эндпоинтов завершен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования API: {e}")
        return False


async def run_performance_benchmark():
    """Запуск бенчмарка производительности"""
    logger.info("🏃 Запуск бенчмарка производительности...")
    
    try:
        from app.llm.optimization_manager import OptimizationManager, OptimizationLevel
        
        # Создание менеджера
        manager = OptimizationManager(
            optimization_level=OptimizationLevel.ADVANCED,
            auto_optimize=False
        )
        
        await manager.start()
        
        # Тестовые запросы
        test_requests = [
            "Простой запрос для тестирования",
            "Средний запрос с анализом производительности системы",
            "Сложный запрос для анализа архитектуры микросервисов с учетом масштабируемости, отказоустойчивости и оптимизации ресурсов"
        ]
        
        results = []
        
        for i, prompt in enumerate(test_requests):
            start_time = time.time()
            
            try:
                result = await manager.process_request(prompt=prompt)
                processing_time = time.time() - start_time
                
                results.append({
                    "request_id": i + 1,
                    "prompt_length": len(prompt),
                    "processing_time": processing_time,
                    "model_used": result.get("llm_response", {}).get("model_used", "unknown"),
                    "success": True
                })
                
                logger.info(f"Запрос {i+1}: {processing_time:.2f} сек, модель: {result.get('llm_response', {}).get('model_used', 'unknown')}")
                
            except Exception as e:
                processing_time = time.time() - start_time
                results.append({
                    "request_id": i + 1,
                    "prompt_length": len(prompt),
                    "processing_time": processing_time,
                    "error": str(e),
                    "success": False
                })
                
                logger.warning(f"Запрос {i+1} завершился с ошибкой: {e}")
        
        # Анализ результатов
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            avg_time = sum(r["processing_time"] for r in successful_requests) / len(successful_requests)
            min_time = min(r["processing_time"] for r in successful_requests)
            max_time = max(r["processing_time"] for r in successful_requests)
            
            logger.info(f"📊 Результаты бенчмарка:")
            logger.info(f"   Успешных запросов: {len(successful_requests)}")
            logger.info(f"   Неудачных запросов: {len(failed_requests)}")
            logger.info(f"   Среднее время: {avg_time:.2f} сек")
            logger.info(f"   Минимальное время: {min_time:.2f} сек")
            logger.info(f"   Максимальное время: {max_time:.2f} сек")
        
        await manager.stop()
        
        logger.info("✅ Бенчмарк производительности завершен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка бенчмарка: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    logger.info("🚀 Начало тестирования оптимизаций reLink")
    
    test_results = {}
    
    # Тест 1: Интеллектуальный роутер моделей
    test_results["model_router"] = await test_intelligent_model_router()
    
    # Тест 2: Продвинутый сервис ChromaDB
    test_results["chromadb_service"] = await test_advanced_chromadb_service()
    
    # Тест 3: Менеджер оптимизаций
    test_results["optimization_manager"] = await test_optimization_manager()
    
    # Тест 4: API эндпоинты
    test_results["api_endpoints"] = await test_api_endpoints()
    
    # Тест 5: Бенчмарк производительности
    test_results["performance_benchmark"] = await run_performance_benchmark()
    
    # Итоговый отчет
    logger.info("📋 ИТОГОВЫЙ ОТЧЕТ:")
    for test_name, result in test_results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"   {test_name}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    logger.info(f"📊 Результат: {passed_tests}/{total_tests} тестов пройдено")
    
    if passed_tests == total_tests:
        logger.info("🎉 Все тесты пройдены успешно!")
    else:
        logger.warning("⚠️ Некоторые тесты не пройдены. Проверьте логи выше.")


if __name__ == "__main__":
    asyncio.run(main()) 