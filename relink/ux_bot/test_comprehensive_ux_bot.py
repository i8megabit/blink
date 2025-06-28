#!/usr/bin/env python3
"""
Комплексный тест UX-бота reLink
Тестирует собственную интеграцию бота с подробным логированием LLM
"""

import asyncio
import logging
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core import UXBotCore
from app.config import settings
from app.models import UserProfile, TestScenario

# Настройка подробного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ux_bot_comprehensive_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Отдельный логгер для LLM взаимодействий
llm_logger = logging.getLogger('LLM_Interaction')
llm_logger.setLevel(logging.INFO)

# Создаем файл для логов LLM
llm_handler = logging.FileHandler('llm_interactions.log')
llm_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
llm_logger.addHandler(llm_handler)


class ComprehensiveUXBotTest:
    """Комплексный тест UX-бота"""
    
    def __init__(self):
        self.ux_bot: Optional[UXBotCore] = None
        self.test_results: Dict[str, Any] = {}
        self.start_time = None
        self.end_time = None
        
    async def run_comprehensive_test(self):
        """Запуск комплексного теста"""
        logger.info("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТА UX-БОТА")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        
        try:
            # 1. Инициализация UX-бота
            await self._test_initialization()
            
            # 2. Проверка интеграции с LLM
            await self._test_llm_integration()
            
            # 3. Тестирование собственной интеграции
            await self._test_self_integration()
            
            # 4. Проверка всех сценариев
            await self._test_all_scenarios()
            
            # 5. Финальная проверка
            await self._test_final_checks()
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в комплексном тесте: {e}")
            self.test_results["critical_error"] = str(e)
        
        finally:
            self.end_time = time.time()
            await self._generate_final_report()
    
    async def _test_initialization(self):
        """Тест инициализации UX-бота"""
        logger.info("📋 1. ТЕСТ ИНИЦИАЛИЗАЦИИ")
        
        try:
            # Создание UX-бота
            self.ux_bot = UXBotCore()
            
            # Инициализация с профилем SEO-эксперта
            success = await self.ux_bot.initialize(user_profile_id="seo_expert")
            
            if success:
                logger.info("✅ UX-бот успешно инициализирован")
                logger.info(f"   Сессия ID: {self.ux_bot.session_id}")
                logger.info(f"   Профиль: {self.ux_bot.current_user_profile.name}")
                
                # Запуск сессии
                await self.ux_bot.start_session()
                logger.info("✅ Сессия UX-бота запущена")
                
                self.test_results["initialization"] = "PASSED"
            else:
                logger.error("❌ Ошибка инициализации UX-бота")
                self.test_results["initialization"] = "FAILED"
                
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте инициализации: {e}")
            self.test_results["initialization"] = f"ERROR: {e}"
    
    async def _test_llm_integration(self):
        """Тест интеграции с LLM"""
        logger.info("🧠 2. ТЕСТ ИНТЕГРАЦИИ С LLM")
        
        try:
            # Проверка доступности Ollama
            ollama_status = await self._check_ollama_status()
            
            if ollama_status["available"]:
                logger.info("✅ Ollama доступен")
                logger.info(f"   Модели: {ollama_status['models_count']}")
                logger.info(f"   Доступные модели: {', '.join(ollama_status['models'][:3])}...")
                
                # Тест простого запроса к LLM
                llm_response = await self._test_llm_request()
                
                if llm_response:
                    logger.info("✅ LLM запрос выполнен успешно")
                    llm_logger.info(f"🤖 LLM ОТВЕТ: {llm_response[:200]}...")
                    self.test_results["llm_integration"] = "PASSED"
                else:
                    logger.warning("⚠️ LLM запрос не выполнен")
                    self.test_results["llm_integration"] = "WARNING"
            else:
                logger.error("❌ Ollama недоступен")
                self.test_results["llm_integration"] = "FAILED"
                
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте LLM интеграции: {e}")
            self.test_results["llm_integration"] = f"ERROR: {e}"
    
    async def _test_self_integration(self):
        """Тест собственной интеграции UX-бота"""
        logger.info("🎯 3. ТЕСТ СОБСТВЕННОЙ ИНТЕГРАЦИИ")
        
        try:
            # Переход на главную страницу
            logger.info("   Переход на главную страницу reLink...")
            await self.ux_bot.browser_service.navigate_to("http://localhost:3000")
            
            # Поиск страницы Testing
            logger.info("   Поиск страницы Testing...")
            testing_link = await self.ux_bot.browser_service.find_element("a[href*='testing'], [data-testid='testing-link']")
            
            if testing_link:
                logger.info("✅ Страница Testing найдена")
                
                # Клик по ссылке Testing
                await self.ux_bot.browser_service.click_element(testing_link)
                logger.info("✅ Переход на страницу Testing")
                
                # Ожидание загрузки
                await asyncio.sleep(2)
                
                # Поиск элементов UX-бота
                logger.info("   Поиск элементов UX-бота...")
                ux_bot_elements = await self._find_ux_bot_elements()
                
                if ux_bot_elements:
                    logger.info(f"✅ Найдено элементов UX-бота: {len(ux_bot_elements)}")
                    
                    # Тестирование элементов управления
                    await self._test_ux_bot_controls(ux_bot_elements)
                    
                    self.test_results["self_integration"] = "PASSED"
                else:
                    logger.warning("⚠️ Элементы UX-бота не найдены")
                    self.test_results["self_integration"] = "WARNING"
            else:
                logger.warning("⚠️ Страница Testing не найдена")
                self.test_results["self_integration"] = "WARNING"
                
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте собственной интеграции: {e}")
            self.test_results["self_integration"] = f"ERROR: {e}"
    
    async def _test_all_scenarios(self):
        """Тест всех доступных сценариев"""
        logger.info("📝 4. ТЕСТ ВСЕХ СЦЕНАРИЕВ")
        
        try:
            scenarios = self.ux_bot.scenario_service.list_scenarios()
            logger.info(f"   Доступно сценариев: {len(scenarios)}")
            
            # Запуск специального сценария самотестирования
            self_test_scenario = self.ux_bot.scenario_service.get_scenario("ux_bot_self_test")
            
            if self_test_scenario:
                logger.info("   Запуск сценария самотестирования...")
                
                # Выполнение сценария
                result = await self.ux_bot.execute_scenario(self_test_scenario)
                
                if result.success:
                    logger.info("✅ Сценарий самотестирования выполнен успешно")
                    logger.info(f"   Выполнено шагов: {len(result.completed_steps)}")
                    logger.info(f"   Найдено проблем: {len(result.issues)}")
                    
                    self.test_results["scenarios"] = "PASSED"
                else:
                    logger.warning("⚠️ Сценарий самотестирования выполнен с ошибками")
                    self.test_results["scenarios"] = "WARNING"
            else:
                logger.warning("⚠️ Сценарий самотестирования не найден")
                self.test_results["scenarios"] = "WARNING"
                
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте сценариев: {e}")
            self.test_results["scenarios"] = f"ERROR: {e}"
    
    async def _test_final_checks(self):
        """Финальные проверки"""
        logger.info("🔍 5. ФИНАЛЬНЫЕ ПРОВЕРКИ")
        
        try:
            # Проверка статистики
            stats = self.ux_bot.get_statistics()
            logger.info(f"   Статистика UX-бота:")
            logger.info(f"     - Выполнено действий: {stats['actions_performed']}")
            logger.info(f"     - Найдено проблем: {stats['issues_found']}")
            logger.info(f"     - Доступно сценариев: {stats['scenarios_available']}")
            
            # Проверка логов
            log_file = "ux_bot.log"
            if os.path.exists(log_file):
                log_size = os.path.getsize(log_file)
                logger.info(f"   Размер лог-файла: {log_size} байт")
            
            # Проверка LLM логов
            llm_log_file = "llm_interactions.log"
            if os.path.exists(llm_log_file):
                llm_log_size = os.path.getsize(llm_log_file)
                logger.info(f"   Размер LLM логов: {llm_log_size} байт")
            
            self.test_results["final_checks"] = "PASSED"
            
        except Exception as e:
            logger.error(f"❌ Ошибка в финальных проверках: {e}")
            self.test_results["final_checks"] = f"ERROR: {e}"
    
    async def _check_ollama_status(self) -> Dict[str, Any]:
        """Проверка статуса Ollama"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "available": True,
                            "models_count": len(data.get("models", [])),
                            "models": [model["name"] for model in data.get("models", [])]
                        }
                    else:
                        return {"available": False}
        except Exception as e:
            logger.error(f"Ошибка проверки Ollama: {e}")
            return {"available": False}
    
    async def _test_llm_request(self) -> Optional[str]:
        """Тест запроса к LLM"""
        try:
            # Простой тестовый запрос
            test_prompt = "Привет! Это тест UX-бота. Ответь одним предложением."
            
            # Отправка запроса через API клиент
            response = await self.ux_bot.api_client.post(
                "/api/v1/llm/chat",
                json={
                    "prompt": test_prompt,
                    "model": "qwen2.5:7b-instruct",
                    "max_tokens": 100
                }
            )
            
            if response and response.get("response"):
                llm_logger.info(f"🤖 LLM ЗАПРОС: {test_prompt}")
                llm_logger.info(f"🤖 LLM ОТВЕТ: {response['response']}")
                return response["response"]
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка теста LLM запроса: {e}")
            return None
    
    async def _find_ux_bot_elements(self) -> List[Any]:
        """Поиск элементов UX-бота на странице"""
        try:
            selectors = [
                "[data-testid*='ux'], [data-testid*='bot']",
                ".ux-bot, .bot-controls",
                "[aria-label*='UX'], [aria-label*='Bot']",
                "button:contains('UX'), button:contains('Bot')"
            ]
            
            elements = []
            for selector in selectors:
                try:
                    element = await self.ux_bot.browser_service.find_element(selector)
                    if element:
                        elements.append(element)
                except:
                    continue
            
            return elements
            
        except Exception as e:
            logger.error(f"Ошибка поиска элементов UX-бота: {e}")
            return []
    
    async def _test_ux_bot_controls(self, elements: List[Any]):
        """Тестирование элементов управления UX-бота"""
        try:
            for i, element in enumerate(elements[:3]):  # Тестируем первые 3 элемента
                try:
                    # Получение текста элемента
                    text = await self.ux_bot.browser_service.get_element_text(element)
                    logger.info(f"   Элемент {i+1}: {text}")
                    
                    # Попытка клика (если это кнопка)
                    if "button" in str(element.tag_name).lower():
                        await self.ux_bot.browser_service.click_element(element)
                        logger.info(f"   ✅ Клик по элементу {i+1}")
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    logger.warning(f"   ⚠️ Ошибка тестирования элемента {i+1}: {e}")
                    
        except Exception as e:
            logger.error(f"Ошибка тестирования элементов управления: {e}")
    
    async def _generate_final_report(self):
        """Генерация финального отчета"""
        logger.info("📊 ГЕНЕРАЦИЯ ФИНАЛЬНОГО ОТЧЕТА")
        logger.info("=" * 60)
        
        duration = self.end_time - self.start_time
        
        # Подсчет результатов
        passed = sum(1 for result in self.test_results.values() if "PASSED" in str(result))
        failed = sum(1 for result in self.test_results.values() if "FAILED" in str(result))
        warnings = sum(1 for result in self.test_results.values() if "WARNING" in str(result))
        errors = sum(1 for result in self.test_results.values() if "ERROR" in str(result))
        
        logger.info(f"⏱️  Общее время тестирования: {duration:.2f} секунд")
        logger.info(f"✅ Успешных тестов: {passed}")
        logger.info(f"❌ Проваленных тестов: {failed}")
        logger.info(f"⚠️  Предупреждений: {warnings}")
        logger.info(f"🚨 Ошибок: {errors}")
        
        logger.info("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if "PASSED" in str(result) else "❌" if "FAILED" in str(result) else "⚠️" if "WARNING" in str(result) else "🚨"
            logger.info(f"   {status_icon} {test_name}: {result}")
        
        # Сохранение отчета в файл
        report_file = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("КОМПЛЕКСНЫЙ ТЕСТ UX-БОТА RELINK\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Длительность: {duration:.2f} секунд\n\n")
            
            f.write("РЕЗУЛЬТАТЫ:\n")
            for test_name, result in self.test_results.items():
                f.write(f"  {test_name}: {result}\n")
        
        logger.info(f"📄 Отчет сохранен в файл: {report_file}")
        
        if failed == 0 and errors == 0:
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        else:
            logger.warning("⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛИЛИСЬ")


async def main():
    """Главная функция"""
    logger.info("🤖 ЗАПУСК КОМПЛЕКСНОГО ТЕСТА UX-БОТА RELINK")
    logger.info("Тестирование собственной интеграции с подробным логированием LLM")
    logger.info("=" * 70)
    
    # Создание и запуск теста
    test = ComprehensiveUXBotTest()
    await test.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main()) 