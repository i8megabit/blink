#!/usr/bin/env python3
"""
🎯 Комплексный E2E тест всей цепочки reLink
relink → router → chromadb → ollama → llm

Тестирование полного индексирования домена dagorod.ru
и генерации качественных SEO-рекомендаций
"""

import os
import sys
import time
import json
import requests
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('e2e_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Результат теста"""
    test_name: str
    status: str  # success, error, warning
    score: float  # 0-100
    details: Dict[str, Any]
    duration: float
    timestamp: datetime

@dataclass
class SEORecommendation:
    """SEO-рекомендация"""
    type: str  # technical, content, structure, performance
    priority: str  # high, medium, low
    description: str
    impact_score: float  # 0-100
    implementation_difficulty: str  # easy, medium, hard
    estimated_improvement: str  # ожидаемое улучшение

class ComprehensiveE2ETest:
    """Комплексный E2E тест всей системы reLink"""
    
    def __init__(self, domain: str = "dagorod.ru"):
        self.domain = domain
        self.base_urls = {
            'relink': 'http://localhost:8003',
            'router': 'http://localhost:8001', 
            'chromadb': 'http://localhost:8006',
            'ollama': 'http://localhost:11434',
            'llm_tuning': 'http://localhost:8005'
        }
        self.results: List[TestResult] = []
        self.indexing_data: Dict[str, Any] = {}
        self.seo_recommendations: List[SEORecommendation] = []
        
        # Контекстные данные для сравнений
        self.seo_benchmarks = {
            'internal_linking_score': {
                'excellent': 85,
                'good': 70,
                'average': 50,
                'poor': 30
            },
            'content_quality_score': {
                'excellent': 90,
                'good': 75,
                'average': 60,
                'poor': 40
            },
            'technical_seo_score': {
                'excellent': 95,
                'good': 80,
                'average': 65,
                'poor': 45
            }
        }
        
        # Примеры успешных SEO стратегий
        self.seo_examples = {
            'internal_linking': {
                'good_example': 'https://moz.com/blog/internal-linking-for-seo',
                'best_practices': [
                    'Использование релевантных анкоров',
                    'Логическая структура ссылок',
                    'Равномерное распределение PageRank'
                ]
            },
            'content_optimization': {
                'good_example': 'https://ahrefs.com/blog/content-marketing-strategy/',
                'best_practices': [
                    'Глубокий анализ ключевых слов',
                    'Структурированные данные',
                    'Оптимизация для пользовательского опыта'
                ]
            },
            'technical_seo': {
                'good_example': 'https://backlinko.com/technical-seo-guide',
                'best_practices': [
                    'Оптимизация скорости загрузки',
                    'Мобильная адаптивность',
                    'Безопасность и HTTPS'
                ]
            }
        }
        
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Запуск полного набора тестов"""
        logger.info(f"🚀 Запуск комплексного E2E теста для домена: {self.domain}")
        
        start_time = time.time()
        
        # 1. Проверка доступности всех сервисов
        await self.test_service_availability()
        
        # 2. Тест индексирования домена
        await self.test_domain_indexing()
        
        # 3. Тест работы с ChromaDB
        await self.test_chromadb_integration()
        
        # 4. Тест LLM интеграции
        await self.test_llm_integration()
        
        # 5. Тест генерации SEO-рекомендаций
        await self.test_seo_recommendations()
        
        # 6. Тест углубленного анализа
        await self.test_deep_analysis()
        
        # 7. Тест производительности
        await self.test_performance()
        
        total_duration = time.time() - start_time
        
        # Генерация итогового отчета
        final_report = self.generate_final_report(total_duration)
        
        logger.info(f"✅ E2E тест завершен за {total_duration:.2f} секунд")
        return final_report
    
    async def test_service_availability(self) -> None:
        """Тест доступности всех сервисов"""
        logger.info("🔍 Проверка доступности сервисов...")
        
        for service_name, url in self.base_urls.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health", timeout=10) as response:
                        if response.status == 200:
                            self.results.append(TestResult(
                                test_name=f"service_availability_{service_name}",
                                status="success",
                                score=100.0,
                                details={"url": url, "status_code": response.status},
                                duration=0.1,
                                timestamp=datetime.now()
                            ))
                            logger.info(f"✅ {service_name}: доступен")
                        else:
                            self.results.append(TestResult(
                                test_name=f"service_availability_{service_name}",
                                status="error",
                                score=0.0,
                                details={"url": url, "status_code": response.status},
                                duration=0.1,
                                timestamp=datetime.now()
                            ))
                            logger.error(f"❌ {service_name}: недоступен (код {response.status})")
            except Exception as e:
                self.results.append(TestResult(
                    test_name=f"service_availability_{service_name}",
                    status="error",
                    score=0.0,
                    details={"url": url, "error": str(e)},
                    duration=0.1,
                    timestamp=datetime.now()
                ))
                logger.error(f"❌ {service_name}: ошибка подключения - {e}")
    
    async def test_domain_indexing(self) -> None:
        """Тест индексирования домена"""
        logger.info(f"🌐 Тест индексирования домена {self.domain}...")
        
        start_time = time.time()
        
        try:
            # Запуск индексирования через reLink API
            indexing_payload = {
                "domain": self.domain,
                "max_pages": 50,
                "depth": 3,
                "include_assets": True,
                "crawl_delay": 1
            }
            
            async with aiohttp.ClientSession() as session:
                # Запуск индексирования
                async with session.post(
                    f"{self.base_urls['relink']}/api/index-domain",
                    json=indexing_payload,
                    timeout=300
                ) as response:
                    if response.status == 200:
                        indexing_result = await response.json()
                        self.indexing_data = indexing_result
                        
                        # Анализ результатов индексирования
                        pages_indexed = indexing_result.get('pages_indexed', 0)
                        links_found = indexing_result.get('links_found', 0)
                        errors = indexing_result.get('errors', [])
                        
                        score = min(100.0, (pages_indexed / 10) * 100)  # Базовый score
                        if errors:
                            score *= 0.8  # Штраф за ошибки
                        
                        self.results.append(TestResult(
                            test_name="domain_indexing",
                            status="success" if pages_indexed > 0 else "error",
                            score=score,
                            details={
                                "pages_indexed": pages_indexed,
                                "links_found": links_found,
                                "errors": errors,
                                "domain": self.domain
                            },
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        
                        logger.info(f"✅ Индексирование завершено: {pages_indexed} страниц, {links_found} ссылок")
                    else:
                        self.results.append(TestResult(
                            test_name="domain_indexing",
                            status="error",
                            score=0.0,
                            details={"status_code": response.status},
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        logger.error(f"❌ Ошибка индексирования: код {response.status}")
                        
        except Exception as e:
            self.results.append(TestResult(
                test_name="domain_indexing",
                status="error",
                score=0.0,
                details={"error": str(e)},
                duration=time.time() - start_time,
                timestamp=datetime.now()
            ))
            logger.error(f"❌ Ошибка индексирования: {e}")
    
    async def test_chromadb_integration(self) -> None:
        """Тест интеграции с ChromaDB"""
        logger.info("🗄️ Тест интеграции с ChromaDB...")
        
        start_time = time.time()
        
        try:
            # Проверка подключения к ChromaDB
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_urls['chromadb']}/api/v2/heartbeat") as response:
                    if response.status == 200:
                        # Проверка наличия данных в базе
                        async with session.get(f"{self.base_urls['chromadb']}/api/v2/collections") as collections_response:
                            if collections_response.status == 200:
                                collections = await collections_response.json()
                                
                                # Проверка наличия коллекции для нашего домена
                                domain_collection = None
                                for collection in collections.get('collections', []):
                                    if self.domain in collection.get('name', ''):
                                        domain_collection = collection
                                        break
                                
                                if domain_collection:
                                    # Проверка количества документов
                                    collection_id = domain_collection['id']
                                    async with session.get(
                                        f"{self.base_urls['chromadb']}/api/v2/collections/{collection_id}/count"
                                    ) as count_response:
                                        if count_response.status == 200:
                                            count_data = await count_response.json()
                                            doc_count = count_data.get('count', 0)
                                            
                                            score = min(100.0, (doc_count / 10) * 100)
                                            
                                            self.results.append(TestResult(
                                                test_name="chromadb_integration",
                                                status="success",
                                                score=score,
                                                details={
                                                    "collection_found": True,
                                                    "documents_count": doc_count,
                                                    "collection_name": domain_collection['name']
                                                },
                                                duration=time.time() - start_time,
                                                timestamp=datetime.now()
                                            ))
                                            
                                            logger.info(f"✅ ChromaDB: найдено {doc_count} документов")
                                        else:
                                            self.results.append(TestResult(
                                                test_name="chromadb_integration",
                                                status="warning",
                                                score=50.0,
                                                details={"error": "Не удалось получить количество документов"},
                                                duration=time.time() - start_time,
                                                timestamp=datetime.now()
                                            ))
                                else:
                                    self.results.append(TestResult(
                                        test_name="chromadb_integration",
                                        status="error",
                                        score=0.0,
                                        details={"error": f"Коллекция для домена {self.domain} не найдена"},
                                        duration=time.time() - start_time,
                                        timestamp=datetime.now()
                                    ))
                                    logger.error(f"❌ Коллекция для домена {self.domain} не найдена")
                            else:
                                self.results.append(TestResult(
                                    test_name="chromadb_integration",
                                    status="error",
                                    score=0.0,
                                    details={"error": "Не удалось получить список коллекций"},
                                    duration=time.time() - start_time,
                                    timestamp=datetime.now()
                                ))
                    else:
                        self.results.append(TestResult(
                            test_name="chromadb_integration",
                            status="error",
                            score=0.0,
                            details={"error": "ChromaDB недоступен"},
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        
        except Exception as e:
            self.results.append(TestResult(
                test_name="chromadb_integration",
                status="error",
                score=0.0,
                details={"error": str(e)},
                duration=time.time() - start_time,
                timestamp=datetime.now()
            ))
            logger.error(f"❌ Ошибка интеграции с ChromaDB: {e}")
    
    async def test_llm_integration(self) -> None:
        """Тест интеграции с LLM"""
        logger.info("🧠 Тест интеграции с LLM...")
        
        start_time = time.time()
        
        try:
            # Проверка доступности Ollama
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_urls['ollama']}/api/tags") as response:
                    if response.status == 200:
                        models = await response.json()
                        
                        # Проверка наличия нужных моделей
                        available_models = [model['name'] for model in models.get('models', [])]
                        required_models = ['llama3.1:8b', 'qwen2.5:7b']  # Примеры моделей
                        
                        found_models = [model for model in required_models if any(model in available_model for available_model in available_models)]
                        
                        score = (len(found_models) / len(required_models)) * 100
                        
                        self.results.append(TestResult(
                            test_name="llm_integration",
                            status="success" if found_models else "warning",
                            score=score,
                            details={
                                "available_models": available_models,
                                "found_models": found_models,
                                "required_models": required_models
                            },
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        
                        logger.info(f"✅ LLM: найдено {len(found_models)} из {len(required_models)} моделей")
                    else:
                        self.results.append(TestResult(
                            test_name="llm_integration",
                            status="error",
                            score=0.0,
                            details={"error": "Ollama недоступен"},
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        
        except Exception as e:
            self.results.append(TestResult(
                test_name="llm_integration",
                status="error",
                score=0.0,
                details={"error": str(e)},
                duration=time.time() - start_time,
                timestamp=datetime.now()
            ))
            logger.error(f"❌ Ошибка интеграции с LLM: {e}")
    
    async def test_seo_recommendations(self) -> None:
        """Тест генерации SEO-рекомендаций"""
        logger.info("📊 Тест генерации SEO-рекомендаций...")
        
        start_time = time.time()
        
        try:
            # Запрос SEO-рекомендаций через LLM API
            seo_payload = {
                "domain": self.domain,
                "analysis_type": "comprehensive",
                "include_technical": True,
                "include_content": True,
                "include_structure": True,
                "include_performance": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['llm_tuning']}/api/seo-analysis",
                    json=seo_payload,
                    timeout=120
                ) as response:
                    if response.status == 200:
                        seo_result = await response.json()
                        
                        # Анализ качества рекомендаций
                        recommendations = seo_result.get('recommendations', [])
                        self.seo_recommendations = []
                        
                        for rec in recommendations:
                            self.seo_recommendations.append(SEORecommendation(
                                type=rec.get('type', 'unknown'),
                                priority=rec.get('priority', 'medium'),
                                description=rec.get('description', ''),
                                impact_score=rec.get('impact_score', 0.0),
                                implementation_difficulty=rec.get('difficulty', 'medium'),
                                estimated_improvement=rec.get('improvement', 'unknown')
                            ))
                        
                        # Оценка качества рекомендаций
                        total_recommendations = len(self.seo_recommendations)
                        high_priority_count = len([r for r in self.seo_recommendations if r.priority == 'high'])
                        avg_impact_score = sum(r.impact_score for r in self.seo_recommendations) / max(total_recommendations, 1)
                        
                        # Расчет общего score
                        score = min(100.0, (
                            (total_recommendations / 10) * 30 +  # Количество рекомендаций
                            (high_priority_count / max(total_recommendations, 1)) * 40 +  # Качество приоритетов
                            (avg_impact_score / 100) * 30  # Средний impact score
                        ))
                        
                        self.results.append(TestResult(
                            test_name="seo_recommendations",
                            status="success" if total_recommendations > 0 else "warning",
                            score=score,
                            details={
                                "total_recommendations": total_recommendations,
                                "high_priority_count": high_priority_count,
                                "avg_impact_score": avg_impact_score,
                                "recommendations_by_type": self._group_recommendations_by_type()
                            },
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        
                        logger.info(f"✅ SEO-рекомендации: {total_recommendations} рекомендаций, {high_priority_count} высокого приоритета")
                    else:
                        self.results.append(TestResult(
                            test_name="seo_recommendations",
                            status="error",
                            score=0.0,
                            details={"status_code": response.status},
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        logger.error(f"❌ Ошибка генерации SEO-рекомендаций: код {response.status}")
                        
        except Exception as e:
            self.results.append(TestResult(
                test_name="seo_recommendations",
                status="error",
                score=0.0,
                details={"error": str(e)},
                duration=time.time() - start_time,
                timestamp=datetime.now()
            ))
            logger.error(f"❌ Ошибка генерации SEO-рекомендаций: {e}")
    
    async def test_deep_analysis(self) -> None:
        """Тест углубленного анализа"""
        logger.info("🔍 Тест углубленного анализа...")
        
        start_time = time.time()
        
        try:
            # Запрос углубленного анализа конкретных страниц
            deep_analysis_payload = {
                "domain": self.domain,
                "analysis_type": "deep",
                "target_pages": ["/", "/about", "/services"],  # Примеры страниц
                "analysis_depth": "comprehensive",
                "include_competitor_analysis": True,
                "include_trend_analysis": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_urls['llm_tuning']}/api/deep-analysis",
                    json=deep_analysis_payload,
                    timeout=180
                ) as response:
                    if response.status == 200:
                        analysis_result = await response.json()
                        
                        # Анализ результатов
                        pages_analyzed = len(analysis_result.get('page_analyses', []))
                        insights_found = len(analysis_result.get('insights', []))
                        competitor_data = analysis_result.get('competitor_analysis', {})
                        
                        score = min(100.0, (
                            (pages_analyzed / 3) * 40 +  # Анализ страниц
                            (insights_found / 10) * 40 +  # Количество инсайтов
                            (len(competitor_data) / 5) * 20  # Данные конкурентов
                        ))
                        
                        self.results.append(TestResult(
                            test_name="deep_analysis",
                            status="success" if pages_analyzed > 0 else "warning",
                            score=score,
                            details={
                                "pages_analyzed": pages_analyzed,
                                "insights_found": insights_found,
                                "competitor_data_points": len(competitor_data),
                                "analysis_depth": "comprehensive"
                            },
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        
                        logger.info(f"✅ Углубленный анализ: {pages_analyzed} страниц, {insights_found} инсайтов")
                    else:
                        self.results.append(TestResult(
                            test_name="deep_analysis",
                            status="error",
                            score=0.0,
                            details={"status_code": response.status},
                            duration=time.time() - start_time,
                            timestamp=datetime.now()
                        ))
                        
        except Exception as e:
            self.results.append(TestResult(
                test_name="deep_analysis",
                status="error",
                score=0.0,
                details={"error": str(e)},
                duration=time.time() - start_time,
                timestamp=datetime.now()
            ))
            logger.error(f"❌ Ошибка углубленного анализа: {e}")
    
    async def test_performance(self) -> None:
        """Тест производительности системы"""
        logger.info("⚡ Тест производительности...")
        
        start_time = time.time()
        
        try:
            # Тест времени отклика API
            performance_metrics = {}
            
            async with aiohttp.ClientSession() as session:
                # Тест ChromaDB
                chroma_start = time.time()
                async with session.get(f"{self.base_urls['chromadb']}/api/v2/heartbeat") as response:
                    chroma_time = time.time() - chroma_start
                    performance_metrics['chromadb_response_time'] = chroma_time
                
                # Тест LLM
                llm_start = time.time()
                async with session.get(f"{self.base_urls['ollama']}/api/tags") as response:
                    llm_time = time.time() - llm_start
                    performance_metrics['llm_response_time'] = llm_time
                
                # Тест Router
                router_start = time.time()
                async with session.get(f"{self.base_urls['router']}/health") as response:
                    router_time = time.time() - router_start
                    performance_metrics['router_response_time'] = router_time
            
            # Оценка производительности
            avg_response_time = sum(performance_metrics.values()) / len(performance_metrics)
            
            # Score на основе времени отклика (чем быстрее, тем лучше)
            if avg_response_time < 0.5:
                score = 100.0
            elif avg_response_time < 1.0:
                score = 80.0
            elif avg_response_time < 2.0:
                score = 60.0
            else:
                score = max(0.0, 100.0 - (avg_response_time - 2.0) * 20)
            
            self.results.append(TestResult(
                test_name="performance",
                status="success" if avg_response_time < 2.0 else "warning",
                score=score,
                details=performance_metrics,
                duration=time.time() - start_time,
                timestamp=datetime.now()
            ))
            
            logger.info(f"✅ Производительность: среднее время отклика {avg_response_time:.3f}с")
            
        except Exception as e:
            self.results.append(TestResult(
                test_name="performance",
                status="error",
                score=0.0,
                details={"error": str(e)},
                duration=time.time() - start_time,
                timestamp=datetime.now()
            ))
            logger.error(f"❌ Ошибка теста производительности: {e}")
    
    def _group_recommendations_by_type(self) -> Dict[str, int]:
        """Группировка рекомендаций по типу"""
        grouped = {}
        for rec in self.seo_recommendations:
            grouped[rec.type] = grouped.get(rec.type, 0) + 1
        return grouped
    
    def generate_final_report(self, total_duration: float) -> Dict[str, Any]:
        """Генерация итогового отчета"""
        
        # Расчет общих метрик
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.status == "success"])
        error_tests = len([r for r in self.results if r.status == "error"])
        warning_tests = len([r for r in self.results if r.status == "warning"])
        
        avg_score = sum(r.score for r in self.results) / max(total_tests, 1)
        
        # Определение общего статуса
        if error_tests == 0 and warning_tests == 0:
            overall_status = "excellent"
        elif error_tests == 0:
            overall_status = "good"
        elif error_tests < total_tests / 2:
            overall_status = "fair"
        else:
            overall_status = "poor"
        
        # Детальный анализ по категориям
        category_analysis = {}
        for result in self.results:
            category = result.test_name.split('_')[0]
            if category not in category_analysis:
                category_analysis[category] = {
                    'tests': [],
                    'avg_score': 0.0,
                    'status': 'unknown'
                }
            category_analysis[category]['tests'].append(result)
        
        # Расчет средних scores по категориям
        for category, data in category_analysis.items():
            if data['tests']:
                data['avg_score'] = sum(t.score for t in data['tests']) / len(data['tests'])
                if data['avg_score'] >= 80:
                    data['status'] = 'excellent'
                elif data['avg_score'] >= 60:
                    data['status'] = 'good'
                elif data['avg_score'] >= 40:
                    data['status'] = 'fair'
                else:
                    data['status'] = 'poor'
        
        # Анализ SEO-рекомендаций
        seo_analysis = {
            'total_recommendations': len(self.seo_recommendations),
            'by_priority': {
                'high': len([r for r in self.seo_recommendations if r.priority == 'high']),
                'medium': len([r for r in self.seo_recommendations if r.priority == 'medium']),
                'low': len([r for r in self.seo_recommendations if r.priority == 'low'])
            },
            'by_type': self._group_recommendations_by_type(),
            'avg_impact_score': sum(r.impact_score for r in self.seo_recommendations) / max(len(self.seo_recommendations), 1)
        }
        
        report = {
            'test_info': {
                'domain': self.domain,
                'timestamp': datetime.now().isoformat(),
                'total_duration': total_duration,
                'overall_status': overall_status,
                'overall_score': avg_score
            },
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'error_tests': error_tests,
                'warning_tests': warning_tests,
                'success_rate': (successful_tests / total_tests) * 100 if total_tests > 0 else 0
            },
            'category_analysis': category_analysis,
            'seo_analysis': seo_analysis,
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'status': r.status,
                    'score': r.score,
                    'duration': r.duration,
                    'details': r.details
                }
                for r in self.results
            ],
            'recommendations': [
                {
                    'type': r.type,
                    'priority': r.priority,
                    'description': r.description,
                    'impact_score': r.impact_score,
                    'implementation_difficulty': r.implementation_difficulty,
                    'estimated_improvement': r.estimated_improvement
                }
                for r in self.seo_recommendations
            ]
        }
        
        return report

async def main():
    """Главная функция"""
    # Создание и запуск теста
    tester = ComprehensiveE2ETest("dagorod.ru")
    
    try:
        report = await tester.run_full_test_suite()
        
        # Сохранение отчета
        report_file = f"e2e_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # Вывод итогового результата
        print("\n" + "="*80)
        print("🎯 ИТОГОВЫЙ ОТЧЕТ E2E ТЕСТА")
        print("="*80)
        print(f"Домен: {report['test_info']['domain']}")
        print(f"Общий статус: {report['test_info']['overall_status'].upper()}")
        print(f"Общий score: {report['test_info']['overall_score']:.1f}/100")
        print(f"Время выполнения: {report['test_info']['total_duration']:.2f} секунд")
        print(f"Успешных тестов: {report['test_summary']['successful_tests']}/{report['test_summary']['total_tests']}")
        print(f"SEO-рекомендаций: {report['seo_analysis']['total_recommendations']}")
        print(f"Отчет сохранен в: {report_file}")
        print("="*80)
        
        # Детальный анализ по категориям
        print("\n📊 АНАЛИЗ ПО КАТЕГОРИЯМ:")
        for category, data in report['category_analysis'].items():
            print(f"  {category.upper()}: {data['status'].upper()} ({data['avg_score']:.1f}/100)")
        
        # Топ SEO-рекомендаций
        if report['recommendations']:
            print(f"\n🔝 ТОП SEO-РЕКОМЕНДАЦИИ:")
            high_priority = [r for r in report['recommendations'] if r['priority'] == 'high']
            for i, rec in enumerate(high_priority[:5], 1):
                print(f"  {i}. [{rec['type'].upper()}] {rec['description'][:100]}...")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в тесте: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 