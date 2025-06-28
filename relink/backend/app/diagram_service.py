"""
🎨 Сервис для работы с SVG диаграммами в reLink
Интеграция с LLM через единый маршрутизатор
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import httpx
import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from .config import settings
from .models import Diagram, DiagramEmbedding, DiagramTemplate, AnalysisHistory, User
from .exceptions import OllamaException, DatabaseException
from .monitoring import logger, monitor_operation

@dataclass
class DiagramGenerationRequest:
    """Запрос на генерацию диаграммы."""
    diagram_type: str
    title: str
    description: str
    components: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    style_config: Optional[Dict[str, Any]] = None
    analysis_id: Optional[int] = None
    user_id: Optional[int] = None

@dataclass
class DiagramGenerationResult:
    """Результат генерации диаграммы."""
    diagram_id: int
    svg_content: str
    quality_score: float
    generation_time: float
    model_used: str
    confidence_score: float
    validation_result: Dict[str, Any]

class DiagramStyle(BaseModel):
    """Стиль диаграммы."""
    theme: str = Field(default="modern", description="Тема диаграммы")
    colors: Dict[str, str] = Field(default_factory=dict, description="Цветовая схема")
    font_family: str = Field(default="Arial, sans-serif", description="Шрифт")
    font_size: int = Field(default=12, description="Размер шрифта")
    stroke_width: int = Field(default=2, description="Толщина линий")
    opacity: float = Field(default=0.9, description="Прозрачность")

class DiagramService:
    """Сервис для работы с SVG диаграммами."""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.default_model = settings.DEFAULT_LLM_MODEL
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @monitor_operation("diagram_generation")
    async def generate_diagram(
        self, 
        request: DiagramGenerationRequest,
        db: AsyncSession
    ) -> DiagramGenerationResult:
        """Генерация SVG диаграммы с использованием LLM."""
        start_time = datetime.now()
        
        try:
            # Получаем шаблон для типа диаграммы
            template = await self._get_template(request.diagram_type, db)
            
            # Формируем промпт для LLM
            prompt = self._build_prompt(request, template)
            
            # Генерируем SVG через LLM
            svg_content = await self._generate_svg_with_llm(prompt)
            
            # Валидируем и оцениваем качество
            validation_result = await self._validate_svg(svg_content)
            
            # Сохраняем в БД
            diagram = await self._save_diagram(
                request, svg_content, validation_result, db
            )
            
            # Создаем эмбеддинги для RAG
            await self._create_embeddings(diagram, db)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return DiagramGenerationResult(
                diagram_id=diagram.id,
                svg_content=svg_content,
                quality_score=validation_result["quality_score"],
                generation_time=generation_time,
                model_used=self.default_model,
                confidence_score=validation_result.get("confidence_score", 0.8),
                validation_result=validation_result
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации диаграммы: {e}")
            raise OllamaException(f"Ошибка генерации диаграммы: {e}")
    
    async def _get_template(self, diagram_type: str, db: AsyncSession) -> Optional[DiagramTemplate]:
        """Получение шаблона для типа диаграммы."""
        try:
            result = await db.execute(
                select(DiagramTemplate).where(
                    DiagramTemplate.diagram_type == diagram_type,
                    DiagramTemplate.is_active == True
                ).order_by(DiagramTemplate.usage_count.desc())
            )
            template = result.scalar_one_or_none()
            
            if not template:
                # Возвращаем базовый шаблон
                return self._get_default_template(diagram_type)
            
            return template
            
        except Exception as e:
            logger.error(f"Ошибка получения шаблона: {e}")
            return self._get_default_template(diagram_type)
    
    def _get_default_template(self, diagram_type: str) -> DiagramTemplate:
        """Получение базового шаблона."""
        base_prompts = {
            "system_architecture": """
Создай профессиональную SVG диаграмму архитектуры системы:

Компоненты: {components}
Связи: {relationships}
Стиль: {style}

Требования:
1. Используй современный дизайн с градиентами
2. Добавь интерактивность и анимации
3. Включи легенду и заголовок
4. Обеспечь accessibility
5. Оптимизируй для веб-отображения

Размеры: 800x600 пикселей
""",
            "data_flow": """
Создай SVG диаграмму потока данных:

Компоненты: {components}
Связи: {relationships}
Стиль: {style}

Требования:
1. Покажи направление потока стрелками
2. Используй разные цвета для типов данных
3. Добавь анимацию движения
4. Сделай интерактивной
5. Включи tooltips

Размеры: 800x600 пикселей
""",
            "microservices": """
Создай SVG диаграмму микросервисной архитектуры:

Сервисы: {components}
Взаимодействия: {relationships}
Стиль: {style}

Требования:
1. Покажи API Gateway
2. Отобрази микросервисы и БД
3. Добавь очереди сообщений
4. Включи мониторинг
5. Сделай анимированной

