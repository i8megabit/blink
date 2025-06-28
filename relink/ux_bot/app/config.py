"""
Конфигурация UX-бота для проекта reLink
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Settings:
    """Настройки UX-бота"""
    
    # URL фронтенда reLink
    frontend_url: str = "http://localhost:3000"
    
    # URL бэкенда reLink
    backend_url: str = "http://localhost:8000"
    
    # URL LLM-роутера
    llm_router_url: str = "http://localhost:8001"
    
    # URL RAG-сервиса
    rag_service_url: str = "http://localhost:8002"
    
    # Настройки браузера
    browser_headless: bool = True
    browser_timeout: int = 30
    browser_implicit_wait: int = 10
    browser_viewport_width: int = 1920
    browser_viewport_height: int = 1080
    
    # Настройки тестирования
    test_timeout: int = 300  # 5 минут
    screenshot_dir: str = "screenshots"
    report_dir: str = "reports"
    
    # Настройки логирования
    log_level: str = "INFO"
    log_file: str = "ux_bot.log"
    
    # Настройки пользовательских профилей
    user_profiles: list = None
    
    # Настройки сценариев
    default_scenarios: list = None
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.user_profiles is None:
            self.user_profiles = [
                {
                    "name": "SEO-специалист",
                    "description": "Профессиональный SEO-инженер",
                    "behavior": "expert",
                    "speed": "normal"
                },
                {
                    "name": "Новичок",
                    "description": "Пользователь без опыта в SEO",
                    "behavior": "exploratory",
                    "speed": "slow"
                },
                {
                    "name": "Менеджер",
                    "description": "Менеджер проектов",
                    "behavior": "goal-oriented",
                    "speed": "fast"
                }
            ]
        
        if self.default_scenarios is None:
            self.default_scenarios = [
                "login_flow",
                "domain_analysis",
                "settings_management",
                "report_generation",
                "data_export"
            ]
        
        # Создание директорий
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)


# Создание глобального объекта настроек
settings = Settings()

# Переопределение настроек из переменных окружения
if os.getenv("FRONTEND_URL"):
    settings.frontend_url = os.getenv("FRONTEND_URL")

if os.getenv("BACKEND_URL"):
    settings.backend_url = os.getenv("BACKEND_URL")

if os.getenv("LLM_ROUTER_URL"):
    settings.llm_router_url = os.getenv("LLM_ROUTER_URL")

if os.getenv("RAG_SERVICE_URL"):
    settings.rag_service_url = os.getenv("RAG_SERVICE_URL")

if os.getenv("BROWSER_HEADLESS"):
    settings.browser_headless = os.getenv("BROWSER_HEADLESS").lower() == "true"

if os.getenv("LOG_LEVEL"):
    settings.log_level = os.getenv("LOG_LEVEL") 