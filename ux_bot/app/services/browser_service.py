"""
🌐 Сервис браузера для технического анализа UI

Обеспечивает:
- Технический анализ DOM и метаданных
- Извлечение интерактивных элементов
- Анализ JavaScript и API endpoints
- Сбор технической информации о UI
"""

import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from playwright.async_api import async_playwright, Browser, Page
from ..models import BrowserConfig, UIElement, ElementType
from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class TechnicalAnalysis:
    """Технический анализ страницы"""
    url: str
    title: str
    meta_tags: Dict[str, str]
    forms: List[Dict[str, Any]]
    buttons: List[UIElement]
    inputs: List[UIElement]
    links: List[UIElement]
    javascript_files: List[str]
    css_files: List[str]
    api_endpoints: List[str]
    network_requests: List[Dict[str, Any]]
    dom_structure: Dict[str, Any]
    accessibility_info: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class BrowserService:
    """Сервис для управления браузером"""
    
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.session_id: Optional[str] = None
        
    async def start_session(self, session_id: str) -> bool:
        """Запуск сессии браузера"""
        try:
            logger.info(f"Запуск сессии браузера: {session_id}")
            
            # Настройка Chrome options
            chrome_options = Options()
            
            if self.config.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument(f"--user-agent={self.config.user_agent}")
            chrome_options.add_argument(f"--window-size={self.config.viewport_width},{self.config.viewport_height}")
            
            # Добавление дополнительных аргументов
            for arg in self.config.additional_args:
                chrome_options.add_argument(arg)
            
            # Создание драйвера
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.config.implicit_wait)
            
            # Настройка WebDriverWait
            self.wait = WebDriverWait(self.driver, self.config.wait_timeout)
            
            # Сохранение ID сессии
            self.session_id = session_id
            
            logger.info(f"Сессия браузера запущена: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при запуске сессии браузера: {e}")
            return False
    
    async def close_session(self):
        """Закрытие сессии браузера"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info(f"Сессия браузера закрыта: {self.session_id}")
            except Exception as e:
                logger.error(f"Ошибка при закрытии сессии: {e}")
            finally:
                self.driver = None
                self.wait = None
                self.session_id = None
    
    async def navigate_to(self, url: str) -> bool:
        """Переход на URL"""
        try:
            logger.info(f"Переход на URL: {url}")
            self.driver.get(url)
            
            # Ожидание загрузки страницы
            await asyncio.sleep(2)
            
            logger.info(f"Успешно перешли на: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при переходе на URL {url}: {e}")
            return False
    
    async def get_current_url(self) -> str:
        """Получение текущего URL"""
        return self.driver.current_url if self.driver else ""
    
    async def get_page_title(self) -> str:
        """Получение заголовка страницы"""
        return self.driver.title if self.driver else ""
    
    async def find_element(self, selector: str, timeout: Optional[int] = None) -> Optional[Any]:
        """Поиск элемента по селектору"""
        try:
            wait_time = timeout or self.config.wait_timeout
            wait = WebDriverWait(self.driver, wait_time)
            
            # Определение типа селектора
            if selector.startswith('#'):
                element = wait.until(EC.presence_of_element_located((By.ID, selector[1:])))
            elif selector.startswith('.'):
                element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, selector[1:])))
            elif selector.startswith('//'):
                element = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            else:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            
            return element
            
        except TimeoutException:
            logger.warning(f"Элемент не найден: {selector}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при поиске элемента {selector}: {e}")
            return None
    
    async def find_elements(self, selector: str) -> List[Any]:
        """Поиск всех элементов по селектору"""
        try:
            if selector.startswith('#'):
                elements = self.driver.find_elements(By.ID, selector[1:])
            elif selector.startswith('.'):
                elements = self.driver.find_elements(By.CLASS_NAME, selector[1:])
            elif selector.startswith('//'):
                elements = self.driver.find_elements(By.XPATH, selector)
            else:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            
            return elements
            
        except Exception as e:
            logger.error(f"Ошибка при поиске элементов {selector}: {e}")
            return []
    
    async def click_element(self, selector: str) -> bool:
        """Клик по элементу"""
        try:
            element = await self.find_element(selector)
            if element:
                element.click()
                logger.info(f"Клик по элементу: {selector}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при клике по элементу {selector}: {e}")
            return False
    
    async def type_text(self, selector: str, text: str) -> bool:
        """Ввод текста в элемент"""
        try:
            element = await self.find_element(selector)
            if element:
                element.clear()
                element.send_keys(text)
                logger.info(f"Введен текст в элемент {selector}: {text}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при вводе текста в элемент {selector}: {e}")
            return False
    
    async def scroll_to_element(self, selector: str) -> bool:
        """Прокрутка к элементу"""
        try:
            element = await self.find_element(selector)
            if element:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                await asyncio.sleep(1)
                logger.info(f"Прокрутка к элементу: {selector}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при прокрутке к элементу {selector}: {e}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Ожидание появления элемента"""
        try:
            element = await self.find_element(selector, timeout)
            return element is not None
            
        except Exception as e:
            logger.error(f"Ошибка при ожидании элемента {selector}: {e}")
            return False
    
    async def take_screenshot(self, filename: str) -> Optional[str]:
        """Создание скриншота"""
        try:
            if not self.driver:
                return None
            
            # Создание пути для скриншота
            import os
            screenshot_path = os.path.join(settings.screenshot_dir, filename)
            
            # Создание скриншота
            self.driver.save_screenshot(screenshot_path)
            
            logger.info(f"Скриншот сохранен: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании скриншота: {e}")
            return None
    
    async def get_page_source(self) -> str:
        """Получение исходного кода страницы"""
        return self.driver.page_source if self.driver else ""
    
    async def execute_script(self, script: str) -> Any:
        """Выполнение JavaScript кода"""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            logger.error(f"Ошибка при выполнении скрипта: {e}")
            return None
    
    async def get_element_info(self, selector: str) -> Optional[UIElement]:
        """Получение информации об элементе"""
        try:
            element = await self.find_element(selector)
            if not element:
                return None
            
            # Определение типа элемента
            tag_name = element.tag_name.lower()
            element_type = ElementType.OTHER
            
            if tag_name in ['button', 'input[type="button"]', 'input[type="submit"]']:
                element_type = ElementType.BUTTON
            elif tag_name == 'input':
                element_type = ElementType.INPUT
            elif tag_name == 'a':
                element_type = ElementType.LINK
            elif tag_name == 'img':
                element_type = ElementType.IMAGE
            elif tag_name in ['form']:
                element_type = ElementType.FORM
            elif tag_name in ['nav', 'ul', 'ol']:
                element_type = ElementType.NAVIGATION
            
            # Получение атрибутов
            attributes = {}
            for attr in ['id', 'class', 'name', 'type', 'value', 'href', 'src', 'alt']:
                value = element.get_attribute(attr)
                if value:
                    attributes[attr] = value
            
            # Получение позиции и размера
            location = element.location
            size = element.size
            
            return UIElement(
                selector=selector,
                element_type=element_type,
                text=element.text,
                attributes=attributes,
                is_visible=element.is_displayed(),
                is_enabled=element.is_enabled(),
                position={'x': location['x'], 'y': location['y']} if location else None,
                size={'width': size['width'], 'height': size['height']} if size else None
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации об элементе {selector}: {e}")
            return None
    
    async def check_element_visibility(self, selector: str) -> bool:
        """Проверка видимости элемента"""
        try:
            element = await self.find_element(selector)
            return element.is_displayed() if element else False
        except Exception as e:
            logger.error(f"Ошибка при проверке видимости элемента {selector}: {e}")
            return False
    
    async def check_element_enabled(self, selector: str) -> bool:
        """Проверка активности элемента"""
        try:
            element = await self.find_element(selector)
            return element.is_enabled() if element else False
        except Exception as e:
            logger.error(f"Ошибка при проверке активности элемента {selector}: {e}")
            return False
    
    async def analyze_page_technically(self, url: str) -> TechnicalAnalysis:
        """Полный технический анализ страницы"""
        try:
            if not await self.navigate_to(url):
                raise Exception("Не удалось перейти на страницу")
            
            # Базовый анализ
            title = await self._get_page_title()
            meta_tags = await self._extract_meta_tags()
            
            # Анализ DOM
            forms = await self._analyze_forms()
            buttons = await self._extract_buttons()
            inputs = await self._extract_inputs()
            links = await self._extract_links()
            
            # Анализ ресурсов
            javascript_files = await self._extract_javascript_files()
            css_files = await self._extract_css_files()
            
            # Анализ API и сетевых запросов
            api_endpoints = await self._extract_api_endpoints()
            network_requests = await self._capture_network_requests()
            
            # Структура DOM
            dom_structure = await self._analyze_dom_structure()
            
            # Доступность
            accessibility_info = await self._analyze_accessibility()
            
            # Производительность
            performance_metrics = await self._get_performance_metrics()
            
            return TechnicalAnalysis(
                url=url,
                title=title,
                meta_tags=meta_tags,
                forms=forms,
                buttons=buttons,
                inputs=inputs,
                links=links,
                javascript_files=javascript_files,
                css_files=css_files,
                api_endpoints=api_endpoints,
                network_requests=network_requests,
                dom_structure=dom_structure,
                accessibility_info=accessibility_info,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"Ошибка технического анализа страницы: {e}")
            raise
    
    async def _get_page_title(self) -> str:
        """Получение заголовка страницы"""
        try:
            if self.driver:
                return self.driver.title
            return ""
        except:
            return ""
    
    async def _extract_meta_tags(self) -> Dict[str, str]:
        """Извлечение мета-тегов"""
        try:
            if self.driver:
                meta_elements = self.driver.find_elements(By.TAG_NAME, "meta")
                meta_tags = {}
                for meta in meta_elements:
                    name = meta.get_attribute("name") or meta.get_attribute("property")
                    content = meta.get_attribute("content")
                    if name and content:
                        meta_tags[name] = content
                return meta_tags
            return {}
        except Exception as e:
            logger.error(f"Ошибка извлечения мета-тегов: {e}")
            return {}
    
    async def _analyze_forms(self) -> List[Dict[str, Any]]:
        """Анализ форм на странице"""
        try:
            forms = []
            
            if self.driver:
                form_elements = self.driver.find_elements(By.TAG_NAME, "form")
                for form in form_elements:
                    form_data = {
                        "action": form.get_attribute("action"),
                        "method": form.get_attribute("method"),
                        "id": form.get_attribute("id"),
                        "class": form.get_attribute("class"),
                        "inputs": []
                    }
                    
                    # Анализ полей ввода в форме
                    inputs = form.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        input_data = {
                            "type": inp.get_attribute("type"),
                            "name": inp.get_attribute("name"),
                            "id": inp.get_attribute("id"),
                            "placeholder": inp.get_attribute("placeholder"),
                            "required": inp.get_attribute("required") is not None
                        }
                        form_data["inputs"].append(input_data)
                    
                    forms.append(form_data)
            
            return forms
            
        except Exception as e:
            logger.error(f"Ошибка анализа форм: {e}")
            return []
    
    async def _extract_buttons(self) -> List[UIElement]:
        """Извлечение кнопок"""
        try:
            buttons = []
            
            if self.driver:
                button_elements = self.driver.find_elements(By.TAG_NAME, "button")
                button_elements.extend(self.driver.find_elements(By.CSS_SELECTOR, "[role='button']"))
                
                for button in button_elements:
                    try:
                        button_data = UIElement(
                            tag_name=button.tag_name,
                            element_type="button",
                            text=button.text,
                            attributes={
                                "id": button.get_attribute("id"),
                                "class": button.get_attribute("class"),
                                "type": button.get_attribute("type"),
                                "disabled": button.get_attribute("disabled")
                            },
                            xpath=self._get_xpath(button),
                            css_selector=self._get_css_selector(button),
                            is_visible=button.is_displayed(),
                            is_enabled=button.is_enabled(),
                            position={"x": button.location["x"], "y": button.location["y"]},
                            size={"width": button.size["width"], "height": button.size["height"]}
                        )
                        buttons.append(button_data)
                    except:
                        continue
            
            return buttons
            
        except Exception as e:
            logger.error(f"Ошибка извлечения кнопок: {e}")
            return []
    
    async def _extract_inputs(self) -> List[UIElement]:
        """Извлечение полей ввода"""
        try:
            inputs = []
            
            if self.driver:
                input_elements = self.driver.find_elements(By.TAG_NAME, "input")
                textarea_elements = self.driver.find_elements(By.TAG_NAME, "textarea")
                select_elements = self.driver.find_elements(By.TAG_NAME, "select")
                
                all_elements = input_elements + textarea_elements + select_elements
                
                for element in all_elements:
                    try:
                        element_data = UIElement(
                            tag_name=element.tag_name,
                            element_type="input",
                            text=element.get_attribute("placeholder") or "",
                            attributes={
                                "id": element.get_attribute("id"),
                                "class": element.get_attribute("class"),
                                "type": element.get_attribute("type"),
                                "name": element.get_attribute("name"),
                                "required": element.get_attribute("required") is not None
                            },
                            xpath=self._get_xpath(element),
                            css_selector=self._get_css_selector(element),
                            is_visible=element.is_displayed(),
                            is_enabled=element.is_enabled(),
                            position={"x": element.location["x"], "y": element.location["y"]},
                            size={"width": element.size["width"], "height": element.size["height"]}
                        )
                        inputs.append(element_data)
                    except:
                        continue
            
            return inputs
            
        except Exception as e:
            logger.error(f"Ошибка извлечения полей ввода: {e}")
            return []
    
    async def _extract_links(self) -> List[UIElement]:
        """Извлечение ссылок"""
        try:
            links = []
            
            if self.driver:
                link_elements = self.driver.find_elements(By.TAG_NAME, "a")
                
                for link in link_elements:
                    try:
                        link_data = UIElement(
                            tag_name=link.tag_name,
                            element_type="link",
                            text=link.text,
                            attributes={
                                "id": link.get_attribute("id"),
                                "class": link.get_attribute("class"),
                                "href": link.get_attribute("href"),
                                "target": link.get_attribute("target")
                            },
                            xpath=self._get_xpath(link),
                            css_selector=self._get_css_selector(link),
                            is_visible=link.is_displayed(),
                            is_enabled=link.is_enabled(),
                            position={"x": link.location["x"], "y": link.location["y"]},
                            size={"width": link.size["width"], "height": link.size["height"]}
                        )
                        links.append(link_data)
                    except:
                        continue
            
            return links
            
        except Exception as e:
            logger.error(f"Ошибка извлечения ссылок: {e}")
            return []
    
    async def _extract_javascript_files(self) -> List[str]:
        """Извлечение JavaScript файлов"""
        try:
            js_files = []
            
            if self.driver:
                script_elements = self.driver.find_elements(By.TAG_NAME, "script")
                for script in script_elements:
                    src = script.get_attribute("src")
                    if src:
                        js_files.append(src)
            
            return js_files
            
        except Exception as e:
            logger.error(f"Ошибка извлечения JavaScript файлов: {e}")
            return []
    
    async def _extract_css_files(self) -> List[str]:
        """Извлечение CSS файлов"""
        try:
            css_files = []
            
            if self.driver:
                link_elements = self.driver.find_elements(By.TAG_NAME, "link")
                for link in link_elements:
                    rel = link.get_attribute("rel")
                    href = link.get_attribute("href")
                    if rel == "stylesheet" and href:
                        css_files.append(href)
            
            return css_files
            
        except Exception as e:
            logger.error(f"Ошибка извлечения CSS файлов: {e}")
            return []
    
    async def _extract_api_endpoints(self) -> List[str]:
        """Извлечение API endpoints из JavaScript"""
        try:
            endpoints = []
            
            if self.driver:
                # Анализ JavaScript кода на странице
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                for script in scripts:
                    script_content = script.get_attribute("innerHTML")
                    if script_content:
                        # Поиск URL паттернов
                        import re
                        url_patterns = [
                            r'["\'](/api/[^"\']*)["\']',
                            r'["\'](https?://[^/]+/api/[^"\']*)["\']',
                            r'fetch\(["\']([^"\']*)["\']',
                            r'axios\.(get|post|put|delete)\(["\']([^"\']*)["\']'
                        ]
                        
                        for pattern in url_patterns:
                            matches = re.findall(pattern, script_content)
                            endpoints.extend(matches)
            
            return list(set(endpoints))  # Убираем дубликаты
            
        except Exception as e:
            logger.error(f"Ошибка извлечения API endpoints: {e}")
            return []
    
    async def _capture_network_requests(self) -> List[Dict[str, Any]]:
        """Захват сетевых запросов"""
        try:
            requests = []
            
            if self.driver:
                # Playwright может захватывать сетевые запросы
                page = self.driver
                
                # Слушаем сетевые события
                async def handle_request(request):
                    requests.append({
                        "url": request.url,
                        "method": request.method,
                        "headers": request.headers,
                        "post_data": request.post_data
                    })
                
                page.on("request", handle_request)
                
                # Ждем немного для захвата запросов
                await asyncio.sleep(2)
            
            return requests
            
        except Exception as e:
            logger.error(f"Ошибка захвата сетевых запросов: {e}")
            return []
    
    async def _analyze_dom_structure(self) -> Dict[str, Any]:
        """Анализ структуры DOM"""
        try:
            dom_structure = {
                "total_elements": 0,
                "element_types": {},
                "nested_levels": 0,
                "complexity_score": 0
            }
            
            if self.driver:
                # Подсчет элементов
                all_elements = self.driver.find_elements(By.XPATH, "//*")
                dom_structure["total_elements"] = len(all_elements)
                
                # Анализ типов элементов
                for element in all_elements:
                    tag_name = element.tag_name
                    dom_structure["element_types"][tag_name] = dom_structure["element_types"].get(tag_name, 0) + 1
            
            # Расчет сложности
            dom_structure["complexity_score"] = self._calculate_complexity_score(dom_structure)
            
            return dom_structure
            
        except Exception as e:
            logger.error(f"Ошибка анализа структуры DOM: {e}")
            return {}
    
    async def _analyze_accessibility(self) -> Dict[str, Any]:
        """Анализ доступности"""
        try:
            accessibility_info = {
                "aria_labels": [],
                "alt_texts": [],
                "semantic_elements": [],
                "accessibility_score": 0
            }
            
            if self.driver:
                # ARIA labels
                aria_elements = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label]")
                for element in aria_elements:
                    accessibility_info["aria_labels"].append({
                        "element": element.tag_name,
                        "aria_label": element.get_attribute("aria-label")
                    })
                
                # Alt texts
                img_elements = self.driver.find_elements(By.TAG_NAME, "img")
                for img in img_elements:
                    alt = img.get_attribute("alt")
                    if alt:
                        accessibility_info["alt_texts"].append(alt)
            
            # Расчет score доступности
            accessibility_info["accessibility_score"] = self._calculate_accessibility_score(accessibility_info)
            
            return accessibility_info
            
        except Exception as e:
            logger.error(f"Ошибка анализа доступности: {e}")
            return {}
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        try:
            metrics = {}
            
            if self.driver:
                # Метрики через Playwright
                performance = await self.driver.execute_script("""
                    () => {
                        const perfData = performance.getEntriesByType('navigation')[0];
                        return {
                            loadTime: perfData.loadEventEnd - perfData.loadEventStart,
                            domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                            firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                            firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                        };
                    }
                """)
                metrics.update(performance)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Ошибка получения метрик производительности: {e}")
            return {}
    
    def _get_xpath(self, element) -> str:
        """Получение XPath элемента (Selenium)"""
        try:
            return self.driver.execute_script("""
                function getXPath(element) {
                    if (element.id !== '') {
                        return 'id("' + element.id + '")';
                    }
                    if (element === document.body) {
                        return element.tagName;
                    }
                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element) {
                            return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                }
                return getXPath(arguments[0]);
            """, element)
        except:
            return ""
    
    def _get_css_selector(self, element) -> str:
        """Получение CSS селектора элемента (Selenium)"""
        try:
            if element.get_attribute("id"):
                return f"#{element.get_attribute('id')}"
            elif element.get_attribute("class"):
                classes = element.get_attribute("class").split()
                return f".{'.'.join(classes)}"
            else:
                return element.tag_name
        except:
            return ""
    
    def _calculate_complexity_score(self, dom_structure: Dict[str, Any]) -> float:
        """Расчет score сложности DOM"""
        try:
            total_elements = dom_structure.get("total_elements", 0)
            element_types = dom_structure.get("element_types", {})
            
            # Базовая сложность по количеству элементов
            complexity = min(total_elements / 100, 1.0)
            
            # Дополнительная сложность по разнообразию типов
            type_diversity = len(element_types) / 20  # Нормализация
            complexity += min(type_diversity, 0.5)
            
            return min(complexity, 1.0)
            
        except:
            return 0.0
    
    def _calculate_accessibility_score(self, accessibility_info: Dict[str, Any]) -> float:
        """Расчет score доступности"""
        try:
            aria_labels = len(accessibility_info.get("aria_labels", []))
            alt_texts = len(accessibility_info.get("alt_texts", []))
            
            # Базовый score
            score = 0.0
            
            # ARIA labels
            if aria_labels > 0:
                score += min(aria_labels / 10, 0.3)
            
            # Alt texts
            if alt_texts > 0:
                score += min(alt_texts / 20, 0.3)
            
            # Семантические элементы
            semantic_elements = len(accessibility_info.get("semantic_elements", []))
            if semantic_elements > 0:
                score += min(semantic_elements / 15, 0.4)
            
            return min(score, 1.0)
            
        except:
            return 0.0 