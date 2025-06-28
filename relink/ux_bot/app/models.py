"""
Модели данных для UX-бота
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TestStatus(Enum):
    """Статусы тестов"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ElementType(Enum):
    """Типы элементов UI"""
    BUTTON = "button"
    INPUT = "input"
    LINK = "link"
    IMAGE = "image"
    TEXT = "text"
    FORM = "form"
    NAVIGATION = "navigation"
    MODAL = "modal"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TABLE = "table"
    CARD = "card"
    OTHER = "other"


class IssueSeverity(Enum):
    """Уровни критичности проблем"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class UIElement:
    """Элемент пользовательского интерфейса"""
    selector: str
    element_type: ElementType
    text: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)
    is_visible: bool = True
    is_enabled: bool = True
    position: Optional[Dict[str, int]] = None
    size: Optional[Dict[str, int]] = None


@dataclass
class TestStep:
    """Шаг тестового сценария"""
    step_id: str
    description: str
    action: str  # click, type, scroll, wait, etc.
    target: Optional[str] = None  # селектор элемента
    value: Optional[str] = None  # значение для ввода
    expected_result: Optional[str] = None
    timeout: int = 10
    retry_count: int = 3
    dependencies: List[str] = field(default_factory=list)


@dataclass
class TestScenario:
    """Тестовый сценарий"""
    scenario_id: str
    name: str
    description: str
    steps: List[TestStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    priority: str = "medium"
    timeout: int = 300
    user_profile: Optional[str] = None


@dataclass
class TestResult:
    """Результат выполнения теста"""
    test_id: str
    scenario_id: str
    step_id: Optional[str] = None
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PageAnalysis:
    """Анализ страницы"""
    url: str
    title: str
    elements: List[UIElement] = field(default_factory=list)
    accessibility_issues: List[Dict[str, Any]] = field(default_factory=list)
    responsiveness_issues: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    screenshot_path: Optional[str] = None
    analysis_time: datetime = field(default_factory=datetime.now)


@dataclass
class UserProfile:
    """Профиль пользователя для симуляции"""
    name: str
    description: str
    behavior: str  # expert, exploratory, goal-oriented
    speed: str  # slow, normal, fast
    preferences: Dict[str, Any] = field(default_factory=dict)
    typical_actions: List[str] = field(default_factory=list)


@dataclass
class ScenarioContext:
    """Контекст выполнения сценария"""
    scenario_id: str
    session_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    results: List[TestResult] = field(default_factory=list)
    start_time: float = field(default_factory=lambda: datetime.now().timestamp())
    browser_service: Optional[Any] = None
    api_client: Optional[Any] = None
    current_page: Optional[str] = None
    user_profile: Optional[UserProfile] = None


@dataclass
class Issue:
    """Проблема, найденная во время тестирования"""
    issue_id: str
    type: str  # accessibility, responsiveness, functionality, performance
    severity: IssueSeverity
    description: str
    location: Optional[str] = None  # URL или селектор
    element: Optional[UIElement] = None
    screenshot_path: Optional[str] = None
    recommendation: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class Recommendation:
    """Рекомендация по улучшению"""
    recommendation_id: str
    issue_id: str
    priority: IssueSeverity
    issue: str
    solution: str
    impact: str  # high, medium, low
    effort: str  # low, medium, high
    category: str  # accessibility, performance, usability, security


@dataclass
class TestReport:
    """Отчет о тестировании"""
    report_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Статистика
    total_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    
    # Проблемы и рекомендации
    issues: List[Issue] = field(default_factory=list)
    recommendations: List[Recommendation] = field(default_factory=list)
    
    # Детальные результаты
    page_analyses: List[PageAnalysis] = field(default_factory=list)
    scenario_results: List[TestResult] = field(default_factory=list)
    
    # Метаданные
    user_profile: Optional[UserProfile] = None
    test_environment: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        """Процент успешных тестов"""
        if self.total_tests == 0:
            return 0.0
        return (self.successful_tests / self.total_tests) * 100
    
    @property
    def critical_issues_count(self) -> int:
        """Количество критических проблем"""
        return len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL])
    
    @property
    def high_priority_recommendations(self) -> List[Recommendation]:
        """Рекомендации высокого приоритета"""
        return [r for r in self.recommendations if r.priority in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]]


@dataclass
class BrowserConfig:
    """Конфигурация браузера"""
    engine: str = "selenium"  # selenium, playwright
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    viewport_width: int = 1920
    viewport_height: int = 1080
    wait_timeout: int = 10
    implicit_wait: int = 5
    additional_args: List[str] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIConfig:
    """Конфигурация API клиента"""
    base_url: str
    timeout: int = 30
    retry_count: int = 3
    headers: Dict[str, str] = field(default_factory=dict)
    auth_token: Optional[str] = None
    verify_ssl: bool = True 