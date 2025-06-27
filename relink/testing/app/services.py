"""
Сервисы для микросервиса тестирования reLink
"""

import asyncio
import time
import psutil
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .models import (
    TestRequest, TestResult, TestSuite, TestExecution, TestReport, 
    TestMetrics, TestStatus, TestType, TestFilter
)
from .config import settings


logger = logging.getLogger(__name__)


class TestExecutor:
    """Исполнитель тестов"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.testing.max_concurrent_tests)
        self.active_tests: Dict[str, asyncio.Task] = {}
    
    async def execute_test(self, test_request: TestRequest) -> TestResult:
        """Выполнение одиночного теста"""
        test_id = f"test_{int(time.time() * 1000)}"
        
        # Создаем результат теста
        result = TestResult(
            test_id=test_id,
            status=TestStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        try:
            # Определяем таймаут
            timeout = test_request.timeout or self._get_default_timeout(test_request.test_type)
            
            # Выполняем тест с таймаутом
            test_result = await asyncio.wait_for(
                self._run_test(test_request, result),
                timeout=timeout
            )
            
            return test_result
            
        except asyncio.TimeoutError:
            result.status = TestStatus.TIMEOUT
            result.message = f"Тест превысил таймаут {timeout} секунд"
            result.finished_at = datetime.utcnow()
            return result
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error = str(e)
            result.stack_trace = self._get_stack_trace(e)
            result.finished_at = datetime.utcnow()
            return result
    
    async def _run_test(self, test_request: TestRequest, result: TestResult) -> TestResult:
        """Внутренний метод выполнения теста"""
        try:
            # Собираем метрики до выполнения
            start_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
            start_cpu = psutil.cpu_percent()
            
            # Выполняем тест в зависимости от типа
            if test_request.test_type == TestType.UNIT:
                test_data = await self._run_unit_test(test_request)
            elif test_request.test_type == TestType.INTEGRATION:
                test_data = await self._run_integration_test(test_request)
            elif test_request.test_type == TestType.PERFORMANCE:
                test_data = await self._run_performance_test(test_request)
            elif test_request.test_type == TestType.API:
                test_data = await self._run_api_test(test_request)
            elif test_request.test_type == TestType.SECURITY:
                test_data = await self._run_security_test(test_request)
            else:
                test_data = await self._run_generic_test(test_request)
            
            # Собираем метрики после выполнения
            end_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
            end_cpu = psutil.cpu_percent()
            
            # Обновляем результат
            result.status = TestStatus.PASSED if test_data["success"] else TestStatus.FAILED
            result.finished_at = datetime.utcnow()
            result.passed = test_data.get("passed", 0)
            result.failed = test_data.get("failed", 0)
            result.skipped = test_data.get("skipped", 0)
            result.total = test_data.get("total", 0)
            result.message = test_data.get("message", "")
            result.memory_usage = end_memory - start_memory
            result.cpu_usage = (start_cpu + end_cpu) / 2
            result.metadata = test_data.get("metadata", {})
            
            return result
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error = str(e)
            result.stack_trace = self._get_stack_trace(e)
            result.finished_at = datetime.utcnow()
            return result
    
    async def _run_unit_test(self, test_request: TestRequest) -> Dict[str, Any]:
        """Выполнение unit теста"""
        # Симуляция выполнения unit теста
        await asyncio.sleep(0.1)  # Имитация работы
        
        return {
            "success": True,
            "passed": 5,
            "failed": 0,
            "skipped": 0,
            "total": 5,
            "message": "Unit тест выполнен успешно",
            "metadata": {"test_type": "unit"}
        }
    
    async def _run_integration_test(self, test_request: TestRequest) -> Dict[str, Any]:
        """Выполнение integration теста"""
        # Симуляция выполнения integration теста
        await asyncio.sleep(1.0)  # Имитация работы
        
        return {
            "success": True,
            "passed": 10,
            "failed": 0,
            "skipped": 1,
            "total": 11,
            "message": "Integration тест выполнен успешно",
            "metadata": {"test_type": "integration"}
        }
    
    async def _run_performance_test(self, test_request: TestRequest) -> Dict[str, Any]:
        """Выполнение performance теста"""
        # Симуляция выполнения performance теста
        iterations = test_request.parameters.get("iterations", 100)
        await asyncio.sleep(2.0)  # Имитация работы
        
        return {
            "success": True,
            "passed": iterations,
            "failed": 0,
            "skipped": 0,
            "total": iterations,
            "message": f"Performance тест выполнен за {iterations} итераций",
            "metadata": {
                "test_type": "performance",
                "iterations": iterations,
                "avg_response_time": 0.5
            }
        }
    
    async def _run_api_test(self, test_request: TestRequest) -> Dict[str, Any]:
        """Выполнение API теста"""
        # Симуляция выполнения API теста
        await asyncio.sleep(0.5)  # Имитация работы
        
        return {
            "success": True,
            "passed": 3,
            "failed": 0,
            "skipped": 0,
            "total": 3,
            "message": "API тест выполнен успешно",
            "metadata": {"test_type": "api", "endpoints_tested": 3}
        }
    
    async def _run_security_test(self, test_request: TestRequest) -> Dict[str, Any]:
        """Выполнение security теста"""
        # Симуляция выполнения security теста
        await asyncio.sleep(1.5)  # Имитация работы
        
        return {
            "success": True,
            "passed": 8,
            "failed": 0,
            "skipped": 0,
            "total": 8,
            "message": "Security тест выполнен успешно",
            "metadata": {"test_type": "security", "vulnerabilities_found": 0}
        }
    
    async def _run_generic_test(self, test_request: TestRequest) -> Dict[str, Any]:
        """Выполнение generic теста"""
        # Симуляция выполнения generic теста
        await asyncio.sleep(0.3)  # Имитация работы
        
        return {
            "success": True,
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "total": 1,
            "message": "Generic тест выполнен успешно",
            "metadata": {"test_type": "generic"}
        }
    
    def _get_default_timeout(self, test_type: TestType) -> int:
        """Получение таймаута по умолчанию для типа теста"""
        timeouts = {
            TestType.UNIT: settings.testing.unit_test_timeout,
            TestType.INTEGRATION: settings.testing.integration_test_timeout,
            TestType.PERFORMANCE: settings.testing.performance_test_timeout,
            TestType.LOAD: settings.testing.load_test_timeout,
            TestType.API: 30,
            TestType.SECURITY: 60,
            TestType.UI: 120,
            TestType.E2E: 300,
            TestType.BENCHMARK: 600
        }
        return timeouts.get(test_type, settings.testing.default_timeout)
    
    def _get_stack_trace(self, exception: Exception) -> str:
        """Получение stack trace из исключения"""
        import traceback
        return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))


class TestSuiteExecutor:
    """Исполнитель наборов тестов"""
    
    def __init__(self, test_executor: TestExecutor):
        self.test_executor = test_executor
    
    async def execute_suite(self, test_suite: TestSuite) -> List[TestResult]:
        """Выполнение набора тестов"""
        results = []
        
        if test_suite.parallel:
            # Параллельное выполнение
            tasks = []
            for test in test_suite.tests:
                task = asyncio.create_task(self.test_executor.execute_test(test))
                tasks.append(task)
            
            # Ждем завершения всех тестов
            suite_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in suite_results:
                if isinstance(result, Exception):
                    # Создаем результат с ошибкой
                    error_result = TestResult(
                        test_id=f"error_{int(time.time() * 1000)}",
                        status=TestStatus.ERROR,
                        started_at=datetime.utcnow(),
                        finished_at=datetime.utcnow(),
                        error=str(result),
                        stack_trace=self._get_stack_trace(result)
                    )
                    results.append(error_result)
                else:
                    results.append(result)
                    
                # Проверяем, нужно ли остановиться при ошибке
                if (test_suite.stop_on_failure and 
                    result.status in [TestStatus.FAILED, TestStatus.ERROR]):
                    break
        else:
            # Последовательное выполнение
            for test in test_suite.tests:
                result = await self.test_executor.execute_test(test)
                results.append(result)
                
                # Проверяем, нужно ли остановиться при ошибке
                if (test_suite.stop_on_failure and 
                    result.status in [TestStatus.FAILED, TestStatus.ERROR]):
                    break
        
        return results
    
    def _get_stack_trace(self, exception: Exception) -> str:
        """Получение stack trace из исключения"""
        import traceback
        return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))


class MetricsCollector:
    """Сборщик метрик тестирования"""
    
    def __init__(self):
        self.metrics_history: List[TestMetrics] = []
    
    def collect_metrics(self, execution_id: str, results: List[TestResult]) -> TestMetrics:
        """Сбор метрик из результатов тестов"""
        if not results:
            return TestMetrics(
                execution_id=execution_id,
                response_time_avg=0.0,
                response_time_min=0.0,
                response_time_max=0.0,
                response_time_std=0.0,
                memory_usage_avg=0.0,
                cpu_usage_avg=0.0,
                throughput=0.0,
                error_rate=0.0
            )
        
        # Собираем данные
        durations = [r.duration for r in results if r.duration is not None]
        memory_usage = [r.memory_usage for r in results if r.memory_usage is not None]
        cpu_usage = [r.cpu_usage for r in results if r.cpu_usage is not None]
        
        # Подсчитываем ошибки
        total_tests = len(results)
        error_tests = len([r for r in results if r.status in [TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT]])
        
        # Вычисляем метрики
        metrics = TestMetrics(
            execution_id=execution_id,
            response_time_avg=statistics.mean(durations) if durations else 0.0,
            response_time_min=min(durations) if durations else 0.0,
            response_time_max=max(durations) if durations else 0.0,
            response_time_std=statistics.stdev(durations) if len(durations) > 1 else 0.0,
            memory_usage_avg=statistics.mean(memory_usage) if memory_usage else 0.0,
            cpu_usage_avg=statistics.mean(cpu_usage) if cpu_usage else 0.0,
            throughput=total_tests / (sum(durations) if durations else 1.0),
            error_rate=(error_tests / total_tests * 100) if total_tests > 0 else 0.0
        )
        
        # Сохраняем в историю
        self.metrics_history.append(metrics)
        
        return metrics
    
    def get_metrics_history(self, execution_id: str, limit: int = 100) -> List[TestMetrics]:
        """Получение истории метрик"""
        return [
            m for m in self.metrics_history 
            if m.execution_id == execution_id
        ][-limit:]


class ReportGenerator:
    """Генератор отчетов о тестировании"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
    
    def generate_report(self, execution: TestExecution) -> TestReport:
        """Генерация отчета о выполнении"""
        if not execution.results:
            return TestReport(
                execution_id=execution.id,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                total_duration=0.0,
                average_duration=0.0,
                success_rate=0.0,
                results=[]
            )
        
        # Подсчитываем статистику
        total_tests = len(execution.results)
        passed_tests = len([r for r in execution.results if r.is_successful])
        failed_tests = len([r for r in execution.results if not r.is_successful and r.status != TestStatus.SKIPPED])
        skipped_tests = len([r for r in execution.results if r.status == TestStatus.SKIPPED])
        
        # Временные метрики
        durations = [r.duration for r in execution.results if r.duration is not None]
        total_duration = sum(durations) if durations else 0.0
        average_duration = statistics.mean(durations) if durations else 0.0
        
        # Процент успешности
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        # Создаем отчет
        report = TestReport(
            execution_id=execution.id,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            total_duration=total_duration,
            average_duration=average_duration,
            success_rate=success_rate,
            results=execution.results
        )
        
        return report
    
    def generate_html_report(self, report: TestReport) -> str:
        """Генерация HTML отчета"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report - {report.execution_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
                .metric {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .success {{ color: green; }}
                .failure {{ color: red; }}
                .warning {{ color: orange; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Report</h1>
                <p><strong>Execution ID:</strong> {report.execution_id}</p>
                <p><strong>Generated:</strong> {report.generated_at}</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>Total Tests</h3>
                    <p class="{'success' if report.total_tests > 0 else 'warning'}">{report.total_tests}</p>
                </div>
                <div class="metric">
                    <h3>Passed</h3>
                    <p class="success">{report.passed_tests}</p>
                </div>
                <div class="metric">
                    <h3>Failed</h3>
                    <p class="failure">{report.failed_tests}</p>
                </div>
                <div class="metric">
                    <h3>Skipped</h3>
                    <p class="warning">{report.skipped_tests}</p>
                </div>
                <div class="metric">
                    <h3>Success Rate</h3>
                    <p class="{'success' if report.success_rate >= 80 else 'failure'}">{report.success_rate:.1f}%</p>
                </div>
                <div class="metric">
                    <h3>Duration</h3>
                    <p>{report.total_duration:.2f}s</p>
                </div>
            </div>
            
            <h2>Test Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test ID</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for result in report.results:
            status_class = "success" if result.is_successful else "failure"
            html += f"""
                    <tr>
                        <td>{result.test_id}</td>
                        <td class="{status_class}">{result.status.value}</td>
                        <td>{result.duration:.2f}s</td>
                        <td>{result.message or ''}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return html


