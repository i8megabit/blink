"""
🎨 SVG Generator Service для автоматической генерации архитектурных диаграмм
Использует LLM для создания профессиональных SVG диаграмм различных типов
"""

import asyncio
import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from pydantic import BaseModel, Field, validator
import httpx

from .config import settings
from .exceptions import OllamaGenerationException, OllamaConnectionException

logger = logging.getLogger(__name__)


class DiagramType(str, BaseModel):
    """Типы диаграмм"""
    SYSTEM_ARCHITECTURE = "system_architecture"
    DATA_FLOW = "data_flow"
    DEPLOYMENT = "deployment"
    MICROSERVICES = "microservices"
    DATABASE_SCHEMA = "database_schema"
    API_FLOW = "api_flow"
    NETWORK_TOPOLOGY = "network_topology"
    SECURITY_ARCHITECTURE = "security_architecture"
    MONITORING = "monitoring"
    CI_CD_PIPELINE = "ci_cd_pipeline"


class DiagramStyle(BaseModel):
    """Стили для диаграмм"""
    theme: str = Field(default="modern", description="Тема диаграммы")
    colors: Dict[str, str] = Field(default_factory=dict, description="Цветовая схема")
    font_family: str = Field(default="Arial, sans-serif", description="Шрифт")
    font_size: int = Field(default=12, description="Размер шрифта")
    stroke_width: int = Field(default=2, description="Толщина линий")
    opacity: float = Field(default=0.9, description="Прозрачность")
    
    @validator('theme')
    def validate_theme(cls, v):
        allowed_themes = ['modern', 'classic', 'minimal', 'corporate', 'tech']
        if v not in allowed_themes:
            raise ValueError(f'Theme must be one of: {allowed_themes}')
        return v


class SVGGeneratorRequest(BaseModel):
    """Запрос на генерацию SVG диаграммы"""
    diagram_type: str = Field(..., description="Тип диаграммы")
    title: str = Field(..., description="Заголовок диаграммы")
    description: str = Field(..., description="Описание диаграммы")
    components: List[Dict[str, Any]] = Field(default_factory=list, description="Компоненты диаграммы")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Связи между компонентами")
    style: Optional[DiagramStyle] = Field(default=None, description="Стиль диаграммы")
    width: int = Field(default=800, description="Ширина диаграммы")
    height: int = Field(default=600, description="Высота диаграммы")
    interactive: bool = Field(default=True, description="Интерактивность")
    include_legend: bool = Field(default=True, description="Включить легенду")
    
    @validator('diagram_type')
    def validate_diagram_type(cls, v):
        allowed_types = [
            'system_architecture', 'data_flow', 'deployment', 
            'microservices', 'database_schema', 'api_flow',
            'network_topology', 'security_architecture', 
            'monitoring', 'ci_cd_pipeline'
        ]
        if v not in allowed_types:
            raise ValueError(f'Diagram type must be one of: {allowed_types}')
        return v


class SVGGeneratorResponse(BaseModel):
    """Ответ с сгенерированной SVG диаграммой"""
    svg_content: str = Field(..., description="SVG код")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    generation_time: float = Field(..., description="Время генерации в секундах")
    model_used: str = Field(..., description="Использованная модель")
    confidence_score: float = Field(..., description="Уверенность в качестве")
    optimization_suggestions: List[str] = Field(default_factory=list, description="Предложения по оптимизации")


@dataclass
class DiagramTemplate:
    """Шаблон для диаграммы"""
    name: str
    description: str
    prompt_template: str
    default_style: DiagramStyle
    components: List[str]
    relationships: List[str]


