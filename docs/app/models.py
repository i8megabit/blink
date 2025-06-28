"""
Pydantic модели для микросервиса документации
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VersionInfo(BaseModel):
    """Информация о версии"""
    version: str = Field(..., description="Номер версии")
    build_date: Optional[str] = Field(None, description="Дата сборки")
    commit_hash: Optional[str] = Field(None, description="Хеш коммита")
    branch: Optional[str] = Field(None, description="Ветка")
    environment: Optional[str] = Field(None, description="Окружение")


class ChangelogEntry(BaseModel):
    """Запись в changelog"""
    version: str = Field(..., description="Версия")
    date: Optional[str] = Field(None, description="Дата")
    changes: List[str] = Field(default_factory=list, description="Список изменений")
    features: List[str] = Field(default_factory=list, description="Новые функции")
    fixes: List[str] = Field(default_factory=list, description="Исправления")
    breaking: List[str] = Field(default_factory=list, description="Критические изменения")


class DocumentationContent(BaseModel):
    """Содержимое документации"""
    title: str = Field(..., description="Заголовок")
    content: str = Field(..., description="Содержимое в HTML")
    raw_content: str = Field(..., description="Сырое содержимое")
    last_modified: Optional[datetime] = Field(None, description="Время последнего изменения")
    file_path: Optional[str] = Field(None, description="Путь к файлу")


class ReadmeInfo(BaseModel):
    """Информация о README"""
    title: str = Field(..., description="Заголовок")
    description: str = Field(..., description="Описание")
    sections: List[Dict[str, Any]] = Field(default_factory=list, description="Секции")
    content: str = Field(..., description="Полное содержимое в HTML")


class RoadmapInfo(BaseModel):
    """Информация о roadmap"""
    title: str = Field(..., description="Заголовок")
    phases: List[Dict[str, Any]] = Field(default_factory=list, description="Фазы разработки")
    features: List[Dict[str, Any]] = Field(default_factory=list, description="Планируемые функции")
    timeline: Optional[str] = Field(None, description="Временная шкала")


class FAQEntry(BaseModel):
    """Запись FAQ"""
    question: str = Field(..., description="Вопрос")
    answer: str = Field(..., description="Ответ")
    category: Optional[str] = Field(None, description="Категория")
    tags: List[str] = Field(default_factory=list, description="Теги")


class AboutInfo(BaseModel):
    """Информация о проекте"""
    name: str = Field(..., description="Название проекта")
    description: str = Field(..., description="Описание")
    version: str = Field(..., description="Версия")
    author: str = Field(..., description="Автор")
    license: str = Field(..., description="Лицензия")
    repository: Optional[str] = Field(None, description="Репозиторий")
    features: List[str] = Field(default_factory=list, description="Основные функции")


class HowItWorksInfo(BaseModel):
    """Информация о том, как работает система"""
    title: str = Field(..., description="Заголовок")
    overview: str = Field(..., description="Обзор")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Шаги работы")
    architecture: Optional[str] = Field(None, description="Архитектура")
    technologies: List[str] = Field(default_factory=list, description="Используемые технологии")


class CacheStats(BaseModel):
    """Статистика кэша"""
    connected: bool = Field(..., description="Подключен ли к Redis")
    total_keys: int = Field(0, description="Общее количество ключей")
    memory_used: str = Field("N/A", description="Используемая память")
    connected_clients: int = Field(0, description="Количество подключенных клиентов")
    uptime: int = Field(0, description="Время работы в секундах")
    error: Optional[str] = Field(None, description="Ошибка, если есть")


class HealthResponse(BaseModel):
    """Ответ на health check"""
    status: str = Field(..., description="Статус")
    timestamp: datetime = Field(..., description="Временная метка")
    version: str = Field(..., description="Версия сервиса")
    cache_status: str = Field(..., description="Статус кэша")
    uptime: Optional[float] = Field(None, description="Время работы")


class APIResponse(BaseModel):
    """Базовый ответ API"""
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение")
    data: Optional[Any] = Field(None, description="Данные")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Временная метка")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    success: bool = Field(False, description="Успешность операции")
    error: str = Field(..., description="Описание ошибки")
    error_code: Optional[str] = Field(None, description="Код ошибки")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Временная метка")


# 🚀 НОВЫЕ МОДЕЛИ ДЛЯ АВТОМАТИЧЕСКОЙ ДОКУМЕНТАЦИИ МИКРОСЕРВИСОВ

class MicroserviceInfo(BaseModel):
    """Информация о микросервисе"""
    name: str = Field(..., description="Название микросервиса")
    display_name: str = Field(..., description="Отображаемое название")
    version: str = Field(..., description="Версия")
    description: str = Field(..., description="Описание")
    category: str = Field(..., description="Категория")
    status: str = Field(..., description="Статус")
    health_url: str = Field(..., description="URL для проверки здоровья")
    docs_url: Optional[str] = Field(None, description="URL документации")
    api_url: Optional[str] = Field(None, description="URL API")
    repository_url: Optional[str] = Field(None, description="URL репозитория")
    technologies: List[str] = Field(default_factory=list, description="Используемые технологии")
    features: List[str] = Field(default_factory=list, description="Основные функции")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Дата создания")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Дата обновления")


class ServiceEndpoint(BaseModel):
    """Эндпоинт микросервиса"""
    path: str = Field(..., description="Путь эндпоинта")
    method: str = Field(..., description="HTTP метод")
    description: str = Field(..., description="Описание")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="Параметры")
    request_body: Optional[Dict[str, Any]] = Field(None, description="Тело запроса")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="Схема ответа")
    requires_auth: bool = Field(False, description="Требует ли аутентификации")
    rate_limit: Optional[int] = Field(None, description="Лимит запросов")
    deprecated: bool = Field(False, description="Устарел ли эндпоинт")


class ServiceDocumentation(BaseModel):
    """Документация микросервиса"""
    service: MicroserviceInfo = Field(..., description="Информация о сервисе")
    readme: Optional[str] = Field(None, description="README в markdown")
    api_docs: List[ServiceEndpoint] = Field(default_factory=list, description="API документация")
    architecture: Optional[str] = Field(None, description="Описание архитектуры")
    deployment: Optional[str] = Field(None, description="Инструкции по развертыванию")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Конфигурация")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Примеры использования")
    troubleshooting: Optional[str] = Field(None, description="Решение проблем")
    changelog: List[ChangelogEntry] = Field(default_factory=list, description="История изменений")
    last_sync: datetime = Field(default_factory=datetime.utcnow, description="Время последней синхронизации")


class ServiceDiscovery(BaseModel):
    """Обнаружение микросервисов"""
    service_name: str = Field(..., description="Название сервиса")
    base_url: str = Field(..., description="Базовый URL")
    health_endpoint: str = Field(..., description="Эндпоинт здоровья")
    docs_endpoint: Optional[str] = Field(None, description="Эндпоинт документации")
    openapi_endpoint: Optional[str] = Field(None, description="Эндпоинт OpenAPI")
    readme_path: Optional[str] = Field(None, description="Путь к README")
    enabled: bool = Field(True, description="Включен ли сервис")
    sync_interval: int = Field(300, description="Интервал синхронизации в секундах")
    last_check: Optional[datetime] = Field(None, description="Время последней проверки")


class DocumentationSync(BaseModel):
    """Синхронизация документации"""
    service_name: str = Field(..., description="Название сервиса")
    sync_type: str = Field(..., description="Тип синхронизации")
    status: str = Field(..., description="Статус")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Время начала")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    documents_updated: int = Field(0, description="Количество обновленных документов")
    documents_created: int = Field(0, description="Количество созданных документов")


class DocumentationSearch(BaseModel):
    """Поиск документации"""
    query: str = Field(..., description="Поисковый запрос")
    services: List[str] = Field(default_factory=list, description="Фильтр по сервисам")
    categories: List[str] = Field(default_factory=list, description="Фильтр по категориям")
    tags: List[str] = Field(default_factory=list, description="Фильтр по тегам")
    limit: int = Field(20, description="Лимит результатов")
    offset: int = Field(0, description="Смещение")


class DocumentationSearchResult(BaseModel):
    """Результат поиска документации"""
    query: str = Field(..., description="Поисковый запрос")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Результаты")
    total: int = Field(0, description="Общее количество")
    search_time_ms: int = Field(0, description="Время поиска в миллисекундах")
    suggestions: List[str] = Field(default_factory=list, description="Предложения") 