class TestingService:
    """Основной сервис тестирования"""
    
    def __init__(self):
        self.test_executor = TestExecutor()
        self.suite_executor = TestSuiteExecutor(self.test_executor)
        self.metrics_collector = MetricsCollector()
        self.report_generator = ReportGenerator(self.metrics_collector)
        self.executions: Dict[str, TestExecution] = {}
    
    async def run_test(self, test_request: TestRequest) -> TestExecution:
        """Запуск одиночного теста"""
        execution = TestExecution(
            test_request=test_request,
            status=TestStatus.PENDING
        )
        
        # Сохраняем выполнение
        self.executions[execution.id] = execution
        
        # Запускаем выполнение асинхронно
        asyncio.create_task(self._execute_single_test(execution))
        
        return execution
    
    async def run_suite(self, test_suite: TestSuite) -> TestExecution:
        """Запуск набора тестов"""
        execution = TestExecution(
            test_suite=test_suite,
            status=TestStatus.PENDING
        )
        
        # Сохраняем выполнение
        self.executions[execution.id] = execution
        
        # Запускаем выполнение асинхронно
        asyncio.create_task(self._execute_suite(execution))
        
        return execution
    
    async def _execute_single_test(self, execution: TestExecution):
        """Выполнение одиночного теста"""
        try:
            execution.status = TestStatus.RUNNING
            execution.started_at = datetime.utcnow()
            
            # Выполняем тест
            result = await self.test_executor.execute_test(execution.test_request)
            execution.results = [result]
            execution.progress = 100.0
            
            # Обновляем статус
            if result.is_successful:
                execution.status = TestStatus.PASSED
            else:
                execution.status = TestStatus.FAILED
            
            execution.finished_at = datetime.utcnow()
            
        except Exception as e:
            execution.status = TestStatus.ERROR
            execution.finished_at = datetime.utcnow()
            logger.error(f"Error executing test: {e}")
    
    async def _execute_suite(self, execution: TestExecution):
        """Выполнение набора тестов"""
        try:
            execution.status = TestStatus.RUNNING
            execution.started_at = datetime.utcnow()
            
            # Выполняем набор тестов
            results = await self.suite_executor.execute_suite(execution.test_suite)
            execution.results = results
            
            # Обновляем прогресс
            execution.progress = 100.0
            
            # Определяем общий статус
            if all(r.is_successful for r in results):
                execution.status = TestStatus.PASSED
            elif any(r.status == TestStatus.ERROR for r in results):
                execution.status = TestStatus.ERROR
            else:
                execution.status = TestStatus.FAILED
            
            execution.finished_at = datetime.utcnow()
            
        except Exception as e:
            execution.status = TestStatus.ERROR
            execution.finished_at = datetime.utcnow()
            logger.error(f"Error executing suite: {e}")
    
    def get_execution(self, execution_id: str) -> Optional[TestExecution]:
        """Получение выполнения по ID"""
        return self.executions.get(execution_id)
    
    def get_executions(self, filter_params: TestFilter) -> List[TestExecution]:
        """Получение списка выполнений с фильтрацией"""
        executions = list(self.executions.values())
        
        # Применяем фильтры
        if filter_params.test_type:
            executions = [e for e in executions if 
                         (e.test_request and e.test_request.test_type == filter_params.test_type) or
                         (e.test_suite and any(t.test_type == filter_params.test_type for t in e.test_suite.tests))]
        
        if filter_params.status:
            executions = [e for e in executions if e.status == filter_params.status]
        
        if filter_params.created_after:
            executions = [e for e in executions if e.created_at >= filter_params.created_after]
        
        if filter_params.created_before:
            executions = [e for e in executions if e.created_at <= filter_params.created_before]
        
        if filter_params.name_contains:
            executions = [e for e in executions if 
                         (e.test_request and filter_params.name_contains.lower() in e.test_request.name.lower()) or
                         (e.test_suite and filter_params.name_contains.lower() in e.test_suite.name.lower())]
        
        # Сортировка
        reverse = filter_params.sort_order == "desc"
        executions.sort(key=lambda x: getattr(x, filter_params.sort_by), reverse=reverse)
        
        # Пагинация
        start = filter_params.offset
        end = start + filter_params.limit
        return executions[start:end]
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Отмена выполнения"""
        execution = self.executions.get(execution_id)
        if execution and execution.status == TestStatus.RUNNING:
            execution.status = TestStatus.CANCELLED
            execution.finished_at = datetime.utcnow()
            return True
        return False
    
    def generate_report(self, execution_id: str) -> Optional[TestReport]:
        """Генерация отчета"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return self.report_generator.generate_report(execution)
    
    def collect_metrics(self, execution_id: str) -> Optional[TestMetrics]:
        """Сбор метрик"""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return self.metrics_collector.collect_metrics(execution_id, execution.results) 