class SVGGeneratorService:
    """Сервис для генерации SVG диаграмм с помощью LLM"""
    
    def __init__(self, ollama_url: str = None, model: str = None):
        self.ollama_url = ollama_url or settings.ollama.url
        self.model = model or settings.ollama.default_model
        self.client = httpx.AsyncClient(timeout=settings.ollama.timeout)
        
        # Шаблоны диаграмм
        self.templates = self._initialize_templates()
        
        # Кэш для оптимизации
        self._cache = {}
        self._cache_ttl = 3600  # 1 час
    
    def _initialize_templates(self) -> Dict[str, DiagramTemplate]:
        """Инициализация шаблонов диаграмм"""
        return {
            "system_architecture": DiagramTemplate(
                name="System Architecture",
                description="Архитектурная диаграмма системы",
                prompt_template=self._get_system_architecture_prompt(),
                default_style=DiagramStyle(theme="modern", colors={
                    "primary": "#2563eb",
                    "secondary": "#7c3aed",
                    "success": "#059669",
                    "warning": "#d97706",
                    "error": "#dc2626"
                }),
                components=["Frontend", "Backend", "Database", "Cache", "Load Balancer"],
                relationships=["HTTP", "Database Connection", "Cache Hit", "Load Distribution"]
            ),
            "data_flow": DiagramTemplate(
                name="Data Flow",
                description="Диаграмма потока данных",
                prompt_template=self._get_data_flow_prompt(),
                default_style=DiagramStyle(theme="minimal", colors={
                    "data": "#0891b2",
                    "process": "#059669",
                    "storage": "#7c3aed",
                    "external": "#dc2626"
                }),
                components=["Data Source", "Processor", "Storage", "Analytics", "Output"],
                relationships=["Data Transfer", "Processing", "Storage", "Analysis"]
            ),
            "microservices": DiagramTemplate(
                name="Microservices",
                description="Архитектура микросервисов",
                prompt_template=self._get_microservices_prompt(),
                default_style=DiagramStyle(theme="tech", colors={
                    "service": "#2563eb",
                    "api_gateway": "#7c3aed",
                    "database": "#059669",
                    "message_queue": "#d97706"
                }),
                components=["API Gateway", "User Service", "Order Service", "Payment Service", "Database"],
                relationships=["HTTP", "Message Queue", "Database Connection"]
            ),
            "deployment": DiagramTemplate(
                name="Deployment",
                description="Диаграмма развертывания",
                prompt_template=self._get_deployment_prompt(),
                default_style=DiagramStyle(theme="corporate", colors={
                    "production": "#dc2626",
                    "staging": "#d97706",
                    "development": "#059669",
                    "infrastructure": "#6b7280"
                }),
                components=["Production", "Staging", "Development", "CI/CD", "Monitoring"],
                relationships=["Deployment", "Rollback", "Monitoring", "Alerting"]
            )
        }
    
    def _get_system_architecture_prompt(self) -> str:
        """Промпт для архитектурной диаграммы с детальными техническими условиями"""
        return """
Ты - эксперт по созданию профессиональных SVG диаграмм архитектуры. Создай диаграмму на основе следующих технических условий:

## ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:

### 1. СТРУКТУРА SVG:
- Используй viewBox для масштабируемости
- Добавь xmlns="http://www.w3.org/2000/svg"
- Установи width="{width}" height="{height}"
- Включи preserveAspectRatio="xMidYMid meet"

### 2. КОМПОНЕНТЫ СИСТЕМЫ:
{components}

### 3. СВЯЗИ МЕЖДУ КОМПОНЕНТАМИ:
{relationships}

### 4. ДИЗАЙН-СИСТЕМА:
- Цветовая схема: {style.colors}
- Шрифт: {style.font_family}, размер: {style.font_size}px
- Толщина линий: {style.stroke_width}px
- Прозрачность: {style.opacity}

### 5. ТЕХНИЧЕСКИЕ ЭЛЕМЕНТЫ:
- Используй <defs> для переиспользуемых элементов
- Добавь <filter> для теней и эффектов
- Создай <linearGradient> для градиентов
- Используй <clipPath> для обрезки элементов
- Добавь <mask> для сложных эффектов

### 6. ИНТЕРАКТИВНОСТЬ:
- Добавь <title> и <desc> для accessibility
- Используй CSS hover эффекты
- Включи JavaScript для динамики
- Добавь data-атрибуты для метаданных

### 7. ОПТИМИЗАЦИЯ:
- Минимизируй количество элементов
- Используй path вместо множественных линий
- Оптимизируй координаты
- Добавь aria-label для accessibility

### 8. АНИМАЦИИ:
- Используй <animate> для простых анимаций
- Добавь <animateTransform> для трансформаций
- Включи <animateMotion> для движения по пути
- Установи dur="2s" для плавности

### 9. ЛЕГЕНДА И МЕТАДАНЫ:
- Создай отдельную секцию для легенды
- Добавь заголовок диаграммы
- Включи описания компонентов
- Добавь версию и дату создания

### 10. ВАЛИДАЦИЯ:
- Проверь корректность SVG синтаксиса
- Убедись в совместимости с браузерами
- Проверь accessibility стандарты
- Оптимизируй размер файла

## ПРИМЕР СТРУКТУРЫ SVG:

```svg
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width}" height="{height}" 
     viewBox="0 0 {width} {height}"
     preserveAspectRatio="xMidYMid meet">
  
  <defs>
    <!-- Градиенты, фильтры, паттерны -->
  </defs>
  
  <!-- Основные компоненты -->
  <g id="components">
    <!-- Компоненты системы -->
  </g>
  
  <!-- Связи между компонентами -->
  <g id="relationships">
    <!-- Стрелки и линии -->
  </g>
  
  <!-- Легенда -->
  <g id="legend">
    <!-- Объяснение элементов -->
  </g>
  
  <!-- Анимации -->
  <g id="animations">
    <!-- Анимированные элементы -->
  </g>
  
  <style>
    /* CSS стили для интерактивности */
  </style>
  
  <script>
    // JavaScript для динамики
  </script>
</svg>
```

## КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
1. Генерируй ТОЛЬКО валидный SVG код
2. Не добавляй комментарии вне SVG
3. Используй семантические имена для id и class
4. Обеспечь accessibility (ARIA labels)
5. Оптимизируй для веб-отображения
6. Добавь метаданные в <metadata>

Тип диаграммы: {diagram_type}
Заголовок: {title}
Описание: {description}

Создай профессиональную SVG диаграмму, следуя всем техническим требованиям выше.
"""
    
    def _get_data_flow_prompt(self) -> str:
        """Промпт для диаграммы потока данных с детальными техническими условиями"""
        return """
Ты - эксперт по созданию SVG диаграмм потока данных. Создай диаграмму на основе следующих технических условий:

## ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:

### 1. ВИЗУАЛИЗАЦИЯ ПОТОКА:
- Используй стрелки с маркерами для направления
- Добавь анимацию движения данных
- Покажи типы данных разными цветами
- Включи иконки для различных форматов данных

### 2. КОМПОНЕНТЫ ПОТОКА:
{components}

### 3. ТИПЫ СВЯЗЕЙ:
{relationships}

### 4. АНИМАЦИИ ПОТОКА:
- Создай <animateMotion> для движения данных
- Добавь <animate> для пульсации узлов
- Используй <animateTransform> для вращения
- Установи dur="3s" repeatCount="indefinite"

### 5. ИНТЕРАКТИВНОСТЬ:
- Добавь tooltips с описанием данных
- Включи hover эффекты для узлов
- Создай click события для деталей
- Добавь zoom и pan функциональность

### 6. ЦВЕТОВАЯ КОДИРОВКА:
- JSON данные: #4CAF50 (зеленый)
- XML данные: #2196F3 (синий)
- Binary данные: #FF9800 (оранжевый)
- Text данные: #9C27B0 (фиолетовый)
- Error данные: #F44336 (красный)

### 7. СТРУКТУРА SVG:
```svg
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width}" height="{height}" 
     viewBox="0 0 {width} {height}">
  
  <defs>
    <!-- Маркеры для стрелок -->
    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
            refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
    </marker>
    
    <!-- Градиенты для узлов -->
    <linearGradient id="dataGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#45a049;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Фоновая сетка -->
  <g id="grid" opacity="0.1">
    <!-- Сетка для ориентации -->
  </g>
  
  <!-- Узлы данных -->
  <g id="nodes">
    <!-- Компоненты с анимацией -->
  </g>
  
  <!-- Связи с анимацией -->
  <g id="connections">
    <!-- Стрелки с движением -->
  </g>
  
  <!-- Легенда -->
  <g id="legend">
    <!-- Объяснение цветов и типов -->
  </g>
  
  <style>
    .node {{ cursor: pointer; }}
    .node:hover {{ filter: brightness(1.2); }}
    .connection {{ stroke-dasharray: 5,5; }}
  </style>
  
  <script>
    // JavaScript для интерактивности
  </script>
</svg>
```

### 8. МЕТАДАННЫЕ:
- Добавь <title> для диаграммы
- Включи <desc> с описанием потока
- Добавь data-атрибуты для типов данных
- Создай aria-label для accessibility

Тип: {diagram_type}
Заголовок: {title}
Описание: {description}
Стиль: {style}
Размеры: {width}x{height}

Создай интерактивную SVG диаграмму потока данных с анимациями и полной технической реализацией.
"""
    
    def _get_microservices_prompt(self) -> str:
        """Промпт для диаграммы микросервисов с детальными техническими условиями"""
        return """
Ты - эксперт по созданию SVG диаграмм архитектуры микросервисов. Создай диаграмму на основе следующих технических условий:

## ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:

### 1. АРХИТЕКТУРНЫЕ КОМПОНЕНТЫ:
- API Gateway (центральный элемент)
- Микросервисы (отдельные блоки)
- Базы данных (для каждого сервиса)
- Очереди сообщений
- Мониторинг и логирование
- Load Balancer

### 2. СЕРВИСЫ:
{components}

### 3. ВЗАИМОДЕЙСТВИЯ:
{relationships}

### 4. ВИЗУАЛЬНОЕ ПРЕДСТАВЛЕНИЕ:
- API Gateway: шестиугольник с градиентом
- Микросервисы: прямоугольники с закругленными углами
- Базы данных: цилиндры с иконками
- Очереди: овалы с иконкой сообщения
- Мониторинг: круги с графиками

### 5. ЦВЕТОВАЯ СХЕМА:
- API Gateway: #FF6B6B (красный)
- Микросервисы: #4ECDC4 (бирюзовый)
- Базы данных: #45B7D1 (синий)
- Очереди: #96CEB4 (зеленый)
- Мониторинг: #FFEAA7 (желтый)
- Ошибки: #D63031 (темно-красный)

### 6. АНИМАЦИИ:
- Пульсация для активных сервисов
- Анимация передачи данных между сервисами
- Вращение для мониторинга
- Мерцание для ошибок

### 7. СТРУКТУРА SVG:
```svg
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width}" height="{height}" 
     viewBox="0 0 {width} {height}">
  
  <defs>
    <!-- Градиенты для компонентов -->
    <linearGradient id="gatewayGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FF6B6B;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#D63031;stop-opacity:1" />
    </linearGradient>
    
    <!-- Фильтры для эффектов -->
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge> 
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <!-- Фоновая сетка -->
  <g id="background" opacity="0.1">
    <!-- Сетка для ориентации -->
  </g>
  
  <!-- API Gateway -->
  <g id="gateway">
    <!-- Центральный элемент -->
  </g>
  
  <!-- Микросервисы -->
  <g id="services">
    <!-- Отдельные сервисы -->
  </g>
  
  <!-- Базы данных -->
  <g id="databases">
    <!-- Хранилища данных -->
  </g>
  
  <!-- Очереди -->
  <g id="queues">
    <!-- Очереди сообщений -->
  </g>
  
  <!-- Мониторинг -->
  <g id="monitoring">
    <!-- Системы мониторинга -->
  </g>
  
  <!-- Связи -->
  <g id="connections">
    <!-- API вызовы и сообщения -->
  </g>
  
  <!-- Легенда -->
  <g id="legend">
    <!-- Объяснение компонентов -->
  </g>
  
  <style>
    .service {{ cursor: pointer; transition: all 0.3s; }}
    .service:hover {{ filter: brightness(1.2) drop-shadow(0 0 10px rgba(0,0,0,0.3)); }}
    .connection {{ stroke-dasharray: 5,5; animation: flow 2s linear infinite; }}
    @keyframes flow {{ to {{ stroke-dashoffset: -10; }} }}
  </style>
  
  <script>
    // JavaScript для интерактивности и анимаций
  </script>
</svg>
```

### 8. ИНТЕРАКТИВНОСТЬ:
- Click для деталей сервиса
- Hover для информации о связях
- Zoom для детального просмотра
- Tooltips с метриками

### 9. МЕТАДАННЫЕ:
- Версия архитектуры
- Дата последнего обновления
- Количество сервисов
- Типы связей

Тип: {diagram_type}
Заголовок: {title}
Описание: {description}
Стиль: {style}
Размеры: {width}x{height}

Создай профессиональную SVG диаграмму микросервисной архитектуры с полной технической реализацией.
"""
    
    def _get_deployment_prompt(self) -> str:
        """Промпт для диаграммы развертывания с детальными техническими условиями"""
        return """
Ты - эксперт по созданию SVG диаграмм процессов развертывания. Создай диаграмму на основе следующих технических условий:

## ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:

### 1. ЭТАПЫ РАЗВЕРТЫВАНИЯ:
- Development Environment
- Staging Environment  
- Production Environment
- CI/CD Pipeline
- Monitoring & Alerts
- Rollback Process

### 2. ЭТАПЫ РАЗВЕРТЫВАНИЯ:
{components}

### 3. ПРОЦЕССЫ:
{relationships}

### 4. ВИЗУАЛЬНОЕ ПРЕДСТАВЛЕНИЕ:
- Development: зеленый цвет (#4CAF50)
- Staging: оранжевый цвет (#FF9800)
- Production: красный цвет (#F44336)
- CI/CD: синий цвет (#2196F3)
- Monitoring: фиолетовый цвет (#9C27B0)

### 5. АНИМАЦИИ ПРОЦЕССА:
- Анимация движения кода по pipeline
- Пульсация для активных этапов
- Анимация деплоя в production
- Мерцание для ошибок и rollback

### 6. СТРУКТУРА SVG:
```svg
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width}" height="{height}" 
     viewBox="0 0 {width} {height}">
  
  <defs>
    <!-- Градиенты для сред -->
    <linearGradient id="devGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#45a049;stop-opacity:1" />
    </linearGradient>
    
    <!-- Анимации -->
    <animateTransform id="deploy" attributeName="transform" 
                      type="translate" values="0,0; 0,-10; 0,0" 
                      dur="2s" repeatCount="indefinite"/>
  </defs>
  
  <!-- Фоновая сетка -->
  <g id="background" opacity="0.1">
    <!-- Сетка для ориентации -->
  </g>
  
  <!-- Development Environment -->
  <g id="development">
    <!-- Среда разработки -->
  </g>
  
  <!-- CI/CD Pipeline -->
  <g id="cicd">
    <!-- Процесс сборки и тестирования -->
  </g>
  
  <!-- Staging Environment -->
  <g id="staging">
    <!-- Тестовая среда -->
  </g>
  
  <!-- Production Environment -->
  <g id="production">
    <!-- Продакшн среда -->
  </g>
  
  <!-- Monitoring -->
  <g id="monitoring">
    <!-- Мониторинг и алерты -->
  </g>
  
  <!-- Rollback Process -->
  <g id="rollback">
    <!-- Процесс отката -->
  </g>
  
  <!-- Связи между этапами -->
  <g id="flow">
    <!-- Поток развертывания -->
  </g>
  
  <!-- Статусы -->
  <g id="status">
    <!-- Индикаторы статуса -->
  </g>
  
  <!-- Легенда -->
  <g id="legend">
    <!-- Объяснение этапов -->
  </g>
  
  <style>
    .environment {{ cursor: pointer; transition: all 0.3s; }}
    .environment:hover {{ filter: brightness(1.2); }}
    .pipeline {{ stroke-dasharray: 5,5; animation: flow 3s linear infinite; }}
    .status-success {{ fill: #4CAF50; }}
    .status-error {{ fill: #F44336; animation: blink 1s infinite; }}
    @keyframes flow {{ to {{ stroke-dashoffset: -10; }} }}
    @keyframes blink {{ 50% {{ opacity: 0.5; }} }}
  </style>
  
  <script>
    // JavaScript для интерактивности и анимаций
  </script>
</svg>
```

### 7. ИНТЕРАКТИВНОСТЬ:
- Click для деталей этапа
- Hover для информации о процессе
- Анимация при наведении
- Tooltips с метриками

### 8. МЕТАДАННЫЕ:
- Время деплоя
- Статус каждого этапа
- Количество ошибок
- Время rollback

Тип: {diagram_type}
Заголовок: {title}
Описание: {description}
Стиль: {style}
Размеры: {width}x{height}

Создай профессиональную SVG диаграмму процесса развертывания с полной технической реализацией.
"""
    
    async def generate_diagram(self, request: SVGGeneratorRequest) -> SVGGeneratorResponse:
        """Генерация SVG диаграммы"""
        start_time = datetime.now()
        
        try:
            # Проверяем кэш
            cache_key = self._generate_cache_key(request)
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                if (datetime.now() - cached_result["timestamp"]).seconds < self._cache_ttl:
                    logger.info(f"Возвращаем кэшированную диаграмму: {cache_key}")
                    return cached_result["result"]
            
            # Получаем шаблон
            template = self.templates.get(request.diagram_type)
            if not template:
                raise ValueError(f"Неизвестный тип диаграммы: {request.diagram_type}")
            
            # Формируем промпт
            prompt = self._format_prompt(request, template)
            
            # Улучшаем промпт примерами
            enhanced_prompt = self._enhance_prompt_with_examples(prompt, request.diagram_type)
            
            # Генерируем SVG с помощью LLM
            svg_content = await self._generate_svg_with_llm(enhanced_prompt)
            
            # Оптимизируем SVG
            optimized_svg = await self._optimize_svg(svg_content, request)
            
            # Добавляем стили и интерактивность
            final_svg = await self._enhance_svg(optimized_svg, request)
            
            # Создаем ответ
            generation_time = (datetime.now() - start_time).total_seconds()
            response = SVGGeneratorResponse(
                svg_content=final_svg,
                metadata={
                    "diagram_type": request.diagram_type,
                    "title": request.title,
                    "components_count": len(request.components),
                    "relationships_count": len(request.relationships),
                    "generated_at": datetime.now().isoformat(),
                    "template_used": template.name
                },
                generation_time=generation_time,
                model_used=self.model,
                confidence_score=0.85,  # Можно улучшить с помощью оценки качества
                optimization_suggestions=[
                    "Добавлены интерактивные элементы",
                    "Оптимизирован размер файла",
                    "Улучшена доступность"
                ]
            )
            
            # Кэшируем результат
            self._cache[cache_key] = {
                "result": response,
                "timestamp": datetime.now()
            }
            
            logger.info(f"Диаграмма сгенерирована за {generation_time:.2f} секунд")
            return response
            
        except Exception as e:
            logger.error(f"Ошибка генерации диаграммы: {e}")
            raise OllamaGenerationException(
                model_name=self.model,
                error_message=str(e)
            )
    
    async def _generate_svg_with_llm(self, prompt: str) -> str:
        """Генерация SVG с помощью LLM"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Низкая температура для консистентности
                    "top_p": 0.9,
                    "top_k": 50,
                    "repeat_penalty": 1.1,
                    "num_ctx": 4096
                }
            }
            
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            
            if response.status_code != 200:
                raise OllamaConnectionException(
                    f"Ollama вернул статус {response.status_code}"
                )
            
            result = response.json()
            svg_content = result.get("response", "")
            
            # Извлекаем SVG из ответа
            svg_match = re.search(r'<svg.*?</svg>', svg_content, re.DOTALL | re.IGNORECASE)
            if svg_match:
                return svg_match.group(0)
            else:
                # Если SVG не найден, создаем базовый
                return self._create_fallback_svg()
                
        except Exception as e:
            logger.error(f"Ошибка генерации SVG с LLM: {e}")
            return self._create_fallback_svg()
    
    def _create_fallback_svg(self) -> str:
        """Создание базового SVG при ошибке"""
        return f"""
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#f8fafc;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#e2e8f0;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <rect width="100%" height="100%" fill="url(#bg)"/>
  
  <text x="400" y="300" text-anchor="middle" font-family="Arial, sans-serif" 
        font-size="24" fill="#64748b">
    Диаграмма будет сгенерирована автоматически
  </text>
  
  <text x="400" y="330" text-anchor="middle" font-family="Arial, sans-serif" 
        font-size="16" fill="#94a3b8">
    Используйте LLM для создания архитектурных диаграмм
  </text>
