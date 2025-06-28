"""
API клиент для взаимодействия с бэкендом reLink
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from httpx import AsyncClient, Response

from .config import settings, TestConfig
from .models import APITestCase, APITestResult, TestStatus


class APIClient:
    """
    Клиент для взаимодействия с API reLink
    
    Обеспечивает аутентификацию, выполнение запросов к API
    и тестирование всех эндпоинтов системы.
    """
    
    def __init__(self):
        """Инициализация API клиента"""
        self.logger = logging.getLogger(__name__)
        self.base_url = settings.backend_url
        self.client: Optional[AsyncClient] = None
        self.token: Optional[str] = None
        self.last_response: Optional[Response] = None
        self.session_headers: Dict[str, str] = {}
        
        # Кэш для результатов запросов
        self.cache: Dict[str, Any] = {}
        
        self.logger.info(f"API клиент инициализирован для {self.base_url}")
    
    async def initialize(self) -> None:
        """Инициализация HTTP клиента"""
        timeout = httpx.Timeout(settings.browser_timeout)
        self.client = AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "User-Agent": "UXBot/1.0.0",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        self.logger.info("HTTP клиент инициализирован")
    
    async def close(self) -> None:
        """Закрытие HTTP клиента"""
        if self.client:
            await self.client.aclose()
            self.logger.info("HTTP клиент закрыт")
    
    async def login(self, email: str, password: str) -> str:
        """
        Аутентификация пользователя
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            
        Returns:
            JWT токен
        """
        try:
            response = await self._make_request(
                "POST",
                TestConfig.API_ENDPOINTS["auth_login"],
                json={
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session_headers["Authorization"] = f"Bearer {self.token}"
                self.logger.info(f"Успешная аутентификация: {email}")
                return self.token
            else:
                raise Exception(f"Ошибка аутентификации: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Ошибка аутентификации: {e}")
            raise
    
    async def register(self, email: str, password: str, name: str) -> Dict[str, Any]:
        """
        Регистрация нового пользователя
        
        Args:
            email: Email пользователя
            password: Пароль пользователя
            name: Имя пользователя
            
        Returns:
            Данные зарегистрированного пользователя
        """
        try:
            response = await self._make_request(
                "POST",
                TestConfig.API_ENDPOINTS["auth_register"],
                json={
                    "email": email,
                    "password": password,
                    "name": name
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                self.logger.info(f"Успешная регистрация: {email}")
                return data
            else:
                raise Exception(f"Ошибка регистрации: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Ошибка регистрации: {e}")
            raise
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья API"""
        try:
            response = await self._make_request("GET", TestConfig.API_ENDPOINTS["health"])
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса здоровья: {e}")
            raise
    
    async def get_domains(self) -> List[Dict[str, Any]]:
        """Получение списка доменов"""
        try:
            response = await self._make_request(
                "GET", 
                TestConfig.API_ENDPOINTS["domains"],
                headers=self.session_headers
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка получения доменов: {e}")
            raise
    
    async def analyze_domain(self, domain: str, comprehensive: bool = False) -> Dict[str, Any]:
        """
        Анализ домена
        
        Args:
            domain: Домен для анализа
            comprehensive: Комплексный анализ
            
        Returns:
            Результат анализа
        """
        try:
            response = await self._make_request(
                "POST",
                TestConfig.API_ENDPOINTS["analysis"],
                json={
                    "domain": domain,
                    "comprehensive": comprehensive
                },
                headers=self.session_headers
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка анализа домена {domain}: {e}")
            raise
    
    async def get_analysis_history(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение истории анализов"""
        try:
            response = await self._make_request(
                "GET",
                f"{TestConfig.API_ENDPOINTS['history']}?limit={limit}&offset={offset}",
                headers=self.session_headers
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка получения истории анализов: {e}")
            raise
    
    async def get_benchmarks(self) -> List[Dict[str, Any]]:
        """Получение списка бенчмарков"""
        try:
            response = await self._make_request(
                "GET",
                TestConfig.API_ENDPOINTS["benchmarks"],
                headers=self.session_headers
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка получения бенчмарков: {e}")
            raise
    
    async def run_benchmark(self, name: str, description: str = None) -> Dict[str, Any]:
        """
        Запуск бенчмарка
        
        Args:
            name: Название бенчмарка
            description: Описание
            
        Returns:
            Результат выполнения бенчмарка
        """
        try:
            response = await self._make_request(
                "POST",
                "/api/v1/benchmarks/run",
                json={
                    "name": name,
                    "description": description,
                    "benchmark_type": "seo_advanced",
                    "models": ["qwen2.5:7b-instruct-turbo"],
                    "iterations": 3
                },
                headers=self.session_headers
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка запуска бенчмарка {name}: {e}")
            raise
    
    async def get_settings(self) -> Dict[str, Any]:
        """Получение настроек приложения"""
        try:
            response = await self._make_request(
                "GET",
                TestConfig.API_ENDPOINTS["settings"],
                headers=self.session_headers
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка получения настроек: {e}")
            raise
    
    async def get_ollama_status(self) -> Dict[str, Any]:
        """Получение статуса Ollama"""
        try:
            response = await self._make_request(
                "GET",
                TestConfig.API_ENDPOINTS["ollama_status"],
                headers=self.session_headers
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка получения статуса Ollama: {e}")
            raise
    
    async def export_data(self, format: str, analysis_ids: List[int]) -> Dict[str, Any]:
        """
        Экспорт данных
        
        Args:
            format: Формат экспорта (json, csv, pdf)
            analysis_ids: ID анализов для экспорта
            
        Returns:
            Результат экспорта
        """
        try:
            response = await self._make_request(
                "POST",
                "/api/v1/export",
                json={
                    "format": format,
                    "analysis_ids": analysis_ids
                },
                headers=self.session_headers
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Ошибка экспорта данных: {e}")
            raise
    
    async def test_microservice_integration(self, service_name: str) -> Dict[str, Any]:
        """
        Тестирование интеграции с микросервисом
        
        Args:
            service_name: Название микросервиса
            
        Returns:
            Результат тестирования
        """
        service_urls = {
            "llm_tuning": settings.llm_tuning_url,
            "monitoring": settings.monitoring_url,
            "docs": settings.docs_url,
            "testing": settings.testing_url
        }
        
        if service_name not in service_urls:
            raise ValueError(f"Неизвестный микросервис: {service_name}")
        
        try:
            service_url = service_urls[service_name]
            async with AsyncClient() as client:
                response = await client.get(f"{service_url}/health")
                return {
                    "service": service_name,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "status_code": response.status_code
                }
        except Exception as e:
            self.logger.error(f"Ошибка тестирования микросервиса {service_name}: {e}")
            return {
                "service": service_name,
                "status": "error",
                "error": str(e)
            }
    
    async def run_api_test_case(self, test_case: APITestCase) -> APITestResult:
        """
        Выполнение тестового случая API
        
        Args:
            test_case: Тестовый случай
            
        Returns:
            Результат выполнения
        """
        result = APITestResult(
            test_case_id=test_case.id,
            test_case_name=test_case.name,
            status=TestStatus.RUNNING,
            request_time=datetime.utcnow()
        )
        
        try:
            # Подготовка заголовков
            headers = {**self.session_headers, **test_case.headers}
            
            # Выполнение запроса
            response = await self._make_request(
                test_case.method,
                test_case.endpoint,
                params=test_case.params,
                json=test_case.body,
                headers=headers,
                timeout=test_case.timeout
            )
            
            result.response_time = datetime.utcnow()
            result.duration = (result.response_time - result.request_time).total_seconds()
            result.status_code = response.status_code
            result.response_body = response.json() if response.content else None
            
            # Проверка статуса
            if response.status_code == test_case.expected_status:
                result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.FAILED
                result.error_message = f"Expected status {test_case.expected_status}, got {response.status_code}"
            
            # Валидация ответа
            if test_case.expected_response:
                validation_errors = self._validate_response(
                    result.response_body, 
                    test_case.expected_response
                )
                if validation_errors:
                    result.validation_errors = validation_errors
                    result.status = TestStatus.FAILED
            
            # Сбор метрик производительности
            result.performance_metrics = PerformanceMetrics(
                api_response_time=result.duration,
                timestamp=result.response_time
            )
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.response_time = datetime.utcnow()
            self.logger.error(f"Ошибка выполнения API теста {test_case.name}: {e}")
        
        return result
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Response:
        """
        Выполнение HTTP запроса
        
        Args:
            method: HTTP метод
            endpoint: Эндпоинт
            params: Параметры запроса
            json: JSON данные
            headers: Заголовки
            timeout: Таймаут
            
        Returns:
            HTTP ответ
        """
        if not self.client:
            raise Exception("HTTP клиент не инициализирован")
        
        try:
            # Кэширование для GET запросов
            cache_key = f"{method}:{endpoint}:{hash(str(params))}"
            if method == "GET" and cache_key in self.cache:
                self.logger.debug(f"Использование кэша для {endpoint}")
                return self.cache[cache_key]
            
            # Выполнение запроса
            response = await self.client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json,
                headers=headers,
                timeout=timeout or settings.browser_timeout
            )
            
            self.last_response = response
            
            # Кэширование успешных GET запросов
            if method == "GET" and response.status_code == 200:
                self.cache[cache_key] = response
            
            return response
            
        except Exception as e:
            self.logger.error(f"Ошибка HTTP запроса {method} {endpoint}: {e}")
            raise
    
    def _validate_response(self, actual: Any, expected: Any) -> List[str]:
        """
        Валидация ответа API
        
        Args:
            actual: Фактический ответ
            expected: Ожидаемый ответ
            
        Returns:
            Список ошибок валидации
        """
        errors = []
        
        if isinstance(expected, dict) and isinstance(actual, dict):
            for key, expected_value in expected.items():
                if key not in actual:
                    errors.append(f"Missing key: {key}")
                elif actual[key] != expected_value:
                    errors.append(f"Value mismatch for {key}: expected {expected_value}, got {actual[key]}")
        
        elif actual != expected:
            errors.append(f"Response mismatch: expected {expected}, got {actual}")
        
        return errors
    
    def get_last_response_status(self) -> Optional[int]:
        """Получение статуса последнего ответа"""
        return self.last_response.status_code if self.last_response else None
    
    async def is_healthy(self) -> bool:
        """Проверка здоровья API клиента"""
        try:
            await self.get_health_status()
            return True
        except Exception:
            return False
    
    async def make_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Универсальный метод для выполнения запросов
        
        Args:
            request_data: Данные запроса
            
        Returns:
            Результат запроса
        """
        method = request_data.get("method", "GET")
        endpoint = request_data.get("endpoint", "/")
        params = request_data.get("params")
        json_data = request_data.get("json")
        headers = request_data.get("headers")
        
        response = await self._make_request(
            method=method,
            endpoint=endpoint,
            params=params,
            json=json_data,
            headers=headers
        )
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.content else None,
            "elapsed": response.elapsed.total_seconds()
        }
    
    async def get_status(self) -> str:
        """Получение статуса API"""
        try:
            health = await self.get_health_status()
            return health.get("status", "unknown")
        except Exception:
            return "error" 