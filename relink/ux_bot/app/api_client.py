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

logger = logging.getLogger(__name__)

class APIClient:
    """Клиент для взаимодействия с API reLink"""
    
    def __init__(self):
        self.base_url = settings.BACKEND_URL
        self.llm_router_url = f"{self.base_url}/api/llm"
        self.rag_url = f"{self.base_url}/api/rag"
        self.testing_url = f"{self.base_url}/api/testing"
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def get_llm_guidance(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Получение руководства от LLM роутера
        
        Args:
            request_data: Данные запроса включая профиль пользователя и контекст
            
        Returns:
            Словарь с руководством для следующего действия
        """
        try:
            if not self.session:
                raise Exception("API клиент не инициализирован")
            
            # Формирование запроса к LLM роутеру
            llm_request = {
                "service_type": "ux_testing",
                "prompt": self._build_ux_prompt(request_data),
                "context": {
                    "session_id": request_data.get("session_id"),
                    "profile": request_data.get("profile"),
                    "current_context": request_data.get("current_context"),
                    "action_history": request_data.get("action_history", [])
                },
                "llm_model": "qwen2.5:7b-instruct-turbo",
                "temperature": 0.7,
                "max_tokens": 1024,
                "use_rag": True,
                "priority": "high"
            }
            
            logger.info(f"Отправка запроса к LLM роутеру: {llm_request['service_type']}")
            
            async with self.session.post(
                f"{self.llm_router_url}/process",
                json=llm_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info("Получен ответ от LLM роутера")
                    return self._parse_llm_response(result)
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка LLM роутера: {response.status} - {error_text}")
                    return self._get_fallback_guidance()
                    
        except Exception as e:
            logger.error(f"Ошибка получения руководства от LLM: {e}")
            return self._get_fallback_guidance()
    
    def _build_ux_prompt(self, request_data: Dict[str, Any]) -> str:
        """Построение промпта для UX тестирования"""
        profile = request_data.get("profile", {})
        context = request_data.get("current_context", {})
        history = request_data.get("action_history", [])
        
        prompt = f"""
Ты - эксперт по UX тестированию, анализирующий веб-интерфейс.

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
- Имя: {profile.get('name', 'Неизвестно')}
- Возраст: {profile.get('age', 'Неизвестно')}
- Профессия: {profile.get('occupation', 'Неизвестно')}
- Технический уровень: {profile.get('tech_level', 'Неизвестно')}
- Скорость просмотра: {profile.get('browsing_speed', 'Неизвестно')}
- Терпение: {profile.get('patience', 'Неизвестно')}
- Стиль исследования: {profile.get('exploration_style', 'Неизвестно')}

ТЕКУЩИЙ КОНТЕКСТ:
- URL: {context.get('url', 'Неизвестно')}
- Заголовок страницы: {context.get('title', 'Неизвестно')}
- Доступные элементы: {context.get('available_elements', [])}

ИСТОРИЯ ДЕЙСТВИЙ (последние 3):
{chr(10).join([f"- {action}" for action in history])}

ТВОЯ ЗАДАЧА:
Проанализируй ситуацию и дай конкретные инструкции для следующего действия, которое выполнит этот пользователь.

УЧТИ:
1. Характер пользователя (терпение, технический уровень)
2. Логику исследования интерфейса
3. Естественность поведения
4. Цель тестирования функционала

ОТВЕТ ДОЛЖЕН БЫТЬ В JSON ФОРМАТЕ:
{{
    "action": "тип_действия",
    "target": "селектор_или_описание_цели",
    "reason": "обоснование_действия",
    "expected_outcome": "ожидаемый_результат",
    "confidence": 0.0-1.0,
    "human_delay": "время_задержки_в_секундах"
}}

ДОСТУПНЫЕ ТИПЫ ДЕЙСТВИЙ:
- click: клик по элементу
- type: ввод текста (формат: "селектор:текст")
- scroll: прокрутка (up/down/top/bottom/селектор)
- hover: наведение на элемент
- wait: ожидание (время_в_секундах)
- navigate: переход по ссылке
- extract: извлечение данных (all_forms/all_links/селектор)
- analyze: анализ страницы
- custom_js: выполнение JS кода
- stop: завершение сессии

БУДЬ КОНКРЕТЕН И ПРАКТИЧЕН!
"""
        
        return prompt
    
    def _parse_llm_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Парсинг ответа от LLM"""
        try:
            content = response.get("content", "")
            
            # Попытка извлечь JSON из ответа
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                
                try:
                    parsed = json.loads(json_str)
                    logger.info(f"Успешно распарсен ответ LLM: {parsed.get('action')}")
                    return parsed
                except json.JSONDecodeError:
                    logger.warning("Не удалось распарсить JSON из ответа LLM")
            
            # Fallback - попытка извлечь действие из текста
            return self._extract_action_from_text(content)
            
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа LLM: {e}")
            return self._get_fallback_guidance()
    
    def _extract_action_from_text(self, text: str) -> Dict[str, Any]:
        """Извлечение действия из текстового ответа"""
        text_lower = text.lower()
        
        if "click" in text_lower:
            return {"action": "click", "target": "button", "reason": "Извлечено из текста", "confidence": 0.5}
        elif "type" in text_lower or "ввод" in text_lower:
            return {"action": "type", "target": "input:test", "reason": "Извлечено из текста", "confidence": 0.5}
        elif "scroll" in text_lower or "прокрут" in text_lower:
            return {"action": "scroll", "target": "down", "reason": "Извлечено из текста", "confidence": 0.5}
        elif "wait" in text_lower or "ждать" in text_lower:
            return {"action": "wait", "target": "2", "reason": "Извлечено из текста", "confidence": 0.5}
        else:
            return self._get_fallback_guidance()
    
    def _get_fallback_guidance(self) -> Dict[str, Any]:
        """Fallback руководство при ошибках"""
        return {
            "action": "wait",
            "target": "3",
            "reason": "Fallback - ожидание",
            "expected_outcome": "Пауза для анализа",
            "confidence": 0.3,
            "human_delay": 3
        }
    
    async def send_ui_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Отправка данных анализа UI в RAG
        
        Args:
            analysis_data: Данные анализа интерфейса
            
        Returns:
            True если успешно отправлено
        """
        try:
            if not self.session:
                raise Exception("API клиент не инициализирован")
            
            # Формирование данных для RAG
            rag_data = {
                "type": "ui_analysis",
                "session_id": analysis_data.get("session_id"),
                "profile_id": analysis_data.get("profile_id"),
                "url": analysis_data.get("url"),
                "timestamp": analysis_data.get("timestamp"),
                "content": json.dumps(analysis_data.get("analysis", {}), ensure_ascii=False),
                "metadata": {
                    "source": "ux_bot",
                    "analysis_type": "ui_structure",
                    "profile": analysis_data.get("profile_id")
                }
            }
            
            logger.info(f"Отправка анализа UI в RAG: {analysis_data.get('url')}")
            
            async with self.session.post(
                f"{self.rag_url}/store",
                json=rag_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    logger.info("Анализ UI успешно отправлен в RAG")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка отправки в RAG: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка отправки анализа UI: {e}")
            return False
    
    async def send_test_report(self, report_data: Dict[str, Any]) -> bool:
        """
        Отправка отчета о тестировании
        
        Args:
            report_data: Данные отчета
            
        Returns:
            True если успешно отправлено
        """
        try:
            if not self.session:
                raise Exception("API клиент не инициализирован")
            
            logger.info(f"Отправка отчета о тестировании: {report_data.get('session_id')}")
            
            async with self.session.post(
                f"{self.testing_url}/reports",
                json=report_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    logger.info("Отчет о тестировании успешно отправлен")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка отправки отчета: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
            return False
    
    async def get_rag_context(self, query: str, session_id: str) -> List[Dict[str, Any]]:
        """
        Получение контекста из RAG для улучшения решений
        
        Args:
            query: Запрос для поиска
            session_id: ID сессии
            
        Returns:
            Список релевантных документов
        """
        try:
            if not self.session:
                raise Exception("API клиент не инициализирован")
            
            search_data = {
                "query": query,
                "session_id": session_id,
                "limit": 5,
                "filters": {
                    "type": "ui_analysis",
                    "source": "ux_bot"
                }
            }
            
            logger.info(f"Поиск контекста в RAG: {query}")
            
            async with self.session.post(
                f"{self.rag_url}/search",
                json=search_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Найдено {len(result.get('documents', []))} документов в RAG")
                    return result.get("documents", [])
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка поиска в RAG: {response.status} - {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Ошибка получения контекста из RAG: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Проверка здоровья API"""
        try:
            if not self.session:
                return False
            
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья API: {e}")
            return False
    
    async def get_llm_router_stats(self) -> Dict[str, Any]:
        """Получение статистики LLM роутера"""
        try:
            if not self.session:
                raise Exception("API клиент не инициализирован")
            
            async with self.session.get(f"{self.llm_router_url}/stats") as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Ошибка получения статистики LLM: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Ошибка получения статистики LLM: {e}")
            return {} 