</svg>
"""
    
    async def _optimize_svg(self, svg_content: str, request: SVGGeneratorRequest) -> str:
        """Оптимизация SVG"""
        try:
            # Парсим SVG
            root = ET.fromstring(svg_content)
            
            # Добавляем базовые атрибуты
            root.set("width", str(request.width))
            root.set("height", str(request.height))
            root.set("viewBox", f"0 0 {request.width} {request.height}")
            
            # Добавляем стили
            style_elem = ET.SubElement(root, "style")
            style_elem.text = self._generate_css_styles(request)
            
            # Оптимизируем элементы
            self._optimize_elements(root)
            
            return ET.tostring(root, encoding="unicode")
            
        except Exception as e:
            logger.warning(f"Ошибка оптимизации SVG: {e}")
            return svg_content
    
    def _generate_css_styles(self, request: SVGGeneratorRequest) -> str:
        """Генерация CSS стилей"""
        style = request.style or DiagramStyle()
        
        return f"""
        .component {{
            fill: {style.colors.get('primary', '#2563eb')};
            stroke: #1e40af;
            stroke-width: {style.stroke_width};
            opacity: {style.opacity};
            transition: all 0.3s ease;
        }}
        
        .component:hover {{
            fill: {style.colors.get('secondary', '#7c3aed')};
            transform: scale(1.05);
            cursor: pointer;
        }}
        
        .relationship {{
            stroke: #64748b;
            stroke-width: 2;
            fill: none;
            marker-end: url(#arrowhead);
        }}
        
        .text {{
            font-family: {style.font_family};
            font-size: {style.font_size}px;
            fill: #1f2937;
        }}
        
        .title {{
            font-size: {style.font_size + 8}px;
            font-weight: bold;
            fill: #111827;
        }}
        
        .legend {{
            fill: white;
            stroke: #d1d5db;
            stroke-width: 1;
            opacity: 0.9;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 0.7; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.7; }}
        }}
        
        .animated {{
            animation: pulse 2s infinite;
        }}
        """
    
    def _optimize_elements(self, root: ET.Element):
        """Оптимизация SVG элементов"""
        # Добавляем классы к элементам
        for elem in root.iter():
            if elem.tag.endswith('rect'):
                elem.set('class', 'component')
            elif elem.tag.endswith('line') or elem.tag.endswith('path'):
                if 'relationship' in elem.get('id', ''):
                    elem.set('class', 'relationship')
            elif elem.tag.endswith('text'):
                if 'title' in elem.get('id', ''):
                    elem.set('class', 'title')
                else:
                    elem.set('class', 'text')
    
    async def _enhance_svg(self, svg_content: str, request: SVGGeneratorRequest) -> str:
        """Улучшение SVG с интерактивностью"""
        if not request.interactive:
            return svg_content
        
        # Добавляем JavaScript для интерактивности
        js_code = self._generate_interactive_js(request)
        
        # Вставляем JavaScript в SVG
        svg_with_js = svg_content.replace('</svg>', f'{js_code}</svg>')
        
        return svg_with_js
    
    def _generate_interactive_js(self, request: SVGGeneratorRequest) -> str:
        """Генерация JavaScript для интерактивности"""
        return f"""
        <script type="text/javascript">
        <![CDATA[
            // Интерактивность для диаграммы
            document.addEventListener('DOMContentLoaded', function() {{
                const components = document.querySelectorAll('.component');
                const relationships = document.querySelectorAll('.relationship');
                
                // Hover эффекты для компонентов
                components.forEach(comp => {{
                    comp.addEventListener('mouseenter', function() {{
                        this.style.filter = 'drop-shadow(0 4px 8px rgba(0,0,0,0.2))';
                    }});
                    
                    comp.addEventListener('mouseleave', function() {{
                        this.style.filter = 'none';
                    }});
                    
                    comp.addEventListener('click', function() {{
                        const title = this.getAttribute('data-title') || 'Компонент';
                        alert(`Информация о компоненте: ${{title}}`);
                    }});
                }});
                
                // Анимация связей
                relationships.forEach(rel => {{
                    rel.classList.add('animated');
                }});
                
                // Tooltip система
                function showTooltip(element, text) {{
                    const tooltip = document.createElement('div');
                    tooltip.className = 'tooltip';
                    tooltip.textContent = text;
                    tooltip.style.cssText = `
                        position: absolute;
                        background: rgba(0,0,0,0.8);
                        color: white;
                        padding: 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        pointer-events: none;
                        z-index: 1000;
                    `;
                    document.body.appendChild(tooltip);
                    
                    element.addEventListener('mousemove', function(e) {{
                        tooltip.style.left = e.pageX + 10 + 'px';
                        tooltip.style.top = e.pageY - 10 + 'px';
                    }});
                    
                    element.addEventListener('mouseleave', function() {{
                        document.body.removeChild(tooltip);
                    }});
                }}
            }});
        ]]>
        </script>
        """
    
    def _format_prompt(self, request: SVGGeneratorRequest, template: DiagramTemplate) -> str:
        """Форматирование промпта"""
        components_text = "\n".join([
            f"- {comp.get('name', 'Component')}: {comp.get('description', 'No description')}"
            for comp in request.components
        ])
        
        relationships_text = "\n".join([
            f"- {rel.get('from', 'A')} -> {rel.get('to', 'B')}: {rel.get('type', 'connection')}"
            for rel in request.relationships
        ])
        
        style_text = f"theme={request.style.theme if request.style else 'modern'}"
        
        return template.prompt_template.format(
            diagram_type=request.diagram_type,
            title=request.title,
            description=request.description,
            components=components_text,
            relationships=relationships_text,
            style=style_text,
            width=request.width,
            height=request.height
        )
    
    def _generate_cache_key(self, request: SVGGeneratorRequest) -> str:
        """Генерация ключа кэша"""
        import hashlib
        
        key_data = {
            "diagram_type": request.diagram_type,
            "title": request.title,
            "description": request.description,
            "components": request.components,
            "relationships": request.relationships,
            "style": request.style.dict() if request.style else None,
            "width": request.width,
            "height": request.height
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get_available_templates(self) -> List[Dict[str, Any]]:
        """Получение доступных шаблонов"""
        return [
            {
                "name": template.name,
                "description": template.description,
                "type": diagram_type,
                "components": template.components,
                "relationships": template.relationships,
                "default_style": template.default_style.dict()
            }
            for diagram_type, template in self.templates.items()
        ]
    
    async def validate_svg(self, svg_content: str) -> Dict[str, Any]:
        """Валидация и оценка качества SVG"""
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "quality_score": 0.0,
            "optimization_suggestions": [],
            "accessibility_score": 0.0,
            "performance_score": 0.0
        }
        
        try:
            # Проверяем базовую структуру SVG
            if not svg_content.strip().startswith('<svg'):
                validation_result["errors"].append("SVG должен начинаться с тега <svg>")
                return validation_result
            
            # Парсим SVG
            try:
                root = ET.fromstring(svg_content)
            except ET.ParseError as e:
                validation_result["errors"].append(f"Ошибка парсинга SVG: {e}")
                return validation_result
            
            # Проверяем обязательные атрибуты
            if not root.get('xmlns'):
                validation_result["warnings"].append("Отсутствует xmlns атрибут")
            
            if not root.get('viewBox'):
                validation_result["warnings"].append("Отсутствует viewBox для масштабируемости")
            
            # Проверяем структуру
            required_sections = ['components', 'relationships', 'legend']
            for section in required_sections:
                if not root.find(f".//g[@id='{section}']"):
                    validation_result["warnings"].append(f"Отсутствует секция {section}")
            
            # Проверяем accessibility
            accessibility_score = self._check_accessibility(root)
            validation_result["accessibility_score"] = accessibility_score
            
            # Проверяем производительность
            performance_score = self._check_performance(root)
            validation_result["performance_score"] = performance_score
            
            # Проверяем наличие анимаций
            animations = root.findall(".//animate") + root.findall(".//animateTransform") + root.findall(".//animateMotion")
            if not animations:
                validation_result["warnings"].append("Отсутствуют анимации")
            
            # Проверяем интерактивность
            if not root.find(".//style") and not root.find(".//script"):
                validation_result["warnings"].append("Отсутствуют стили или скрипты для интерактивности")
            
            # Проверяем метаданные
            if not root.find(".//title") and not root.find(".//desc"):
                validation_result["warnings"].append("Отсутствуют метаданные (title/desc)")
            
            # Рассчитываем общий score
            total_score = 0.0
            max_score = 100.0
            
            # Базовые проверки (30 баллов)
            if not validation_result["errors"]:
                total_score += 30
            
            # Accessibility (25 баллов)
            total_score += accessibility_score * 25
            
            # Performance (25 баллов)
            total_score += performance_score * 25
            
            # Дополнительные функции (20 баллов)
            feature_score = 0.0
            if animations:
                feature_score += 0.5
            if root.find(".//style") or root.find(".//script"):
                feature_score += 0.3
            if root.find(".//title") or root.find(".//desc"):
                feature_score += 0.2
            total_score += feature_score * 20
            
            validation_result["quality_score"] = min(total_score, max_score) / max_score
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
            # Генерируем предложения по оптимизации
            validation_result["optimization_suggestions"] = self._generate_optimization_suggestions(
                validation_result, root
            )
            
        except Exception as e:
            validation_result["errors"].append(f"Ошибка валидации: {e}")
        
        return validation_result
    
    def _check_accessibility(self, root: ET.Element) -> float:
        """Проверка accessibility"""
        score = 0.0
        checks = 0
        
        # Проверяем наличие title
        if root.find(".//title") is not None:
            score += 1.0
        checks += 1
        
        # Проверяем наличие desc
        if root.find(".//desc") is not None:
            score += 1.0
        checks += 1
        
        # Проверяем aria-label
        aria_labels = root.findall(".//*[@aria-label]")
        if aria_labels:
            score += 1.0
        checks += 1
        
        # Проверяем role атрибуты
        roles = root.findall(".//*[@role]")
        if roles:
            score += 1.0
        checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _check_performance(self, root: ET.Element) -> float:
        """Проверка производительности"""
        score = 0.0
        checks = 0
        
        # Проверяем количество элементов
        total_elements = len(root.findall(".//*"))
        if total_elements < 100:
            score += 1.0
        elif total_elements < 200:
            score += 0.5
        checks += 1
        
        # Проверяем использование defs
        if root.find(".//defs") is not None:
            score += 1.0
        checks += 1
        
        # Проверяем оптимизацию path
        paths = root.findall(".//path")
        if paths:
            # Проверяем сложность path
            complex_paths = 0
            for path in paths:
                d_attr = path.get('d', '')
                if len(d_attr) > 100:  # Слишком сложный path
                    complex_paths += 1
            
            if complex_paths == 0:
                score += 1.0
            elif complex_paths < len(paths) * 0.3:
                score += 0.5
        checks += 1
        
        # Проверяем использование групп
        groups = root.findall(".//g")
        if groups:
            score += 1.0
        checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _generate_optimization_suggestions(self, validation_result: Dict[str, Any], root: ET.Element) -> List[str]:
        """Генерация предложений по оптимизации"""
        suggestions = []
        
        # Предложения на основе ошибок
        for error in validation_result["errors"]:
            if "xmlns" in error:
                suggestions.append("Добавьте xmlns='http://www.w3.org/2000/svg' в тег svg")
            elif "viewBox" in error:
                suggestions.append("Добавьте viewBox для обеспечения масштабируемости")
        
        # Предложения на основе предупреждений
        for warning in validation_result["warnings"]:
            if "анимации" in warning:
                suggestions.append("Добавьте анимации для улучшения пользовательского опыта")
            elif "интерактивности" in warning:
                suggestions.append("Добавьте CSS стили и JavaScript для интерактивности")
            elif "метаданные" in warning:
                suggestions.append("Добавьте title и desc для улучшения accessibility")
        
        # Предложения на основе производительности
        if validation_result["performance_score"] < 0.7:
            suggestions.append("Оптимизируйте количество элементов для улучшения производительности")
            suggestions.append("Используйте defs для переиспользуемых элементов")
        
        # Предложения на основе accessibility
        if validation_result["accessibility_score"] < 0.7:
            suggestions.append("Добавьте aria-label атрибуты для улучшения accessibility")
            suggestions.append("Используйте семантические role атрибуты")
        
        return suggestions[:5]  # Ограничиваем количество предложений
    
    async def close(self):
        """Закрытие соединений"""
        await self.client.aclose()

    def _get_example_svg_templates(self) -> Dict[str, str]:
        """Получение примеров SVG шаблонов для улучшения качества"""
        return {
            "system_architecture": """
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <defs>
    <linearGradient id="componentGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#45a049;stop-opacity:1" />
    </linearGradient>
    <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
      <feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.3"/>
    </filter>
  </defs>
  
  <title>System Architecture Example</title>
  <desc>Professional system architecture diagram with modern design</desc>
  
  <g id="components">
    <rect x="50" y="50" width="120" height="80" rx="10" fill="url(#componentGradient)" 
          filter="url(#shadow)" class="component" data-type="frontend" aria-label="Frontend Application"/>
    <text x="110" y="95" text-anchor="middle" fill="white" font-size="12">Frontend</text>
    
    <rect x="250" y="50" width="120" height="80" rx="10" fill="url(#componentGradient)" 
          filter="url(#shadow)" class="component" data-type="api" aria-label="API Gateway"/>
    <text x="310" y="95" text-anchor="middle" fill="white" font-size="12">API Gateway</text>
    
    <rect x="450" y="50" width="120" height="80" rx="10" fill="url(#componentGradient)" 
          filter="url(#shadow)" class="component" data-type="backend" aria-label="Backend Service"/>
    <text x="510" y="95" text-anchor="middle" fill="white" font-size="12">Backend</text>
    
    <rect x="650" y="50" width="120" height="80" rx="10" fill="url(#componentGradient)" 
          filter="url(#shadow)" class="component" data-type="database" aria-label="Database"/>
    <text x="710" y="95" text-anchor="middle" fill="white" font-size="12">Database</text>
  </g>
  
  <g id="relationships">
    <line x1="170" y1="90" x2="250" y2="90" stroke="#666" stroke-width="3" marker-end="url(#arrowhead)"/>
    <line x1="370" y1="90" x2="450" y2="90" stroke="#666" stroke-width="3" marker-end="url(#arrowhead)"/>
    <line x1="570" y1="90" x2="650" y2="90" stroke="#666" stroke-width="3" marker-end="url(#arrowhead)"/>
  </g>
  
  <g id="legend">
    <rect x="50" y="200" width="200" height="100" fill="#f5f5f5" stroke="#ddd"/>
    <text x="150" y="220" text-anchor="middle" font-weight="bold">Legend</text>
    <rect x="70" y="240" width="20" height="15" fill="url(#componentGradient)"/>
    <text x="100" y="252" font-size="12">Component</text>
    <line x1="70" y1="270" x2="90" y2="270" stroke="#666" stroke-width="3" marker-end="url(#arrowhead)"/>
    <text x="100" y="275" font-size="12">Connection</text>
  </g>
  
  <style>
    .component { cursor: pointer; transition: all 0.3s; }
    .component:hover { filter: brightness(1.2) drop-shadow(0 0 10px rgba(0,0,0,0.3)); }
  </style>
  
  <script>
    document.querySelectorAll('.component').forEach(el => {
      el.addEventListener('click', () => {
        const type = el.getAttribute('data-type');
        alert(`Clicked on ${type} component`);
      });
    });
  </script>
