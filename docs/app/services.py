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
import aiohttp
import asyncio
import json
from urllib.parse import urljoin, urlparse

from .models import (
    VersionInfo, ChangelogEntry, DocumentationContent, ReadmeInfo,
    RoadmapInfo, FAQEntry, AboutInfo, HowItWorksInfo,
    MicroserviceInfo, ServiceEndpoint, ServiceDocumentation,
    ServiceDiscovery, DocumentationSync, DocumentationSearch,
    DocumentationSearchResult
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
                logger.warning("Version file not found")
                return None
            
            with open(self.version_file, 'r', encoding='utf-8') as f:
                version = f.read().strip()
            
            version_info = VersionInfo(
                version=version,
                build_date=datetime.utcnow().isoformat(),
                environment=os.getenv('ENVIRONMENT', 'development')
            )
            
            await cache.set(cache_key, version_info.dict(), ttl=3600)
            logger.info(f"Version info updated: {version}")
            return version_info
            
        except Exception as e:
            logger.error(f"Error reading version info: {e}")
            return None
    
    async def get_readme_info(self, force_refresh: bool = False) -> Optional[ReadmeInfo]:
        """Получение README документации"""
        cache_key = "readme_info"
        
        if not force_refresh:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug("README info loaded from cache")
                return ReadmeInfo(**cached_data)
        
        try:
            if not self.readme_file.exists():
                logger.warning("README file not found")
                return None
            
            with open(self.readme_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсинг README
            lines = content.split('\n')
            title = "README"
            description = ""
            sections = []
            
            current_section = None
            current_content = []
            
            for line in lines:
                if line.startswith('# '):
                    if current_section:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content).strip()
                        })
                    current_section = line[2:].strip()
                    current_content = []
                elif line.startswith('## '):
                    if current_section:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content).strip()
                        })
                    current_section = line[3:].strip()
                    current_content = []
                elif current_section:
                    current_content.append(line)
                elif not description and line.strip():
                    description = line.strip()
            
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content).strip()
                })
            
            # Конвертация в HTML
            html_content = markdown.markdown(content)
            
            readme_info = ReadmeInfo(
                title=title,
                description=description,
                sections=sections,
                content=html_content
            )
            
            await cache.set(cache_key, readme_info.dict(), ttl=3600)
            logger.info("README info updated")
            return readme_info
            
        except Exception as e:
            logger.error(f"Error reading README: {e}")
            return None
    
    async def get_roadmap_info(self, force_refresh: bool = False) -> Optional[RoadmapInfo]:
        """Получение технического roadmap"""
        cache_key = "roadmap_info"
        
        if not force_refresh:
            cached_data = await cache.get(cache_key)
            if cached_data:
                logger.debug("Roadmap info loaded from cache")
                return RoadmapInfo(**cached_data)
        
        try:
            roadmap_file = self.docs_path / "TECHNICAL_ROADMAP.md"
            if not roadmap_file.exists():
                logger.warning("Roadmap file not found")
                return None
            
            with open(roadmap_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсинг roadmap
            lines = content.split('\n')
            title = "Technical Roadmap"
            phases = []
            features = []
            
            current_phase = None
            current_features = []
            
            for line in lines:
                if line.startswith('## Phase'):
                    if current_phase:
                        phases.append({
                            'name': current_phase,
                            'features': current_features
                        })
                    current_phase = line[2:].strip()
                    current_features = []
                elif line.startswith('- ') and current_phase:
                    feature = line[2:].strip()
                    current_features.append(feature)
                    features.append({
                        'name': feature,
                        'phase': current_phase
                    })
            
            if current_phase:
                phases.append({
                    'name': current_phase,
                    'features': current_features
                })
            
            roadmap_info = RoadmapInfo(
                title=title,
                phases=phases,
                features=features
            )
            
            await cache.set(cache_key, roadmap_info.dict(), ttl=3600)
            logger.info("Roadmap info updated")
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
            faq_file = self.docs_path / "FAQ.md"
            if not faq_file.exists():
                logger.warning("FAQ file not found")
                return []
            
            with open(faq_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Парсинг FAQ
            faq_entries = []
            current_question = None
            current_answer = []
            
            for line in content.split('\n'):
                if line.startswith('### '):
                    if current_question:
                        faq_entries.append(FAQEntry(
                            question=current_question,
                            answer='\n'.join(current_answer).strip()
                        ))
                    current_question = line[4:].strip()
                    current_answer = []
                elif current_question and line.strip():
                    current_answer.append(line)
            
            if current_question:
                faq_entries.append(FAQEntry(
                    question=current_question,
                    answer='\n'.join(current_answer).strip()
                ))
            
            await cache.set(cache_key, [entry.dict() for entry in faq_entries], ttl=3600)
            logger.info(f"FAQ entries updated: {len(faq_entries)} entries")
            return faq_entries
            
        except Exception as e:
            logger.error(f"Error reading FAQ: {e}")
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
            version_info = await self.get_version_info()
            
            about_info = AboutInfo(
                name="SEO Link Recommender",
                description="Интеллектуальная система для анализа и оптимизации SEO",
                version=version_info.version if version_info else "1.0.0",
                author="reLink Team",
                license="MIT",
                repository="https://github.com/relink/seo-recommender",
                features=[
                    "Анализ WordPress сайтов",
                    "SEO рекомендации",
                    "Генерация диаграмм",
                    "LLM интеграция",
                    "Микросервисная архитектура"
                ]
            )
            
            await cache.set(cache_key, about_info.dict(), ttl=3600)
            logger.info("About info updated")
            return about_info
            
        except Exception as e:
            logger.error(f"Error getting about info: {e}")
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
                overview="Система использует микросервисную архитектуру для анализа WordPress сайтов и генерации SEO рекомендаций",
                steps=[
                    {
                        "step": 1,
                        "title": "Анализ сайта",
                        "description": "Система анализирует WordPress сайт, извлекая информацию о структуре, контенте и SEO"
                    },
                    {
                        "step": 2,
                        "title": "LLM обработка",
                        "description": "Языковая модель обрабатывает данные и генерирует рекомендации"
                    },
                    {
                        "step": 3,
                        "title": "Генерация диаграмм",
                        "description": "Создаются визуальные диаграммы для лучшего понимания структуры"
                    },
                    {
                        "step": 4,
                        "title": "Формирование отчета",
                        "description": "Система формирует детальный отчет с рекомендациями"
                    }
                ],
                architecture="Микросервисная архитектура с использованием FastAPI, PostgreSQL и Redis",
                technologies=["Python", "FastAPI", "PostgreSQL", "Redis", "Ollama", "React"]
            )
            
            await cache.set(cache_key, how_it_works_info.dict(), ttl=3600)
            logger.info("How it works info updated")
            return how_it_works_info
            
        except Exception as e:
            logger.error(f"Error getting how it works info: {e}")
            return None


# 🚀 НОВЫЙ СЕРВИС ДЛЯ АВТОМАТИЧЕСКОЙ ДОКУМЕНТАЦИИ МИКРОСЕРВИСОВ

class MicroserviceDocumentationService:
    """Сервис для автоматического обнаружения и синхронизации документации микросервисов"""
    
    def __init__(self):
        self.discovered_services: Dict[str, ServiceDiscovery] = {}
        self.service_docs: Dict[str, ServiceDocumentation] = {}
        self.sync_history: List[DocumentationSync] = []
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Инициализация сервиса"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Загрузка конфигурации сервисов
        await self._load_service_config()
        logger.info(f"Microservice documentation service initialized with {len(self.discovered_services)} services")
    
    async def _load_service_config(self):
        """Загрузка конфигурации сервисов"""
        # Конфигурация известных сервисов
        services_config = [
            {
                "name": "backend",
                "base_url": "http://backend:8000",
                "health_endpoint": "/api/v1/health",
                "docs_endpoint": "/docs",
                "openapi_endpoint": "/openapi.json",
                "readme_path": "/app/README.md",
                "category": "core",
                "display_name": "Backend API",
                "description": "Основной API сервис для анализа WordPress сайтов"
            },
            {
                "name": "llm-tuning",
                "base_url": "http://llm-tuning:8001",
                "health_endpoint": "/api/v1/health",
                "docs_endpoint": "/docs",
                "openapi_endpoint": "/openapi.json",
                "readme_path": "/app/README.md",
                "category": "ai",
                "display_name": "LLM Tuning Service",
                "description": "Сервис для тюнинга и оптимизации языковых моделей"
            },
            {
                "name": "benchmark",
                "base_url": "http://benchmark:8002",
                "health_endpoint": "/health",
                "docs_endpoint": "/docs",
                "openapi_endpoint": "/openapi.json",
                "readme_path": "/app/README.md",
                "category": "testing",
                "display_name": "Benchmark Service",
                "description": "Сервис для бенчмаркинга и тестирования производительности"
            },
            {
                "name": "testing",
                "base_url": "http://testing-service:8000",
                "health_endpoint": "/api/v1/health",
                "docs_endpoint": "/docs",
                "openapi_endpoint": "/openapi.json",
                "readme_path": "/app/README.md",
                "category": "testing",
                "display_name": "Testing Service",
                "description": "Сервис для автоматизированного тестирования"
            },
            {
                "name": "monitoring",
                "base_url": "http://monitoring:8002",
                "health_endpoint": "/api/v1/health",
                "docs_endpoint": "/docs",
                "openapi_endpoint": "/openapi.json",
                "readme_path": "/app/README.md",
                "category": "monitoring",
                "display_name": "Monitoring Service",
                "description": "Сервис мониторинга и метрик системы"
            }
        ]
        
        for config in services_config:
            discovery = ServiceDiscovery(**config)
            self.discovered_services[config["name"]] = discovery
    
    async def discover_services(self) -> List[MicroserviceInfo]:
        """Обнаружение доступных микросервисов"""
        discovered = []
        
        for service_name, discovery in self.discovered_services.items():
            if not discovery.enabled:
                continue
            
            try:
                health_url = urljoin(discovery.base_url, discovery.health_endpoint)
                async with self.session.get(health_url) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        
                        service_info = MicroserviceInfo(
                            name=service_name,
                            display_name=discovery.display_name or service_name,
                            version=health_data.get("version", "1.0.0"),
                            description=discovery.description or "",
                            category=discovery.category or "unknown",
                            status="healthy",
                            health_url=health_url,
                            docs_url=urljoin(discovery.base_url, discovery.docs_endpoint) if discovery.docs_endpoint else None,
                            api_url=urljoin(discovery.base_url, discovery.openapi_endpoint) if discovery.openapi_endpoint else None
                        )
                        
                        discovered.append(service_info)
                        discovery.last_check = datetime.utcnow()
                        
                        logger.info(f"Discovered service: {service_name} ({service_info.status})")
                    else:
                        logger.warning(f"Service {service_name} health check failed: {response.status}")
                        
            except Exception as e:
                logger.error(f"Error discovering service {service_name}: {e}")
                discovery.last_check = datetime.utcnow()
        
        return discovered
    
    async def sync_service_documentation(self, service_name: str) -> DocumentationSync:
        """Синхронизация документации конкретного сервиса"""
        sync_record = DocumentationSync(
            service_name=service_name,
            sync_type="manual",
            status="running"
        )
        
        try:
            discovery = self.discovered_services.get(service_name)
            if not discovery:
                raise ValueError(f"Service {service_name} not found in configuration")
            
            # Получение информации о сервисе
            service_info = await self._get_service_info(discovery)
            
            # Получение README
            readme_content = await self._get_service_readme(discovery)
            
            # Получение API документации
            api_docs = await self._get_service_api_docs(discovery)
            
            # Создание документации сервиса
            service_doc = ServiceDocumentation(
                service=service_info,
                readme=readme_content,
                api_docs=api_docs,
                last_sync=datetime.utcnow()
            )
            
            # Сохранение в кэш
            cache_key = f"service_docs:{service_name}"
            await cache.set(cache_key, service_doc.dict(), ttl=3600)
            
            self.service_docs[service_name] = service_doc
            
            sync_record.status = "completed"
            sync_record.completed_at = datetime.utcnow()
            sync_record.documents_updated = 1
            
            logger.info(f"Documentation synced for service: {service_name}")
            
        except Exception as e:
            sync_record.status = "failed"
            sync_record.completed_at = datetime.utcnow()
            sync_record.error_message = str(e)
            logger.error(f"Error syncing documentation for {service_name}: {e}")
        
        self.sync_history.append(sync_record)
        return sync_record
    
    async def _get_service_info(self, discovery: ServiceDiscovery) -> MicroserviceInfo:
        """Получение информации о сервисе"""
        health_url = urljoin(discovery.base_url, discovery.health_endpoint)
        
        async with self.session.get(health_url) as response:
            health_data = await response.json()
            
            return MicroserviceInfo(
                name=discovery.service_name,
                display_name=discovery.display_name or discovery.service_name,
                version=health_data.get("version", "1.0.0"),
                description=discovery.description or "",
                category=discovery.category or "unknown",
                status="healthy",
                health_url=health_url,
                docs_url=urljoin(discovery.base_url, discovery.docs_endpoint) if discovery.docs_endpoint else None,
                api_url=urljoin(discovery.base_url, discovery.openapi_endpoint) if discovery.openapi_endpoint else None
            )
    
    async def _get_service_readme(self, discovery: ServiceDiscovery) -> Optional[str]:
        """Получение README сервиса"""
        if not discovery.readme_path:
            return None
        
        try:
            # Попытка получить README через API эндпоинт
            readme_url = urljoin(discovery.base_url, "/api/v1/docs/readme")
            async with self.session.get(readme_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("content", "")
        except Exception as e:
            logger.warning(f"Could not get README via API for {discovery.service_name}: {e}")
        
        return None
    
    async def _get_service_api_docs(self, discovery: ServiceDiscovery) -> List[ServiceEndpoint]:
        """Получение API документации сервиса"""
        if not discovery.openapi_endpoint:
            return []
        
        try:
            openapi_url = urljoin(discovery.base_url, discovery.openapi_endpoint)
            async with self.session.get(openapi_url) as response:
                if response.status == 200:
                    openapi_data = await response.json()
                    return self._parse_openapi_spec(openapi_data)
        except Exception as e:
            logger.warning(f"Could not get OpenAPI spec for {discovery.service_name}: {e}")
        
        return []
    
    def _parse_openapi_spec(self, openapi_data: Dict[str, Any]) -> List[ServiceEndpoint]:
        """Парсинг OpenAPI спецификации"""
        endpoints = []
        
        paths = openapi_data.get("paths", {})
        for path, methods in paths.items():
            for method, spec in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = ServiceEndpoint(
                        path=path,
                        method=method.upper(),
                        description=spec.get("summary", "") or spec.get("description", ""),
                        parameters=spec.get("parameters", []),
                        request_body=spec.get("requestBody", {}),
                        response_schema=spec.get("responses", {}),
                        requires_auth="security" in spec,
                        deprecated=spec.get("deprecated", False)
                    )
                    endpoints.append(endpoint)
        
        return endpoints
    
    async def search_documentation(self, search: DocumentationSearch) -> DocumentationSearchResult:
        """Поиск по документации всех сервисов"""
        start_time = datetime.utcnow()
        results = []
        
        # Поиск по кэшированной документации
        for service_name, service_doc in self.service_docs.items():
            if search.services and service_name not in search.services:
                continue
            
            if search.categories and service_doc.service.category not in search.categories:
                continue
            
            # Поиск в README
            if service_doc.readme and search.query.lower() in service_doc.readme.lower():
                results.append({
                    "type": "readme",
                    "service": service_name,
                    "title": f"README - {service_doc.service.display_name}",
                    "content": service_doc.readme[:200] + "...",
                    "url": f"/docs/services/{service_name}",
                    "relevance_score": 0.8
                })
            
            # Поиск в API документации
            for endpoint in service_doc.api_docs:
                if (search.query.lower() in endpoint.description.lower() or
                    search.query.lower() in endpoint.path.lower()):
                    results.append({
                        "type": "api",
                        "service": service_name,
                        "title": f"{endpoint.method} {endpoint.path}",
                        "content": endpoint.description,
                        "url": f"/docs/services/{service_name}#{endpoint.path}",
                        "relevance_score": 0.6
                    })
        
        # Сортировка по релевантности
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Пагинация
        total = len(results)
        results = results[search.offset:search.offset + search.limit]
        
        search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return DocumentationSearchResult(
            query=search.query,
            results=results,
            total=total,
            search_time_ms=int(search_time),
            suggestions=[]
        )
    
    async def get_service_documentation(self, service_name: str) -> Optional[ServiceDocumentation]:
        """Получение документации конкретного сервиса"""
        # Сначала проверяем кэш
        cache_key = f"service_docs:{service_name}"
        cached_data = await cache.get(cache_key)
        
        if cached_data:
            return ServiceDocumentation(**cached_data)
        
        # Если нет в кэше, синхронизируем
        await self.sync_service_documentation(service_name)
        return self.service_docs.get(service_name)
    
    async def get_all_services(self) -> List[MicroserviceInfo]:
        """Получение списка всех сервисов"""
        services = []
        
        for service_name, service_doc in self.service_docs.items():
            services.append(service_doc.service)
        
        return services
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.session:
            await self.session.close()


# Глобальные экземпляры сервисов
docs_service = DocumentationService()
microservice_docs_service = MicroserviceDocumentationService() 