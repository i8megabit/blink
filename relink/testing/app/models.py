"""
Модели данных для микросервиса тестирования reLink
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
import uuid


class TestType(str, Enum):
    """Типы тестов"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    LOAD = "load"
    SECURITY = "security"
    API = "api"
    UI = "ui"
    E2E = "e2e"
    BENCHMARK = "benchmark"


class TestStatus(str, Enum):
    """Статусы тестов"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TestPriority(str, Enum):
    """Приоритеты тестов"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestEnvironment(str, Enum):
    """Окружения для тестирования"""
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TestRequest(BaseModel):
    """Запрос на запуск теста"""
    name: str = Field(..., min_length=1, max_length=200, description="Название теста")
    description: Optional[str] = Field(None, max_length=1000, description="Описание теста")
    test_type: TestType = Field(..., description="Тип теста")
    priority: TestPriority = Field(default=TestPriority.MEDIUM, description="Приоритет")
    environment: TestEnvironment = Field(default=TestEnvironment.LOCAL, description="Окружение")
    
    # Параметры теста
    timeout: Optional[int] = Field(None, ge=1, le=3600, description="Таймаут в секундах")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Параметры теста")
    
    # Настройки выполнения
    retry_count: int = Field(default=0, ge=0, le=5, description="Количество повторов")
    parallel: bool = Field(default=False, description="Запуск в параллели")
    
    # Зависимости
    dependencies: Optional[List[str]] = Field(default_factory=list, description="Зависимости от других тестов")
    
    @validator("name")
    def validate_name(cls, v):
        """Валидация названия теста"""
        if not v.strip():
            raise ValueError("Название теста не может быть пустым")
        return v.strip()
    
    @validator("timeout")
    def validate_timeout(cls, v, values):
        """Валидация таймаута в зависимости от типа теста"""
        if v is not None:
            test_type = values.get("test_type")
            if test_type == TestType.UNIT and v > 60:
                raise ValueError("Unit тесты не могут иметь таймаут больше 60 секунд")
            elif test_type == TestType.PERFORMANCE and v < 30:
                raise ValueError("Performance тесты должны иметь таймаут минимум 30 секунд")
        return v


class TestResult(BaseModel):
    """Результат выполнения теста"""
    test_id: str = Field(..., description="ID теста")
    status: TestStatus = Field(..., description="Статус выполнения")
    
    # Временные метки
    started_at: datetime = Field(..., description="Время начала")
    finished_at: Optional[datetime] = Field(None, description="Время завершения")
    duration: Optional[float] = Field(None, ge=0, description="Длительность в секундах")
    
    # Результаты
    passed: Optional[int] = Field(None, ge=0, description="Количество пройденных проверок")
    failed: Optional[int] = Field(None, ge=0, description="Количество проваленных проверок")
    skipped: Optional[int] = Field(None, ge=0, description="Количество пропущенных проверок")
    total: Optional[int] = Field(None, ge=0, description="Общее количество проверок")
    
    # Детали
    message: Optional[str] = Field(None, description="Сообщение о результате")
    error: Optional[str] = Field(None, description="Ошибка, если есть")
    stack_trace: Optional[str] = Field(None, description="Stack trace ошибки")
    
    # Метрики
    memory_usage: Optional[float] = Field(None, ge=0, description="Использование памяти в MB")
    cpu_usage: Optional[float] = Field(None, ge=0, le=100, description="Использование CPU в %")
    
    # Дополнительные данные
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Дополнительные данные")
    
    @root_validator
    def validate_timing(cls, values):
        """Валидация временных меток"""
        started_at = values.get("started_at")
        finished_at = values.get("finished_at")
        
        if finished_at and started_at and finished_at < started_at:
            raise ValueError("Время завершения не может быть раньше времени начала")
        
        if finished_at and started_at:
            duration = (finished_at - started_at).total_seconds()
            values["duration"] = duration
        
        return values
    
    @property
    def is_successful(self) -> bool:
        """Проверка успешности теста"""
        return self.status in [TestStatus.PASSED, TestStatus.SKIPPED]
    
    @property
    def success_rate(self) -> Optional[float]:
        """Процент успешности"""
        if self.total and self.total > 0:
            return (self.passed or 0) / self.total * 100
        return None


