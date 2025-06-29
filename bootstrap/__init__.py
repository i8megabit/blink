"""
🚀 reLink Bootstrap - Единая основа для всех микросервисов

Этот модуль предоставляет общую инфраструктуру для всех микросервисов reLink:
- Конфигурация
- Подключение к БД
- LLM интеграция
- RAG сервисы
- Мониторинг
- Логирование
"""

__version__ = "1.0.0"
__author__ = "reLink Team"
__email__ = "i8megabit@gmail.com"

from .config import get_settings
from .database import get_database
from .cache import get_cache
from .llm_router import get_llm_router
from .rag_service import get_rag_service
from .ollama_client import get_ollama_client
from .monitoring import get_service_monitor
from .logging import setup_logging

__all__ = [
    "get_settings",
    "get_database", 
    "get_cache",
    "get_llm_router",
    "get_rag_service",
    "get_ollama_client",
    "get_service_monitor",
    "setup_logging"
] 