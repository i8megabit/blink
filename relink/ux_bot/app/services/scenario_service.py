"""
Сервис управления сценариями тестирования UX
Создает и выполняет пользовательские сценарии для тестирования интерфейса
"""

import asyncio
import json
import random
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging
from datetime import datetime

from ..models import TestScenario, TestStep, TestResult, UserProfile, TestStatus, Issue, IssueSeverity, ScenarioType, UserAction
from ..services.browser_service import BrowserService
from ..api_client import APIClient
from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class ScenarioContext:
    """Контекст выполнения сценария"""
    scenario_id: str
    session_id: str
    variables: Dict[str, Any]
    results: List[TestResult]
    start_time: float
    browser_service: BrowserService
    api_client: APIClient
    user_profile: Optional[UserProfile] = None


class ScenarioService:
    """Сервис для управления и выполнения сценариев тестирования UX"""
    
    def __init__(self):
        self.scenarios: Dict[str, TestScenario] = {}
        self.custom_actions: Dict[str, Callable] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self._load_builtin_scenarios()
        self._register_custom_actions()
        self._initialize_user_profiles()
    
    def _load_builtin_scenarios(self):
        """Загрузка встроенных сценариев"""
        self.scenarios.update({
            "login_flow": self._create_login_scenario(),
            "domain_analysis": self._create_domain_analysis_scenario(),
            "benchmark_comparison": self._create_benchmark_scenario(),
            "settings_management": self._create_settings_scenario(),
            "export_functionality": self._create_export_scenario(),
            "full_user_journey": self._create_full_journey_scenario(),
            "ux_bot_self_test": self._create_ux_bot_self_test_scenario()
        })
    
    def _create_login_scenario(self) -> TestScenario:
        """Создание сценария входа в систему"""
        return TestScenario(
            id="login_flow",
            name="Тестирование входа в систему",
            description="Полный цикл входа пользователя в систему reLink",
            type=ScenarioType.AUTHENTICATION,
            steps=[
                TestStep(
                    id="navigate_to_login",
                    name="Переход на страницу входа",
                    action=UserAction(
                        type="navigate",
                        target="login_page",
                        data={"url": f"{settings.frontend_url}/login"}
                    ),
                    expected_result="Страница входа загружена",
                    timeout=10
                ),
                TestStep(
                    id="fill_username",
                    name="Ввод имени пользователя",
                    action=UserAction(
                        type="type_text",
                        target="username_field",
                        data={
                            "selector": "#username",
                            "text": "{{username}}"
                        }
                    ),
                    expected_result="Поле имени пользователя заполнено",
                    timeout=5
                ),
                TestStep(
                    id="fill_password",
                    name="Ввод пароля",
                    action=UserAction(
                        type="type_text",
                        target="password_field",
                        data={
                            "selector": "#password",
                            "text": "{{password}}"
                        }
                    ),
                    expected_result="Поле пароля заполнено",
                    timeout=5
                ),
                TestStep(
                    id="click_login_button",
                    name="Нажатие кнопки входа",
                    action=UserAction(
                        type="click",
                        target="login_button",
                        data={"selector": "button[type='submit']"}
                    ),
                    expected_result="Кнопка входа нажата",
                    timeout=5
                ),
                TestStep(
                    id="wait_for_dashboard",
                    name="Ожидание загрузки дашборда",
                    action=UserAction(
                        type="wait_for_element",
                        target="dashboard",
                        data={"selector": ".dashboard", "timeout": 15}
                    ),
                    expected_result="Дашборд загружен",
                    timeout=15
                )
            ],
            variables={
                "username": "test_user",
                "password": "test_password"
            }
        )
    
    def _create_domain_analysis_scenario(self) -> TestScenario:
        """Создание сценария анализа домена"""
        return TestScenario(
            id="domain_analysis",
            name="Тестирование анализа домена",
            description="Полный цикл анализа домена в системе reLink",
            type=ScenarioType.FUNCTIONAL,
            steps=[
                TestStep(
                    id="navigate_to_dashboard",
                    name="Переход на дашборд",
                    action=UserAction(
                        type="navigate",
                        target="dashboard",
                        data={"url": f"{settings.frontend_url}/dashboard"}
                    ),
                    expected_result="Дашборд загружен",
                    timeout=10
                ),
                TestStep(
                    id="click_add_domain",
                    name="Нажатие кнопки добавления домена",
                    action=UserAction(
                        type="click",
                        target="add_domain_button",
                        data={"selector": ".add-domain-btn"}
                    ),
                    expected_result="Модальное окно добавления домена открыто",
                    timeout=5
                ),
                TestStep(
                    id="fill_domain_name",
                    name="Ввод названия домена",
                    action=UserAction(
                        type="type_text",
                        target="domain_input",
                        data={
                            "selector": "#domain-input",
                            "text": "{{domain_name}}"
                        }
                    ),
                    expected_result="Поле домена заполнено",
                    timeout=5
                ),
                TestStep(
                    id="click_analyze_button",
                    name="Нажатие кнопки анализа",
                    action=UserAction(
                        type="click",
                        target="analyze_button",
                        data={"selector": ".analyze-btn"}
                    ),
                    expected_result="Анализ запущен",
                    timeout=5
                ),
                TestStep(
                    id="wait_for_analysis_complete",
                    name="Ожидание завершения анализа",
                    action=UserAction(
                        type="wait_for_element",
                        target="analysis_results",
                        data={"selector": ".analysis-results", "timeout": 60}
                    ),
                    expected_result="Результаты анализа отображены",
                    timeout=60
                ),
                TestStep(
                    id="verify_analysis_data",
                    name="Проверка данных анализа",
                    action=UserAction(
                        type="custom",
                        target="verify_analysis",
                        data={"custom_action": "verify_analysis_data"}
                    ),
                    expected_result="Данные анализа корректны",
                    timeout=10
                )
            ],
            variables={
                "domain_name": "example.com"
            }
        )
    
    def _create_benchmark_scenario(self) -> TestScenario:
        """Создание сценария сравнения бенчмарков"""
        return TestScenario(
            id="benchmark_comparison",
            name="Тестирование сравнения бенчмарков",
            description="Тестирование функционала сравнения доменов",
            type=ScenarioType.FUNCTIONAL,
            steps=[
                TestStep(
                    id="navigate_to_benchmarks",
                    name="Переход на страницу бенчмарков",
                    action=UserAction(
                        type="navigate",
                        target="benchmarks_page",
                        data={"url": f"{settings.frontend_url}/benchmarks"}
                    ),
                    expected_result="Страница бенчмарков загружена",
                    timeout=10
                ),
                TestStep(
                    id="select_domains",
                    name="Выбор доменов для сравнения",
                    action=UserAction(
                        type="custom",
                        target="select_domains",
                        data={"custom_action": "select_benchmark_domains"}
                    ),
                    expected_result="Домены выбраны",
                    timeout=10
                ),
                TestStep(
                    id="click_compare_button",
                    name="Нажатие кнопки сравнения",
                    action=UserAction(
                        type="click",
                        target="compare_button",
                        data={"selector": ".compare-btn"}
                    ),
                    expected_result="Сравнение запущено",
                    timeout=5
                ),
                TestStep(
                    id="wait_for_comparison_results",
                    name="Ожидание результатов сравнения",
                    action=UserAction(
                        type="wait_for_element",
                        target="comparison_results",
                        data={"selector": ".comparison-results", "timeout": 30}
                    ),
                    expected_result="Результаты сравнения отображены",
                    timeout=30
                )
            ],
            variables={}
        )
    
    def _create_settings_scenario(self) -> TestScenario:
        """Создание сценария управления настройками"""
        return TestScenario(
            id="settings_management",
            name="Тестирование управления настройками",
            description="Тестирование функционала настроек пользователя",
            type=ScenarioType.FUNCTIONAL,
            steps=[
                TestStep(
                    id="navigate_to_settings",
                    name="Переход в настройки",
                    action=UserAction(
                        type="navigate",
                        target="settings_page",
                        data={"url": f"{settings.frontend_url}/settings"}
                    ),
                    expected_result="Страница настроек загружена",
                    timeout=10
                ),
                TestStep(
                    id="change_theme",
                    name="Изменение темы",
                    action=UserAction(
                        type="click",
                        target="theme_selector",
                        data={"selector": ".theme-selector"}
                    ),
                    expected_result="Тема изменена",
                    timeout=5
                ),
                TestStep(
                    id="save_settings",
                    name="Сохранение настроек",
                    action=UserAction(
                        type="click",
                        target="save_button",
                        data={"selector": ".save-settings-btn"}
                    ),
                    expected_result="Настройки сохранены",
                    timeout=5
                )
            ],
            variables={}
        )
    
    def _create_export_scenario(self) -> TestScenario:
        """Создание сценария экспорта данных"""
        return TestScenario(
            id="export_functionality",
            name="Тестирование экспорта данных",
            description="Тестирование функционала экспорта результатов",
            type=ScenarioType.FUNCTIONAL,
            steps=[
                TestStep(
                    id="navigate_to_results",
                    name="Переход к результатам",
                    action=UserAction(
                        type="navigate",
                        target="results_page",
                        data={"url": f"{settings.frontend_url}/results"}
                    ),
                    expected_result="Страница результатов загружена",
                    timeout=10
                ),
                TestStep(
                    id="select_export_format",
                    name="Выбор формата экспорта",
                    action=UserAction(
                        type="click",
                        target="export_format",
                        data={"selector": ".export-format-selector"}
                    ),
                    expected_result="Формат экспорта выбран",
                    timeout=5
                ),
                TestStep(
                    id="click_export_button",
                    name="Нажатие кнопки экспорта",
                    action=UserAction(
                        type="click",
                        target="export_button",
                        data={"selector": ".export-btn"}
                    ),
                    expected_result="Экспорт запущен",
                    timeout=5
                ),
                TestStep(
                    id="wait_for_download",
                    name="Ожидание загрузки файла",
                    action=UserAction(
                        type="custom",
                        target="wait_download",
                        data={"custom_action": "wait_for_file_download"}
                    ),
                    expected_result="Файл загружен",
                    timeout=30
                )
            ],
            variables={}
        )
    
    def _create_full_journey_scenario(self) -> TestScenario:
        """Создание полного пользовательского сценария"""
        return TestScenario(
            id="full_user_journey",
            name="Полный пользовательский сценарий",
            description="Полный цикл использования системы reLink",
            type=ScenarioType.END_TO_END,
            steps=[
                # Вход в систему
                TestStep(
                    id="login",
                    name="Вход в систему",
                    action=UserAction(
                        type="custom",
                        target="login_flow",
                        data={"custom_action": "execute_login_flow"}
                    ),
                    expected_result="Пользователь вошел в систему",
                    timeout=30
                ),
                # Добавление домена
                TestStep(
                    id="add_domain",
                    name="Добавление домена",
                    action=UserAction(
                        type="custom",
                        target="add_domain_flow",
                        data={"custom_action": "execute_add_domain_flow"}
                    ),
                    expected_result="Домен добавлен и проанализирован",
                    timeout=120
                ),
                # Просмотр результатов
                TestStep(
                    id="view_results",
                    name="Просмотр результатов",
                    action=UserAction(
                        type="custom",
                        target="view_results_flow",
                        data={"custom_action": "execute_view_results_flow"}
                    ),
                    expected_result="Результаты отображены",
                    timeout=30
                ),
                # Экспорт данных
                TestStep(
                    id="export_data",
                    name="Экспорт данных",
                    action=UserAction(
                        type="custom",
                        target="export_flow",
                        data={"custom_action": "execute_export_flow"}
                    ),
                    expected_result="Данные экспортированы",
                    timeout=60
                )
            ],
            variables={
                "username": "test_user",
                "password": "test_password",
                "domain_name": "example.com"
            }
        )
    
    def _create_ux_bot_self_test_scenario(self) -> TestScenario:
        """Создание сценария тестирования собственной интеграции UX-бота"""
        return TestScenario(
            id="ux_bot_self_test",
            name="UX-бот тестирует свою интеграцию",
            description="Комплексный тест: UX-бот находит страницу Testing, тестирует свой функционал и проверяет интеграцию",
            priority="critical",
            steps=[
                TestStep(
                    id="navigate_to_testing",
                    name="Переход на страницу Testing",
                    description="Найти и перейти на страницу с тестированием",
                    action=UserAction(
                        type="navigate",
                        target="testing_page",
                        data={"url": "http://localhost:3000/testing"}
                    ),
                    expected_result="Страница Testing загружена"
                ),
                TestStep(
                    id="find_ux_bot_section",
                    name="Поиск раздела UX-бота",
                    description="Найти раздел или вкладку, связанную с UX-ботом",
                    action=UserAction(
                        type="find_element",
                        target="ux_bot_section",
                        data={"selector": "[data-testid='ux-bot'], .ux-bot, [aria-label*='UX'], [aria-label*='Bot']"}
                    ),
                    expected_result="Найден раздел UX-бота"
                ),
                TestStep(
                    id="click_ux_bot_tab",
                    name="Клик по вкладке UX-бота",
                    description="Открыть вкладку с функционалом UX-бота",
                    action=UserAction(
                        type="click",
                        target="ux_bot_tab",
                        data={"selector": "[data-testid='ux-bot-tab'], .ux-bot-tab, [aria-label*='UX Bot']"}
                    ),
                    expected_result="Вкладка UX-бота открыта"
                ),
                TestStep(
                    id="check_ux_bot_controls",
                    name="Проверка элементов управления",
                    description="Найти кнопки запуска, остановки и настройки UX-бота",
                    action=UserAction(
                        type="find_elements",
                        target="ux_bot_controls",
                        data={"selectors": ["button[aria-label*='Start'], button[aria-label*='Run'], button[aria-label*='Launch']", "button[aria-label*='Stop'], button[aria-label*='Cancel']", "button[aria-label*='Settings'], button[aria-label*='Configure']"]}
                    ),
                    expected_result="Найдены элементы управления UX-ботом"
                ),
                TestStep(
                    id="start_ux_bot_test",
                    name="Запуск теста UX-бота",
                    description="Запустить тестирование через UX-бота",
                    action=UserAction(
                        type="click",
                        target="start_ux_bot_test",
                        data={"selector": "button[aria-label*='Start'], button[aria-label*='Run'], button[aria-label*='Launch']"}
                    ),
                    expected_result="Тест UX-бота запущен"
                ),
                TestStep(
                    id="wait_for_test_progress",
                    name="Ожидание прогресса теста",
                    description="Дождаться начала выполнения теста",
                    action=UserAction(
                        type="wait",
                        target="wait_for_test_progress",
                        data={"timeout": 5}
                    ),
                    expected_result="Тест начал выполняться"
                ),
                TestStep(
                    id="check_test_status",
                    name="Проверка статуса теста",
                    description="Проверить статус выполнения теста",
                    action=UserAction(
                        type="find_element",
                        target="test_status",
                        data={"selector": "[data-testid='test-status'], .test-status, [aria-label*='Status']"}
                    ),
                    expected_result="Статус теста отображается"
                ),
                TestStep(
                    id="wait_for_completion",
                    name="Ожидание завершения",
                    description="Дождаться завершения теста",
                    action=UserAction(
                        type="wait",
                        target="wait_for_completion",
                        data={"timeout": 30}
                    ),
                    expected_result="Тест завершен"
                ),
                TestStep(
                    id="check_results",
                    name="Проверка результатов",
                    description="Проверить результаты тестирования",
                    action=UserAction(
                        type="find_element",
                        target="test_results",
                        data={"selector": "[data-testid='test-results'], .test-results, [aria-label*='Results']"}
                    ),
                    expected_result="Результаты теста отображаются"
                ),
                TestStep(
                    id="analyze_logs",
                    name="Анализ логов",
                    description="Проверить логи выполнения теста",
                    action=UserAction(
                        type="find_element",
                        target="test_logs",
                        data={"selector": "[data-testid='test-logs'], .test-logs, [aria-label*='Logs']"}
                    ),
                    expected_result="Логи теста доступны"
                ),
                TestStep(
                    id="check_metrics",
                    name="Проверка метрик",
                    description="Проверить метрики производительности",
                    action=UserAction(
                        type="find_element",
                        target="test_metrics",
                        data={"selector": "[data-testid='test-metrics'], .test-metrics, [aria-label*='Metrics']"}
                    ),
                    expected_result="Метрики отображаются"
                ),
                TestStep(
                    id="export_results",
                    name="Экспорт результатов",
                    description="Попытаться экспортировать результаты теста",
                    action=UserAction(
                        type="click",
                        target="export_results",
                        data={"selector": "button[aria-label*='Export'], button[aria-label*='Download'], button[aria-label*='Save']"}
                    ),
                    expected_result="Экспорт результатов доступен"
                )
            ]
        )
    
    def _register_custom_actions(self):
        """Регистрация пользовательских действий"""
        self.custom_actions.update({
            "verify_analysis_data": self._verify_analysis_data,
            "select_benchmark_domains": self._select_benchmark_domains,
            "wait_for_file_download": self._wait_for_file_download,
            "execute_login_flow": self._execute_login_flow,
            "execute_add_domain_flow": self._execute_add_domain_flow,
            "execute_view_results_flow": self._execute_view_results_flow,
            "execute_export_flow": self._execute_export_flow
        })
    
    async def execute_scenario(self, scenario_id: str, context: ScenarioContext) -> List[TestResult]:
        """Выполнение сценария"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Сценарий {scenario_id} не найден")
        
        scenario = self.scenarios[scenario_id]
        logger.info(f"Начинаем выполнение сценария: {scenario.name}")
        
        results = []
        
        for step in scenario.steps:
            try:
                logger.info(f"Выполняем шаг: {step.name}")
                
                # Подстановка переменных
                step_data = self._substitute_variables(step.action.data, context.variables)
                
                # Выполнение действия
                result = await self._execute_step(step, step_data, context)
                results.append(result)
                
                # Проверка результата
                if not result.success:
                    logger.error(f"Шаг {step.name} завершился с ошибкой: {result.error_message}")
                    break
                
                # Пауза между шагами
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
            except Exception as e:
                logger.error(f"Ошибка выполнения шага {step.name}: {e}")
                results.append(TestResult(
                    step_id=step.id,
                    success=False,
                    error_message=str(e),
                    duration=0,
                    timestamp=time.time()
                ))
                break
        
        return results
    
    async def _execute_step(self, step: TestStep, data: Dict[str, Any], context: ScenarioContext) -> TestResult:
        """Выполнение отдельного шага"""
        start_time = time.time()
        
        try:
            if step.action.type == "custom":
                # Пользовательское действие
                custom_action = self.custom_actions.get(data.get("custom_action"))
                if custom_action:
                    await custom_action(data, context)
                else:
                    raise ValueError(f"Пользовательское действие {data.get('custom_action')} не найдено")
            
            elif step.action.type == "navigate":
                # Навигация
                success = await context.browser_service.navigate_to(data["url"])
                if not success:
                    raise Exception("Не удалось перейти на указанный URL")
            
            elif step.action.type == "click":
                # Клик
                success = await context.browser_service.click_element(
                    data["selector"], 
                    data.get("selector_type", "css")
                )
                if not success:
                    raise Exception("Не удалось выполнить клик")
            
            elif step.action.type == "type_text":
                # Ввод текста
                success = await context.browser_service.type_text(
                    data["selector"],
                    data["text"],
                    data.get("selector_type", "css")
                )
                if not success:
                    raise Exception("Не удалось ввести текст")
            
            elif step.action.type == "wait_for_element":
                # Ожидание элемента
                success = await context.browser_service.wait_for_element(
                    data["selector"],
                    data.get("selector_type", "css"),
                    data.get("timeout")
                )
                if not success:
                    raise Exception("Элемент не появился в течение указанного времени")
            
            else:
                raise ValueError(f"Неподдерживаемый тип действия: {step.action.type}")
            
            duration = time.time() - start_time
            
            return TestResult(
                step_id=step.id,
                success=True,
                duration=duration,
                timestamp=time.time()
            )
            
        except Exception as e:
            duration = time.time() - start_time
            
            return TestResult(
                step_id=step.id,
                success=False,
                error_message=str(e),
                duration=duration,
                timestamp=time.time()
            )
    
    def _substitute_variables(self, data: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Подстановка переменных в данные"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                    var_name = value[2:-2].strip()
                    result[key] = variables.get(var_name, value)
                elif isinstance(value, (dict, list)):
                    result[key] = self._substitute_variables(value, variables)
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._substitute_variables(item, variables) for item in data]
        else:
            return data
    
    # Пользовательские действия
    async def _verify_analysis_data(self, data: Dict[str, Any], context: ScenarioContext):
        """Проверка данных анализа"""
        # Проверяем наличие ключевых элементов на странице
        elements_to_check = [
            ".analysis-score",
            ".analysis-metrics",
            ".analysis-chart"
        ]
        
        for selector in elements_to_check:
            element = await context.browser_service.find_element(selector)
            if not element:
                raise Exception(f"Элемент {selector} не найден на странице")
    
    async def _select_benchmark_domains(self, data: Dict[str, Any], context: ScenarioContext):
        """Выбор доменов для сравнения"""
        # Выбираем первые несколько доменов из списка
        domain_selectors = [
            ".domain-item:nth-child(1) .select-checkbox",
            ".domain-item:nth-child(2) .select-checkbox"
        ]
        
        for selector in domain_selectors:
            await context.browser_service.click_element(selector)
            await asyncio.sleep(0.5)
    
    async def _wait_for_file_download(self, data: Dict[str, Any], context: ScenarioContext):
        """Ожидание загрузки файла"""
        # Проверяем наличие индикатора загрузки
        download_indicator = ".download-progress"
        await context.browser_service.wait_for_element(download_indicator, timeout=10)
        
        # Ждем завершения загрузки
        await asyncio.sleep(5)
    
    async def _execute_login_flow(self, data: Dict[str, Any], context: ScenarioContext):
        """Выполнение полного цикла входа"""
        login_scenario = self.scenarios["login_flow"]
        login_context = ScenarioContext(
            scenario_id="login_flow",
            session_id=context.session_id,
            variables=context.variables,
            results=[],
            start_time=time.time(),
            browser_service=context.browser_service,
            api_client=context.api_client
        )
        
        await self.execute_scenario("login_flow", login_context)
    
    async def _execute_add_domain_flow(self, data: Dict[str, Any], context: ScenarioContext):
        """Выполнение цикла добавления домена"""
        domain_scenario = self.scenarios["domain_analysis"]
        domain_context = ScenarioContext(
            scenario_id="domain_analysis",
            session_id=context.session_id,
            variables=context.variables,
            results=[],
            start_time=time.time(),
            browser_service=context.browser_service,
            api_client=context.api_client
        )
        
        await self.execute_scenario("domain_analysis", domain_context)
    
    async def _execute_view_results_flow(self, data: Dict[str, Any], context: ScenarioContext):
        """Выполнение цикла просмотра результатов"""
        # Переход к результатам
        await context.browser_service.navigate_to(f"{settings.frontend_url}/results")
        
        # Ожидание загрузки результатов
        await context.browser_service.wait_for_element(".results-list", timeout=15)
        
        # Клик по первому результату
        await context.browser_service.click_element(".result-item:first-child")
        
        # Ожидание загрузки деталей
        await context.browser_service.wait_for_element(".result-details", timeout=10)
    
    async def _execute_export_flow(self, data: Dict[str, Any], context: ScenarioContext):
        """Выполнение цикла экспорта"""
        export_scenario = self.scenarios["export_functionality"]
        export_context = ScenarioContext(
            scenario_id="export_functionality",
            session_id=context.session_id,
            variables=context.variables,
            results=[],
            start_time=time.time(),
            browser_service=context.browser_service,
            api_client=context.api_client
        )
        
        await self.execute_scenario("export_functionality", export_context)
    
    def get_scenario(self, scenario_id: str) -> Optional[TestScenario]:
        """Получение сценария по ID"""
        return self.scenarios.get(scenario_id)
    
    def list_scenarios(self) -> List[TestScenario]:
        """Список всех доступных сценариев"""
        return list(self.scenarios.values())
    
    def add_custom_scenario(self, scenario: TestScenario):
        """Добавление пользовательского сценария"""
        self.scenarios[scenario.id] = scenario
        logger.info(f"Добавлен пользовательский сценарий: {scenario.name}")
    
    def add_custom_action(self, name: str, action: Callable):
        """Добавление пользовательского действия"""
        self.custom_actions[name] = action
        logger.info(f"Добавлено пользовательское действие: {name}")
    
    def _initialize_user_profiles(self):
        """Инициализация профилей пользователей"""
        
        # Профиль SEO-специалиста
        seo_expert = UserProfile(
            name="SEO-специалист",
            description="Профессиональный SEO-инженер с опытом работы",
            behavior="expert",
            speed="normal",
            preferences={
                "focus_on_metrics": True,
                "detailed_analysis": True,
                "technical_seo": True
            },
            typical_actions=[
                "analyze_domain",
                "check_metrics",
                "generate_reports",
                "export_data"
            ]
        )
        
        # Профиль новичка
        beginner = UserProfile(
            name="Новичок",
            description="Пользователь без опыта в SEO",
            behavior="exploratory",
            speed="slow",
            preferences={
                "guided_tours": True,
                "simple_interface": True,
                "help_tooltips": True
            },
            typical_actions=[
                "explore_interface",
                "read_help",
                "try_features",
                "ask_questions"
            ]
        )
        
        # Профиль менеджера
        manager = UserProfile(
            name="Менеджер",
            description="Менеджер проектов, фокусируется на результатах",
            behavior="goal-oriented",
            speed="fast",
            preferences={
                "quick_overview": True,
                "summary_reports": True,
                "team_collaboration": True
            },
            typical_actions=[
                "view_dashboard",
                "check_progress",
                "generate_summaries",
                "share_reports"
            ]
        )
        
        self.user_profiles = {
            "seo_expert": seo_expert,
            "beginner": beginner,
            "manager": manager
        }
        
        logger.info(f"Инициализировано {len(self.user_profiles)} профилей пользователей")
    
    def get_user_profile(self, profile_id: str) -> Optional[UserProfile]:
        """Получение профиля пользователя по ID"""
        return self.user_profiles.get(profile_id)
    
    def get_all_user_profiles(self) -> List[UserProfile]:
        """Получение всех профилей пользователей"""
        return list(self.user_profiles.values())
    
    def create_scenario_context(self, scenario_id: str, session_id: str, 
                               user_profile: Optional[UserProfile] = None) -> ScenarioContext:
        """Создание контекста для выполнения сценария"""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Сценарий не найден: {scenario_id}")
        
        return ScenarioContext(
            scenario_id=scenario_id,
            session_id=session_id,
            variables=scenario.variables.copy(),
            results=[],
            start_time=time.time(),
            browser_service=None,
            api_client=None,
            user_profile=user_profile
        )
    
    def get_scenario_statistics(self) -> Dict[str, Any]:
        """Получение статистики сценариев"""
        total_scenarios = len(self.scenarios)
        total_steps = sum(len(scenario.steps) for scenario in self.scenarios.values())
        
        # Группировка по типам
        scenario_types = {}
        for scenario in self.scenarios.values():
            scenario_type = getattr(scenario, 'type', 'unknown')
            if scenario_type not in scenario_types:
                scenario_types[scenario_type] = 0
            scenario_types[scenario_type] += 1
        
        # Группировка по приоритетам
        priorities = {}
        for scenario in self.scenarios.values():
            priority = getattr(scenario, 'priority', 'medium')
            if priority not in priorities:
                priorities[priority] = 0
            priorities[priority] += 1
        
        return {
            "total_scenarios": total_scenarios,
            "total_steps": total_steps,
            "average_steps_per_scenario": total_steps / total_scenarios if total_scenarios > 0 else 0,
            "scenario_types": scenario_types,
            "priorities": priorities,
            "user_profiles_count": len(self.user_profiles)
        } 