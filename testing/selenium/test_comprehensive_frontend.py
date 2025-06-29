#!/usr/bin/env python3
"""
🧪 КОМПЛЕКСНЫЙ ТЕСТ ФРОНТЕНДА reLink
Интеграция Selenium + RAG + LLM для полного тестирования UI
"""

import pytest
import asyncio
import time
import json
import httpx
from typing import Dict, Any, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
RAG_URL = "http://localhost:8001"
LLM_ROUTER_URL = "http://localhost:8002"

# Путь к браузеру
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

class FrontendTester:
    """Класс для комплексного тестирования фронтенда"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.actions = ActionChains(driver)
        self.test_results = []
        
    async def test_page_load_performance(self) -> Dict[str, Any]:
        """Тест производительности загрузки страницы"""
        logger.info("🔍 Тестирование производительности загрузки страницы")
        
        start_time = time.time()
        self.driver.get(FRONTEND_URL)
        
        # Ожидание полной загрузки
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        load_time = time.time() - start_time
        
        # Получение метрик производительности
        performance_metrics = self.driver.execute_script("""
            return {
                navigationStart: performance.timing.navigationStart,
                loadEventEnd: performance.timing.loadEventEnd,
                domContentLoadedEventEnd: performance.timing.domContentLoadedEventEnd,
                firstPaint: performance.getEntriesByType('paint')[0]?.startTime,
                firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime
            }
        """)
        
        result = {
            "test": "page_load_performance",
            "load_time": load_time,
            "performance_metrics": performance_metrics,
            "success": load_time < 5.0  # Ожидаем загрузку менее 5 секунд
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Время загрузки: {load_time:.2f}s")
        return result
    
    async def test_ui_elements_accessibility(self) -> Dict[str, Any]:
        """Тест доступности UI элементов"""
        logger.info("♿ Тестирование доступности UI элементов")
        
        accessibility_issues = []
        
        # Проверка ARIA атрибутов
        elements_without_aria = self.driver.find_elements(
            By.CSS_SELECTOR, 
            "button, input, select, textarea, a[href]"
        )
        
        for element in elements_without_aria:
            aria_label = element.get_attribute("aria-label")
            aria_labelledby = element.get_attribute("aria-labelledby")
            role = element.get_attribute("role")
            
            if not any([aria_label, aria_labelledby, role]):
                accessibility_issues.append({
                    "element": element.tag_name,
                    "issue": "Missing ARIA attributes",
                    "html": element.get_attribute("outerHTML")[:100]
                })
        
        # Проверка контрастности цветов (базовая)
        text_elements = self.driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, h3, h4, h5, h6, span, div")
        for element in text_elements[:10]:  # Проверяем первые 10 элементов
            color = element.value_of_css_property("color")
            background_color = element.value_of_css_property("background-color")
            
            # Простая проверка контрастности
            if color == background_color:
                accessibility_issues.append({
                    "element": element.tag_name,
                    "issue": "Low color contrast",
                    "color": color,
                    "background": background_color
                })
        
        result = {
            "test": "ui_elements_accessibility",
            "accessibility_issues": accessibility_issues,
            "success": len(accessibility_issues) == 0
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Найдено проблем доступности: {len(accessibility_issues)}")
        return result
    
    async def test_user_interactions(self) -> Dict[str, Any]:
        """Тест пользовательских взаимодействий"""
        logger.info("👆 Тестирование пользовательских взаимодействий")
        
        interaction_results = []
        
        # Тест кликов по кнопкам
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        for button in buttons[:5]:  # Тестируем первые 5 кнопок
            try:
                # Прокрутка к кнопке
                self.driver.execute_script("arguments[0].scrollIntoView();", button)
                time.sleep(0.5)
                
                # Клик
                button.click()
                time.sleep(1)
                
                interaction_results.append({
                    "element": "button",
                    "action": "click",
                    "success": True
                })
                
            except Exception as e:
                interaction_results.append({
                    "element": "button",
                    "action": "click",
                    "success": False,
                    "error": str(e)
                })
        
        # Тест ввода в поля
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        for input_field in inputs[:3]:  # Тестируем первые 3 поля
            try:
                input_field.clear()
                input_field.send_keys("test input")
                time.sleep(0.5)
                
                interaction_results.append({
                    "element": "input",
                    "action": "type",
                    "success": True
                })
                
            except Exception as e:
                interaction_results.append({
                    "element": "input",
                    "action": "type",
                    "success": False,
                    "error": str(e)
                })
        
        # Тест прокрутки
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            interaction_results.append({
                "element": "page",
                "action": "scroll",
                "success": True
            })
            
        except Exception as e:
            interaction_results.append({
                "element": "page",
                "action": "scroll",
                "success": False,
                "error": str(e)
            })
        
        result = {
            "test": "user_interactions",
            "interactions": interaction_results,
            "success": all(r["success"] for r in interaction_results)
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Успешных взаимодействий: {sum(1 for r in interaction_results if r['success'])}/{len(interaction_results)}")
        return result
    
    async def test_responsive_design(self) -> Dict[str, Any]:
        """Тест адаптивного дизайна"""
        logger.info("📱 Тестирование адаптивного дизайна")
        
        screen_sizes = [
            (1920, 1080, "desktop"),
            (1366, 768, "laptop"),
            (768, 1024, "tablet"),
            (375, 667, "mobile")
        ]
        
        responsive_results = []
        
        for width, height, device in screen_sizes:
            try:
                self.driver.set_window_size(width, height)
                time.sleep(1)
                
                # Проверка переполнения элементов
                overflow_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "*[style*='overflow: hidden'], *[style*='overflow: auto']"
                )
                
                # Проверка видимости основных элементов
                body = self.driver.find_element(By.TAG_NAME, "body")
                is_visible = body.is_displayed()
                
                responsive_results.append({
                    "device": device,
                    "size": f"{width}x{height}",
                    "overflow_elements": len(overflow_elements),
                    "body_visible": is_visible,
                    "success": is_visible
                })
                
            except Exception as e:
                responsive_results.append({
                    "device": device,
                    "size": f"{width}x{height}",
                    "error": str(e),
                    "success": False
                })
        
        result = {
            "test": "responsive_design",
            "devices": responsive_results,
            "success": all(r["success"] for r in responsive_results)
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Протестировано устройств: {len(responsive_results)}")
        return result
    
    async def test_api_integration(self) -> Dict[str, Any]:
        """Тест интеграции с API"""
        logger.info("🔗 Тестирование интеграции с API")
        
        api_results = []
        
        # Тест health check
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BACKEND_URL}/health")
                api_results.append({
                    "endpoint": "health",
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
        except Exception as e:
            api_results.append({
                "endpoint": "health",
                "error": str(e),
                "success": False
            })
        
        # Тест RAG сервиса
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{RAG_URL}/health")
                api_results.append({
                    "endpoint": "rag_health",
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
        except Exception as e:
            api_results.append({
                "endpoint": "rag_health",
                "error": str(e),
                "success": False
            })
        
        # Тест LLM роутера
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{LLM_ROUTER_URL}/health")
                api_results.append({
                    "endpoint": "llm_router_health",
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                })
        except Exception as e:
            api_results.append({
                "endpoint": "llm_router_health",
                "error": str(e),
                "success": False
            })
        
        result = {
            "test": "api_integration",
            "endpoints": api_results,
            "success": all(r["success"] for r in api_results)
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Успешных API вызовов: {sum(1 for r in api_results if r['success'])}/{len(api_results)}")
        return result
    
    async def test_llm_rag_integration(self) -> Dict[str, Any]:
        """Тест интеграции с LLM и RAG"""
        logger.info("🧠 Тестирование интеграции с LLM и RAG")
        
        llm_rag_results = []
        
        # Тест RAG поиска
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{RAG_URL}/api/v1/search",
                    json={
                        "query": "SEO analysis",
                        "collection": "default",
                        "top_k": 3
                    }
                )
                
                if response.status_code == 200:
                    results = response.json()
                    llm_rag_results.append({
                        "service": "rag_search",
                        "success": True,
                        "results_count": len(results.get("results", []))
                    })
                else:
                    llm_rag_results.append({
                        "service": "rag_search",
                        "success": False,
                        "status_code": response.status_code
                    })
                    
        except Exception as e:
            llm_rag_results.append({
                "service": "rag_search",
                "success": False,
                "error": str(e)
            })
        
        # Тест LLM роутера
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{LLM_ROUTER_URL}/api/v1/route",
                    json={
                        "prompt": "What is SEO?",
                        "model": "auto",
                        "context": {}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_rag_results.append({
                        "service": "llm_router",
                        "success": True,
                        "has_response": "response" in result
                    })
                else:
                    llm_rag_results.append({
                        "service": "llm_router",
                        "success": False,
                        "status_code": response.status_code
                    })
                    
        except Exception as e:
            llm_rag_results.append({
                "service": "llm_router",
                "success": False,
                "error": str(e)
            })
        
        result = {
            "test": "llm_rag_integration",
            "services": llm_rag_results,
            "success": all(r["success"] for r in llm_rag_results)
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Успешных AI сервисов: {sum(1 for r in llm_rag_results if r['success'])}/{len(llm_rag_results)}")
        return result
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Запуск комплексного тестирования"""
        logger.info("🚀 Запуск комплексного тестирования фронтенда")
        
        start_time = time.time()
        
        # Выполнение всех тестов
        await self.test_page_load_performance()
        await self.test_ui_elements_accessibility()
        await self.test_user_interactions()
        await self.test_responsive_design()
        await self.test_api_integration()
        await self.test_llm_rag_integration()
        
        total_time = time.time() - start_time
        
        # Подсчет результатов
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        
        comprehensive_result = {
            "test_suite": "comprehensive_frontend_test",
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "total_time": total_time,
            "results": self.test_results,
            "overall_success": successful_tests == total_tests
        }
        
        logger.info(f"🎯 Результаты тестирования:")
        logger.info(f"   Всего тестов: {total_tests}")
        logger.info(f"   Успешных: {successful_tests}")
        logger.info(f"   Неудачных: {total_tests - successful_tests}")
        logger.info(f"   Процент успеха: {comprehensive_result['success_rate']:.1f}%")
        logger.info(f"   Общее время: {total_time:.2f}s")
        
        return comprehensive_result

@pytest.fixture(scope="module")
def driver():
    """Фикстура для создания драйвера браузера"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.binary_location = BRAVE_PATH
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    yield driver
    driver.quit()

@pytest.mark.asyncio
async def test_comprehensive_frontend(driver):
    """Комплексный тест фронтенда"""
    tester = FrontendTester(driver)
    result = await tester.run_comprehensive_test()
    
    # Сохранение результатов в файл
    with open('frontend_test_results.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    # Проверка общего успеха
    assert result["overall_success"], f"Тестирование не прошло. Успех: {result['success_rate']:.1f}%"

if __name__ == "__main__":
    # Запуск теста напрямую
    pytest.main([__file__, "-v"]) 