Размеры: 800x600 пикселей
"""
        }
        
        return DiagramTemplate(
            name=f"default_{diagram_type}",
            description=f"Базовый шаблон для {diagram_type}",
            diagram_type=diagram_type,
            prompt_template=base_prompts.get(diagram_type, base_prompts["system_architecture"]),
            default_style={},
            is_active=True
        )
    
    def _build_prompt(self, request: DiagramGenerationRequest, template: DiagramTemplate) -> str:
        """Формирование промпта для LLM."""
        style = request.style_config or template.default_style
        
        # Форматируем компоненты и связи
        components_text = "\n".join([
            f"- {comp.get('name', 'Component')}: {comp.get('description', '')}"
            for comp in request.components
        ])
        
        relationships_text = "\n".join([
            f"- {rel.get('from', '')} -> {rel.get('to', '')}: {rel.get('type', 'connection')}"
            for rel in request.relationships
        ])
        
        # Создаем промпт с примерами
        prompt = f"""
Ты - эксперт по созданию профессиональных SVG диаграмм. Создай диаграмму на основе следующих требований:

## ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ:

### 1. СТРУКТУРА SVG:
- Используй viewBox для масштабируемости
- Добавь xmlns="http://www.w3.org/2000/svg"
- Установи width="800" height="600"
- Включи preserveAspectRatio="xMidYMid meet"

### 2. КОМПОНЕНТЫ СИСТЕМЫ:
{components_text}

### 3. СВЯЗИ МЕЖДУ КОМПОНЕНТАМИ:
{relationships_text}

### 4. ДИЗАЙН-СИСТЕМА:
- Цветовая схема: {style.get('colors', {})}
- Шрифт: {style.get('font_family', 'Arial, sans-serif')}
- Размер шрифта: {style.get('font_size', 12)}px
- Толщина линий: {style.get('stroke_width', 2)}px

### 5. ТЕХНИЧЕСКИЕ ЭЛЕМЕНТЫ:
- Используй <defs> для переиспользуемых элементов
- Добавь <filter> для теней и эффектов
- Создай <linearGradient> для градиентов
- Используй <clipPath> для обрезки элементов

### 6. ИНТЕРАКТИВНОСТЬ:
- Добавь <title> и <desc> для accessibility
- Используй CSS hover эффекты
- Включи JavaScript для динамики
- Добавь data-атрибуты для метаданных

### 7. АНИМАЦИИ:
- Используй <animate> для простых анимаций
- Добавь <animateTransform> для трансформаций
- Включи <animateMotion> для движения по пути
- Установи dur="2s" для плавности

## ПРИМЕР СТРУКТУРЫ SVG:

```svg
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
  
  <title>{request.title}</title>
  <desc>{request.description}</desc>
  
  <g id="components">
    <!-- Компоненты системы -->
  </g>
  
  <g id="relationships">
    <!-- Стрелки и линии -->
  </g>
  
  <g id="legend">
    <!-- Объяснение элементов -->
  </g>
  
  <style>
    .component {{ cursor: pointer; transition: all 0.3s; }}
    .component:hover {{ filter: brightness(1.2) drop-shadow(0 0 10px rgba(0,0,0,0.3)); }}
  </style>
  
  <script>
    // JavaScript для интерактивности
  </script>
</svg>
```

## КРИТИЧЕСКИЕ ТРЕБОВАНИЯ:
1. Генерируй ТОЛЬКО валидный SVG код
2. Не добавляй комментарии вне SVG
3. Используй семантические имена для id и class
4. Обеспечь accessibility (ARIA labels)
5. Оптимизируй для веб-отображения

Тип диаграммы: {request.diagram_type}
Заголовок: {request.title}
Описание: {request.description}

Создай профессиональную SVG диаграмму, следуя всем техническим требованиям выше.
"""
        
        return prompt
    
    async def _generate_svg_with_llm(self, prompt: str) -> str:
        """Генерация SVG с помощью LLM."""
        try:
            payload = {
                "model": self.default_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
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
                raise OllamaException(f"Ollama вернул статус {response.status_code}")
            
            result = response.json()
            svg_content = result.get("response", "")
            
            # Извлекаем SVG из ответа
            import re
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
        """Создание базового SVG при ошибке."""
        return """
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <defs>
    <linearGradient id="fallbackGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FF6B6B;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#D63031;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <title>Fallback Diagram</title>
  <desc>Базовая диаграмма при ошибке генерации</desc>
  
  <rect x="50" y="50" width="700" height="500" fill="url(#fallbackGradient)" rx="10"/>
  <text x="400" y="300" text-anchor="middle" fill="white" font-size="24" font-family="Arial, sans-serif">
    Диаграмма будет сгенерирована
  </text>
  <text x="400" y="330" text-anchor="middle" fill="white" font-size="16" font-family="Arial, sans-serif">
    Попробуйте еще раз
  </text>
