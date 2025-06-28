#!/usr/bin/env python3
"""
Быстрый тест UX-бота reLink без реальных HTTP запросов
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core import UXBotCore
from app.config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ux_bot_fast_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def test_ux_bot_initialization():
    """Тест инициализации UX-бота"""
    logger.info("=== Тест инициализации UX-бота ===")
    
    try:
        # Создание и инициализация UX-бота
        ux_bot = UXBotCore()
        await ux_bot.initialize(user_profile_id="seo_expert")
        
        logger.info("✅ UX-бот успешно инициализирован")
        logger.info(f"Профиль пользователя: {ux_bot.current_user_profile.name if ux_bot.current_user_profile else 'Не задан'}")
        logger.info(f"Сессия ID: {ux_bot.session_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации UX-бота: {e}")
        return False


async def test_user_profiles():
    """Тест профилей пользователей"""
    logger.info("=== Тест профилей пользователей ===")
    
    try:
        # Создание сервиса сценариев для доступа к профилям
        from app.services.scenario_service import ScenarioService
        scenario_service = ScenarioService()
        
        # Получение всех профилей
        profiles = scenario_service.get_all_user_profiles()
        
        logger.info(f"Доступно профилей: {len(profiles)}")
        
        for profile in profiles:
            logger.info(f"Профиль: {profile.name}")
            logger.info(f"  Описание: {profile.description}")
            logger.info(f"  Поведение: {profile.behavior}")
            logger.info(f"  Скорость: {profile.speed}")
            logger.info(f"  Предпочтения: {profile.preferences}")
            logger.info(f"  Типичные действия: {profile.typical_actions}")
            logger.info("---")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста профилей пользователей: {e}")
        return False


async def test_scenarios():
    """Тест сценариев"""
    logger.info("=== Тест сценариев ===")
    
    try:
        # Создание сервиса сценариев
        from app.services.scenario_service import ScenarioService
        scenario_service = ScenarioService()
        
        # Получение всех сценариев
        scenarios = scenario_service.list_scenarios()
        
        logger.info(f"Доступно сценариев: {len(scenarios)}")
        
        for scenario in scenarios:
            logger.info(f"Сценарий: {scenario.name}")
            logger.info(f"  ID: {scenario.scenario_id}")
            logger.info(f"  Описание: {scenario.description}")
            logger.info(f"  Приоритет: {scenario.priority}")
            logger.info(f"  Шагов: {len(scenario.steps)}")
            logger.info(f"  Таймаут: {scenario.timeout}с")
            
            # Детали шагов
            for i, step in enumerate(scenario.steps[:3]):  # Показываем первые 3 шага
                logger.info(f"    Шаг {i+1}: {step.description}")
                logger.info(f"      Действие: {step.action}")
                logger.info(f"      Цель: {step.target}")
            
            if len(scenario.steps) > 3:
                logger.info(f"    ... и еще {len(scenario.steps) - 3} шагов")
            
            logger.info("---")
        
        # Статистика сценариев
        stats = scenario_service.get_scenario_statistics()
        logger.info(f"Статистика сценариев: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста сценариев: {e}")
        return False


async def test_mock_page_analysis():
    """Тест анализа страницы с моками"""
    logger.info("=== Тест анализа страницы (мок) ===")
    
    try:
        # Создание и инициализация UX-бота
        ux_bot = UXBotCore()
        await ux_bot.initialize(user_profile_id="seo_expert")
        
        # Создаем мок анализа страницы
        from app.models import PageAnalysis
        mock_analysis = PageAnalysis(
            url="https://example.com",
            title="Example Page",
            elements=[
                {"type": "button", "text": "Submit", "selector": "button[type='submit']"},
                {"type": "input", "text": "", "selector": "input[name='email']"},
                {"type": "link", "text": "Home", "selector": "a[href='/']"}
            ],
            accessibility_issues=[
                {"type": "contrast", "severity": "medium", "description": "Low contrast text"}
            ],
            responsiveness_issues=[
                {"type": "overflow", "severity": "low", "description": "Content overflow on mobile"}
            ],
            performance_metrics={
                "load_time": 1.2,
                "first_paint": 0.8,
                "first_contentful_paint": 1.0
            }
        )
        
        logger.info(f"✅ Мок анализ создан")
        logger.info(f"URL: {mock_analysis.url}")
        logger.info(f"Заголовок: {mock_analysis.title}")
        logger.info(f"Найдено элементов: {len(mock_analysis.elements)}")
        logger.info(f"Проблемы доступности: {len(mock_analysis.accessibility_issues)}")
        logger.info(f"Проблемы отзывчивости: {len(mock_analysis.responsiveness_issues)}")
        logger.info(f"Метрики производительности: {len(mock_analysis.performance_metrics)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста анализа страницы: {e}")
        return False


async def test_api_client():
    """Тест API клиента"""
    logger.info("=== Тест API клиента ===")
    
    try:
        from app.api_client import APIClient
        from app.models import APIConfig
        
        # Создание конфигурации API
        config = APIConfig(
            base_url="http://localhost:8000",
            timeout=5
        )
        
        # Создание API клиента
        api_client = APIClient(config)
        
        logger.info("✅ API клиент создан")
        logger.info(f"Base URL: {config.base_url}")
        logger.info(f"Timeout: {config.timeout}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка теста API клиента: {e}")
        return False


async def main():
    """Основная функция быстрого тестирования"""
    logger.info("🚀 Запуск быстрого тестирования UX-бота reLink")
    logger.info(f"Время начала: {datetime.now()}")
    
    # Список быстрых тестов
    tests = [
        ("Инициализация UX-бота", test_ux_bot_initialization),
        ("Профили пользователей", test_user_profiles),
        ("Сценарии", test_scenarios),
        ("Анализ страницы (мок)", test_mock_page_analysis),
        ("API клиент", test_api_client),
    ]
    
    # Результаты тестов
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Запуск теста: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ Тест '{test_name}' ПРОЙДЕН")
            else:
                logger.error(f"❌ Тест '{test_name}' ПРОВАЛЕН")
                
        except Exception as e:
            logger.error(f"❌ Тест '{test_name}' ВЫЗВАЛ ИСКЛЮЧЕНИЕ: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    logger.info(f"\n{'='*50}")
    logger.info("ИТОГОВЫЙ ОТЧЕТ")
    logger.info(f"{'='*50}")
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    logger.info(f"Всего тестов: {total_tests}")
    logger.info(f"Пройдено: {passed_tests}")
    logger.info(f"Провалено: {total_tests - passed_tests}")
    logger.info(f"Процент успеха: {(passed_tests / total_tests) * 100:.1f}%")
    
    logger.info("\nДетали:")
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\nВремя завершения: {datetime.now()}")
    
    # Возвращаем успех только если все тесты пройдены
    return passed_tests == total_tests


if __name__ == "__main__":
    try:
        # Запуск быстрых тестов
        success = asyncio.run(main())
        
        if success:
            logger.info("🎉 Все быстрые тесты успешно пройдены!")
            sys.exit(0)
        else:
            logger.error("💥 Некоторые тесты провалились!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        sys.exit(1) 