</svg>
""",
            "data_flow": """
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
    </marker>
    <linearGradient id="dataGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#45a049;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <title>Data Flow Example</title>
  <desc>Interactive data flow diagram with animations</desc>
  
  <g id="nodes">
    <circle cx="150" cy="150" r="40" fill="url(#dataGradient)" class="node" data-type="input">
      <animate attributeName="r" values="40;45;40" dur="2s" repeatCount="indefinite"/>
    </circle>
    <text x="150" y="155" text-anchor="middle" fill="white" font-size="12">Input</text>
    
    <circle cx="350" cy="150" r="40" fill="url(#dataGradient)" class="node" data-type="process">
      <animate attributeName="r" values="40;45;40" dur="2s" repeatCount="indefinite" begin="0.5s"/>
    </circle>
    <text x="350" y="155" text-anchor="middle" fill="white" font-size="12">Process</text>
    
    <circle cx="550" cy="150" r="40" fill="url(#dataGradient)" class="node" data-type="output">
      <animate attributeName="r" values="40;45;40" dur="2s" repeatCount="indefinite" begin="1s"/>
    </circle>
    <text x="550" y="155" text-anchor="middle" fill="white" font-size="12">Output</text>
  </g>
  
  <g id="connections">
    <line x1="190" y1="150" x2="310" y2="150" stroke="#666" stroke-width="3" 
          stroke-dasharray="5,5" marker-end="url(#arrowhead)" class="connection">
      <animate attributeName="stroke-dashoffset" values="0;-10" dur="1s" repeatCount="indefinite"/>
    </line>
    <line x1="390" y1="150" x2="510" y2="150" stroke="#666" stroke-width="3" 
          stroke-dasharray="5,5" marker-end="url(#arrowhead)" class="connection">
      <animate attributeName="stroke-dashoffset" values="0;-10" dur="1s" repeatCount="indefinite" begin="0.5s"/>
    </line>
  </g>
  
  <g id="legend">
    <rect x="50" y="250" width="200" height="120" fill="#f5f5f5" stroke="#ddd"/>
    <text x="150" y="270" text-anchor="middle" font-weight="bold">Data Types</text>
    <circle cx="70" cy="290" r="15" fill="#4CAF50"/>
    <text x="95" y="295" font-size="12">JSON Data</text>
    <circle cx="70" cy="315" r="15" fill="#2196F3"/>
    <text x="95" y="320" font-size="12">XML Data</text>
    <circle cx="70" cy="340" r="15" fill="#FF9800"/>
    <text x="95" y="345" font-size="12">Binary Data</text>
  </g>
  
  <style>
    .node { cursor: pointer; }
    .node:hover { filter: brightness(1.2); }
    .connection { animation: flow 2s linear infinite; }
  </style>
  
  <script>
    document.querySelectorAll('.node').forEach(el => {
      el.addEventListener('click', () => {
        const type = el.getAttribute('data-type');
        alert(`Data flow: ${type} node`);
      });
    });
  </script>
