"""
📝 Логирование для всех микросервисов reLink
"""

import sys
import logging
from typing import Optional
import structlog
from pythonjsonlogger import jsonlogger

from .config import get_settings

def setup_logging():
    """Настройка структурированного логирования"""
    
    settings = get_settings()
    
    # Настройка базового логирования
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(message)s",
        stream=sys.stdout
    )
    
    # Настройка structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Создание логгера
    logger = structlog.get_logger()
    logger.info(
        "Logging configured",
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT
    )
    
    return logger

def get_logger(name: Optional[str] = None):
    """Получение логгера"""
    return structlog.get_logger(name) 