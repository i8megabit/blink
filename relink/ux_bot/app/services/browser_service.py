"""
Сервис управления браузером для UX тестирования
Поддерживает Selenium и Playwright для имитации пользовательского поведения
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from playwright.async_api import async_playwright, Browser, Page
import logging

from ..config import settings
from ..models import BrowserConfig, UIElement, UserAction, BrowserSession

logger = logging.getLogger(__name__)


class BrowserService:
    """Сервис для управления браузером и имитации пользовательских действий"""
    
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.driver: Optional[webdriver.Remote] = None
        self.playwright_browser: Optional[Browser] = None
        self.playwright_page: Optional[Page] = None
        self.session: Optional[BrowserSession] = None
        self.wait_timeout = config.wait_timeout
        
    async def start_session(self, session_id: str) -> BrowserSession:
        """Запуск новой сессии браузера"""
        try:
            if self.config.engine == "selenium":
                await self._start_selenium_session(session_id)
            elif self.config.engine == "playwright":
                await self._start_playwright_session(session_id)
            else:
                raise ValueError(f"Неподдерживаемый движок браузера: {self.config.engine}")
                
            self.session = BrowserSession(
                session_id=session_id,
                engine=self.config.engine,
                user_agent=self.config.user_agent,
                viewport_width=self.config.viewport_width,
                viewport_height=self.config.viewport_height,
                started_at=time.time()
            )
            
            logger.info(f"Сессия браузера {session_id} запущена с движком {self.config.engine}")
            return self.session
            
        except Exception as e:
            logger.error(f"Ошибка запуска сессии браузера: {e}")
            raise
    
    async def _start_selenium_session(self, session_id: str):
        """Запуск сессии Selenium"""
        options = webdriver.ChromeOptions()
        
        # Настройки для headless режима
        if self.config.headless:
            options.add_argument("--headless")
        
        # Настройки производительности
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        
        # User agent
        if self.config.user_agent:
            options.add_argument(f"--user-agent={self.config.user_agent}")
        
        # Размер окна
        options.add_argument(f"--window-size={self.config.viewport_width},{self.config.viewport_height}")
        
        # Дополнительные настройки
        for arg in self.config.additional_args:
            options.add_argument(arg)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(self.config.implicit_wait)
        
        # Установка размера окна
        self.driver.set_window_size(self.config.viewport_width, self.config.viewport_height)
    
    async def _start_playwright_session(self, session_id: str):
        """Запуск сессии Playwright"""
        self.playwright = await async_playwright().start()
        
        # Выбор браузера
        if self.config.browser_type == "chromium":
            browser_instance = self.playwright.chromium
        elif self.config.browser_type == "firefox":
            browser_instance = self.playwright.firefox
        elif self.config.browser_type == "webkit":
            browser_instance = self.playwright.webkit
        else:
            browser_instance = self.playwright.chromium
        
        # Запуск браузера
        self.playwright_browser = await browser_instance.launch(
            headless=self.config.headless,
            args=self.config.additional_args
        )
        
        # Создание контекста
        context = await self.playwright_browser.new_context(
            user_agent=self.config.user_agent,
            viewport={
                'width': self.config.viewport_width,
                'height': self.config.viewport_height
            }
        )
        
        # Создание страницы
        self.playwright_page = await context.new_page()
    
    async def navigate_to(self, url: str) -> bool:
        """Переход на указанный URL"""
        try:
            if self.config.engine == "selenium":
                self.driver.get(url)
                # Ждем загрузки страницы
                WebDriverWait(self.driver, self.wait_timeout).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            elif self.config.engine == "playwright":
                await self.playwright_page.goto(url, wait_until="networkidle")
            
            logger.info(f"Успешный переход на {url}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка перехода на {url}: {e}")
            return False
    
    async def find_element(self, selector: str, selector_type: str = "css") -> Optional[UIElement]:
        """Поиск элемента на странице"""
        try:
            if self.config.engine == "selenium":
                return await self._find_element_selenium(selector, selector_type)
            elif self.config.engine == "playwright":
                return await self._find_element_playwright(selector, selector_type)
        except Exception as e:
            logger.error(f"Ошибка поиска элемента {selector}: {e}")
            return None
    
    async def _find_element_selenium(self, selector: str, selector_type: str) -> Optional[UIElement]:
        """Поиск элемента через Selenium"""
        try:
            if selector_type == "css":
                element = WebDriverWait(self.driver, self.wait_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            elif selector_type == "xpath":
                element = WebDriverWait(self.driver, self.wait_timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
            elif selector_type == "id":
                element = WebDriverWait(self.driver, self.wait_timeout).until(
                    EC.presence_of_element_located((By.ID, selector))
                )
            else:
                raise ValueError(f"Неподдерживаемый тип селектора: {selector_type}")
            
            return UIElement(
                selector=selector,
                selector_type=selector_type,
                text=element.text,
                tag_name=element.tag_name,
                is_displayed=element.is_displayed(),
                is_enabled=element.is_enabled()
            )
            
        except TimeoutException:
            logger.warning(f"Элемент {selector} не найден в течение {self.wait_timeout} секунд")
            return None
    
    async def _find_element_playwright(self, selector: str, selector_type: str) -> Optional[UIElement]:
        """Поиск элемента через Playwright"""
        try:
            if selector_type == "css":
                element = await self.playwright_page.wait_for_selector(selector, timeout=self.wait_timeout * 1000)
            elif selector_type == "xpath":
                element = await self.playwright_page.wait_for_selector(f"xpath={selector}", timeout=self.wait_timeout * 1000)
            else:
                raise ValueError(f"Неподдерживаемый тип селектора: {selector_type}")
            
            if element:
                text_content = await element.text_content()
                tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()
                
                return UIElement(
                    selector=selector,
                    selector_type=selector_type,
                    text=text_content or "",
                    tag_name=tag_name,
                    is_displayed=is_visible,
                    is_enabled=is_enabled
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Элемент {selector} не найден: {e}")
            return None
    
    async def click_element(self, selector: str, selector_type: str = "css") -> bool:
        """Клик по элементу"""
        try:
            if self.config.engine == "selenium":
                return await self._click_element_selenium(selector, selector_type)
            elif self.config.engine == "playwright":
                return await self._click_element_playwright(selector, selector_type)
        except Exception as e:
            logger.error(f"Ошибка клика по элементу {selector}: {e}")
            return False
    
    async def _click_element_selenium(self, selector: str, selector_type: str) -> bool:
        """Клик через Selenium"""
        element = await self.find_element(selector, selector_type)
        if not element:
            return False
        
        if selector_type == "css":
            web_element = self.driver.find_element(By.CSS_SELECTOR, selector)
        elif selector_type == "xpath":
            web_element = self.driver.find_element(By.XPATH, selector)
        elif selector_type == "id":
            web_element = self.driver.find_element(By.ID, selector)
        else:
            return False
        
        # Прокрутка к элементу
        self.driver.execute_script("arguments[0].scrollIntoView(true);", web_element)
        time.sleep(0.5)  # Небольшая пауза для стабилизации
        
        # Клик
        web_element.click()
        return True
    
    async def _click_element_playwright(self, selector: str, selector_type: str) -> bool:
        """Клик через Playwright"""
        try:
            if selector_type == "css":
                await self.playwright_page.click(selector)
            elif selector_type == "xpath":
                await self.playwright_page.click(f"xpath={selector}")
            else:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка клика через Playwright: {e}")
            return False
    
    async def type_text(self, selector: str, text: str, selector_type: str = "css") -> bool:
        """Ввод текста в поле"""
        try:
            if self.config.engine == "selenium":
                return await self._type_text_selenium(selector, text, selector_type)
            elif self.config.engine == "playwright":
                return await self._type_text_playwright(selector, text, selector_type)
        except Exception as e:
            logger.error(f"Ошибка ввода текста в {selector}: {e}")
            return False
    
    async def _type_text_selenium(self, selector: str, text: str, selector_type: str) -> bool:
        """Ввод текста через Selenium"""
        element = await self.find_element(selector, selector_type)
        if not element:
            return False
        
        if selector_type == "css":
            web_element = self.driver.find_element(By.CSS_SELECTOR, selector)
        elif selector_type == "xpath":
            web_element = self.driver.find_element(By.XPATH, selector)
        elif selector_type == "id":
            web_element = self.driver.find_element(By.ID, selector)
        else:
            return False
        
        # Очистка поля
        web_element.clear()
        
        # Ввод текста с имитацией человеческого поведения
        for char in text:
            web_element.send_keys(char)
            time.sleep(0.05)  # Небольшая пауза между символами
        
        return True
    
    async def _type_text_playwright(self, selector: str, text: str, selector_type: str) -> bool:
        """Ввод текста через Playwright"""
        try:
            if selector_type == "css":
                await self.playwright_page.fill(selector, text)
            elif selector_type == "xpath":
                await self.playwright_page.fill(f"xpath={selector}", text)
            else:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка ввода текста через Playwright: {e}")
            return False
    
    async def wait_for_element(self, selector: str, selector_type: str = "css", timeout: int = None) -> bool:
        """Ожидание появления элемента"""
        timeout = timeout or self.wait_timeout
        
        try:
            if self.config.engine == "selenium":
                return await self._wait_for_element_selenium(selector, selector_type, timeout)
            elif self.config.engine == "playwright":
                return await self._wait_for_element_playwright(selector, selector_type, timeout)
        except Exception as e:
            logger.error(f"Ошибка ожидания элемента {selector}: {e}")
            return False
    
    async def _wait_for_element_selenium(self, selector: str, selector_type: str, timeout: int) -> bool:
        """Ожидание элемента через Selenium"""
        try:
            if selector_type == "css":
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            elif selector_type == "xpath":
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
            elif selector_type == "id":
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.ID, selector))
                )
            else:
                return False
            
            return True
        except TimeoutException:
            return False
    
    async def _wait_for_element_playwright(self, selector: str, selector_type: str, timeout: int) -> bool:
        """Ожидание элемента через Playwright"""
        try:
            if selector_type == "css":
                await self.playwright_page.wait_for_selector(selector, timeout=timeout * 1000)
            elif selector_type == "xpath":
                await self.playwright_page.wait_for_selector(f"xpath={selector}", timeout=timeout * 1000)
            else:
                return False
            
            return True
        except Exception:
            return False
    
    async def take_screenshot(self, filename: str = None) -> str:
        """Создание скриншота"""
        if not filename:
            filename = f"screenshot_{int(time.time())}.png"
        
        try:
            if self.config.engine == "selenium":
                self.driver.save_screenshot(filename)
            elif self.config.engine == "playwright":
                await self.playwright_page.screenshot(path=filename)
            
            logger.info(f"Скриншот сохранен: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Ошибка создания скриншота: {e}")
            return ""
    
    async def get_page_title(self) -> str:
        """Получение заголовка страницы"""
        try:
            if self.config.engine == "selenium":
                return self.driver.title
            elif self.config.engine == "playwright":
                return await self.playwright_page.title()
        except Exception as e:
            logger.error(f"Ошибка получения заголовка страницы: {e}")
            return ""
    
    async def get_current_url(self) -> str:
        """Получение текущего URL"""
        try:
            if self.config.engine == "selenium":
                return self.driver.current_url
            elif self.config.engine == "playwright":
                return self.playwright_page.url
        except Exception as e:
            logger.error(f"Ошибка получения текущего URL: {e}")
            return ""
    
    async def execute_script(self, script: str) -> Any:
        """Выполнение JavaScript кода"""
        try:
            if self.config.engine == "selenium":
                return self.driver.execute_script(script)
            elif self.config.engine == "playwright":
                return await self.playwright_page.evaluate(script)
        except Exception as e:
            logger.error(f"Ошибка выполнения скрипта: {e}")
            return None
    
    async def close_session(self):
        """Закрытие сессии браузера"""
        try:
            if self.config.engine == "selenium" and self.driver:
                self.driver.quit()
                self.driver = None
            elif self.config.engine == "playwright":
                if self.playwright_page:
                    await self.playwright_page.close()
                if self.playwright_browser:
                    await self.playwright_browser.close()
                if hasattr(self, 'playwright'):
                    await self.playwright.stop()
            
            if self.session:
                self.session.ended_at = time.time()
                self.session.duration = self.session.ended_at - self.session.started_at
            
            logger.info("Сессия браузера закрыта")
            
        except Exception as e:
            logger.error(f"Ошибка закрытия сессии браузера: {e}")
    
    async def __aenter__(self):
        """Контекстный менеджер - вход"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        await self.close_session() 