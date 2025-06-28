#!/usr/bin/env python3
"""
Скрипт для тестирования UX бота на проекте reLink
Запускает полный анализ пользовательского опыта и генерирует отчет
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к модулям UX бота
sys.path.append(str(Path(__file__).parent))

from app.core import UXBot
from app.config import settings
from app.models import TestScenario, TestResult
from app.services.browser_service import BrowserService, BrowserConfig
from app.services.scenario_service import ScenarioService, ScenarioContext
from app.services.api_client import APIClient

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ux_bot_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class UXBotTester:
    """Тестер UX бота для проекта reLink"""
    
    def __init__(self):
        self.ux_bot = None
        self.browser_service = None
        self.scenario_service = None
        self.api_client = None
        self.test_results = []
        
    async def setup(self):
        """Настройка компонентов для тестирования"""
        logger.info("Настройка компонентов UX бота...")
        
        # Конфигурация браузера
        browser_config = BrowserConfig(
            engine="selenium",
            headless=True,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport_width=1920,
            viewport_height=1080,
            wait_timeout=10,
            implicit_wait=5,
            additional_args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions"
            ]
        )
        
        # Инициализация сервисов
        self.browser_service = BrowserService(browser_config)
        self.scenario_service = ScenarioService()
        self.api_client = APIClient()
        
        # Инициализация UX бота
        self.ux_bot = UXBot(
            browser_service=self.browser_service,
            scenario_service=self.scenario_service,
            api_client=self.api_client
        )
        
        logger.info("Компоненты настроены успешно")
    
    async def test_frontend_analysis(self):
        """Тестирование анализа фронтенда"""
        logger.info("Начинаем анализ фронтенда reLink...")
        
        try:
            # Запуск сессии браузера
            session = await self.browser_service.start_session("frontend_test")
            
            # Анализ главной страницы
            await self.analyze_main_page()
            
            # Анализ страницы входа
            await self.analyze_login_page()
            
            # Анализ дашборда
            await self.analyze_dashboard()
            
            # Анализ страницы анализа доменов
            await self.analyze_domain_analysis_page()
            
            # Анализ страницы настроек
            await self.analyze_settings_page()
            
            logger.info("Анализ фронтенда завершен")
            
        except Exception as e:
            logger.error(f"Ошибка при анализе фронтенда: {e}")
            self.test_results.append({
                'test': 'frontend_analysis',
                'status': 'failed',
                'error': str(e)
            })
    
    async def analyze_main_page(self):
        """Анализ главной страницы"""
        logger.info("Анализируем главную страницу...")
        
        try:
            # Переход на главную страницу
            success = await self.browser_service.navigate_to(settings.frontend_url)
            if not success:
                raise Exception("Не удалось загрузить главную страницу")
            
            # Получение информации о странице
            title = await self.browser_service.get_page_title()
            current_url = await self.browser_service.get_current_url()
            
            logger.info(f"Загружена страница: {title} ({current_url})")
            
            # Поиск ключевых элементов
            elements_to_check = [
                ("header", ".header, header, .navbar, nav"),
                ("main_content", ".main, main, .content, .container"),
                ("footer", ".footer, footer"),
                ("navigation", ".nav, .navigation, .menu"),
                ("call_to_action", ".cta, .btn, button"),
                ("logo", ".logo, .brand, img[alt*='logo']"),
                ("search", "input[type='search'], .search, #search"),
                ("user_menu", ".user-menu, .profile, .account")
            ]
            
            found_elements = []
            missing_elements = []
            
            for element_name, selector in elements_to_check:
                element = await self.browser_service.find_element(selector)
                if element:
                    found_elements.append(element_name)
                    logger.info(f"✓ Найден элемент: {element_name}")
                else:
                    missing_elements.append(element_name)
                    logger.warning(f"✗ Не найден элемент: {element_name}")
            
            # Проверка доступности
            accessibility_issues = await self.check_accessibility()
            
            # Проверка отзывчивости
            responsiveness_issues = await self.check_responsiveness()
            
            # Создание скриншота
            screenshot_path = await self.browser_service.take_screenshot("main_page.png")
            
            # Анализ результатов
            analysis = {
                'page': 'main_page',
                'title': title,
                'url': current_url,
                'found_elements': found_elements,
                'missing_elements': missing_elements,
                'accessibility_issues': accessibility_issues,
                'responsiveness_issues': responsiveness_issues,
                'screenshot': screenshot_path
            }
            
            self.test_results.append({
                'test': 'main_page_analysis',
                'status': 'completed',
                'data': analysis
            })
            
            # Генерация рекомендаций
            await self.generate_recommendations(analysis)
            
        except Exception as e:
            logger.error(f"Ошибка при анализе главной страницы: {e}")
            self.test_results.append({
                'test': 'main_page_analysis',
                'status': 'failed',
                'error': str(e)
            })
    
    async def analyze_login_page(self):
        """Анализ страницы входа"""
        logger.info("Анализируем страницу входа...")
        
        try:
            # Переход на страницу входа
            login_url = f"{settings.frontend_url}/login"
            success = await self.browser_service.navigate_to(login_url)
            if not success:
                raise Exception("Не удалось загрузить страницу входа")
            
            # Поиск элементов формы входа
            login_elements = [
                ("username_field", "input[name='username'], input[type='email'], #username, .username-input"),
                ("password_field", "input[name='password'], input[type='password'], #password, .password-input"),
                ("login_button", "button[type='submit'], .login-btn, #login, input[type='submit']"),
                ("remember_me", "input[type='checkbox'], .remember-me"),
                ("forgot_password", "a[href*='forgot'], .forgot-password"),
                ("register_link", "a[href*='register'], .register-link")
            ]
            
            found_elements = []
            missing_elements = []
            
            for element_name, selector in login_elements:
                element = await self.browser_service.find_element(selector)
                if element:
                    found_elements.append(element_name)
                    logger.info(f"✓ Найден элемент входа: {element_name}")
                else:
                    missing_elements.append(element_name)
                    logger.warning(f"✗ Не найден элемент входа: {element_name}")
            
            # Тестирование валидации формы
            validation_issues = await self.test_form_validation()
            
            # Создание скриншота
            screenshot_path = await self.browser_service.take_screenshot("login_page.png")
            
            analysis = {
                'page': 'login_page',
                'found_elements': found_elements,
                'missing_elements': missing_elements,
                'validation_issues': validation_issues,
                'screenshot': screenshot_path
            }
            
            self.test_results.append({
                'test': 'login_page_analysis',
                'status': 'completed',
                'data': analysis
            })
            
        except Exception as e:
            logger.error(f"Ошибка при анализе страницы входа: {e}")
            self.test_results.append({
                'test': 'login_page_analysis',
                'status': 'failed',
                'error': str(e)
            })
    
    async def analyze_dashboard(self):
        """Анализ дашборда"""
        logger.info("Анализируем дашборд...")
        
        try:
            # Переход на дашборд
            dashboard_url = f"{settings.frontend_url}/dashboard"
            success = await self.browser_service.navigate_to(dashboard_url)
            if not success:
                logger.warning("Не удалось загрузить дашборд (возможно, требуется авторизация)")
                return
            
            # Поиск элементов дашборда
            dashboard_elements = [
                ("sidebar", ".sidebar, .nav-sidebar, .side-nav"),
                ("main_content", ".main-content, .dashboard-content"),
                ("stats_cards", ".stats-card, .metric-card, .stat-card"),
                ("charts", ".chart, .graph, canvas"),
                ("recent_activity", ".recent-activity, .activity-feed"),
                ("quick_actions", ".quick-actions, .action-buttons"),
                ("notifications", ".notifications, .alerts"),
                ("user_profile", ".user-profile, .profile-info")
            ]
            
            found_elements = []
            missing_elements = []
            
            for element_name, selector in dashboard_elements:
                element = await self.browser_service.find_element(selector)
                if element:
                    found_elements.append(element_name)
                    logger.info(f"✓ Найден элемент дашборда: {element_name}")
                else:
                    missing_elements.append(element_name)
                    logger.warning(f"✗ Не найден элемент дашборда: {element_name}")
            
            # Создание скриншота
            screenshot_path = await self.browser_service.take_screenshot("dashboard.png")
            
            analysis = {
                'page': 'dashboard',
                'found_elements': found_elements,
                'missing_elements': missing_elements,
                'screenshot': screenshot_path
            }
            
            self.test_results.append({
                'test': 'dashboard_analysis',
                'status': 'completed',
                'data': analysis
            })
            
        except Exception as e:
            logger.error(f"Ошибка при анализе дашборда: {e}")
            self.test_results.append({
                'test': 'dashboard_analysis',
                'status': 'failed',
                'error': str(e)
            })
    
    async def analyze_domain_analysis_page(self):
        """Анализ страницы анализа доменов"""
        logger.info("Анализируем страницу анализа доменов...")
        
        try:
            # Переход на страницу анализа
            analysis_url = f"{settings.frontend_url}/analysis"
            success = await self.browser_service.navigate_to(analysis_url)
            if not success:
                logger.warning("Не удалось загрузить страницу анализа доменов")
                return
            
            # Поиск элементов анализа
            analysis_elements = [
                ("domain_input", "input[name='domain'], #domain, .domain-input"),
                ("analyze_button", "button[type='submit'], .analyze-btn, #analyze"),
                ("results_section", ".results, .analysis-results, .output"),
                ("progress_indicator", ".progress, .loading, .spinner"),
                ("export_button", ".export-btn, .download-btn, button[data-action='export']"),
                ("history_section", ".history, .previous-analyses"),
                ("filters", ".filters, .filter-controls"),
                ("comparison_tools", ".compare, .comparison-tools")
            ]
            
            found_elements = []
            missing_elements = []
            
            for element_name, selector in analysis_elements:
                element = await self.browser_service.find_element(selector)
                if element:
                    found_elements.append(element_name)
                    logger.info(f"✓ Найден элемент анализа: {element_name}")
                else:
                    missing_elements.append(element_name)
                    logger.warning(f"✗ Не найден элемент анализа: {element_name}")
            
            # Создание скриншота
            screenshot_path = await self.browser_service.take_screenshot("domain_analysis.png")
            
            analysis = {
                'page': 'domain_analysis',
                'found_elements': found_elements,
                'missing_elements': missing_elements,
                'screenshot': screenshot_path
            }
            
            self.test_results.append({
                'test': 'domain_analysis_analysis',
                'status': 'completed',
                'data': analysis
            })
            
        except Exception as e:
            logger.error(f"Ошибка при анализе страницы анализа доменов: {e}")
            self.test_results.append({
                'test': 'domain_analysis_analysis',
                'status': 'failed',
                'error': str(e)
            })
    
    async def analyze_settings_page(self):
        """Анализ страницы настроек"""
        logger.info("Анализируем страницу настроек...")
        
        try:
            # Переход на страницу настроек
            settings_url = f"{settings.frontend_url}/settings"
            success = await self.browser_service.navigate_to(settings_url)
            if not success:
                logger.warning("Не удалось загрузить страницу настроек")
                return
            
            # Поиск элементов настроек
            settings_elements = [
                ("profile_section", ".profile-settings, .user-settings"),
                ("preferences", ".preferences, .user-preferences"),
                ("security_settings", ".security, .password-settings"),
                ("notifications", ".notifications-settings"),
                ("theme_selector", ".theme-selector, .dark-mode-toggle"),
                ("language_selector", ".language-selector, .locale-selector"),
                ("save_button", ".save-settings, button[type='submit']"),
                ("cancel_button", ".cancel, .reset-settings")
            ]
            
            found_elements = []
            missing_elements = []
            
            for element_name, selector in settings_elements:
                element = await self.browser_service.find_element(selector)
                if element:
                    found_elements.append(element_name)
                    logger.info(f"✓ Найден элемент настроек: {element_name}")
                else:
                    missing_elements.append(element_name)
                    logger.warning(f"✗ Не найден элемент настроек: {element_name}")
            
            # Создание скриншота
            screenshot_path = await self.browser_service.take_screenshot("settings_page.png")
            
            analysis = {
                'page': 'settings',
                'found_elements': found_elements,
                'missing_elements': missing_elements,
                'screenshot': screenshot_path
            }
            
            self.test_results.append({
                'test': 'settings_page_analysis',
                'status': 'completed',
                'data': analysis
            })
            
        except Exception as e:
            logger.error(f"Ошибка при анализе страницы настроек: {e}")
            self.test_results.append({
                'test': 'settings_page_analysis',
                'status': 'failed',
                'error': str(e)
            })
    
    async def check_accessibility(self):
        """Проверка доступности"""
        logger.info("Проверяем доступность...")
        
        issues = []
        
        try:
            # Проверка ARIA атрибутов
            aria_elements = await self.browser_service.execute_script("""
                return document.querySelectorAll('[aria-*]');
            """)
            
            if aria_elements:
                logger.info(f"Найдено {len(aria_elements)} элементов с ARIA атрибутами")
            else:
                issues.append("Отсутствуют ARIA атрибуты для доступности")
            
            # Проверка семантических тегов
            semantic_tags = await self.browser_service.execute_script("""
                return {
                    'main': document.querySelectorAll('main').length,
                    'nav': document.querySelectorAll('nav').length,
                    'header': document.querySelectorAll('header').length,
                    'footer': document.querySelectorAll('footer').length,
                    'section': document.querySelectorAll('section').length,
                    'article': document.querySelectorAll('article').length,
                    'aside': document.querySelectorAll('aside').length
                };
            """)
            
            logger.info(f"Семантические теги: {semantic_tags}")
            
            # Проверка alt атрибутов для изображений
            images_without_alt = await self.browser_service.execute_script("""
                return document.querySelectorAll('img:not([alt])').length;
            """)
            
            if images_without_alt > 0:
                issues.append(f"Найдено {images_without_alt} изображений без alt атрибутов")
            
            # Проверка контрастности (базовая)
            contrast_issues = await self.browser_service.execute_script("""
                // Базовая проверка контрастности
                const elements = document.querySelectorAll('*');
                const lowContrastElements = [];
                
                for (let el of elements) {
                    const style = window.getComputedStyle(el);
                    const color = style.color;
                    const backgroundColor = style.backgroundColor;
                    
                    // Простая проверка на белый текст на белом фоне
                    if (color === 'rgb(255, 255, 255)' && backgroundColor === 'rgb(255, 255, 255)') {
                        lowContrastElements.push(el.tagName);
                    }
                }
                
                return lowContrastElements.length;
            """)
            
            if contrast_issues > 0:
                issues.append(f"Возможные проблемы с контрастностью: {contrast_issues} элементов")
            
        except Exception as e:
            logger.error(f"Ошибка при проверке доступности: {e}")
            issues.append(f"Ошибка проверки доступности: {str(e)}")
        
        return issues
    
    async def check_responsiveness(self):
        """Проверка отзывчивости"""
        logger.info("Проверяем отзывчивость...")
        
        issues = []
        
        try:
            # Тестирование на разных размерах экрана
            screen_sizes = [
                (1920, 1080, "desktop"),
                (1366, 768, "laptop"),
                (768, 1024, "tablet"),
                (375, 667, "mobile")
            ]
            
            for width, height, device in screen_sizes:
                await self.browser_service.execute_script(f"""
                    window.resizeTo({width}, {height});
                """)
                
                await asyncio.sleep(1)
                
                # Проверка переполнения элементов
                overflow_issues = await self.browser_service.execute_script(f"""
                    const elements = document.querySelectorAll('*');
                    const overflowElements = [];
                    
                    for (let el of elements) {{
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        
                        // Проверка на выход за границы экрана
                        if (rect.right > {width} || rect.bottom > {height}) {{
                            overflowElements.push({{
                                tag: el.tagName,
                                class: el.className,
                                right: rect.right,
                                bottom: rect.bottom
                            }});
                        }}
                    }}
                    
                    return overflowElements;
                """)
                
                if overflow_issues:
                    issues.append(f"Проблемы отзывчивости на {device}: {len(overflow_issues)} элементов выходят за границы")
                
                logger.info(f"Проверка {device} ({width}x{height}): {'OK' if not overflow_issues else 'ISSUES'}")
            
        except Exception as e:
            logger.error(f"Ошибка при проверке отзывчивости: {e}")
            issues.append(f"Ошибка проверки отзывчивости: {str(e)}")
        
        return issues
    
    async def test_form_validation(self):
        """Тестирование валидации форм"""
        logger.info("Тестируем валидацию форм...")
        
        issues = []
        
        try:
            # Поиск форм на странице
            forms = await self.browser_service.execute_script("""
                return document.querySelectorAll('form');
            """)
            
            if not forms:
                logger.info("Формы не найдены на странице")
                return issues
            
            logger.info(f"Найдено {len(forms)} форм")
            
            # Проверка обязательных полей
            required_fields = await self.browser_service.execute_script("""
                return document.querySelectorAll('input[required], select[required], textarea[required]');
            """)
            
            logger.info(f"Найдено {len(required_fields)} обязательных полей")
            
            # Проверка валидации email
            email_fields = await self.browser_service.execute_script("""
                return document.querySelectorAll('input[type="email"]');
            """)
            
            if email_fields:
                logger.info(f"Найдено {len(email_fields)} полей email")
                
                # Тестирование невалидного email
                for i, field in enumerate(email_fields):
                    await self.browser_service.execute_script(f"""
                        const field = document.querySelectorAll('input[type="email"]')[{i}];
                        field.value = 'invalid-email';
                        field.dispatchEvent(new Event('blur'));
                    """)
                    
                    await asyncio.sleep(0.5)
                    
                    # Проверка сообщения об ошибке
                    error_message = await self.browser_service.execute_script(f"""
                        const field = document.querySelectorAll('input[type="email"]')[{i}];
                        const errorElement = field.parentNode.querySelector('.error, .invalid-feedback, [role="alert"]');
                        return errorElement ? errorElement.textContent : null;
                    """)
                    
                    if not error_message:
                        issues.append(f"Отсутствует валидация для поля email #{i+1}")
            
        except Exception as e:
            logger.error(f"Ошибка при тестировании валидации форм: {e}")
            issues.append(f"Ошибка тестирования валидации: {str(e)}")
        
        return issues
    
    async def generate_recommendations(self, analysis):
        """Генерация рекомендаций на основе анализа"""
        logger.info("Генерируем рекомендации...")
        
        recommendations = []
        
        # Анализ отсутствующих элементов
        if analysis.get('missing_elements'):
            for element in analysis['missing_elements']:
                if element == 'header':
                    recommendations.append({
                        'priority': 'high',
                        'category': 'navigation',
                        'issue': 'Отсутствует заголовок страницы',
                        'solution': 'Добавить семантический тег <header> с навигацией и логотипом',
                        'code_example': '''
<header class="bg-white shadow-sm">
  <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between h-16">
      <div class="flex items-center">
        <img class="h-8 w-auto" src="/logo.svg" alt="reLink Logo">
      </div>
      <div class="flex items-center space-x-4">
        <a href="/dashboard" class="text-gray-700 hover:text-gray-900">Dashboard</a>
        <a href="/analysis" class="text-gray-700 hover:text-gray-900">Analysis</a>
      </div>
    </div>
  </nav>
</header>
                        '''
                    })
                elif element == 'main_content':
                    recommendations.append({
                        'priority': 'critical',
                        'category': 'content',
                        'issue': 'Отсутствует основное содержимое',
                        'solution': 'Добавить семантический тег <main> с основным контентом страницы',
                        'code_example': '''
<main class="flex-1">
  <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
    <!-- Основной контент страницы -->
  </div>
</main>
                        '''
                    })
                elif element == 'call_to_action':
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'conversion',
                        'issue': 'Отсутствуют призывы к действию',
                        'solution': 'Добавить кнопки CTA для основных действий пользователя',
                        'code_example': '''
<button class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Начать анализ
</button>
                        '''
                    })
        
        # Анализ проблем доступности
        if analysis.get('accessibility_issues'):
            for issue in analysis['accessibility_issues']:
                if 'ARIA' in issue:
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'accessibility',
                        'issue': 'Отсутствуют ARIA атрибуты',
                        'solution': 'Добавить ARIA атрибуты для улучшения доступности',
                        'code_example': '''
<button aria-label="Закрыть модальное окно" class="close-btn">
  <span aria-hidden="true">&times;</span>
</button>
                        '''
                    })
                elif 'alt' in issue:
                    recommendations.append({
                        'priority': 'medium',
                        'category': 'accessibility',
                        'issue': 'Изображения без alt атрибутов',
                        'solution': 'Добавить описательные alt атрибуты для всех изображений',
                        'code_example': '''
<img src="/hero-image.jpg" alt="Анализ SEO показателей домена" class="hero-image">
                        '''
                    })
        
        # Анализ проблем отзывчивости
        if analysis.get('responsiveness_issues'):
            for issue in analysis['responsiveness_issues']:
                recommendations.append({
                    'priority': 'high',
                    'category': 'responsive',
                    'issue': 'Проблемы с отзывчивостью',
                    'solution': 'Использовать CSS Grid и Flexbox для адаптивной верстки',
                    'code_example': '''
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <div class="bg-white p-4 rounded-lg shadow">
    <!-- Карточка контента -->
  </div>
</div>
                        '''
                })
        
        # Сохранение рекомендаций
        analysis['recommendations'] = recommendations
        
        # Вывод рекомендаций
        if recommendations:
            logger.info(f"Сгенерировано {len(recommendations)} рекомендаций:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"{i}. [{rec['priority'].upper()}] {rec['issue']}")
                logger.info(f"   Решение: {rec['solution']}")
    
    async def run_user_scenarios(self):
        """Запуск пользовательских сценариев"""
        logger.info("Запускаем пользовательские сценарии...")
        
        try:
            # Получение доступных сценариев
            scenarios = self.scenario_service.list_scenarios()
            logger.info(f"Доступно сценариев: {len(scenarios)}")
            
            # Выполнение ключевых сценариев
            key_scenarios = ['login_flow', 'domain_analysis', 'settings_management']
            
            for scenario_id in key_scenarios:
                scenario = self.scenario_service.get_scenario(scenario_id)
                if scenario:
                    logger.info(f"Выполняем сценарий: {scenario.name}")
                    
                    # Создание контекста для сценария
                    context = ScenarioContext(
                        scenario_id=scenario_id,
                        session_id=f"scenario_{scenario_id}",
                        variables=scenario.variables,
                        results=[],
                        start_time=asyncio.get_event_loop().time(),
                        browser_service=self.browser_service,
                        api_client=self.api_client
                    )
                    
                    # Выполнение сценария
                    results = await self.scenario_service.execute_scenario(scenario_id, context)
                    
                    # Анализ результатов
                    success_count = sum(1 for r in results if r.success)
                    total_count = len(results)
                    
                    logger.info(f"Сценарий {scenario.name}: {success_count}/{total_count} шагов выполнено успешно")
                    
                    self.test_results.append({
                        'test': f'scenario_{scenario_id}',
                        'status': 'completed' if success_count == total_count else 'partial',
                        'data': {
                            'scenario_name': scenario.name,
                            'total_steps': total_count,
                            'successful_steps': success_count,
                            'results': results
                        }
                    })
                else:
                    logger.warning(f"Сценарий {scenario_id} не найден")
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении пользовательских сценариев: {e}")
            self.test_results.append({
                'test': 'user_scenarios',
                'status': 'failed',
                'error': str(e)
            })
    
    async def generate_final_report(self):
        """Генерация финального отчета"""
        logger.info("Генерируем финальный отчет...")
        
        # Статистика тестов
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r['status'] == 'completed')
        failed_tests = sum(1 for r in self.test_results if r['status'] == 'failed')
        partial_tests = sum(1 for r in self.test_results if r['status'] == 'partial')
        
        # Сбор всех проблем
        all_issues = []
        all_recommendations = []
        
        for result in self.test_results:
            if result['status'] == 'completed' and 'data' in result:
                data = result['data']
                
                # Проблемы доступности
                if 'accessibility_issues' in data:
                    all_issues.extend(data['accessibility_issues'])
                
                # Проблемы отзывчивости
                if 'responsiveness_issues' in data:
                    all_issues.extend(data['responsiveness_issues'])
                
                # Проблемы валидации
                if 'validation_issues' in data:
                    all_issues.extend(data['validation_issues'])
                
                # Рекомендации
                if 'recommendations' in data:
                    all_recommendations.extend(data['recommendations'])
                
                # Отсутствующие элементы
                if 'missing_elements' in data:
                    for element in data['missing_elements']:
                        all_issues.append(f"Отсутствует элемент: {element}")
        
        # Создание отчета
        report = {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'partial_tests': partial_tests,
                'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'issues': {
                'total_issues': len(all_issues),
                'accessibility_issues': len([i for i in all_issues if 'доступность' in i.lower() or 'aria' in i.lower()]),
                'responsiveness_issues': len([i for i in all_issues if 'отзывчивость' in i.lower()]),
                'validation_issues': len([i for i in all_issues if 'валидация' in i.lower()]),
                'missing_elements': len([i for i in all_issues if 'отсутствует' in i.lower()])
            },
            'recommendations': {
                'total_recommendations': len(all_recommendations),
                'critical': len([r for r in all_recommendations if r['priority'] == 'critical']),
                'high': len([r for r in all_recommendations if r['priority'] == 'high']),
                'medium': len([r for r in all_recommendations if r['priority'] == 'medium']),
                'low': len([r for r in all_recommendations if r['priority'] == 'low'])
            },
            'detailed_results': self.test_results,
            'all_issues': all_issues,
            'all_recommendations': all_recommendations
        }
        
        # Сохранение отчета
        import json
        with open('ux_bot_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Вывод краткого отчета
        logger.info("=" * 60)
        logger.info("ОТЧЕТ UX БОТА")
        logger.info("=" * 60)
        logger.info(f"Всего тестов: {total_tests}")
        logger.info(f"Успешных: {successful_tests}")
        logger.info(f"Частично успешных: {partial_tests}")
        logger.info(f"Неудачных: {failed_tests}")
        logger.info(f"Процент успеха: {report['summary']['success_rate']:.1f}%")
        logger.info("")
        logger.info(f"Найдено проблем: {report['issues']['total_issues']}")
        logger.info(f"Сгенерировано рекомендаций: {report['recommendations']['total_recommendations']}")
        logger.info("")
        
        if all_recommendations:
            logger.info("КРИТИЧЕСКИЕ РЕКОМЕНДАЦИИ:")
            critical_recs = [r for r in all_recommendations if r['priority'] == 'critical']
            for rec in critical_recs[:3]:  # Показываем топ-3
                logger.info(f"• {rec['issue']}")
                logger.info(f"  Решение: {rec['solution']}")
                logger.info("")
        
        logger.info("Полный отчет сохранен в файл: ux_bot_report.json")
        logger.info("=" * 60)
        
        return report
    
    async def cleanup(self):
        """Очистка ресурсов"""
        logger.info("Очистка ресурсов...")
        
        if self.browser_service:
            await self.browser_service.close_session()
        
        logger.info("Очистка завершена")


async def main():
    """Главная функция тестирования"""
    tester = UXBotTester()
    
    try:
        # Настройка
        await tester.setup()
        
        # Тестирование фронтенда
        await tester.test_frontend_analysis()
        
        # Запуск пользовательских сценариев
        await tester.run_user_scenarios()
        
        # Генерация отчета
        report = await tester.generate_final_report()
        
        return report
        
    except Exception as e:
        logger.error(f"Критическая ошибка при тестировании: {e}")
        return None
        
    finally:
        # Очистка
        await tester.cleanup()


if __name__ == "__main__":
    # Запуск тестирования
    report = asyncio.run(main())
    
    if report:
        print("\n✅ Тестирование UX бота завершено успешно!")
        print(f"📊 Процент успеха: {report['summary']['success_rate']:.1f}%")
        print(f"🐛 Найдено проблем: {report['issues']['total_issues']}")
        print(f"💡 Рекомендаций: {report['recommendations']['total_recommendations']}")
    else:
        print("\n❌ Тестирование UX бота завершилось с ошибкой!")
        sys.exit(1) 