</svg>
"""
    
    async def _validate_svg(self, svg_content: str) -> Dict[str, Any]:
        """Валидация и оценка качества SVG."""
        validation_result = {
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "quality_score": 0.0,
            "accessibility_score": 0.0,
            "performance_score": 0.0,
            "confidence_score": 0.8
        }
        
        try:
            # Проверяем базовую структуру SVG
            if not svg_content.strip().startswith('<svg'):
                validation_result["errors"].append("SVG должен начинаться с тега <svg>")
                return validation_result
            
            # Парсим SVG
            import xml.etree.ElementTree as ET
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
            animations = root.findall(".//animate") + root.findall(".//animateTransform") + root.findall(".//animateMotion")
            if animations:
                feature_score += 0.5
            if root.find(".//style") or root.find(".//script"):
                feature_score += 0.3
            if root.find(".//title") or root.find(".//desc"):
                feature_score += 0.2
            total_score += feature_score * 20
            
            validation_result["quality_score"] = min(total_score, max_score) / max_score
            validation_result["is_valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            validation_result["errors"].append(f"Ошибка валидации: {e}")
        
        return validation_result
    
    def _check_accessibility(self, root) -> float:
        """Проверка accessibility."""
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
        
        return score / checks if checks > 0 else 0.0
    
    def _check_performance(self, root) -> float:
        """Проверка производительности."""
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
        
        # Проверяем использование групп
        groups = root.findall(".//g")
        if groups:
            score += 1.0
        checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    async def _save_diagram(
        self, 
        request: DiagramGenerationRequest,
        svg_content: str,
        validation_result: Dict[str, Any],
        db: AsyncSession
    ) -> Diagram:
        """Сохранение диаграммы в БД."""
        try:
            diagram = Diagram(
                analysis_id=request.analysis_id,
                user_id=request.user_id,
                diagram_type=request.diagram_type,
                title=request.title,
                description=request.description,
                svg_content=svg_content,
                svg_metadata={
                    "components_count": len(request.components),
                    "relationships_count": len(request.relationships),
                    "style_config": request.style_config or {}
                },
                quality_score=validation_result["quality_score"],
                accessibility_score=validation_result["accessibility_score"],
                performance_score=validation_result["performance_score"],
                validation_errors=validation_result["errors"],
                optimization_suggestions=validation_result["warnings"],
                llm_model_used=self.default_model,
                confidence_score=validation_result.get("confidence_score", 0.8),
                components=request.components,
                relationships=request.relationships,
                style_config=request.style_config or {},
                status="generated"
            )
            
            db.add(diagram)
            await db.commit()
            await db.refresh(diagram)
            
            return diagram
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка сохранения диаграммы: {e}")
            raise DatabaseException(f"Ошибка сохранения диаграммы: {e}")
    
    async def _create_embeddings(self, diagram: Diagram, db: AsyncSession):
        """Создание эмбеддингов для RAG поиска."""
        try:
            # Создаем эмбеддинг для заголовка
            title_embedding = await self._create_text_embedding(diagram.title)
            title_emb = DiagramEmbedding(
                diagram_id=diagram.id,
                embedding_type="title",
                vector_model="text-embedding-3-small",
                embedding_vector=json.dumps(title_embedding.tolist()),
                dimension=len(title_embedding),
                context_text=diagram.title,
                semantic_keywords=self._extract_keywords(diagram.title)
            )
            db.add(title_emb)
            
            # Создаем эмбеддинг для описания
            if diagram.description:
                desc_embedding = await self._create_text_embedding(diagram.description)
                desc_emb = DiagramEmbedding(
                    diagram_id=diagram.id,
                    embedding_type="description",
                    vector_model="text-embedding-3-small",
                    embedding_vector=json.dumps(desc_embedding.tolist()),
                    dimension=len(desc_embedding),
                    context_text=diagram.description,
                    semantic_keywords=self._extract_keywords(diagram.description)
                )
                db.add(desc_emb)
            
            # Создаем эмбеддинг для компонентов
            components_text = " ".join([
                f"{comp.get('name', '')} {comp.get('description', '')}"
                for comp in diagram.components
            ])
            if components_text:
                comp_embedding = await self._create_text_embedding(components_text)
                comp_emb = DiagramEmbedding(
                    diagram_id=diagram.id,
                    embedding_type="components",
                    vector_model="text-embedding-3-small",
                    embedding_vector=json.dumps(comp_embedding.tolist()),
                    dimension=len(comp_embedding),
                    context_text=components_text,
                    semantic_keywords=self._extract_keywords(components_text)
                )
                db.add(comp_emb)
            
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка создания эмбеддингов: {e}")
    
    async def _create_text_embedding(self, text: str) -> np.ndarray:
        """Создание эмбеддинга для текста."""
        try:
            # Используем Ollama для создания эмбеддингов
            payload = {
                "model": "nomic-embed-text",
                "prompt": text
            }
            
            response = await self.client.post(
                f"{self.ollama_url}/api/embeddings",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return np.array(result.get("embedding", []))
            else:
                # Fallback: создаем случайный эмбеддинг
                return np.random.rand(384)
                
        except Exception as e:
            logger.error(f"Ошибка создания эмбеддинга: {e}")
            return np.random.rand(384)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из текста."""
        # Простая реализация - можно улучшить с помощью NLTK или spaCy
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        # Убираем стоп-слова
        stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'об', 'за', 'при', 'под', 'над'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return list(set(keywords))[:10]  # Возвращаем топ-10 уникальных слов
    
    @monitor_operation("diagram_search")
    async def search_diagrams(
        self,
        query: str,
        diagram_type: Optional[str] = None,
        limit: int = 10,
        db: AsyncSession = None
    ) -> List[Diagram]:
        """Поиск диаграмм с использованием RAG."""
        try:
            # Создаем эмбеддинг для запроса
            query_embedding = await self._create_text_embedding(query)
            
            # Получаем все эмбеддинги
            result = await db.execute(
                select(DiagramEmbedding).where(
                    DiagramEmbedding.embedding_type.in_(["title", "description", "components"])
                )
            )
            embeddings = result.scalars().all()
            
            # Вычисляем сходство
            similarities = []
            for emb in embeddings:
                try:
                    emb_vector = np.array(json.loads(emb.embedding_vector))
                    similarity = np.dot(query_embedding, emb_vector) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(emb_vector)
                    )
                    similarities.append((similarity, emb.diagram_id))
                except Exception as e:
                    logger.error(f"Ошибка вычисления сходства: {e}")
                    continue
            
            # Сортируем по сходству
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Получаем диаграммы
            diagram_ids = [diagram_id for _, diagram_id in similarities[:limit]]
            
            if diagram_ids:
                result = await db.execute(
                    select(Diagram).where(
                        Diagram.id.in_(diagram_ids),
                        Diagram.status == "generated"
                    )
                )
                diagrams = result.scalars().all()
                
                # Сортируем по порядку сходства
                diagram_dict = {d.id: d for d in diagrams}
                sorted_diagrams = [diagram_dict[diagram_id] for diagram_id in diagram_ids if diagram_id in diagram_dict]
                
                return sorted_diagrams
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка поиска диаграмм: {e}")
            return []
    
    @monitor_operation("diagram_optimization")
    async def optimize_diagram(self, diagram_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Оптимизация существующей диаграммы."""
        try:
            # Получаем диаграмму
            result = await db.execute(
                select(Diagram).where(Diagram.id == diagram_id)
            )
            diagram = result.scalar_one_or_none()
            
            if not diagram:
                raise DatabaseException("Диаграмма не найдена")
            
            # Анализируем текущую диаграмму
            validation_result = await self._validate_svg(diagram.svg_content)
            
            # Если качество низкое, пытаемся улучшить
            if validation_result["quality_score"] < 0.7:
                # Создаем улучшенный запрос
                improved_request = DiagramGenerationRequest(
                    diagram_type=diagram.diagram_type,
                    title=diagram.title,
                    description=diagram.description,
                    components=diagram.components,
                    relationships=diagram.relationships,
                    style_config=diagram.style_config,
                    analysis_id=diagram.analysis_id,
                    user_id=diagram.user_id
                )
                
                # Генерируем улучшенную версию
                improved_result = await self.generate_diagram(improved_request, db)
                
                # Обновляем оригинальную диаграмму
                diagram.svg_content = improved_result.svg_content
                diagram.quality_score = improved_result.quality_score
                diagram.accessibility_score = improved_result.validation_result["accessibility_score"]
                diagram.performance_score = improved_result.validation_result["performance_score"]
                diagram.validation_errors = improved_result.validation_result["errors"]
                diagram.optimization_suggestions = improved_result.validation_result["warnings"]
                diagram.status = "optimized"
                diagram.version += 1
                
                await db.commit()
                
                return {
                    "success": True,
                    "improved_quality": improved_result.quality_score,
                    "original_quality": validation_result["quality_score"],
                    "improvement": improved_result.quality_score - validation_result["quality_score"]
                }
            
            return {
                "success": True,
                "message": "Диаграмма уже имеет высокое качество",
                "quality_score": validation_result["quality_score"]
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка оптимизации диаграммы: {e}")
            raise DatabaseException(f"Ошибка оптимизации диаграммы: {e}")

# Глобальный экземпляр сервиса
diagram_service = DiagramService() 