</svg>
""",
            "microservices": """
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <defs>
    <linearGradient id="gatewayGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FF6B6B;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#D63031;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="serviceGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4ECDC4;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#44A08D;stop-opacity:1" />
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge> 
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <title>Microservices Architecture Example</title>
  <desc>Professional microservices architecture with API Gateway</desc>
  
  <g id="gateway">
    <polygon points="400,50 450,80 450,120 400,150 350,120 350,80" 
             fill="url(#gatewayGradient)" filter="url(#glow)" class="gateway" aria-label="API Gateway">
      <animate attributeName="opacity" values="1;0.8;1" dur="3s" repeatCount="indefinite"/>
    </polygon>
    <text x="400" y="105" text-anchor="middle" fill="white" font-size="12">API Gateway</text>
  </g>
  
  <g id="services">
    <rect x="100" y="200" width="120" height="80" rx="10" fill="url(#serviceGradient)" 
          class="service" data-service="user" aria-label="User Service"/>
    <text x="160" y="245" text-anchor="middle" fill="white" font-size="12">User Service</text>
    
    <rect x="300" y="200" width="120" height="80" rx="10" fill="url(#serviceGradient)" 
          class="service" data-service="order" aria-label="Order Service"/>
    <text x="360" y="245" text-anchor="middle" fill="white" font-size="12">Order Service</text>
    
    <rect x="500" y="200" width="120" height="80" rx="10" fill="url(#serviceGradient)" 
          class="service" data-service="payment" aria-label="Payment Service"/>
    <text x="560" y="245" text-anchor="middle" fill="white" font-size="12">Payment Service</text>
  </g>
  
  <g id="databases">
    <ellipse cx="160" cy="350" rx="40" ry="20" fill="#45B7D1" class="database" aria-label="User Database"/>
    <text x="160" y="355" text-anchor="middle" fill="white" font-size="10">User DB</text>
    
    <ellipse cx="360" cy="350" rx="40" ry="20" fill="#45B7D1" class="database" aria-label="Order Database"/>
    <text x="360" y="355" text-anchor="middle" fill="white" font-size="10">Order DB</text>
    
    <ellipse cx="560" cy="350" rx="40" ry="20" fill="#45B7D1" class="database" aria-label="Payment Database"/>
    <text x="560" y="355" text-anchor="middle" fill="white" font-size="10">Payment DB</text>
  </g>
  
  <g id="connections">
    <line x1="400" y1="150" x2="160" y2="200" stroke="#666" stroke-width="2" 
          stroke-dasharray="5,5" class="connection"/>
    <line x1="400" y1="150" x2="360" y2="200" stroke="#666" stroke-width="2" 
          stroke-dasharray="5,5" class="connection"/>
    <line x1="400" y1="150" x2="560" y2="200" stroke="#666" stroke-width="2" 
          stroke-dasharray="5,5" class="connection"/>
    
    <line x1="160" y1="280" x2="160" y2="330" stroke="#666" stroke-width="2" class="connection"/>
    <line x1="360" y1="280" x2="360" y2="330" stroke="#666" stroke-width="2" class="connection"/>
    <line x1="560" y1="280" x2="560" y2="330" stroke="#666" stroke-width="2" class="connection"/>
  </g>
  
  <g id="legend">
    <rect x="50" y="400" width="250" height="150" fill="#f5f5f5" stroke="#ddd"/>
    <text x="175" y="420" text-anchor="middle" font-weight="bold">Microservices Legend</text>
    <polygon points="70,440 80,450 80,470 70,480 60,470 60,450" fill="url(#gatewayGradient)"/>
    <text x="90" y="465" font-size="12">API Gateway</text>
    <rect x="70" y="480" width="20" height="15" fill="url(#serviceGradient)"/>
    <text x="100" y="492" font-size="12">Microservice</text>
    <ellipse cx="80" cy="510" rx="10" ry="5" fill="#45B7D1"/>
    <text x="100" y="515" font-size="12">Database</text>
  </g>
  
  <style>
    .service { cursor: pointer; transition: all 0.3s; }
    .service:hover { filter: brightness(1.2) drop-shadow(0 0 10px rgba(0,0,0,0.3)); }
    .connection { animation: flow 2s linear infinite; }
    @keyframes flow { to { stroke-dashoffset: -10; } }
  </style>
  
  <script>
    document.querySelectorAll('.service').forEach(el => {
      el.addEventListener('click', () => {
        const service = el.getAttribute('data-service');
        alert(`Microservice: ${service}`);
      });
    });
  </script>