class TestSuite(BaseModel):
    """Набор тестов"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Уникальный ID")
    name: str = Field(..., min_length=1, max_length=200, description="Название набора")
    description: Optional[str] = Field(None, max_length=1000, description="Описание")
    
    # Тесты в наборе
    tests: List[TestRequest] = Field(..., min_items=1, description="Список тестов")
    
    # Настройки выполнения
    parallel: bool = Field(default=False, description="Параллельное выполнение")
    stop_on_failure: bool = Field(default=False, description="Остановка при первой ошибке")
    timeout: Optional[int] = Field(None, ge=1, le=7200, description="Общий таймаут")
    
    # Метаданные
    tags: List[str] = Field(default_factory=list, description="Теги")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Время создания")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Время обновления")
    
    @validator("tests")
    def validate_tests(cls, v):
        """Валидация списка тестов"""
        if not v:
            raise ValueError("Набор тестов должен содержать хотя бы один тест")
        
        # Проверка уникальности названий тестов
        names = [test.name for test in v]
        if len(names) != len(set(names)):
            raise ValueError("Названия тестов в наборе должны быть уникальными")
        
        return v


class TestExecution(BaseModel):
    """Выполнение теста или набора тестов"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Уникальный ID")
    
    # Что выполняется
    test_request: Optional[TestRequest] = Field(None, description="Запрос на выполнение теста")
    test_suite: Optional[TestSuite] = Field(None, description="Набор тестов")
    
    # Статус выполнения
    status: TestStatus = Field(default=TestStatus.PENDING, description="Статус")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Прогресс в %")
    
    # Временные метки
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Время создания")
    started_at: Optional[datetime] = Field(None, description="Время начала")
    finished_at: Optional[datetime] = Field(None, description="Время завершения")
    
    # Результаты
    results: List[TestResult] = Field(default_factory=list, description="Результаты тестов")
    
    # Метаданные
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные данные")
    
    @root_validator
    def validate_execution_type(cls, values):
        """Валидация типа выполнения"""
        test_request = values.get("test_request")
        test_suite = values.get("test_suite")
        
        if not test_request and not test_suite:
            raise ValueError("Должен быть указан либо test_request, либо test_suite")
        
        if test_request and test_suite:
            raise ValueError("Нельзя указывать одновременно test_request и test_suite")
        
        return values
    
    @property
    def is_single_test(self) -> bool:
        """Проверка, что это одиночный тест"""
        return self.test_request is not None
    
    @property
    def is_suite(self) -> bool:
        """Проверка, что это набор тестов"""
        return self.test_suite is not None
    
    @property
    def total_tests(self) -> int:
        """Общее количество тестов"""
        if self.test_request:
            return 1
        elif self.test_suite:
            return len(self.test_suite.tests)
        return 0
    
    @property
    def completed_tests(self) -> int:
        """Количество завершенных тестов"""
        return len([r for r in self.results if r.finished_at is not None])
    
    @property
    def successful_tests(self) -> int:
        """Количество успешных тестов"""
        return len([r for r in self.results if r.is_successful])
    
    @property
    def failed_tests(self) -> int:
        """Количество проваленных тестов"""
        return len([r for r in self.results if not r.is_successful and r.status != TestStatus.SKIPPED])


