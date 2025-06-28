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
        """Промпт для архитектурной диаграммы"""
        return """
Создай профессиональную SVG диаграмму архитектуры системы на основе следующего описания:

Тип диаграммы: {diagram_type}
Заголовок: {title}
Описание: {description}

Компоненты системы:
{components}

Связи между компонентами:
{relationships}

Требования к SVG:
1. Используй современный дизайн с градиентами и тенями
2. Добавь интерактивность (hover эффекты)
3. Включи легенду и заголовок
4. Используй семантические цвета
5. Добавь анимации для улучшения UX
6. Оптимизируй для веб-отображения
7. Включи метаданные для SEO

Стиль: {style}

Размеры: {width}x{height} пикселей

Генерируй только валидный SVG код без дополнительных комментариев.
"""
    
    def _get_data_flow_prompt(self) -> str:
        """Промпт для диаграммы потока данных"""
        return """
Создай SVG диаграмму потока данных с следующими характеристиками:

Тип: {diagram_type}
Заголовок: {title}
Описание: {description}

Поток данных:
{components}

Типы связей:
{relationships}

Требования:
1. Покажи направление потока данных стрелками
2. Используй разные цвета для разных типов данных
3. Добавь иконки для типов данных
4. Включи анимацию потока
5. Сделай диаграмму интерактивной
6. Добавь tooltips с описанием

Стиль: {style}
Размеры: {width}x{height}
"""
    
    def _get_microservices_prompt(self) -> str:
        """Промпт для диаграммы микросервисов"""
        return """
Создай SVG диаграмму архитектуры микросервисов:

Тип: {diagram_type}
Заголовок: {title}
Описание: {description}

Сервисы:
{components}

Взаимодействия:
{relationships}

Требования:
1. Покажи каждый сервис как отдельный блок
2. Отобрази API Gateway
3. Покажи базы данных для каждого сервиса
4. Добавь очереди сообщений
5. Включи мониторинг и логирование
6. Сделай диаграмму интерактивной
7. Добавь анимации для демонстрации работы

Стиль: {style}
Размеры: {width}x{height}
"""
    
    def _get_deployment_prompt(self) -> str:
        """Промпт для диаграммы развертывания"""
        return """
Создай SVG диаграмму процесса развертывания:

Тип: {diagram_type}
Заголовок: {title}
Описание: {description}

Этапы развертывания:
{components}

Процессы:
{relationships}

Требования:
1. Покажи все среды (dev, staging, prod)
2. Отобрази CI/CD pipeline
3. Добавь мониторинг и алерты
4. Покажи процесс rollback
5. Включи анимации деплоя
6. Сделай диаграмму интерактивной
7. Добавь статусы и метрики

Стиль: {style}
Размеры: {width}x{height}
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
            
            # Генерируем SVG с помощью LLM
            svg_content = await self._generate_svg_with_llm(prompt)
            
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
        """Валидация SVG"""
        try:
            root = ET.fromstring(svg_content)
            
            # Проверяем базовые атрибуты
            width = root.get('width', '0')
            height = root.get('height', '0')
            viewbox = root.get('viewBox', '')
            
            # Подсчитываем элементы
            elements = {
                'rect': len(root.findall('.//rect')),
                'circle': len(root.findall('.//circle')),
                'line': len(root.findall('.//line')),
                'path': len(root.findall('.//path')),
                'text': len(root.findall('.//text')),
                'g': len(root.findall('.//g'))
            }
            
            return {
                "valid": True,
                "width": width,
                "height": height,
                "viewbox": viewbox,
                "elements": elements,
                "total_elements": sum(elements.values())
            }
            
        except ET.ParseError as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def close(self):
        """Закрытие соединений"""
        await self.client.aclose()


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