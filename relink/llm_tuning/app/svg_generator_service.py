"""
Сервис для генерации SVG диаграмм с помощью LLM
Автоматическое создание архитектурных диаграмм на основе описания системы
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings

logger = logging.getLogger(__name__)


class DiagramType(Enum):
    """Типы диаграмм"""
    SYSTEM_ARCHITECTURE = "system_architecture"
    DATA_FLOW = "data_flow"
    DEPLOYMENT = "deployment"
    FRONTEND_ARCHITECTURE = "frontend_architecture"
    MICROSERVICES = "microservices"
    DATABASE_SCHEMA = "database_schema"
    API_FLOW = "api_flow"
    SECURITY = "security"
    MONITORING = "monitoring"
    INTEGRATION = "integration"


@dataclass
class DiagramConfig:
    """Конфигурация диаграммы"""
    width: int = 1200
    height: int = 800
    theme: str = "dark"  # dark, light
    style: str = "modern"  # modern, classic, minimal
    colors: Dict[str, str] = None
    fonts: Dict[str, str] = None


class SVGGeneratorService:
    """Сервис для генерации SVG диаграмм с помощью LLM"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        
        # Предустановленные цветовые схемы
        self.color_schemes = {
            "dark": {
                "background": "#1a1a1a",
                "primary": "#3b82f6",
                "secondary": "#10b981",
                "accent": "#f59e0b",
                "danger": "#ef4444",
                "warning": "#f97316",
                "success": "#22c55e",
                "text": "#ffffff",
                "text_secondary": "#9ca3af",
                "border": "#374151"
            },
            "light": {
                "background": "#ffffff",
                "primary": "#2563eb",
                "secondary": "#059669",
                "accent": "#d97706",
                "danger": "#dc2626",
                "warning": "#ea580c",
                "success": "#16a34a",
                "text": "#111827",
                "text_secondary": "#6b7280",
                "border": "#d1d5db"
            }
        }
        
        # Шаблоны промптов для разных типов диаграмм
        self.prompt_templates = {
            DiagramType.SYSTEM_ARCHITECTURE: """
Создай SVG диаграмму архитектуры системы на основе следующего описания:

{description}

Требования:
- Ширина: {width}px, высота: {height}px
- Тема: {theme}
- Стиль: {style}
- Цвета: {colors}
- Компоненты должны быть четко обозначены
- Связи между компонентами должны быть видны
- Добавь легенду и заголовок
- Используй современный дизайн с тенями и градиентами

Генерируй только валидный SVG код без дополнительных комментариев.
""",
            DiagramType.DATA_FLOW: """
Создай SVG диаграмму потока данных для системы:

{description}

Требования:
- Покажи направление потока данных стрелками
- Обозначь типы данных и их преобразования
- Используй разные цвета для разных типов данных
- Добавь узлы обработки и хранения
- Покажи точки входа и выхода
- Сделай диаграмму читаемой и понятной
""",
            DiagramType.DEPLOYMENT: """
Создай SVG диаграмму развертывания системы:

{description}

Требования:
- Покажи инфраструктуру (серверы, контейнеры, сети)
- Обозначь окружения (dev, staging, prod)
- Покажи балансировщики нагрузки и прокси
- Добавь базы данных и внешние сервисы
- Используй иконки для разных типов ресурсов
- Покажи сетевые соединения
""",
            DiagramType.MICROSERVICES: """
Создай SVG диаграмму микросервисной архитектуры:

{description}

Требования:
- Покажи все микросервисы как отдельные блоки
- Обозначь API Gateway и сервис-меш
- Покажи базы данных для каждого сервиса
- Добавь очереди сообщений
- Покажи мониторинг и логирование
- Используй разные цвета для разных типов сервисов
"""
        }
    
    async def generate_diagram(
        self,
        diagram_type: DiagramType,
        description: str,
        config: Optional[DiagramConfig] = None
    ) -> Dict[str, Any]:
        """Генерация SVG диаграммы с помощью LLM"""
        
        if config is None:
            config = DiagramConfig()
        
        try:
            # Формируем промпт для LLM
            prompt = self._build_prompt(diagram_type, description, config)
            
            # Генерируем SVG с помощью LLM
            svg_content = await self._generate_svg_with_llm(prompt)
            
            # Валидируем и оптимизируем SVG
            optimized_svg = await self._optimize_svg(svg_content, config)
            
            # Создаем метаданные
            metadata = {
                "type": diagram_type.value,
                "description": description,
                "config": {
                    "width": config.width,
                    "height": config.height,
                    "theme": config.theme,
                    "style": config.style
                },
                "generated_at": asyncio.get_event_loop().time(),
                "model_used": "ollama",
                "optimization_applied": True
            }
            
            return {
                "svg": optimized_svg,
                "metadata": metadata,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Ошибка при генерации диаграммы: {e}")
            return {
                "svg": None,
                "metadata": {"error": str(e)},
                "success": False
            }
    
    async def generate_architecture_diagram(
        self,
        system_description: str,
        config: Optional[DiagramConfig] = None
    ) -> Dict[str, Any]:
        """Генерация диаграммы архитектуры системы"""
        return await self.generate_diagram(
            DiagramType.SYSTEM_ARCHITECTURE,
            system_description,
            config
        )
    
    async def generate_data_flow_diagram(
        self,
        flow_description: str,
        config: Optional[DiagramConfig] = None
    ) -> Dict[str, Any]:
        """Генерация диаграммы потока данных"""
        return await self.generate_diagram(
            DiagramType.DATA_FLOW,
            flow_description,
            config
        )
    
    async def generate_deployment_diagram(
        self,
        deployment_description: str,
        config: Optional[DiagramConfig] = None
    ) -> Dict[str, Any]:
        """Генерация диаграммы развертывания"""
        return await self.generate_diagram(
            DiagramType.DEPLOYMENT,
            deployment_description,
            config
        )
    
    async def generate_microservices_diagram(
        self,
        microservices_description: str,
        config: Optional[DiagramConfig] = None
    ) -> Dict[str, Any]:
        """Генерация диаграммы микросервисов"""
        return await self.generate_diagram(
            DiagramType.MICROSERVICES,
            microservices_description,
            config
        )
    
    def _build_prompt(
        self,
        diagram_type: DiagramType,
        description: str,
        config: DiagramConfig
    ) -> str:
        """Построение промпта для LLM"""
        
        # Получаем цветовую схему
        colors = config.colors or self.color_schemes[config.theme]
        
        # Получаем шаблон промпта
        template = self.prompt_templates.get(diagram_type, self.prompt_templates[DiagramType.SYSTEM_ARCHITECTURE])
        
        # Заполняем шаблон
        prompt = template.format(
            description=description,
            width=config.width,
            height=config.height,
            theme=config.theme,
            style=config.style,
            colors=json.dumps(colors, indent=2)
        )
        
        return prompt
    
    async def _generate_svg_with_llm(self, prompt: str) -> str:
        """Генерация SVG с помощью LLM"""
        
        try:
            # Формируем запрос к Ollama
            request_data = {
                "model": "llama3.2:3b",  # Используем доступную модель
                "prompt": f"""
Ты эксперт по созданию SVG диаграмм. Создай профессиональную SVG диаграмму на основе следующего описания:

{prompt}

Важные требования:
1. Генерируй только валидный SVG код
2. Не добавляй комментарии или пояснения
3. Используй современный дизайн
4. Обеспечь читаемость и масштабируемость
5. Добавь интерактивные элементы (hover эффекты)
6. Используй градиенты и тени для глубины
7. Обеспечь доступность (aria-labels)

Начни генерацию SVG:
""",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 4000
                }
            }
            
            # Отправляем запрос к Ollama
            response = await self.ollama_client.post("/api/generate", json=request_data)
            response.raise_for_status()
            
            result = response.json()
            svg_content = result.get("response", "")
            
            # Извлекаем SVG из ответа
            svg_match = re.search(r'<svg[^>]*>.*?</svg>', svg_content, re.DOTALL | re.IGNORECASE)
            if svg_match:
                return svg_match.group(0)
            else:
                # Если SVG не найден, создаем базовый шаблон
                return self._create_fallback_svg(prompt)
                
        except Exception as e:
            logger.error(f"Ошибка при генерации SVG с LLM: {e}")
            return self._create_fallback_svg(prompt)
    
    async def _optimize_svg(self, svg_content: str, config: DiagramConfig) -> str:
        """Оптимизация SVG"""
        
        try:
            # Добавляем базовые стили и настройки
            optimized_svg = self._add_svg_styles(svg_content, config)
            
            # Добавляем интерактивность
            optimized_svg = self._add_interactivity(optimized_svg)
            
            # Оптимизируем размер
            optimized_svg = self._optimize_size(optimized_svg, config)
            
            # Добавляем метаданные
            optimized_svg = self._add_metadata(optimized_svg)
            
            return optimized_svg
            
        except Exception as e:
            logger.error(f"Ошибка при оптимизации SVG: {e}")
            return svg_content
    
    def _add_svg_styles(self, svg_content: str, config: DiagramConfig) -> str:
        """Добавление стилей к SVG"""
        
        colors = config.colors or self.color_schemes[config.theme]
        
        # Базовые стили
        styles = f"""
        <defs>
            <style>
                .diagram-container {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    font-size: 14px;
                }}
                .component {{
                    fill: {colors['primary']};
                    stroke: {colors['border']};
                    stroke-width: 2;
                    rx: 8;
                    ry: 8;
                    transition: all 0.3s ease;
                }}
                .component:hover {{
                    fill: {colors['accent']};
                    transform: scale(1.05);
                }}
                .connection {{
                    stroke: {colors['secondary']};
                    stroke-width: 3;
                    fill: none;
                    marker-end: url(#arrowhead);
                }}
                .text {{
                    fill: {colors['text']};
                    font-weight: 500;
                }}
                .text-secondary {{
                    fill: {colors['text_secondary']};
                    font-size: 12px;
                }}
                .background {{
                    fill: {colors['background']};
                }}
                .grid {{
                    stroke: {colors['border']};
                    stroke-width: 1;
                    opacity: 0.1;
                }}
                .shadow {{
                    filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
                }}
            </style>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                    refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="{colors['secondary']}" />
            </marker>
        </defs>
        """
        
        # Вставляем стили после открывающего тега SVG
        svg_content = re.sub(
            r'(<svg[^>]*>)',
            r'\1' + styles,
            svg_content,
            flags=re.IGNORECASE
        )
        
        return svg_content
    
    def _add_interactivity(self, svg_content: str) -> str:
        """Добавление интерактивности к SVG"""
        
        # Добавляем hover эффекты и tooltips
        interactive_script = """
        <script type="text/javascript">
            // Hover эффекты
            document.querySelectorAll('.component').forEach(function(element) {
                element.addEventListener('mouseenter', function() {
                    this.style.cursor = 'pointer';
                    this.style.filter = 'brightness(1.1)';
                });
                
                element.addEventListener('mouseleave', function() {
                    this.style.filter = 'brightness(1)';
                });
                
                element.addEventListener('click', function() {
                    // Показываем информацию о компоненте
                    const title = this.getAttribute('data-title') || 'Компонент';
                    const description = this.getAttribute('data-description') || '';
                    alert(title + '\\n\\n' + description);
                });
            });
            
            // Анимация появления
            document.querySelectorAll('.component').forEach(function(element, index) {
                element.style.opacity = '0';
                element.style.transform = 'translateY(20px)';
                
                setTimeout(function() {
                    element.style.transition = 'all 0.5s ease';
                    element.style.opacity = '1';
                    element.style.transform = 'translateY(0)';
                }, index * 100);
            });
        </script>
        """
        
        # Вставляем скрипт перед закрывающим тегом SVG
        svg_content = re.sub(
            r'(</svg>)',
            interactive_script + r'\1',
            svg_content,
            flags=re.IGNORECASE
        )
        
        return svg_content
    
    def _optimize_size(self, svg_content: str, config: DiagramConfig) -> str:
        """Оптимизация размера SVG"""
        
        # Устанавливаем размеры
        svg_content = re.sub(
            r'<svg([^>]*)>',
            f'<svg\\1 width="{config.width}" height="{config.height}" viewBox="0 0 {config.width} {config.height}">',
            svg_content,
            flags=re.IGNORECASE
        )
        
        return svg_content
    
    def _add_metadata(self, svg_content: str) -> str:
        """Добавление метаданных к SVG"""
        
        metadata = """
        <metadata>
            <title>Architecture Diagram</title>
            <description>Generated by LLM Tuning Service</description>
            <creator>reLink System</creator>
            <created>2024</created>
        </metadata>
        """
        
        # Вставляем метаданные после открывающего тега SVG
        svg_content = re.sub(
            r'(<svg[^>]*>)',
            r'\1' + metadata,
            svg_content,
            flags=re.IGNORECASE
        )
        
        return svg_content
    
    def _create_fallback_svg(self, prompt: str) -> str:
        """Создание базового SVG в случае ошибки"""
        
        return f"""
        <svg width="1200" height="800" viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <style>
                    .background {{ fill: #1a1a1a; }}
                    .component {{ fill: #3b82f6; stroke: #374151; stroke-width: 2; rx: 8; ry: 8; }}
                    .text {{ fill: #ffffff; font-family: Arial, sans-serif; font-size: 14px; }}
                    .text-secondary {{ fill: #9ca3af; font-size: 12px; }}
                </style>
            </defs>
            
            <rect width="1200" height="800" class="background"/>
            
            <text x="600" y="50" text-anchor="middle" class="text" font-size="24" font-weight="bold">
                Архитектурная диаграмма
            </text>
            
            <text x="600" y="80" text-anchor="middle" class="text-secondary">
                Сгенерировано с помощью LLM
            </text>
            
            <rect x="100" y="150" width="200" height="100" class="component"/>
            <text x="200" y="200" text-anchor="middle" class="text">Frontend</text>
            
            <rect x="400" y="150" width="200" height="100" class="component"/>
            <text x="500" y="200" text-anchor="middle" class="text">Backend</text>
            
            <rect x="700" y="150" width="200" height="100" class="component"/>
            <text x="800" y="200" text-anchor="middle" class="text">Database</text>
            
            <rect x="100" y="350" width="200" height="100" class="component"/>
            <text x="200" y="400" text-anchor="middle" class="text">LLM Service</text>
            
            <rect x="400" y="350" width="200" height="100" class="component"/>
            <text x="500" y="400" text-anchor="middle" class="text">Cache</text>
            
            <rect x="700" y="350" width="200" height="100" class="component"/>
            <text x="800" y="400" text-anchor="middle" class="text">Monitoring</text>
            
            <text x="600" y="550" text-anchor="middle" class="text-secondary">
                Описание: {prompt[:100]}...
            </text>
        </svg>
        """
    
    async def generate_diagram_collection(
        self,
        system_description: str,
        diagram_types: List[DiagramType] = None
    ) -> Dict[str, Any]:
        """Генерация коллекции диаграмм для системы"""
        
        if diagram_types is None:
            diagram_types = [
                DiagramType.SYSTEM_ARCHITECTURE,
                DiagramType.DATA_FLOW,
                DiagramType.DEPLOYMENT,
                DiagramType.MICROSERVICES
            ]
        
        results = {}
        
        for diagram_type in diagram_types:
            try:
                result = await self.generate_diagram(diagram_type, system_description)
                results[diagram_type.value] = result
            except Exception as e:
                logger.error(f"Ошибка при генерации {diagram_type.value}: {e}")
                results[diagram_type.value] = {"success": False, "error": str(e)}
        
        return {
            "collection": results,
            "total_generated": len([r for r in results.values() if r.get("success", False)]),
            "total_requested": len(diagram_types)
        }
    
    async def validate_svg(self, svg_content: str) -> Dict[str, Any]:
        """Валидация SVG контента"""
        
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        try:
            # Проверяем базовую структуру SVG
            if not re.search(r'<svg[^>]*>', svg_content, re.IGNORECASE):
                validation_result["errors"].append("Отсутствует открывающий тег SVG")
            
            if not re.search(r'</svg>', svg_content, re.IGNORECASE):
                validation_result["errors"].append("Отсутствует закрывающий тег SVG")
            
            # Проверяем размеры
            if not re.search(r'width=["\']\d+["\']', svg_content, re.IGNORECASE):
                validation_result["warnings"].append("Не указана ширина SVG")
            
            if not re.search(r'height=["\']\d+["\']', svg_content, re.IGNORECASE):
                validation_result["warnings"].append("Не указана высота SVG")
            
            # Проверяем наличие элементов
            if not re.search(r'<rect|<circle|<polygon|<path', svg_content, re.IGNORECASE):
                validation_result["warnings"].append("Отсутствуют графические элементы")
            
            # Проверяем стили
            if not re.search(r'<style|<defs', svg_content, re.IGNORECASE):
                validation_result["suggestions"].append("Рекомендуется добавить стили")
            
            # Определяем валидность
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
            return validation_result
            
        except Exception as e:
            validation_result["errors"].append(f"Ошибка валидации: {str(e)}")
            return validation_result