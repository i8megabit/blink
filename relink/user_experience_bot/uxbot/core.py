"""
Ядро User Experience Bot
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .config import settings, TestConfig
from .models import (
    TestScenario, TestResult, TestExecution, TestStatus,
    UserAction, ActionType, UserSession, PageState,
    PerformanceMetrics, UIElement, ElementType
)
from .api_client import APIClient
from .ui_simulator import UISimulator
from .scenario_engine import ScenarioEngine
from .metrics_collector import MetricsCollector
from .report_generator import ReportGenerator
from .database import DatabaseManager
from .monitoring import MonitoringService


class UXBot:
    """
    Основной класс User Experience Bot
    
    Координирует выполнение тестовых сценариев, сбор метрик
    и генерацию отчетов для оценки пользовательского опыта.
    """
    
    def __init__(self):
        """Инициализация UX Bot"""
        self.logger = logging.getLogger(__name__)
        self.api_client = APIClient()
        self.ui_simulator = UISimulator()
        self.scenario_engine = ScenarioEngine()
        self.metrics_collector = MetricsCollector()
        self.report_generator = ReportGenerator()
        self.database = DatabaseManager()
        self.monitoring = MonitoringService()
        
        self.current_session: Optional[UserSession] = None
        self.active_execution: Optional[TestExecution] = None
        self.is_running = False
        
        self.logger.info("UX Bot инициализирован")
    
    async def start(self) -> None:
        """Запуск UX Bot"""
        try:
            self.logger.info("Запуск UX Bot...")
            
            # Инициализация компонентов
            await self.database.connect()
            await self.api_client.initialize()
            await self.ui_simulator.initialize()
            await self.monitoring.start()
            
            self.is_running = True
            self.logger.info("UX Bot успешно запущен")
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска UX Bot: {e}")
            raise
    
    async def stop(self) -> None:
        """Остановка UX Bot"""
        try:
            self.logger.info("Остановка UX Bot...")
            
            self.is_running = False
            
            # Завершение активных операций
            if self.active_execution:
                await self.complete_execution()
            
            # Закрытие соединений
            await self.ui_simulator.close()
            await self.api_client.close()
            await self.database.close()
            await self.monitoring.stop()
            
            self.logger.info("UX Bot остановлен")
            
        except Exception as e:
            self.logger.error(f"Ошибка остановки UX Bot: {e}")
            raise
    
    async def run_scenario(self, scenario: TestScenario) -> TestResult:
        """
        Выполнение одного сценария
        
        Args:
            scenario: Сценарий для выполнения
            
        Returns:
            Результат выполнения сценария
        """
        result = TestResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow(),
            total_steps=len(scenario.steps),
            passed_steps=0,
            failed_steps=0,
            skipped_steps=0,
            error_steps=0
        )
        
        try:
            self.logger.info(f"Запуск сценария: {scenario.name}")
            
            # Подготовка окружения
            await self.prepare_environment(scenario)
            
            # Выполнение шагов
            for i, step in enumerate(scenario.steps):
                step_result = await self.execute_step(step, result)
                
                if step_result.status == TestStatus.PASSED:
                    result.passed_steps += 1
                elif step_result.status == TestStatus.FAILED:
                    result.failed_steps += 1
                elif step_result.status == TestStatus.SKIPPED:
                    result.skipped_steps += 1
                elif step_result.status == TestStatus.ERROR:
                    result.error_steps += 1
                
                # Обновление прогресса
                await self.update_progress(result, i + 1, len(scenario.steps))
            
            # Завершение сценария
            result.end_time = datetime.utcnow()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            if result.failed_steps == 0 and result.error_steps == 0:
                result.status = TestStatus.PASSED
            elif result.failed_steps > 0:
                result.status = TestStatus.FAILED
            else:
                result.status = TestStatus.ERROR
            
            self.logger.info(f"Сценарий {scenario.name} завершен: {result.status}")
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.end_time = datetime.utcnow()
            self.logger.error(f"Ошибка выполнения сценария {scenario.name}: {e}")
        
        return result
    
    async def run_test_suite(self, scenarios: List[TestScenario], 
                           parallel: bool = False) -> TestExecution:
        """
        Выполнение набора тестовых сценариев
        
        Args:
            scenarios: Список сценариев
            parallel: Параллельное выполнение
            
        Returns:
            Результат выполнения набора тестов
        """
        execution = TestExecution(
            suite_id=UUID(int=0),  # Временный ID
            suite_name="UX Test Suite",
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow(),
            total_scenarios=len(scenarios),
            passed_scenarios=0,
            failed_scenarios=0,
            skipped_scenarios=0,
            error_scenarios=0,
            environment=settings.environment,
            browser_type=settings.browser_type,
            parallel_workers=settings.test_parallel_workers if parallel else 1
        )
        
        self.active_execution = execution
        
        try:
            self.logger.info(f"Запуск набора тестов: {len(scenarios)} сценариев")
            
            if parallel:
                results = await self.run_scenarios_parallel(scenarios)
            else:
                results = await self.run_scenarios_sequential(scenarios)
            
            execution.results = results
            
            # Подсчет статистики
            for result in results:
                if result.status == TestStatus.PASSED:
                    execution.passed_scenarios += 1
                elif result.status == TestStatus.FAILED:
                    execution.failed_scenarios += 1
                elif result.status == TestStatus.SKIPPED:
                    execution.skipped_scenarios += 1
                elif result.status == TestStatus.ERROR:
                    execution.error_scenarios += 1
            
            execution.end_time = datetime.utcnow()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            
            if execution.failed_scenarios == 0 and execution.error_scenarios == 0:
                execution.status = TestStatus.PASSED
            elif execution.failed_scenarios > 0:
                execution.status = TestStatus.FAILED
            else:
                execution.status = TestStatus.ERROR
            
            self.logger.info(f"Набор тестов завершен: {execution.status}")
            
        except Exception as e:
            execution.status = TestStatus.ERROR
            execution.end_time = datetime.utcnow()
            self.logger.error(f"Ошибка выполнения набора тестов: {e}")
        
        return execution
    
    async def run_scenarios_sequential(self, scenarios: List[TestScenario]) -> List[TestResult]:
        """Последовательное выполнение сценариев"""
        results = []
        for scenario in scenarios:
            result = await self.run_scenario(scenario)
            results.append(result)
        return results
    
    async def run_scenarios_parallel(self, scenarios: List[TestScenario]) -> List[TestResult]:
        """Параллельное выполнение сценариев"""
        semaphore = asyncio.Semaphore(settings.test_parallel_workers)
        
        async def run_scenario_with_semaphore(scenario: TestScenario) -> TestResult:
            async with semaphore:
                return await self.run_scenario(scenario)
        
        tasks = [run_scenario_with_semaphore(scenario) for scenario in scenarios]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка исключений
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                # Создание результата с ошибкой
                error_result = TestResult(
                    scenario_id=UUID(int=0),
                    scenario_name="Unknown",
                    status=TestStatus.ERROR,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    total_steps=0,
                    passed_steps=0,
                    failed_steps=0,
                    skipped_steps=0,
                    error_steps=1,
                    error_message=str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_step(self, step: TestStep, result: TestResult) -> TestStep:
        """
        Выполнение одного шага теста
        
        Args:
            step: Шаг для выполнения
            result: Результат сценария
            
        Returns:
            Обновленный шаг с результатом
        """
        step.start_time = datetime.utcnow()
        step.status = TestStatus.RUNNING
        
        try:
            self.logger.debug(f"Выполнение шага: {step.name}")
            
            # Выполнение действий шага
            for action in step.actions:
                action_result = await self.execute_action(action)
                if not action_result.success:
                    step.status = TestStatus.FAILED
                    step.error_message = action_result.error_message
                    break
            
            # Проверка ожидаемого результата
            if step.status == TestStatus.RUNNING:
                if step.expected_result:
                    actual_result = await self.get_actual_result(step)
                    step.actual_result = actual_result
                    
                    if actual_result == step.expected_result:
                        step.status = TestStatus.PASSED
                    else:
                        step.status = TestStatus.FAILED
                        step.error_message = f"Expected: {step.expected_result}, Got: {actual_result}"
                else:
                    step.status = TestStatus.PASSED
            
            step.end_time = datetime.utcnow()
            step.duration = (step.end_time - step.start_time).total_seconds()
            
        except Exception as e:
            step.status = TestStatus.ERROR
            step.error_message = str(e)
            step.end_time = datetime.utcnow()
            self.logger.error(f"Ошибка выполнения шага {step.name}: {e}")
        
        return step
    
    async def execute_action(self, action: UserAction) -> UserAction:
        """
        Выполнение действия пользователя
        
        Args:
            action: Действие для выполнения
            
        Returns:
            Обновленное действие с результатом
        """
        start_time = time.time()
        
        try:
            if action.action_type == ActionType.CLICK:
                await self.ui_simulator.click_element(action.element_selector)
            elif action.action_type == ActionType.TYPE:
                await self.ui_simulator.type_text(action.element_selector, action.value)
            elif action.action_type == ActionType.SCROLL:
                await self.ui_simulator.scroll_page(action.value)
            elif action.action_type == ActionType.NAVIGATE:
                await self.ui_simulator.navigate_to(action.value)
            elif action.action_type == ActionType.WAIT:
                await asyncio.sleep(float(action.value or 1))
            elif action.action_type == ActionType.API_CALL:
                await self.api_client.make_request(action.metadata)
            elif action.action_type == ActionType.ASSERT:
                await self.assert_condition(action.metadata)
            
            action.duration = time.time() - start_time
            action.success = True
            
        except Exception as e:
            action.duration = time.time() - start_time
            action.success = False
            action.error_message = str(e)
            self.logger.error(f"Ошибка выполнения действия {action.action_type}: {e}")
        
        return action
    
    async def prepare_environment(self, scenario: TestScenario) -> None:
        """Подготовка окружения для сценария"""
        # Создание новой сессии пользователя
        self.current_session = UserSession(
            email=settings.test_user_email
        )
        
        # Аутентификация если требуется
        if any("login" in step.name.lower() for step in scenario.steps):
            await self.authenticate_user()
        
        # Настройка браузера
        await self.ui_simulator.setup_browser()
    
    async def authenticate_user(self) -> None:
        """Аутентификация пользователя"""
        try:
            # Логин через API
            token = await self.api_client.login(
                settings.test_user_email,
                settings.test_user_password
            )
            
            if self.current_session:
                self.current_session.token = token
                self.current_session.is_authenticated = True
            
            self.logger.info("Пользователь аутентифицирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка аутентификации: {e}")
            raise
    
    async def get_actual_result(self, step: TestStep) -> str:
        """Получение фактического результата шага"""
        # Реализация зависит от типа шага
        if "check_results" in step.name.lower():
            return await self.ui_simulator.get_page_text()
        elif "verify_status" in step.name.lower():
            return await self.api_client.get_status()
        else:
            return "completed"
    
    async def assert_condition(self, condition: Dict[str, Any]) -> None:
        """Проверка условия"""
        condition_type = condition.get("type")
        
        if condition_type == "element_visible":
            selector = condition.get("selector")
            is_visible = await self.ui_simulator.is_element_visible(selector)
            if not is_visible:
                raise AssertionError(f"Element {selector} is not visible")
        
        elif condition_type == "text_present":
            text = condition.get("text")
            page_text = await self.ui_simulator.get_page_text()
            if text not in page_text:
                raise AssertionError(f"Text '{text}' not found on page")
        
        elif condition_type == "api_response":
            expected_status = condition.get("status")
            actual_status = await self.api_client.get_last_response_status()
            if actual_status != expected_status:
                raise AssertionError(f"Expected status {expected_status}, got {actual_status}")
    
    async def update_progress(self, result: TestResult, current: int, total: int) -> None:
        """Обновление прогресса выполнения"""
        progress = {
            "scenario": result.scenario_name,
            "current_step": current,
            "total_steps": total,
            "progress_percent": (current / total) * 100,
            "status": result.status.value
        }
        
        await self.monitoring.update_progress(progress)
    
    async def complete_execution(self) -> None:
        """Завершение выполнения тестов"""
        if self.active_execution:
            # Сохранение результатов
            await self.database.save_execution(self.active_execution)
            
            # Генерация отчета
            report = await self.report_generator.generate_report(self.active_execution)
            await self.database.save_report(report)
            
            # Отправка метрик
            await self.metrics_collector.send_metrics(self.active_execution)
            
            self.active_execution = None
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья бота"""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "components": {
                "api_client": await self.api_client.is_healthy(),
                "ui_simulator": await self.ui_simulator.is_healthy(),
                "database": await self.database.is_healthy(),
                "monitoring": await self.monitoring.is_healthy()
            },
            "current_session": self.current_session is not None,
            "active_execution": self.active_execution is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики работы"""
        return await self.database.get_statistics() 