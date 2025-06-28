"""
Конфигурация User Experience Bot
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения UX Bot"""
    
    # Основные настройки
    environment: str = Field(default="development", env="UXBOT_ENVIRONMENT")
    log_level: str = Field(default="INFO", env="UXBOT_LOG_LEVEL")
    report_dir: str = Field(default="./reports", env="UXBOT_REPORT_DIR")
    
    # API настройки
    backend_url: str = Field(default="http://localhost:8000", env="BACKEND_URL")
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # База данных
    database_url: str = Field(
        default="postgresql+asyncpg://uxbot:uxbot@localhost/uxbot_db",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Selenium/Playwright настройки
    browser_type: str = Field(default="chrome", env="BROWSER_TYPE")
    headless: bool = Field(default=True, env="HEADLESS")
    browser_timeout: int = Field(default=30, env="BROWSER_TIMEOUT")
    browser_window_width: int = Field(default=1920, env="BROWSER_WINDOW_WIDTH")
    browser_window_height: int = Field(default=1080, env="BROWSER_WINDOW_HEIGHT")
    
    # Тестирование
    test_parallel_workers: int = Field(default=4, env="TEST_PARALLEL_WORKERS")
    test_retry_count: int = Field(default=3, env="TEST_RETRY_COUNT")
    test_timeout: int = Field(default=300, env="TEST_TIMEOUT")
    
    # Мониторинг
    prometheus_port: int = Field(default=9091, env="PROMETHEUS_PORT")
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    
    # Отчеты
    report_formats: List[str] = Field(default=["json", "html"], env="REPORT_FORMATS")
    screenshot_on_failure: bool = Field(default=True, env="SCREENSHOT_ON_FAILURE")
    video_recording: bool = Field(default=False, env="VIDEO_RECORDING")
    
    # Пользовательские данные
    test_user_email: str = Field(default="test@relink.com", env="TEST_USER_EMAIL")
    test_user_password: str = Field(default="testpass123", env="TEST_USER_PASSWORD")
    
    # Домены для тестирования
    test_domains: List[str] = Field(
        default=["example.com", "test-site.com"],
        env="TEST_DOMAINS"
    )
    
    # Микросервисы
    llm_tuning_url: str = Field(default="http://localhost:8001", env="LLM_TUNING_URL")
    monitoring_url: str = Field(default="http://localhost:8002", env="MONITORING_URL")
    docs_url: str = Field(default="http://localhost:8003", env="DOCS_URL")
    testing_url: str = Field(default="http://localhost:8004", env="TESTING_URL")
    
    # WebSocket
    websocket_enabled: bool = Field(default=True, env="WEBSOCKET_ENABLED")
    websocket_url: str = Field(default="ws://localhost:8000/ws", env="WEBSOCKET_URL")
    
    # Кэширование
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # Безопасность
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    jwt_secret: str = Field(default="uxbot-secret-key", env="JWT_SECRET")
    
    # Логирование
    log_file: str = Field(default="./logs/uxbot.log", env="LOG_FILE")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Уведомления
    slack_webhook: Optional[str] = Field(default=None, env="SLACK_WEBHOOK")
    email_notifications: bool = Field(default=False, env="EMAIL_NOTIFICATIONS")
    
    @validator("test_domains", pre=True)
    def parse_test_domains(cls, v):
        """Парсинг доменов из строки"""
        if isinstance(v, str):
            return [domain.strip() for domain in v.split(",")]
        return v
    
    @validator("report_formats", pre=True)
    def parse_report_formats(cls, v):
        """Парсинг форматов отчетов из строки"""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()


class TestConfig:
    """Конфигурация для тестов"""
    
    # Тестовые данные
    TEST_USER = {
        "email": settings.test_user_email,
        "password": settings.test_user_password,
        "name": "Test User"
    }
    
    # Тестовые домены
    TEST_DOMAINS = settings.test_domains
    
    # Временные интервалы
    TIMEOUTS = {
        "page_load": 30,
        "element_wait": 10,
        "api_call": 15,
        "animation": 2
    }
    
    # Селекторы UI
    SELECTORS = {
        "login_form": "#login-form",
        "email_input": "input[name='email']",
        "password_input": "input[name='password']",
        "login_button": "button[type='submit']",
        "navigation_menu": ".navigation-menu",
        "main_content": ".main-content",
        "loading_spinner": ".loading-spinner",
        "error_message": ".error-message",
        "success_message": ".success-message"
    }
    
    # API endpoints
    API_ENDPOINTS = {
        "health": "/api/v1/health",
        "auth_login": "/api/v1/auth/login",
        "auth_register": "/api/v1/auth/register",
        "domains": "/api/v1/domains",
        "analysis": "/api/v1/seo/analyze",
        "history": "/api/v1/analysis_history",
        "benchmarks": "/api/v1/benchmarks",
        "settings": "/api/v1/settings",
        "ollama_status": "/api/v1/ollama_status"
    }
    
    # Сценарии тестирования
    SCENARIOS = {
        "wordpress_analysis": {
            "name": "WordPress Site Analysis",
            "description": "Полный анализ WordPress сайта",
            "steps": [
                "login",
                "navigate_to_analysis",
                "enter_domain",
                "start_analysis",
                "wait_for_completion",
                "check_results"
            ]
        },
        "seo_recommendations": {
            "name": "SEO Recommendations",
            "description": "Получение SEO рекомендаций",
            "steps": [
                "login",
                "navigate_to_seo",
                "select_domain",
                "generate_recommendations",
                "review_results"
            ]
        },
        "benchmark_testing": {
            "name": "Benchmark Testing",
            "description": "Запуск бенчмарков",
            "steps": [
                "login",
                "navigate_to_benchmarks",
                "select_benchmark",
                "run_test",
                "monitor_progress",
                "analyze_results"
            ]
        },
        "system_monitoring": {
            "name": "System Monitoring",
            "description": "Проверка мониторинга системы",
            "steps": [
                "login",
                "navigate_to_monitoring",
                "check_metrics",
                "verify_alerts",
                "export_data"
            ]
        }
    }


# Экспорт конфигураций
__all__ = ["settings", "TestConfig"] 