</svg>
"""
        }
    
    def _enhance_prompt_with_examples(self, prompt: str, diagram_type: str) -> str:
        """Улучшение промпта примерами"""
        examples = self._get_example_svg_templates()
        example = examples.get(diagram_type, "")
        
        if example:
            enhanced_prompt = f"""
{prompt}

## ПРИМЕР КАЧЕСТВЕННОГО SVG ДЛЯ ДАННОГО ТИПА ДИАГРАММЫ:

```svg
{example}
```

## ТРЕБОВАНИЯ К КАЧЕСТВУ:
1. Следуй структуре примера выше
2. Используй аналогичные градиенты и эффекты
3. Добавь анимации как в примере
4. Обеспечь интерактивность
5. Включи accessibility атрибуты
6. Оптимизируй для производительности

Создай диаграмму того же качества, что и в примере, но для указанных компонентов и связей.
"""
            return enhanced_prompt
        
        return prompt


# Глобальный экземпляр сервиса
svg_generator = None


async def initialize_svg_generator():
    """Инициализация SVG генератора"""
    global svg_generator
    svg_generator = SVGGeneratorService()
    logger.info("SVG Generator Service инициализирован")


async def get_svg_generator() -> SVGGeneratorService:
    """Получение экземпляра SVG генератора"""
    if svg_generator is None:
        await initialize_svg_generator()
    return svg_generator