"""
User Experience Bot - Сервис тестирования пользовательского опыта reLink

Основной пакет для автоматизированного тестирования UI и API
с имитацией реального пользовательского поведения.
"""

__version__ = "1.0.0"
__author__ = "reLink Team"
__description__ = "UX Bot for reLink platform testing"

from .core import UXBot
from .config import settings
from .models import TestResult, TestScenario, UserAction

__all__ = [
    "UXBot",
    "settings", 
    "TestResult",
    "TestScenario",
    "UserAction"
] 