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