class TestReport(BaseModel):
    """Отчет о тестировании"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Уникальный ID")
    execution_id: str = Field(..., description="ID выполнения")
    
    # Общая статистика
    total_tests: int = Field(..., ge=0, description="Общее количество тестов")
    passed_tests: int = Field(..., ge=0, description="Пройденные тесты")
    failed_tests: int = Field(..., ge=0, description="Проваленные тесты")
    skipped_tests: int = Field(..., ge=0, description="Пропущенные тесты")
    
    # Временные метрики
    total_duration: float = Field(..., ge=0, description="Общая длительность")
    average_duration: float = Field(..., ge=0, description="Средняя длительность")
    
    # Успешность
    success_rate: float = Field(..., ge=0, le=100, description="Процент успешности")
    
    # Детали
    results: List[TestResult] = Field(..., description="Детальные результаты")
    
    # Метаданные
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Время генерации")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные данные")
    
    @validator("success_rate")
    def validate_success_rate(cls, v):
        """Валидация процента успешности"""
        if not 0 <= v <= 100:
            raise ValueError("Процент успешности должен быть от 0 до 100")
        return v
    
    @property
    def is_successful(self) -> bool:
        """Проверка общей успешности"""
        return self.failed_tests == 0
    
    @property
    def summary(self) -> Dict[str, Any]:
        """Краткая сводка"""
        return {
            "total": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "skipped": self.skipped_tests,
            "success_rate": self.success_rate,
            "duration": self.total_duration,
            "is_successful": self.is_successful
        }


class TestMetrics(BaseModel):
    """Метрики тестирования"""
    execution_id: str = Field(..., description="ID выполнения")
    
    # Метрики производительности
    response_time_avg: float = Field(..., ge=0, description="Среднее время ответа")
    response_time_min: float = Field(..., ge=0, description="Минимальное время ответа")
    response_time_max: float = Field(..., ge=0, description="Максимальное время ответа")
    response_time_std: float = Field(..., ge=0, description="Стандартное отклонение времени ответа")
    
    # Метрики ресурсов
    memory_usage_avg: float = Field(..., ge=0, description="Среднее использование памяти")
    cpu_usage_avg: float = Field(..., ge=0, le=100, description="Среднее использование CPU")
    
    # Метрики пропускной способности
    throughput: float = Field(..., ge=0, description="Пропускная способность (запросов/сек)")
    
    # Метрики ошибок
    error_rate: float = Field(..., ge=0, le=100, description="Процент ошибок")
    
    # Временные метки
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="Время сбора")
    
    @property
    def is_performance_good(self) -> bool:
        """Проверка качества производительности"""
        return (
            self.response_time_avg < 1.0 and  # Меньше 1 секунды
            self.error_rate < 5.0 and  # Меньше 5% ошибок
            self.cpu_usage_avg < 80.0  # Меньше 80% CPU
        )


class TestFilter(BaseModel):
    """Фильтр для поиска тестов"""
    test_type: Optional[TestType] = Field(None, description="Тип теста")
    status: Optional[TestStatus] = Field(None, description="Статус")
    priority: Optional[TestPriority] = Field(None, description="Приоритет")
    environment: Optional[TestEnvironment] = Field(None, description="Окружение")
    
    # Временные фильтры
    created_after: Optional[datetime] = Field(None, description="Создано после")
    created_before: Optional[datetime] = Field(None, description="Создано до")
    
    # Текстовые фильтры
    name_contains: Optional[str] = Field(None, description="Название содержит")
    description_contains: Optional[str] = Field(None, description="Описание содержит")
    
    # Теги
    tags: Optional[List[str]] = Field(None, description="Теги")
    
    # Пагинация
    limit: int = Field(default=50, ge=1, le=1000, description="Лимит результатов")
    offset: int = Field(default=0, ge=0, description="Смещение")
    
    # Сортировка
    sort_by: str = Field(default="created_at", description="Поле для сортировки")
    sort_order: str = Field(default="desc", description="Порядок сортировки")
    
    @validator("sort_order")
    def validate_sort_order(cls, v):
        """Валидация порядка сортировки"""
        if v not in ["asc", "desc"]:
            raise ValueError("Порядок сортировки должен быть 'asc' или 'desc'")
        return v 