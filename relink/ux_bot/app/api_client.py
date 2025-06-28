"""
🔌 API клиент для UX бота-имитатора

Обеспечивает взаимодействие с LLM роутером и бэкендом reLink для получения руководств
и отправки результатов анализа.
"""

import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from .config import settings
from .models import APIConfig, TestReport, PageAnalysis, Issue

logger = logging.getLogger(__name__)

class APIClient:
    """Клиент для взаимодействия с API сервисов reLink"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        await self.disconnect()
    
    async def connect(self):
        """Подключение к API"""
        try:
            connector = aiohttp.TCPConnector(verify_ssl=self.config.verify_ssl)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            self.session = aiohttp.ClientSession(
                base_url=self.config.base_url,
                headers=self.config.headers,
                connector=connector,
                timeout=timeout
            )
            
            logger.info(f"API клиент подключен к {self.config.base_url}")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к API: {e}")
            raise
    
    async def disconnect(self):
        """Отключение от API"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("API клиент отключен")
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Выполнение HTTP запроса"""
        if not self.session:
            raise RuntimeError("API клиент не подключен")
        
        url = f"{self.config.base_url}{endpoint}"
        request_headers = self.config.headers.copy()
        
        if self.auth_token:
            request_headers["Authorization"] = f"Bearer {self.auth_token}"
        
        if headers:
            request_headers.update(headers)
        
        for attempt in range(self.config.retry_count):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=request_headers
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 401:
                        logger.warning("Неавторизованный запрос, попытка аутентификации")
                        await self._authenticate()
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP {response.status}: {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка сети при попытке {attempt + 1}: {e}")
                if attempt == self.config.retry_count - 1:
                    raise
                await asyncio.sleep(1)
        
        return {"error": "Превышено количество попыток"}
    
    async def _authenticate(self):
        """Аутентификация в API"""
        try:
            # Здесь должна быть логика аутентификации
            # Для демонстрации используем токен из конфига
            if self.config.auth_token:
                self.auth_token = self.config.auth_token
                logger.info("Аутентификация выполнена")
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
    
    # Методы для работы с бэкендом reLink
    
    async def send_page_analysis(self, analysis: PageAnalysis) -> Dict[str, Any]:
        """Отправка анализа страницы в бэкенд"""
        try:
            data = {
                "url": analysis.url,
                "title": analysis.title,
                "elements": [
                    {
                        "selector": elem.selector,
                        "type": elem.element_type.value,
                        "text": elem.text,
                        "attributes": elem.attributes,
                        "is_visible": elem.is_visible,
                        "is_enabled": elem.is_enabled,
                        "position": elem.position,
                        "size": elem.size
                    }
                    for elem in analysis.elements
                ],
                "accessibility_issues": analysis.accessibility_issues,
                "responsiveness_issues": analysis.responsiveness_issues,
                "performance_metrics": analysis.performance_metrics,
                "screenshot_path": analysis.screenshot_path,
                "analysis_time": analysis.analysis_time.isoformat()
            }
            
            result = await self._make_request("POST", "/api/analysis/page", data)
            logger.info(f"Анализ страницы отправлен: {analysis.url}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка отправки анализа страницы: {e}")
            return {"error": str(e)}
    
    async def send_test_report(self, report: TestReport) -> Dict[str, Any]:
        """Отправка отчета о тестировании в бэкенд"""
        try:
            data = {
                "report_id": report.report_id,
                "session_id": report.session_id,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat() if report.end_time else None,
                "duration": report.duration,
                "total_tests": report.total_tests,
                "successful_tests": report.successful_tests,
                "failed_tests": report.failed_tests,
                "skipped_tests": report.skipped_tests,
                "success_rate": report.success_rate,
                "issues": [
                    {
                        "issue_id": issue.issue_id,
                        "type": issue.type,
                        "severity": issue.severity.value,
                        "description": issue.description,
                        "location": issue.location,
                        "screenshot_path": issue.screenshot_path,
                        "recommendation": issue.recommendation,
                        "detected_at": issue.detected_at.isoformat()
                    }
                    for issue in report.issues
                ],
                "recommendations": [
                    {
                        "recommendation_id": rec.recommendation_id,
                        "issue_id": rec.issue_id,
                        "priority": rec.priority.value,
                        "issue": rec.issue,
                        "solution": rec.solution,
                        "impact": rec.impact,
                        "effort": rec.effort,
                        "category": rec.category
                    }
                    for rec in report.recommendations
                ],
                "user_profile": {
                    "name": report.user_profile.name,
                    "behavior": report.user_profile.behavior,
                    "speed": report.user_profile.speed
                } if report.user_profile else None,
                "test_environment": report.test_environment,
                "notes": report.notes
            }
            
            result = await self._make_request("POST", "/api/reports/test", data)
            logger.info(f"Отчет о тестировании отправлен: {report.report_id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета о тестировании: {e}")
            return {"error": str(e)}
    
    async def send_issue(self, issue: Issue) -> Dict[str, Any]:
        """Отправка найденной проблемы в бэкенд"""
        try:
            data = {
                "issue_id": issue.issue_id,
                "type": issue.type,
                "severity": issue.severity.value,
                "description": issue.description,
                "location": issue.location,
                "screenshot_path": issue.screenshot_path,
                "recommendation": issue.recommendation,
                "detected_at": issue.detected_at.isoformat()
            }
            
            result = await self._make_request("POST", "/api/issues", data)
            logger.info(f"Проблема отправлена: {issue.issue_id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка отправки проблемы: {e}")
            return {"error": str(e)}
    
    async def get_test_scenarios(self) -> List[Dict[str, Any]]:
        """Получение списка тестовых сценариев из бэкенда"""
        try:
            result = await self._make_request("GET", "/api/scenarios")
            return result.get("scenarios", [])
            
        except Exception as e:
            logger.error(f"Ошибка получения сценариев: {e}")
            return []
    
    async def get_user_profiles(self) -> List[Dict[str, Any]]:
        """Получение профилей пользователей из бэкенда"""
        try:
            result = await self._make_request("GET", "/api/profiles")
            return result.get("profiles", [])
            
        except Exception as e:
            logger.error(f"Ошибка получения профилей: {e}")
            return []
    
    # Методы для работы с LLM-роутером
    
    async def send_context_to_llm(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка контекста в LLM-роутер для получения инструкций"""
        try:
            data = {
                "context": context_data,
                "timestamp": datetime.now().isoformat(),
                "session_id": context_data.get("session_id")
            }
            
            result = await self._make_request("POST", "/api/llm/context", data)
            logger.info("Контекст отправлен в LLM-роутер")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка отправки контекста в LLM: {e}")
            return {"error": str(e)}
    
    async def get_llm_instruction(self, session_id: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Получение инструкции от LLM-роутера"""
        try:
            data = {
                "session_id": session_id,
                "current_context": current_context,
                "request_type": "instruction"
            }
            
            result = await self._make_request("POST", "/api/llm/instruction", data)
            logger.info(f"Получена инструкция от LLM для сессии {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения инструкции от LLM: {e}")
            return {"error": str(e)}
    
    async def send_action_result(self, session_id: str, action: str, 
                               result: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка результата действия в LLM-роутер"""
        try:
            data = {
                "session_id": session_id,
                "action": action,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            result = await self._make_request("POST", "/api/llm/action-result", data)
            logger.info(f"Результат действия отправлен в LLM: {action}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка отправки результата действия: {e}")
            return {"error": str(e)}
    
    # Методы для работы с RAG-сервисом
    
    async def send_to_rag(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Отправка данных в RAG-сервис для анализа"""
        try:
            result = await self._make_request("POST", "/api/rag/analyze", data)
            logger.info("Данные отправлены в RAG-сервис")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка отправки данных в RAG: {e}")
            return {"error": str(e)}
    
    async def get_rag_insights(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Получение инсайтов от RAG-сервиса"""
        try:
            data = {
                "query": query,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
            result = await self._make_request("POST", "/api/rag/insights", data)
            logger.info("Получены инсайты от RAG-сервиса")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения инсайтов от RAG: {e}")
            return {"error": str(e)}
    
    # Утилитарные методы
    
    async def health_check(self) -> bool:
        """Проверка здоровья API"""
        try:
            result = await self._make_request("GET", "/health")
            return "status" in result and result["status"] == "ok"
            
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья API: {e}")
            return False
    
    async def get_api_info(self) -> Dict[str, Any]:
        """Получение информации об API"""
        try:
            result = await self._make_request("GET", "/api/info")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения информации об API: {e}")
            return {"error": str(e)} 