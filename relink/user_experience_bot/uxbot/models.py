"""
Модели данных для User Experience Bot
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class TestStatus(str, Enum):
    """Статусы тестов"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPriority(str, Enum):
    """Приоритеты тестов"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    """Типы действий пользователя"""
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    HOVER = "hover"
    DRAG = "drag"
    NAVIGATE = "navigate"
    WAIT = "wait"
    API_CALL = "api_call"
    ASSERT = "assert"


class ElementType(str, Enum):
    """Типы элементов UI"""
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXT = "text"
    IMAGE = "image"
    FORM = "form"
    MODAL = "modal"
    TOOLTIP = "tooltip"


class UserAction(BaseModel):
    """Действие пользователя"""
    id: UUID = Field(default_factory=uuid4)
    action_type: ActionType
    element_selector: Optional[str] = None
    element_type: Optional[ElementType] = None
    value: Optional[str] = None
    coordinates: Optional[Dict[str, int]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class TestStep(BaseModel):
    """Шаг теста"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    actions: List[UserAction] = Field(default_factory=list)
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    class Config:
        use_enum_values = True


class TestScenario(BaseModel):
    """Сценарий тестирования"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    category: str
    priority: TestPriority = TestPriority.MEDIUM
    steps: List[TestStep] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    estimated_duration: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class TestResult(BaseModel):
    """Результат выполнения теста"""
    id: UUID = Field(default_factory=uuid4)
    scenario_id: UUID
    scenario_name: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    error_steps: int
    success_rate: float
    error_message: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    video_path: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    browser_info: Dict[str, Any] = Field(default_factory=dict)
    environment_info: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
    
    @validator("success_rate", pre=True, always=True)
    def calculate_success_rate(cls, v, values):
        """Вычисление процента успешности"""
        if "total_steps" in values and values["total_steps"] > 0:
            return (values.get("passed_steps", 0) / values["total_steps"]) * 100
        return 0.0


class TestSuite(BaseModel):
    """Набор тестов"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    scenarios: List[TestScenario] = Field(default_factory=list)
    priority: TestPriority = TestPriority.MEDIUM
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TestExecution(BaseModel):
    """Выполнение набора тестов"""
    id: UUID = Field(default_factory=uuid4)
    suite_id: UUID
    suite_name: str
    results: List[TestResult] = Field(default_factory=list)
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    skipped_scenarios: int
    error_scenarios: int
    success_rate: float
    environment: str
    browser_type: str
    parallel_workers: int
    logs: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class PerformanceMetrics(BaseModel):
    """Метрики производительности"""
    page_load_time: float
    first_contentful_paint: float
    largest_contentful_paint: float
    first_input_delay: float
    cumulative_layout_shift: float
    time_to_interactive: float
    dom_content_loaded: float
    window_load: float
    api_response_time: float
    memory_usage: float
    cpu_usage: float
    network_requests: int
    errors_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UIElement(BaseModel):
    """Элемент пользовательского интерфейса"""
    selector: str
    element_type: ElementType
    text: Optional[str] = None
    value: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    is_visible: bool = True
    is_enabled: bool = True
    coordinates: Dict[str, int] = Field(default_factory=dict)
    size: Dict[str, int] = Field(default_factory=dict)
    screenshot: Optional[str] = None
    
    class Config:
        use_enum_values = True


class PageState(BaseModel):
    """Состояние страницы"""
    url: str
    title: str
    elements: List[UIElement] = Field(default_factory=list)
    performance_metrics: Optional[PerformanceMetrics] = None
    screenshot: Optional[str] = None
    html_content: Optional[str] = None
    console_logs: List[str] = Field(default_factory=list)
    network_requests: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TestReport(BaseModel):
    """Отчет о тестировании"""
    id: UUID = Field(default_factory=uuid4)
    execution_id: UUID
    title: str
    description: str
    summary: Dict[str, Any] = Field(default_factory=dict)
    results: List[TestResult] = Field(default_factory=list)
    performance_summary: Dict[str, Any] = Field(default_factory=dict)
    issues_found: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    format: str = "json"
    file_path: Optional[str] = None


class APITestCase(BaseModel):
    """Тестовый случай для API"""
    id: UUID = Field(default_factory=uuid4)
    name: str
    endpoint: str
    method: str
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    expected_status: int
    expected_response: Optional[Dict[str, Any]] = None
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    timeout: int = 30
    retry_count: int = 3


class APITestResult(BaseModel):
    """Результат тестирования API"""
    id: UUID = Field(default_factory=uuid4)
    test_case_id: UUID
    test_case_name: str
    status: TestStatus
    request_time: datetime
    response_time: Optional[datetime] = None
    duration: Optional[float] = None
    status_code: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = Field(default_factory=list)
    performance_metrics: Optional[PerformanceMetrics] = None


class UserSession(BaseModel):
    """Сессия пользователя"""
    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[str] = None
    email: str
    is_authenticated: bool = False
    token: Optional[str] = None
    session_start: datetime = Field(default_factory=datetime.utcnow)
    session_end: Optional[datetime] = None
    actions: List[UserAction] = Field(default_factory=list)
    page_states: List[PageState] = Field(default_factory=list)
    performance_metrics: List[PerformanceMetrics] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class TestEnvironment(BaseModel):
    """Окружение для тестирования"""
    name: str
    description: str
    backend_url: str
    frontend_url: str
    database_url: str
    redis_url: str
    browser_type: str
    headless: bool
    window_size: Dict[str, int]
    timeouts: Dict[str, int]
    credentials: Dict[str, str] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)


# Экспорт моделей
__all__ = [
    "TestStatus",
    "TestPriority", 
    "ActionType",
    "ElementType",
    "UserAction",
    "TestStep",
    "TestScenario",
    "TestResult",
    "TestSuite",
    "TestExecution",
    "PerformanceMetrics",
    "UIElement",
    "PageState",
    "TestReport",
    "APITestCase",
    "APITestResult",
    "UserSession",
    "TestEnvironment"
] 