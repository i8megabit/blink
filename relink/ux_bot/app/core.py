"""
🧠 Ядро UX бота-имитатора (Фантомаса)

Универсальный бот для тестирования пользовательского опыта любого UI через LLM роутер.
Работает как настоящий пользователь, анализируя интерфейс и принимая осмысленные решения.
"""

import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .config import settings
from .api_client import APIClient
from .models import UIAnalysis, UserAction, TestReport, HumanProfile, BrowserConfig, APIConfig, PageAnalysis, Issue, IssueSeverity, UserProfile, ScenarioContext, TestResult, TestStatus
from .services.browser_service import BrowserService
from .services.scenario_service import ScenarioService

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Типы действий пользователя"""
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    HOVER = "hover"
    WAIT = "wait"
    NAVIGATE = "navigate"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    CUSTOM_JS = "custom_js"

class UIAnalyzer:
    """Анализатор UI для технического исследования интерфейса"""
    
    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self.analysis_data = {}
    
    async def analyze_page_structure(self) -> Dict[str, Any]:
        """Анализ структуры страницы"""
        try:
            # Получение DOM структуры
            dom_elements = self.driver.find_elements(By.XPATH, "//*")
            
            # Анализ форм
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            form_data = []
            for form in forms:
                inputs = form.find_elements(By.TAG_NAME, "input")
                form_data.append({
                    "action": form.get_attribute("action"),
                    "method": form.get_attribute("method"),
                    "inputs": [{"type": inp.get_attribute("type"), "name": inp.get_attribute("name")} for inp in inputs]
                })
            
            # Анализ ссылок
            links = self.driver.find_elements(By.TAG_NAME, "a")
            link_data = [{"href": link.get_attribute("href"), "text": link.text} for link in links]
            
            # Анализ кнопок
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            button_data = [{"text": btn.text, "type": btn.get_attribute("type")} for btn in buttons]
            
            # JavaScript анализ
            js_data = self._analyze_javascript()
            
            # CSS анализ
            css_data = self._analyze_css()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "url": self.driver.current_url,
                "title": self.driver.title,
                "forms": form_data,
                "links": link_data,
                "buttons": button_data,
                "javascript": js_data,
                "css": css_data,
                "meta_tags": self._extract_meta_tags(),
                "accessibility": self._analyze_accessibility()
            }
        except Exception as e:
            logger.error(f"Ошибка анализа структуры страницы: {e}")
            return {"error": str(e)}
    
    def _analyze_javascript(self) -> Dict[str, Any]:
        """Анализ JavaScript на странице"""
        try:
            # Получение всех script тегов
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            js_data = {
                "external_scripts": [],
                "inline_scripts": [],
                "event_listeners": []
            }
            
            for script in scripts:
                src = script.get_attribute("src")
                if src:
                    js_data["external_scripts"].append(src)
                else:
                    content = script.get_attribute("innerHTML")
                    if content:
                        js_data["inline_scripts"].append(content[:200] + "..." if len(content) > 200 else content)
            
            # Анализ через JavaScript
            js_analysis = self.driver.execute_script("""
                return {
                    window_events: Object.keys(window),
                    document_events: Object.keys(document),
                    localStorage: Object.keys(localStorage),
                    sessionStorage: Object.keys(sessionStorage),
                    cookies: document.cookie
                }
            """)
            
            js_data.update(js_analysis)
            return js_data
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_css(self) -> Dict[str, Any]:
        """Анализ CSS стилей"""
        try:
            # Получение всех link тегов с CSS
            css_links = self.driver.find_elements(By.CSS_SELECTOR, "link[rel='stylesheet']")
            css_data = {
                "external_stylesheets": [link.get_attribute("href") for link in css_links],
                "inline_styles": []
            }
            
            # Анализ inline стилей
            elements_with_style = self.driver.find_elements(By.CSS_SELECTOR, "[style]")
            for element in elements_with_style[:10]:  # Ограничиваем количество
                css_data["inline_styles"].append({
                    "tag": element.tag_name,
                    "style": element.get_attribute("style")
                })
            
            return css_data
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_meta_tags(self) -> List[Dict[str, str]]:
        """Извлечение мета-тегов"""
        try:
            meta_tags = self.driver.find_elements(By.TAG_NAME, "meta")
            return [
                {
                    "name": tag.get_attribute("name"),
                    "content": tag.get_attribute("content"),
                    "property": tag.get_attribute("property")
                }
                for tag in meta_tags
            ]
        except Exception as e:
            return []
    
    def _analyze_accessibility(self) -> Dict[str, Any]:
        """Анализ доступности"""
        try:
            # Проверка ARIA атрибутов
            aria_elements = self.driver.find_elements(By.CSS_SELECTOR, "[aria-*]")
            aria_data = []
            for element in aria_elements:
                aria_attrs = {}
                for attr in ["aria-label", "aria-describedby", "aria-hidden", "aria-expanded"]:
                    value = element.get_attribute(attr)
                    if value:
                        aria_attrs[attr] = value
                if aria_attrs:
                    aria_data.append({
                        "tag": element.tag_name,
                        "attributes": aria_attrs
                    })
            
            return {
                "aria_elements": aria_data,
                "alt_images": len(self.driver.find_elements(By.CSS_SELECTOR, "img[alt]")),
                "total_images": len(self.driver.find_elements(By.TAG_NAME, "img"))
            }
        except Exception as e:
            return {"error": str(e)}

class HumanProfileGenerator:
    """Генератор человеческих профилей для имитации реальных пользователей"""
    
    def __init__(self):
        self.profiles = []
        self._load_profiles()
    
    def _load_profiles(self):
        """Загрузка базовых профилей"""
        self.profiles = [
            {
                "name": "Алексей Петров",
                "age": 28,
                "occupation": "разработчик",
                "tech_level": "expert",
                "browsing_speed": "fast",
                "patience": "low",
                "exploration_style": "systematic"
            },
            {
                "name": "Мария Сидорова",
                "age": 35,
                "occupation": "менеджер",
                "tech_level": "intermediate",
                "browsing_speed": "medium",
                "patience": "medium",
                "exploration_style": "curious"
            },
            {
                "name": "Дмитрий Козлов",
                "age": 42,
                "occupation": "дизайнер",
                "tech_level": "advanced",
                "browsing_speed": "slow",
                "patience": "high",
                "exploration_style": "detailed"
            },
            {
                "name": "Анна Волкова",
                "age": 24,
                "occupation": "студент",
                "tech_level": "basic",
                "browsing_speed": "fast",
                "patience": "low",
                "exploration_style": "random"
            }
        ]
    
    def generate_profile(self) -> HumanProfile:
        """Генерация случайного профиля"""
        base_profile = random.choice(self.profiles)
        
        # Добавление случайных вариаций
        profile = HumanProfile(
            id=str(uuid.uuid4()),
            name=base_profile["name"],
            age=base_profile["age"] + random.randint(-5, 5),
            occupation=base_profile["occupation"],
            tech_level=base_profile["tech_level"],
            browsing_speed=base_profile["browsing_speed"],
            patience=base_profile["patience"],
            exploration_style=base_profile["exploration_style"],
            user_agent=self._generate_user_agent(base_profile["tech_level"]),
            screen_resolution=self._generate_screen_resolution(),
            timezone="Europe/Moscow",
            language="ru-RU",
            created_at=datetime.now()
        )
        
        return profile
    
    def _generate_user_agent(self, tech_level: str) -> str:
        """Генерация User-Agent в зависимости от технического уровня"""
        user_agents = {
            "expert": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ],
            "advanced": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
            ],
            "intermediate": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ],
            "basic": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
            ]
        }
        
        return random.choice(user_agents.get(tech_level, user_agents["intermediate"]))
    
    def _generate_screen_resolution(self) -> str:
        """Генерация разрешения экрана"""
        resolutions = [
            "1920x1080", "2560x1440", "1366x768", "1440x900", 
            "1536x864", "1280x720", "3840x2160", "1600x900"
        ]
        return random.choice(resolutions)

class UXImpersonator:
    """
    🎭 UX Имитатор (Фантомас)
    
    Универсальный бот для имитации пользовательского поведения на любом UI.
    Работает через LLM роутер для принятия осмысленных решений.
    """
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.driver: Optional[webdriver.Remote] = None
        self.profile_generator = HumanProfileGenerator()
        self.current_profile: Optional[HumanProfile] = None
        self.ui_analyzer: Optional[UIAnalyzer] = None
        self.session_id = str(uuid.uuid4())
        self.actions_history: List[UserAction] = []
        self.analysis_data: Dict[str, Any] = {}
        
    async def start_session(self, target_url: str, profile: Optional[HumanProfile] = None) -> bool:
        """Запуск сессии тестирования"""
        try:
            # Генерация профиля если не передан
            if not profile:
                self.current_profile = self.profile_generator.generate_profile()
            else:
                self.current_profile = profile
            
            logger.info(f"Запуск сессии с профилем: {self.current_profile.name}")
            
            # Инициализация браузера
            await self._setup_browser()
            
            # Переход на целевой URL
            await self._navigate_to_url(target_url)
            
            # Инициализация анализатора UI
            self.ui_analyzer = UIAnalyzer(self.driver)
            
            # Первичный анализ страницы
            initial_analysis = await self.ui_analyzer.analyze_page_structure()
            self.analysis_data["initial"] = initial_analysis
            
            # Отправка данных в RAG через API
            await self._send_analysis_to_rag(initial_analysis)
            
            logger.info(f"Сессия запущена успешно. URL: {target_url}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска сессии: {e}")
            return False
    
    async def _setup_browser(self):
        """Настройка браузера с человеческими характеристиками"""
        options = webdriver.ChromeOptions()
        
        # Установка User-Agent
        options.add_argument(f"--user-agent={self.current_profile.user_agent}")
        
        # Установка разрешения экрана
        width, height = self.current_profile.screen_resolution.split('x')
        options.add_argument(f"--window-size={width},{height}")
        
        # Дополнительные настройки для имитации человека
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Отключение изображений для ускорения (опционально)
        if self.current_profile.browsing_speed == "fast":
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=options)
        
        # Скрытие автоматизации
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Установка таймаутов
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(30)
    
    async def _navigate_to_url(self, url: str):
        """Переход на URL с человеческими задержками"""
        logger.info(f"Переход на URL: {url}")
        
        # Случайная задержка перед переходом
        await asyncio.sleep(random.uniform(1, 3))
        
        self.driver.get(url)
        
        # Ожидание загрузки страницы
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Человеческая задержка после загрузки
        await asyncio.sleep(random.uniform(2, 5))
    
    async def _send_analysis_to_rag(self, analysis_data: Dict[str, Any]):
        """Отправка данных анализа в RAG через API"""
        try:
            await self.api_client.send_ui_analysis({
                "session_id": self.session_id,
                "profile_id": self.current_profile.id,
                "url": self.driver.current_url,
                "analysis": analysis_data,
                "timestamp": datetime.now().isoformat()
            })
            logger.info("Данные анализа отправлены в RAG")
        except Exception as e:
            logger.error(f"Ошибка отправки данных в RAG: {e}")
    
    async def get_llm_guidance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Получение руководства от LLM через роутер"""
        try:
            # Формирование промпта для LLM
            prompt = self._build_llm_prompt(context)
            
            # Отправка запроса через API к LLM роутеру
            response = await self.api_client.get_llm_guidance({
                "session_id": self.session_id,
                "profile": self.current_profile.dict(),
                "current_context": context,
                "prompt": prompt,
                "action_history": [action.dict() for action in self.actions_history[-5:]]  # Последние 5 действий
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка получения руководства от LLM: {e}")
            return {"action": "wait", "reason": "Ошибка связи с LLM"}
    
    def _build_llm_prompt(self, context: Dict[str, Any]) -> str:
        """Построение промпта для LLM"""
        profile = self.current_profile
        
        prompt = f"""
Ты - UX тестировщик, имитирующий поведение пользователя с профилем:
Имя: {profile.name}
Возраст: {profile.age}
Профессия: {profile.occupation}
Технический уровень: {profile.tech_level}
Скорость просмотра: {profile.browsing_speed}
Терпение: {profile.patience}
Стиль исследования: {profile.exploration_style}

Текущий контекст:
URL: {context.get('url', 'Неизвестно')}
Доступные элементы: {context.get('available_elements', [])}
Последние действия: {context.get('recent_actions', [])}

Проанализируй ситуацию и дай конкретные инструкции для следующего действия.
Формат ответа должен быть JSON:
{{
    "action": "тип_действия",
    "target": "селектор_или_описание",
    "reason": "обоснование_действия",
    "expected_outcome": "ожидаемый_результат",
    "confidence": 0.0-1.0
}}

Типы действий: click, type, scroll, hover, wait, navigate, extract, analyze, custom_js
"""
        
        return prompt
    
    async def execute_action(self, action_guidance: Dict[str, Any]) -> bool:
        """Выполнение действия по руководству LLM"""
        try:
            action_type = action_guidance.get("action")
            target = action_guidance.get("target")
            reason = action_guidance.get("reason", "")
            
            logger.info(f"Выполнение действия: {action_type} -> {target} ({reason})")
            
            # Создание записи действия
            action = UserAction(
                id=str(uuid.uuid4()),
                session_id=self.session_id,
                action_type=ActionType(action_type),
                target=target,
                reason=reason,
                timestamp=datetime.now(),
                success=False
            )
            
            # Выполнение действия
            success = await self._perform_action(action_type, target)
            
            # Обновление статуса
            action.success = success
            
            # Добавление в историю
            self.actions_history.append(action)
            
            # Человеческая задержка после действия
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка выполнения действия: {e}")
            return False
    
    async def _perform_action(self, action_type: str, target: str) -> bool:
        """Выполнение конкретного действия"""
        try:
            if action_type == "click":
                return await self._click_element(target)
            elif action_type == "type":
                return await self._type_text(target)
            elif action_type == "scroll":
                return await self._scroll_page(target)
            elif action_type == "hover":
                return await self._hover_element(target)
            elif action_type == "wait":
                return await self._wait_action(target)
            elif action_type == "navigate":
                return await self._navigate_action(target)
            elif action_type == "extract":
                return await self._extract_data(target)
            elif action_type == "analyze":
                return await self._analyze_page(target)
            elif action_type == "custom_js":
                return await self._execute_custom_js(target)
            else:
                logger.warning(f"Неизвестный тип действия: {action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка выполнения действия {action_type}: {e}")
            return False
    
    async def _click_element(self, target: str) -> bool:
        """Клик по элементу"""
        try:
            element = self._find_element(target)
            if element:
                element.click()
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка клика: {e}")
            return False
    
    async def _type_text(self, target: str) -> bool:
        """Ввод текста"""
        try:
            # Парсинг target: "selector:text"
            if ":" in target:
                selector, text = target.split(":", 1)
            else:
                selector, text = target, "test text"
            
            element = self._find_element(selector)
            if element:
                element.clear()
                # Человеческий ввод с задержками
                for char in text:
                    element.send_keys(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка ввода текста: {e}")
            return False
    
    async def _scroll_page(self, target: str) -> bool:
        """Прокрутка страницы"""
        try:
            if target == "down":
                self.driver.execute_script("window.scrollBy(0, 300);")
            elif target == "up":
                self.driver.execute_script("window.scrollBy(0, -300);")
            elif target == "top":
                self.driver.execute_script("window.scrollTo(0, 0);")
            elif target == "bottom":
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            else:
                # Прокрутка к элементу
                element = self._find_element(target)
                if element:
                    self.driver.execute_script("arguments[0].scrollIntoView();", element)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            return True
        except Exception as e:
            logger.error(f"Ошибка прокрутки: {e}")
            return False
    
    async def _hover_element(self, target: str) -> bool:
        """Наведение на элемент"""
        try:
            element = self._find_element(target)
            if element:
                ActionChains(self.driver).move_to_element(element).perform()
                await asyncio.sleep(random.uniform(0.5, 1.0))
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка наведения: {e}")
            return False
    
    async def _wait_action(self, target: str) -> bool:
        """Ожидание"""
        try:
            if target.isdigit():
                seconds = int(target)
            else:
                seconds = random.uniform(1, 3)
            
            await asyncio.sleep(seconds)
            return True
        except Exception as e:
            logger.error(f"Ошибка ожидания: {e}")
            return False
    
    async def _navigate_action(self, target: str) -> bool:
        """Навигация"""
        try:
            if target.startswith("http"):
                self.driver.get(target)
            else:
                # Поиск ссылки
                link = self._find_element(f"a[href*='{target}']")
                if link:
                    link.click()
                else:
                    return False
            
            await asyncio.sleep(random.uniform(2, 4))
            return True
        except Exception as e:
            logger.error(f"Ошибка навигации: {e}")
            return False
    
    async def _extract_data(self, target: str) -> bool:
        """Извлечение данных"""
        try:
            if target == "all_forms":
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                data = []
                for form in forms:
                    data.append({
                        "action": form.get_attribute("action"),
                        "method": form.get_attribute("method"),
                        "inputs": [inp.get_attribute("name") for inp in form.find_elements(By.TAG_NAME, "input")]
                    })
            elif target == "all_links":
                links = self.driver.find_elements(By.TAG_NAME, "a")
                data = [{"href": link.get_attribute("href"), "text": link.text} for link in links]
            else:
                element = self._find_element(target)
                data = element.text if element else None
            
            # Сохранение извлеченных данных
            self.analysis_data["extracted_data"] = data
            return True
        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
            return False
    
    async def _analyze_page(self, target: str) -> bool:
        """Анализ страницы"""
        try:
            if self.ui_analyzer:
                analysis = await self.ui_analyzer.analyze_page_structure()
                self.analysis_data["current_analysis"] = analysis
                
                # Отправка в RAG
                await self._send_analysis_to_rag(analysis)
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка анализа страницы: {e}")
            return False
    
    async def _execute_custom_js(self, target: str) -> bool:
        """Выполнение кастомного JavaScript"""
        try:
            result = self.driver.execute_script(target)
            self.analysis_data["js_result"] = result
            return True
        except Exception as e:
            logger.error(f"Ошибка выполнения JS: {e}")
            return False
    
    def _find_element(self, selector: str):
        """Поиск элемента по селектору"""
        try:
            # Попытка найти по CSS селектору
            if selector.startswith("."):
                return self.driver.find_element(By.CLASS_NAME, selector[1:])
            elif selector.startswith("#"):
                return self.driver.find_element(By.ID, selector[1:])
            elif selector.startswith("//"):
                return self.driver.find_element(By.XPATH, selector)
            elif selector.startswith("text="):
                text = selector[5:]
                return self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
            else:
                # Попытка найти по различным селекторам
                selectors = [
                    (By.CSS_SELECTOR, selector),
                    (By.XPATH, f"//*[contains(text(), '{selector}')]"),
                    (By.XPATH, f"//*[@placeholder='{selector}']"),
                    (By.XPATH, f"//*[@title='{selector}']")
                ]
                
                for by, sel in selectors:
                    try:
                        return self.driver.find_element(by, sel)
                    except NoSuchElementException:
                        continue
                
                return None
        except Exception as e:
            logger.error(f"Ошибка поиска элемента {selector}: {e}")
            return None
    
    async def run_test_session(self, max_actions: int = 20) -> TestReport:
        """Запуск полной сессии тестирования"""
        logger.info(f"Запуск тестовой сессии. Максимум действий: {max_actions}")
        
        actions_count = 0
        start_time = datetime.now()
        
        try:
            while actions_count < max_actions:
                # Получение текущего контекста
                context = await self._get_current_context()
                
                # Получение руководства от LLM
                guidance = await self.get_llm_guidance(context)
                
                if not guidance or guidance.get("action") == "stop":
                    logger.info("LLM рекомендует остановить сессию")
                    break
                
                # Выполнение действия
                success = await self.execute_action(guidance)
                
                actions_count += 1
                
                if not success:
                    logger.warning(f"Действие {actions_count} не выполнено")
                
                # Проверка на ошибки или проблемы
                if await self._check_for_errors():
                    logger.warning("Обнаружены ошибки на странице")
                    break
                
                # Случайная пауза между действиями
                await asyncio.sleep(random.uniform(1, 3))
            
        except Exception as e:
            logger.error(f"Ошибка в тестовой сессии: {e}")
        
        finally:
            # Создание отчета
            report = await self._generate_test_report(start_time, actions_count)
            
            # Отправка отчета
            await self.api_client.send_test_report(report.dict())
            
            return report
    
    async def _get_current_context(self) -> Dict[str, Any]:
        """Получение текущего контекста страницы"""
        try:
            # Поиск доступных элементов
            available_elements = []
            
            # Кнопки
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons[:5]:  # Ограничиваем количество
                available_elements.append({
                    "type": "button",
                    "text": btn.text,
                    "selector": f"button:contains('{btn.text}')"
                })
            
            # Ссылки
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links[:5]:
                available_elements.append({
                    "type": "link",
                    "text": link.text,
                    "href": link.get_attribute("href")
                })
            
            # Формы
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            for form in forms[:3]:
                available_elements.append({
                    "type": "form",
                    "action": form.get_attribute("action")
                })
            
            return {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "available_elements": available_elements,
                "recent_actions": [action.action_type.value for action in self.actions_history[-3:]],
                "session_duration": (datetime.now() - self.session_start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения контекста: {e}")
            return {"error": str(e)}
    
    async def _check_for_errors(self) -> bool:
        """Проверка на ошибки на странице"""
        try:
            # Проверка на JavaScript ошибки
            js_errors = self.driver.execute_script("return window.errors || [];")
            if js_errors:
                return True
            
            # Проверка на HTTP ошибки
            if "404" in self.driver.title or "500" in self.driver.title:
                return True
            
            # Проверка на элементы ошибок
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .warning")
            if error_elements:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка проверки ошибок: {e}")
            return False
    
    async def _generate_test_report(self, start_time: datetime, actions_count: int) -> TestReport:
        """Генерация отчета о тестировании"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Анализ результатов
        successful_actions = len([a for a in self.actions_history if a.success])
        failed_actions = len([a for a in self.actions_history if not a.success])
        
        # Определение проблем
        issues = []
        if failed_actions > 0:
            issues.append(f"Неудачных действий: {failed_actions}")
        
        if duration < 30:
            issues.append("Слишком короткая сессия")
        
        if actions_count < 5:
            issues.append("Мало действий выполнено")
        
        return TestReport(
            id=str(uuid.uuid4()),
            session_id=self.session_id,
            profile_id=self.current_profile.id,
            target_url=self.driver.current_url if self.driver else "",
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            total_actions=actions_count,
            successful_actions=successful_actions,
            failed_actions=failed_actions,
            issues=issues,
            analysis_data=self.analysis_data,
            actions_history=self.actions_history,
            created_at=datetime.now()
        )
    
    async def stop_session(self):
        """Остановка сессии"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            logger.info("Сессия остановлена")
            
        except Exception as e:
            logger.error(f"Ошибка остановки сессии: {e}")
    
    def __del__(self):
        """Деструктор для очистки ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 

class UXBotCore:
    """Ядро UX-бота - основная логика работы"""
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.browser_service: Optional[BrowserService] = None
        self.api_client: Optional[APIClient] = None
        self.scenario_service: Optional[ScenarioService] = None
        self.current_user_profile: Optional[UserProfile] = None
        self.is_running = False
        self.action_history: List[Dict[str, Any]] = []
        self.issues_found: List[Issue] = []
        
    async def initialize(self, user_profile_id: Optional[str] = None) -> bool:
        """Инициализация UX-бота"""
        try:
            logger.info("Инициализация UX-бота")
            
            # Генерация ID сессии
            self.session_id = str(uuid.uuid4())
            
            # Инициализация профиля пользователя
            if user_profile_id:
                self.scenario_service = ScenarioService()
                self.current_user_profile = self.scenario_service.get_user_profile(user_profile_id)
                if not self.current_user_profile:
                    logger.warning(f"Профиль пользователя не найден: {user_profile_id}")
                    self.current_user_profile = self.scenario_service.get_user_profile("beginner")
            else:
                self.scenario_service = ScenarioService()
                self.current_user_profile = self.scenario_service.get_user_profile("beginner")
            
            # Инициализация конфигурации браузера
            browser_config = BrowserConfig(
                headless=settings.browser_headless,
                user_agent=settings.user_profiles[0]["name"] if settings.user_profiles else "UX Bot",
                wait_timeout=settings.browser_timeout,
                implicit_wait=settings.browser_implicit_wait
            )
            
            # Инициализация сервиса браузера
            self.browser_service = BrowserService(browser_config)
            
            # Инициализация API клиента
            api_config = APIConfig(
                base_url=settings.backend_url,
                timeout=30,
                retry_count=3
            )
            self.api_client = APIClient(api_config)
            
            logger.info(f"UX-бот инициализирован. Сессия: {self.session_id}")
            logger.info(f"Профиль пользователя: {self.current_user_profile.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации UX-бота: {e}")
            return False
    
    async def start_session(self) -> bool:
        """Запуск сессии UX-бота"""
        try:
            if not self.browser_service or not self.api_client:
                raise RuntimeError("UX-бот не инициализирован")
            
            # Запуск сессии браузера
            browser_started = await self.browser_service.start_session(self.session_id)
            if not browser_started:
                raise RuntimeError("Не удалось запустить браузер")
            
            # Подключение к API
            await self.api_client.connect()
            
            # Проверка здоровья API
            api_healthy = await self.api_client.health_check()
            if not api_healthy:
                logger.warning("API недоступен, но продолжаем работу")
            
            self.is_running = True
            logger.info(f"Сессия UX-бота запущена: {self.session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска сессии UX-бота: {e}")
            return False
    
    async def stop_session(self):
        """Остановка сессии UX-бота"""
        try:
            self.is_running = False
            
            # Закрытие браузера
            if self.browser_service:
                await self.browser_service.close_session()
            
            # Отключение от API
            if self.api_client:
                await self.api_client.disconnect()
            
            logger.info(f"Сессия UX-бота остановлена: {self.session_id}")
            
        except Exception as e:
            logger.error(f"Ошибка остановки сессии UX-бота: {e}")
    
    async def run_scenario(self, scenario_id: str) -> TestReport:
        """Запуск тестового сценария"""
        try:
            if not self.is_running:
                raise RuntimeError("UX-бот не запущен")
            
            logger.info(f"Запуск сценария: {scenario_id}")
            
            # Создание контекста сценария
            context = self.scenario_service.create_scenario_context(
                scenario_id=scenario_id,
                session_id=self.session_id,
                user_profile=self.current_user_profile
            )
            
            # Выполнение сценария
            results = await self.scenario_service.execute_scenario(
                context=context,
                browser_service=self.browser_service,
                api_client=self.api_client
            )
            
            # Создание отчета
            report = await self._create_test_report(scenario_id, results)
            
            # Отправка отчета в бэкенд
            if self.api_client:
                await self.api_client.send_test_report(report)
            
            logger.info(f"Сценарий {scenario_id} завершен. Успешность: {report.success_rate:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка выполнения сценария {scenario_id}: {e}")
            # Создание отчета об ошибке
            error_result = TestResult(
                test_id=f"{scenario_id}_error",
                scenario_id=scenario_id,
                status=TestStatus.FAILED,
                start_time=datetime.now(),
                end_time=datetime.now(),
                success=False,
                error_message=str(e)
            )
            return await self._create_test_report(scenario_id, [error_result])
    
    async def analyze_page(self, url: str) -> PageAnalysis:
        """Анализ страницы"""
        try:
            logger.info(f"Анализ страницы: {url}")
            
            # Переход на страницу
            if not await self.browser_service.navigate_to(url):
                raise RuntimeError(f"Не удалось перейти на страницу: {url}")
            
            # Получение базовой информации
            title = await self.browser_service.get_page_title()
            current_url = await self.browser_service.get_current_url()
            
            # Поиск элементов на странице
            elements = []
            common_selectors = [
                "button", "input", "a", "form", "img", "h1", "h2", "h3", 
                ".btn", ".form-control", ".nav-link", ".card"
            ]
            
            for selector in common_selectors:
                found_elements = await self.browser_service.find_elements(selector)
                for i, element in enumerate(found_elements):
                    try:
                        element_info = await self.browser_service.get_element_info(f"{selector}:nth-child({i+1})")
                        if element_info:
                            elements.append(element_info)
                    except:
                        continue
            
            # Создание скриншота
            screenshot_path = await self.browser_service.take_screenshot(
                f"analysis_{url.replace('://', '_').replace('/', '_')}.png"
            )
            
            # Анализ доступности
            accessibility_issues = await self._analyze_accessibility()
            
            # Анализ отзывчивости
            responsiveness_issues = await self._analyze_responsiveness()
            
            # Метрики производительности
            performance_metrics = await self._get_performance_metrics()
            
            # Создание анализа страницы
            analysis = PageAnalysis(
                url=current_url,
                title=title,
                elements=elements,
                accessibility_issues=accessibility_issues,
                responsiveness_issues=responsiveness_issues,
                performance_metrics=performance_metrics,
                screenshot_path=screenshot_path
            )
            
            # Отправка анализа в бэкенд
            if self.api_client:
                await self.api_client.send_page_analysis(analysis)
            
            logger.info(f"Анализ страницы завершен. Найдено элементов: {len(elements)}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа страницы {url}: {e}")
            raise
    
    async def get_llm_instruction(self, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Получение инструкции от LLM-роутера"""
        try:
            if not self.api_client:
                return {"error": "API клиент не инициализирован"}
            
            # Отправка контекста в LLM-роутер
            context_data = {
                "session_id": self.session_id,
                "user_profile": {
                    "name": self.current_user_profile.name,
                    "behavior": self.current_user_profile.behavior,
                    "speed": self.current_user_profile.speed
                } if self.current_user_profile else None,
                "current_context": current_context,
                "action_history": self.action_history[-5:]  # Последние 5 действий
            }
            
            instruction = await self.api_client.get_llm_instruction(
                session_id=self.session_id,
                current_context=context_data
            )
            
            logger.info(f"Получена инструкция от LLM: {instruction.get('action', 'unknown')}")
            
            return instruction
            
        except Exception as e:
            logger.error(f"Ошибка получения инструкции от LLM: {e}")
            return {"error": str(e)}
    
    async def execute_llm_instruction(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение инструкции от LLM"""
        try:
            action = instruction.get("action")
            target = instruction.get("target")
            
            if not action:
                return {"error": "Действие не указано"}
            
            logger.info(f"Выполнение действия: {action} -> {target}")
            
            result = {"success": False, "action": action, "target": target}
            
            # Выполнение действия
            if action == "click":
                result["success"] = await self.browser_service.click_element(target)
                
            elif action == "type":
                if ":" in target:
                    selector, text = target.split(":", 1)
                    result["success"] = await self.browser_service.type_text(selector, text)
                else:
                    result["error"] = "Неверный формат для ввода текста"
                    
            elif action == "scroll":
                if target in ["up", "down", "top", "bottom"]:
                    script = f"window.scrollTo(0, {'0' if target in ['top', 'up'] else 'document.body.scrollHeight'})"
                    await self.browser_service.execute_script(script)
                    result["success"] = True
                else:
                    result["success"] = await self.browser_service.scroll_to_element(target)
                    
            elif action == "wait":
                try:
                    wait_time = float(target)
                    await asyncio.sleep(wait_time)
                    result["success"] = True
                except ValueError:
                    result["error"] = "Неверное время ожидания"
                    
            elif action == "navigate":
                result["success"] = await self.browser_service.navigate_to(target)
                
            elif action == "analyze":
                analysis = await self.analyze_page(target)
                result["success"] = True
                result["analysis"] = analysis
                
            elif action == "stop":
                await self.stop_session()
                result["success"] = True
                
            else:
                result["error"] = f"Неизвестное действие: {action}"
            
            # Добавление действия в историю
            self.action_history.append({
                "action": action,
                "target": target,
                "success": result["success"],
                "timestamp": datetime.now().isoformat(),
                "error": result.get("error")
            })
            
            # Отправка результата в LLM-роутер
            if self.api_client:
                await self.api_client.send_action_result(
                    session_id=self.session_id,
                    action=action,
                    result=result
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка выполнения инструкции: {e}")
            return {"error": str(e), "action": instruction.get("action")}
    
    async def run_interactive_session(self, start_url: str, max_actions: int = 50) -> TestReport:
        """Запуск интерактивной сессии с LLM"""
        try:
            logger.info(f"Запуск интерактивной сессии. Начальный URL: {start_url}")
            
            # Переход на начальную страницу
            if not await self.browser_service.navigate_to(start_url):
                raise RuntimeError(f"Не удалось перейти на {start_url}")
            
            actions_performed = 0
            results = []
            
            while self.is_running and actions_performed < max_actions:
                try:
                    # Получение текущего контекста
                    current_url = await self.browser_service.get_current_url()
                    page_title = await self.browser_service.get_page_title()
                    
                    current_context = {
                        "url": current_url,
                        "title": page_title,
                        "session_id": self.session_id,
                        "actions_performed": actions_performed
                    }
                    
                    # Получение инструкции от LLM
                    instruction = await self.get_llm_instruction(current_context)
                    
                    if "error" in instruction:
                        logger.warning(f"Ошибка получения инструкции: {instruction['error']}")
                        break
                    
                    # Выполнение инструкции
                    result = await self.execute_llm_instruction(instruction)
                    
                    if not result.get("success"):
                        logger.warning(f"Действие не выполнено: {result.get('error')}")
                    
                    actions_performed += 1
                    
                    # Небольшая пауза между действиями
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Ошибка в интерактивной сессии: {e}")
                    break
            
            # Создание отчета
            report = await self._create_interactive_report(actions_performed)
            
            logger.info(f"Интерактивная сессия завершена. Выполнено действий: {actions_performed}")
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка интерактивной сессии: {e}")
            raise
    
    async def _create_test_report(self, scenario_id: str, results: List[TestResult]) -> TestReport:
        """Создание отчета о тестировании"""
        total_tests = len(results)
        successful_tests = len([r for r in results if r.success])
        failed_tests = len([r for r in results if not r.success])
        
        # Анализ проблем
        issues = []
        for result in results:
            if not result.success and result.error_message:
                issue = Issue(
                    issue_id=f"issue_{scenario_id}_{result.step_id or 'unknown'}",
                    type="functionality",
                    severity=IssueSeverity.HIGH if "критическая" in result.error_message.lower() else IssueSeverity.MEDIUM,
                    description=result.error_message,
                    location=result.data.get("url", "unknown"),
                    screenshot_path=result.screenshot_path
                )
                issues.append(issue)
        
        report = TestReport(
            report_id=f"report_{self.session_id}_{scenario_id}",
            session_id=self.session_id,
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            skipped_tests=0,
            issues=issues,
            user_profile=self.current_user_profile,
            test_environment={
                "browser": "Chrome",
                "headless": settings.browser_headless,
                "viewport": f"{settings.browser_viewport_width}x{settings.browser_viewport_height}"
            }
        )
        
        return report
    
    async def _create_interactive_report(self, actions_performed: int) -> TestReport:
        """Создание отчета об интерактивной сессии"""
        report = TestReport(
            report_id=f"interactive_report_{self.session_id}",
            session_id=self.session_id,
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_tests=actions_performed,
            successful_tests=len([a for a in self.action_history if a.get("success")]),
            failed_tests=len([a for a in self.action_history if not a.get("success")]),
            skipped_tests=0,
            issues=self.issues_found,
            user_profile=self.current_user_profile,
            test_environment={
                "browser": "Chrome",
                "headless": settings.browser_headless,
                "mode": "interactive"
            },
            notes=f"Интерактивная сессия с {actions_performed} действиями"
        )
        
        return report
    
    async def _analyze_accessibility(self) -> List[Dict[str, Any]]:
        """Анализ доступности страницы"""
        issues = []
        
        try:
            # Проверка alt-атрибутов изображений
            images = await self.browser_service.find_elements("img")
            for img in images:
                alt = img.get_attribute("alt")
                if not alt:
                    issues.append({
                        "type": "accessibility",
                        "severity": "medium",
                        "description": "Изображение без alt-атрибута",
                        "element": "img"
                    })
            
            # Проверка ARIA-атрибутов
            elements_without_aria = await self.browser_service.find_elements("[role]")
            for elem in elements_without_aria:
                aria_label = elem.get_attribute("aria-label")
                if not aria_label:
                    issues.append({
                        "type": "accessibility",
                        "severity": "low",
                        "description": "Элемент с role без aria-label",
                        "element": elem.tag_name
                    })
            
        except Exception as e:
            logger.error(f"Ошибка анализа доступности: {e}")
        
        return issues
    
    async def _analyze_responsiveness(self) -> List[Dict[str, Any]]:
        """Анализ отзывчивости страницы"""
        issues = []
        
        try:
            # Проверка viewport
            viewport_meta = await self.browser_service.find_element("meta[name='viewport']")
            if not viewport_meta:
                issues.append({
                    "type": "responsiveness",
                    "severity": "high",
                    "description": "Отсутствует meta viewport",
                    "element": "meta"
                })
            
            # Проверка медиа-запросов (базовая)
            css_files = await self.browser_service.find_elements("link[rel='stylesheet']")
            if len(css_files) == 0:
                issues.append({
                    "type": "responsiveness",
                    "severity": "medium",
                    "description": "Отсутствуют CSS файлы",
                    "element": "link"
                })
            
        except Exception as e:
            logger.error(f"Ошибка анализа отзывчивости: {e}")
        
        return issues
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        metrics = {}
        
        try:
            # Базовые метрики через JavaScript
            performance_script = """
            () => {
                const perfData = performance.getEntriesByType('navigation')[0];
                return {
                    loadTime: perfData.loadEventEnd - perfData.loadEventStart,
                    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                    firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                    firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                };
            }
            """
            
            perf_data = await self.browser_service.execute_script(performance_script)
            if perf_data:
                metrics.update(perf_data)
            
        except Exception as e:
            logger.error(f"Ошибка получения метрик производительности: {e}")
        
        return metrics
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики работы UX-бота"""
        return {
            "session_id": self.session_id,
            "is_running": self.is_running,
            "user_profile": self.current_user_profile.name if self.current_user_profile else None,
            "actions_performed": len(self.action_history),
            "issues_found": len(self.issues_found),
            "scenarios_available": len(self.scenario_service.scenarios) if self.scenario_service else 0
        } 