"""
Сервисы для работы с документацией
"""

import os
import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import markdown
from pathlib import Path

from .models import (
    VersionInfo, ChangelogEntry, DocumentationContent, ReadmeInfo,
    RoadmapInfo, FAQEntry, AboutInfo, HowItWorksInfo
)
from .cache import cache
from .config import settings

logger = logging.getLogger(__name__)


class DocumentationService:
    """Сервис для работы с документацией"""
    
    def __init__(self):
        self.docs_path = Path(settings.docs_path)
        self.version_file = Path(settings.version_file)
        self.readme_file = Path(settings.readme_file)
    
    async def get_version_info(self, force_refresh: bool = False) -> Optional[VersionInfo]:
        """Получение информации о версии"""
        cache_key = "version_info"
        
        if not force_refresh:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug("Version info loaded from cache")
                return VersionInfo(**cached_data)
        
        try:
            if not self.version_file.exists():
                logger.warning(f"Version file not found: {self.version_file}")
                return None
            
            version_content = self.version_file.read_text(encoding='utf-8').strip()
            
            # Парсим версию и дополнительную информацию
            version_info = VersionInfo(
                version=version_content,
                build_date=datetime.now().isoformat(),
                environment=os.getenv("ENVIRONMENT", "development")
            )
            
            # Кэшируем результат
            await cache.set(cache_key, version_info.dict())
            logger.info(f"Version info cached: {version_info.version}")
            
            return version_info
            
        except Exception as e:
            logger.error(f"Error reading version info: {e}")
            return None
    
    async def get_readme_info(self, force_refresh: bool = False) -> Optional[ReadmeInfo]:
        """Получение информации из README"""
        cache_key = "readme_info"
        
        if not force_refresh:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug("README info loaded from cache")
                return ReadmeInfo(**cached_data)
        
        try:
            if not self.readme_file.exists():
                logger.warning(f"README file not found: {self.readme_file}")
                return None
            
            content = self.readme_file.read_text(encoding='utf-8')
            
            # Конвертируем Markdown в HTML
            html_content = markdown.markdown(
                content,
                extensions=['extra', 'codehilite', 'toc']
            )
            
            # Парсим заголовок и описание
            lines = content.split('\n')
            title = "README"
            description = ""
            
            for line in lines:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
                elif line.strip() and not description:
                    description = line.strip()
            
            # Разбиваем на секции
            sections = self._parse_markdown_sections(content)
            
            readme_info = ReadmeInfo(
                title=title,
                description=description,
                sections=sections,
                content=html_content
            )
            
            # Кэшируем результат
            await cache.set(cache_key, readme_info.dict())
            logger.info("README info cached")
            
            return readme_info
            
        except Exception as e:
            logger.error(f"Error reading README: {e}")
            return None
    
    async def get_roadmap_info(self, force_refresh: bool = False) -> Optional[RoadmapInfo]:
        """Получение информации о roadmap"""
        cache_key = "roadmap_info"
        
        if not force_refresh:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug("Roadmap info loaded from cache")
                return RoadmapInfo(**cached_data)
        
        try:
            roadmap_file = self.docs_path / "TECHNICAL_ROADMAP.md"
            if not roadmap_file.exists():
                logger.warning(f"Roadmap file not found: {roadmap_file}")
                return None
            
            content = roadmap_file.read_text(encoding='utf-8')
            html_content = markdown.markdown(content, extensions=['extra'])
            
            # Парсим фазы и функции
            phases = self._parse_roadmap_phases(content)
            features = self._parse_roadmap_features(content)
            
            roadmap_info = RoadmapInfo(
                title="Technical Roadmap",
                phases=phases,
                features=features,
                timeline="Q1-Q4 2024"
            )
            
            # Кэшируем результат
            await cache.set(cache_key, roadmap_info.dict())
            logger.info("Roadmap info cached")
            
            return roadmap_info
            
        except Exception as e:
            logger.error(f"Error reading roadmap: {e}")
            return None
    
    async def get_faq_entries(self, force_refresh: bool = False) -> List[FAQEntry]:
        """Получение FAQ"""
        cache_key = "faq_entries"
        
        if not force_refresh:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug("FAQ entries loaded from cache")
                return [FAQEntry(**entry) for entry in cached_data]
        
        try:
            # Создаем базовый FAQ
            faq_entries = [
                FAQEntry(
                    question="Что такое SEO Link Recommender?",
                    answer="SEO Link Recommender - это интеллектуальная система для анализа и рекомендации внутренних ссылок на WordPress сайтах с использованием AI.",
                    category="Общие вопросы",
                    tags=["seo", "ai", "wordpress"]
                ),
                FAQEntry(
                    question="Как работает система?",
                    answer="Система анализирует контент сайта, использует AI для понимания семантики и рекомендует релевантные внутренние ссылки для улучшения SEO.",
                    category="Технические вопросы",
                    tags=["технологии", "анализ", "рекомендации"]
                ),
                FAQEntry(
                    question="Какие модели AI используются?",
                    answer="Система использует Ollama с моделями qwen2.5:7b-turbo для анализа контента и генерации рекомендаций.",
                    category="AI и модели",
                    tags=["ollama", "qwen", "ai"]
                ),
                FAQEntry(
                    question="Как настроить систему?",
                    answer="Система настраивается через Docker Compose. Подробные инструкции доступны в документации.",
                    category="Настройка",
                    tags=["docker", "настройка", "deployment"]
                )
            ]
            
            # Кэшируем результат
            await cache.set(cache_key, [entry.dict() for entry in faq_entries])
            logger.info("FAQ entries cached")
            
            return faq_entries
            
        except Exception as e:
            logger.error(f"Error creating FAQ entries: {e}")
            return []
    
    async def get_about_info(self, force_refresh: bool = False) -> Optional[AboutInfo]:
        """Получение информации о проекте"""
        cache_key = "about_info"
        
        if not force_refresh:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug("About info loaded from cache")
                return AboutInfo(**cached_data)
        
        try:
            about_info = AboutInfo(
                name="SEO Link Recommender",
                description="Интеллектуальная система для анализа и рекомендации внутренних ссылок на WordPress сайтах с использованием AI",
                version="1.0.0",
                author="SEO Team",
                license="MIT",
                repository="https://github.com/seo-team/seo-link-recommender",
                features=[
                    "AI-анализ контента",
                    "Рекомендации внутренних ссылок",
                    "Интеграция с WordPress",
                    "Веб-интерфейс",
                    "API для интеграции",
                    "Кэширование с Redis"
                ]
            )
            
            # Кэшируем результат
            await cache.set(cache_key, about_info.dict())
            logger.info("About info cached")
            
            return about_info
            
        except Exception as e:
            logger.error(f"Error creating about info: {e}")
            return None
    
    async def get_how_it_works_info(self, force_refresh: bool = False) -> Optional[HowItWorksInfo]:
        """Получение информации о том, как работает система"""
        cache_key = "how_it_works_info"
        
        if not force_refresh:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug("How it works info loaded from cache")
                return HowItWorksInfo(**cached_data)
        
        try:
            how_it_works_info = HowItWorksInfo(
                title="Как работает SEO Link Recommender",
                overview="Система использует современные AI технологии для анализа контента и предоставления персонализированных рекомендаций по внутренним ссылкам.",
                steps=[
                    {
                        "step": 1,
                        "title": "Анализ контента",
                        "description": "Система анализирует весь контент сайта, извлекая ключевые темы и семантические связи"
                    },
                    {
                        "step": 2,
                        "title": "AI обработка",
                        "description": "Используя Ollama и модели qwen2.5, система понимает контекст и семантику контента"
                    },
                    {
                        "step": 3,
                        "title": "Генерация рекомендаций",
                        "description": "На основе анализа система генерирует персонализированные рекомендации по внутренним ссылкам"
                    },
                    {
                        "step": 4,
                        "title": "Веб-интерфейс",
                        "description": "Результаты отображаются в удобном веб-интерфейсе с возможностью экспорта"
                    }
                ],
                architecture="Микросервисная архитектура с FastAPI, React, PostgreSQL и Redis",
                technologies=[
                    "FastAPI (Python)",
                    "React (TypeScript)",
                    "PostgreSQL",
                    "Redis",
                    "Ollama (AI)",
                    "Docker",
                    "Nginx"
                ]
            )
            
            # Кэшируем результат
            await cache.set(cache_key, how_it_works_info.dict())
            logger.info("How it works info cached")
            
            return how_it_works_info
            
        except Exception as e:
            logger.error(f"Error creating how it works info: {e}")
            return None
    
    def _parse_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """Парсинг секций из Markdown"""
        sections = []
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            if line.startswith('## '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "title": line[3:].strip(),
                    "content": []
                }
            elif line.startswith('### '):
                if current_section:
                    current_section["content"].append({
                        "subtitle": line[4:].strip(),
                        "type": "subheading"
                    })
            elif line.strip() and current_section:
                current_section["content"].append({
                    "text": line.strip(),
                    "type": "text"
                })
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _parse_roadmap_phases(self, content: str) -> List[Dict[str, Any]]:
        """Парсинг фаз из roadmap"""
        phases = []
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('## Phase'):
                phase_match = re.search(r'Phase (\d+): (.+)', line)
                if phase_match:
                    phases.append({
                        "phase": int(phase_match.group(1)),
                        "title": phase_match.group(2).strip(),
                        "status": "planned"
                    })
        
        return phases
    
    def _parse_roadmap_features(self, content: str) -> List[Dict[str, Any]]:
        """Парсинг функций из roadmap"""
        features = []
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('- [ ]') or line.startswith('- [x]'):
                status = "completed" if line.startswith('- [x]') else "planned"
                feature = line[6:].strip()
                features.append({
                    "feature": feature,
                    "status": status
                })
        
        return features


# Глобальный экземпляр сервиса
docs_service = DocumentationService() 