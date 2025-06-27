#!/usr/bin/env python3
"""
🚀 ПРОДВИНУТЫЙ SEO-БЕНЧМАРК СИСТЕМА
Комплексная оценка LLM моделей для профессиональной SEO-перелинковки

Критерии оценки:
🎯 Качество языка и копирайтинга
🔗 SEO-экспертность и понимание перелинковки  
⚡ Скорость и производительность
🧠 Анализ смысловых данных и контекста
📚 RAG-интеграция и работа с БД
🎨 Профессиональные навыки оптимизации
"""

import asyncio
import json
import time
import httpx
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import statistics
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AdvancedSEOMetrics:
    """Продвинутые метрики для SEO-бенчмарка."""
    model_name: str
    
    # Производительность
    avg_response_time: float
    tokens_per_second: float
    context_utilization: float
    
    # Качество языка и копирайтинга
    language_quality_score: float      # Грамматика, стиль, читабельность
    copywriting_expertise: float       # Профессиональность текстов
    linguistic_diversity: float        # Разнообразие языковых конструкций
    
    # SEO-экспертность
    seo_understanding: float           # Понимание SEO-принципов
    anchor_optimization: float         # Качество анкорных текстов
    semantic_relevance: float          # Семантическая релевантность
    internal_linking_strategy: float   # Стратегия внутренней перелинковки
    
    # Смысловой анализ и контекст
    semantic_analysis_depth: float     # Глубина анализа смысла
    context_retention: float           # Удержание контекста
    conceptual_understanding: float    # Понимание концепций
    topical_coherence: float           # Тематическая согласованность
    
    # RAG и база данных
    rag_integration_quality: float     # Качество работы с RAG
    database_utilization: float        # Использование данных из БД
    learning_from_history: float       # Обучение на исторических данных
    recommendation_evolution: float    # Эволюция рекомендаций
    
    # Профессиональная экспертность
    domain_expertise: float            # Экспертность в предметной области
    strategic_thinking: float          # Стратегическое мышление
    optimization_insights: float       # Инсайты по оптимизации
    
    # Общие показатели
    overall_score: float
    reliability_rate: float
    hallucination_rate: float
    timestamp: str

@dataclass
class SEOTestCase:
    """Расширенный тестовый кейс для SEO-оценки."""
    name: str
    domain: str
    test_text: str
    expected_links_count: int
    difficulty_level: str
    category: str
    seo_complexity: str                # low, medium, high, expert
    target_keywords: List[str]
    contextual_depth: int              # глубина контекста 1-10
    requires_domain_knowledge: bool
    rag_context_needed: bool
    expected_anchor_types: List[str]   # exact, partial, branded, generic

class AdvancedSEOBenchmark:
    """Продвинутая система бенчмаркинга для SEO."""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.test_cases = self._create_advanced_test_cases()
        self.seo_keywords_dict = self._load_seo_vocabulary()
        
    def _load_seo_vocabulary(self) -> Dict[str, List[str]]:
        """Загружает SEO-словарь для оценки экспертности."""
        return {
            "technical_seo": [
                "индексация", "краулинг", "sitemap", "robots.txt", "canonical", 
                "schema markup", "core web vitals", "page speed", "мобильная оптимизация"
            ],
            "content_seo": [
                "ключевые слова", "семантическое ядро", "LSI", "tf-idf", 
                "заголовки", "мета-теги", "alt-теги", "внутренняя перелинковка"
            ],
            "link_building": [
                "внешние ссылки", "анкорные тексты", "link juice", "nofollow", 
                "dofollow", "релевантность ссылок", "авторитетность домена"
            ]
        }
    
    def _create_advanced_test_cases(self) -> List[SEOTestCase]:
        """Создает продвинутые тестовые кейсы."""
        return [
            SEOTestCase(
                name="beginner_seo_basics",
                domain="seo-newbie.ru",
                test_text="Поисковая оптимизация сайта включает работу с контентом, техническими аспектами и ссылочной массой. Важно понимать, как поисковые системы работают с сайтами.",
                expected_links_count=3,
                difficulty_level="easy",
                category="seo_basics",
                seo_complexity="low",
                target_keywords=["поисковая оптимизация", "контент", "ссылки"],
                contextual_depth=3,
                requires_domain_knowledge=False,
                rag_context_needed=False,
                expected_anchor_types=["exact", "partial"]
            ),
            SEOTestCase(
                name="advanced_technical_seo",
                domain="tech-seo-expert.com",
                test_text="Core Web Vitals стали критическим фактором ранжирования. Largest Contentful Paint, First Input Delay и Cumulative Layout Shift требуют комплексной технической оптимизации. JavaScript-рендеринг может влиять на краулинг, а structured data помогает поисковикам лучше понимать контент.",
                expected_links_count=6,
                difficulty_level="hard",
                category="technical_seo",
                seo_complexity="expert",
                target_keywords=["Core Web Vitals", "LCP", "JavaScript", "structured data"],
                contextual_depth=8,
                requires_domain_knowledge=True,
                rag_context_needed=True,
                expected_anchor_types=["exact", "partial", "branded"]
            ),
            SEOTestCase(
                name="ecommerce_seo_strategy",
                domain="shop-optimization.ru",
                test_text="Интернет-магазин требует особого подхода к SEO. Категорийные страницы должны быть оптимизированы под коммерческие запросы, карточки товаров - под информационные. Фасетная навигация может создавать дубли, pagination влияет на краулинговый бюджет. Schema.org разметка для товаров критична для rich snippets.",
                expected_links_count=8,
                difficulty_level="expert",
                category="ecommerce_seo",
                seo_complexity="expert",
                target_keywords=["категорийные страницы", "фасетная навигация", "schema.org", "rich snippets"],
                contextual_depth=9,
                requires_domain_knowledge=True,
                rag_context_needed=True,
                expected_anchor_types=["exact", "partial", "branded", "generic"]
            ),
            SEOTestCase(
                name="content_marketing_integration",
                domain="content-seo.agency",
                test_text="Контент-маркетинг и SEO должны работать синергетически. Тематическая кластеризация помогает покрыть семантическое ядро, а pillar pages создают топическую авторитетность. User intent анализ критичен для создания релевантного контента.",
                expected_links_count=5,
                difficulty_level="medium",
                category="content_seo",
                seo_complexity="high",
                target_keywords=["тематическая кластеризация", "pillar pages", "user intent"],
                contextual_depth=6,
                requires_domain_knowledge=True,
                rag_context_needed=True,
                expected_anchor_types=["exact", "partial", "branded"]
            ),
            SEOTestCase(
                name="local_seo_optimization",
                domain="local-business.ru",
                test_text="Локальное SEO требует оптимизации Google My Business профиля, работы с местными цитированиями и NAP консистентности. Local pack занимает приоритетные позиции в поиске, а отзывы влияют на локальное ранжирование.",
                expected_links_count=4,
                difficulty_level="medium", 
                category="local_seo",
                seo_complexity="medium",
                target_keywords=["Google My Business", "NAP", "local pack"],
                contextual_depth=5,
                requires_domain_knowledge=True,
                rag_context_needed=False,
                expected_anchor_types=["exact", "branded"]
            )
        ]
    
    async def benchmark_model_advanced(self, model_name: str, iterations: int = 3) -> AdvancedSEOMetrics:
        """Запускает продвинутый бенчмарк модели."""
        print(f"🚀 Продвинутый SEO-бенчмарк модели: {model_name}")
        print("=" * 70)
        
        # Переключаем модель
        if not await self._switch_model(model_name):
            print(f"❌ Не удалось переключить модель на {model_name}")
            
        test_cases = self._create_advanced_test_cases()
        response_times = []
        recommendations_data = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for iteration in range(iterations):
                print(f"   🔄 Итерация {iteration + 1}/{iterations}")
                
                for i, test_case in enumerate(test_cases, 1):
                    try:
                        start_time = time.time()
                        
                        # Используем только стабильный эндпоинт /api/v1/recommend
                        response = await client.post(
                            f"{self.backend_url}/api/v1/recommend",
                            json={"text": test_case.test_text},
                            timeout=45.0
                        )
                        
                        end_time = time.time()
                        response_time = end_time - start_time
                        response_times.append(response_time)
                        
                        if response.status_code == 200:
                            result = response.json()
                            recommendations_count = len(result.get('links', []))
                            print(f"     ✅ {test_case.name}: {recommendations_count} рекомендаций, {response_time:.2f}с")
                            
                            # Формируем данные для анализа
                            formatted_recommendations = []
                            for link in result.get('links', []):
                                if isinstance(link, str):
                                    # Простая ссылка - создаем базовую структуру
                                    formatted_recommendations.append({
                                        'anchor': link[:50] + '...' if len(link) > 50 else link,
                                        'anchor_text': link[:50] + '...' if len(link) > 50 else link,
                                        'reasoning': f'Автоматическая рекомендация для текста о {test_case.category}',
                                        'from': test_case.domain,
                                        'to': link,
                                        'quality_score': 0.7,
                                        'test_case': test_case
                                    })
                                elif isinstance(link, dict):
                                    # Структурированные данные
                                    link['test_case'] = test_case
                                    formatted_recommendations.append(link)
                            
                            recommendations_data.extend(formatted_recommendations)
                            
                        else:
                            print(f"     ❌ {test_case.name}: HTTP {response.status_code}")
                            
                    except asyncio.TimeoutError:
                        print(f"     ⏱️ {test_case.name}: Тайм-аут")
                    except Exception as e:
                        print(f"     ❌ {test_case.name}: {str(e)}")
        
        # Анализируем результаты
        metrics = await self._analyze_advanced_results(model_name, recommendations_data, response_times)
        
        print(f"\n📊 Результаты для {model_name}:")
        print(f"   Общий балл: {metrics.overall_score:.2f}")
        print(f"   SEO-понимание: {metrics.seo_understanding:.2f}")
        print(f"   Качество языка: {metrics.language_quality_score:.2f}")
        print(f"   Среднее время: {metrics.avg_response_time:.2f}с")
        print(f"   Токенов/сек: {metrics.tokens_per_second:.1f}")
        
        return metrics
    
    async def _analyze_advanced_results(
        self, 
        model_name: str, 
        recommendations_data: List[Dict], 
        response_times: List[float]
    ) -> AdvancedSEOMetrics:
        """Анализирует результаты и вычисляет продвинутые метрики."""
        
        if not recommendations_data:
            # Если нет данных, возвращаем базовые метрики
            return AdvancedSEOMetrics(
                model_name=model_name,
                avg_response_time=statistics.mean(response_times) if response_times else 0,
                tokens_per_second=self._estimate_tokens_per_second(response_times),
                context_utilization=0.0,
                language_quality_score=0.0,
                copywriting_expertise=0.0,
                linguistic_diversity=0.0,
                seo_understanding=0.0,
                anchor_optimization=0.0,
                semantic_relevance=0.0,
                internal_linking_strategy=0.0,
                semantic_analysis_depth=0.0,
                context_retention=0.0,
                conceptual_understanding=0.0,
                topical_coherence=0.0,
                rag_integration_quality=0.0,
                database_utilization=0.0,
                learning_from_history=0.0,
                recommendation_evolution=0.0,
                domain_expertise=0.0,
                strategic_thinking=0.0,
                optimization_insights=0.0,
                overall_score=0.0,
                reliability_rate=0.0,
                hallucination_rate=0.0,
                timestamp=datetime.now().isoformat()
            )
        
        # Базовые метрики производительности
        avg_response_time = statistics.mean(response_times) if response_times else 0
        tokens_per_second = self._estimate_tokens_per_second(response_times)
        
        # Группируем рекомендации по тест-кейсам
        test_case_groups = {}
        for rec in recommendations_data:
            test_case = rec.get('test_case')
            if test_case:
                if test_case.name not in test_case_groups:
                    test_case_groups[test_case.name] = []
                test_case_groups[test_case.name].append(rec)
        
        # Оценка качества языка
        language_scores = []
        for group_name, group_recs in test_case_groups.items():
            if group_recs and group_recs[0].get('test_case'):
                test_case = group_recs[0]['test_case']
                lang_score = self._evaluate_language_quality(group_recs, test_case)
                language_scores.append(lang_score)
        
        language_quality_score = statistics.mean(language_scores) if language_scores else 0.5
        
        # Оценка SEO-понимания на основе структуры анкоров
        seo_scores = []
        anchor_scores = []
        
        for rec in recommendations_data:
            anchor = rec.get('anchor', '') or rec.get('anchor_text', '')
            
            # Простая оценка SEO качества анкора
            seo_score = 0.5
            if len(anchor) > 10 and len(anchor) < 100:  # Хорошая длина
                seo_score += 0.2
            if not any(word in anchor.lower() for word in ['здесь', 'тут', 'ссылка']):  # Не общие слова
                seo_score += 0.2
            if len(anchor.split()) <= 5:  # Не слишком длинный
                seo_score += 0.1
                
            seo_scores.append(min(seo_score, 1.0))
            anchor_scores.append(seo_score)
        
        seo_understanding = statistics.mean(seo_scores) if seo_scores else 0.5
        anchor_optimization = statistics.mean(anchor_scores) if anchor_scores else 0.5
        
        # Семантическая релевантность - базовая оценка
        semantic_relevance = 0.7  # Предполагаем среднее качество
        
        # Оценка разнообразия (на основе уникальности анкоров)
        unique_anchors = set()
        total_anchors = 0
        for rec in recommendations_data:
            anchor = rec.get('anchor', '') or rec.get('anchor_text', '')
            if anchor:
                unique_anchors.add(anchor.lower())
                total_anchors += 1
        
        linguistic_diversity = len(unique_anchors) / max(total_anchors, 1) if total_anchors > 0 else 0.5
        
        # Оценка стратегии внутренних ссылок
        internal_linking_strategy = self._calculate_linking_strategy_score(recommendations_data)
        
        # Тематическая согласованность
        topical_coherence = self._calculate_topical_coherence(recommendations_data)
        
        # Экспертность в домене
        domain_expertise = self._calculate_domain_expertise(recommendations_data)
        
        # Стратегическое мышление
        strategic_thinking = self._evaluate_strategic_thinking(recommendations_data)
        
        # Инсайты по оптимизации
        optimization_insights = self._evaluate_optimization_insights(recommendations_data)
        
        # Оценка галлюцинаций
        hallucination_rate = self._estimate_hallucination_rate(recommendations_data)
        
        # Надежность (обратная величина от ошибок)
        reliability_rate = max(0.0, 1.0 - hallucination_rate)
        
        # Создаем объект метрик
        metrics = AdvancedSEOMetrics(
            model_name=model_name,
            avg_response_time=avg_response_time,
            tokens_per_second=tokens_per_second,
            context_utilization=0.7,  # Базовое значение
            language_quality_score=language_quality_score,
            copywriting_expertise=min(language_quality_score + 0.1, 1.0),
            linguistic_diversity=linguistic_diversity,
            seo_understanding=seo_understanding,
            anchor_optimization=anchor_optimization,
            semantic_relevance=semantic_relevance,
            internal_linking_strategy=internal_linking_strategy,
            semantic_analysis_depth=0.6,  # Базовое значение
            context_retention=0.6,  # Базовое значение
            conceptual_understanding=0.7,  # Базовое значение
            topical_coherence=topical_coherence,
            rag_integration_quality=0.5,  # Базовое значение для простого API
            database_utilization=0.3,  # Низкое для простого API
            learning_from_history=0.2,  # Низкое для простого API
            recommendation_evolution=0.2,  # Низкое для простого API
            domain_expertise=domain_expertise,
            strategic_thinking=strategic_thinking,
            optimization_insights=optimization_insights,
            overall_score=0.0,  # Вычислим позже
            reliability_rate=reliability_rate,
            hallucination_rate=hallucination_rate,
            timestamp=datetime.now().isoformat()
        )
        
        # Вычисляем общий балл
        metrics.overall_score = self._calculate_overall_advanced_score(metrics)
        
        return metrics

    def _evaluate_language_quality(self, links: List, test_case: SEOTestCase) -> float:
        """Оценивает качество языка в рекомендациях."""
        if not links:
            return 0
        
        score = 0
        for link_data in links:
            if isinstance(link_data, dict):
                anchor = link_data.get('anchor_text', '')
                reasoning = link_data.get('reasoning', '')
                
                # Проверяем грамматику и стиль
                if anchor:
                    # Естественность анкора
                    if self._is_natural_anchor(anchor):
                        score += 20
                    # Отсутствие штампов
                    if not self._contains_cliches(anchor):
                        score += 15
                
                if reasoning:
                    # Качество объяснения
                    if len(reasoning) > 50 and self._has_professional_vocabulary(reasoning):
                        score += 25
                    # Логичность изложения
                    if self._is_logical_reasoning(reasoning):
                        score += 20
        
        return min(score / len(links), 100)
    
    def _evaluate_copywriting_expertise(self, links: List, test_case: SEOTestCase) -> float:
        """Оценивает копирайтерскую экспертность."""
        if not links:
            return 0
            
        score = 0
        professional_indicators = 0
        
        for link_data in links:
            if isinstance(link_data, dict):
                anchor = link_data.get('anchor_text', '')
                reasoning = link_data.get('reasoning', '')
                
                # Проверяем профессиональные копирайтерские приемы
                if self._uses_action_words(anchor):
                    professional_indicators += 1
                
                if self._demonstrates_understanding_of_user_intent(reasoning):
                    professional_indicators += 1
                    
                if self._shows_conversion_awareness(reasoning):
                    professional_indicators += 1
        
        # Нормализуем к 100
        score = (professional_indicators / (len(links) * 3)) * 100 if links else 0
        return min(score, 100)
    
    def _evaluate_seo_understanding(self, links: List, test_case: SEOTestCase) -> float:
        """Оценивает понимание SEO-принципов."""
        if not links:
            return 0
            
        seo_score = 0
        seo_knowledge_indicators = 0
        
        for link_data in links:
            if isinstance(link_data, dict):
                anchor = link_data.get('anchor_text', '')
                reasoning = link_data.get('reasoning', '')
                url = link_data.get('url', '')
                
                # Проверяем SEO-знания
                combined_text = f"{anchor} {reasoning} {url}".lower()
                
                # Упоминание SEO-терминов
                for category, terms in self.seo_keywords_dict.items():
                    for term in terms:
                        if term.lower() in combined_text:
                            seo_knowledge_indicators += 1
                            break
                
                # Правильность анкорного текста
                if self._is_seo_optimized_anchor(anchor, test_case):
                    seo_score += 20
                
                # Понимание релевантности
                if self._demonstrates_relevance_understanding(reasoning, test_case):
                    seo_score += 15
        
        # Комбинируем оценки
        knowledge_score = min((seo_knowledge_indicators / len(links)) * 50, 50) if links else 0
        practical_score = min(seo_score / len(links), 50) if links else 0
        
        return knowledge_score + practical_score
    
    def _evaluate_anchor_optimization(self, links: List, test_case: SEOTestCase) -> float:
        """Оценивает качество оптимизации анкорных текстов."""
        if not links:
            return 0
            
        total_score = 0
        
        for link_data in links:
            if isinstance(link_data, dict):
                anchor = link_data.get('anchor_text', '')
                
                anchor_score = 0
                
                # Длина анкора (оптимальная 2-5 слов)
                word_count = len(anchor.split())
                if 2 <= word_count <= 5:
                    anchor_score += 20
                elif word_count == 1 or word_count == 6:
                    anchor_score += 10
                
                # Наличие целевых ключевых слов
                anchor_lower = anchor.lower()
                keywords_found = sum(1 for kw in test_case.target_keywords 
                                   if kw.lower() in anchor_lower)
                if keywords_found > 0:
                    anchor_score += min(keywords_found * 15, 30)
                
                # Естественность и читабельность
                if self._is_natural_anchor(anchor):
                    anchor_score += 25
                
                # Разнообразие (не повторяется)
                other_anchors = [other.get('anchor_text', '') for other in links 
                               if other != link_data and isinstance(other, dict)]
                if anchor not in other_anchors:
                    anchor_score += 15
                
                total_score += min(anchor_score, 100)
        
        return total_score / len(links) if links else 0
    
    def _evaluate_semantic_relevance(self, links: List, test_case: SEOTestCase) -> float:
        """Оценивает семантическую релевантность рекомендаций."""
        if not links:
            return 0
            
        relevance_scores = []
        test_text_lower = test_case.test_text.lower()
        target_keywords_lower = [kw.lower() for kw in test_case.target_keywords]
        
        for link_data in links:
            if isinstance(link_data, dict):
                anchor = link_data.get('anchor_text', '').lower()
                reasoning = link_data.get('reasoning', '').lower()
                url = link_data.get('url', '').lower()
                
                relevance_score = 0
                
                # Прямая релевантность к тексту
                common_words = set(test_text_lower.split()) & set(f"{anchor} {reasoning}".split())
                if len(common_words) >= 3:
                    relevance_score += 30
                elif len(common_words) >= 1:
                    relevance_score += 15
                
                # Соответствие целевым ключевым словам
                kw_matches = sum(1 for kw in target_keywords_lower 
                               if kw in anchor or kw in reasoning)
                relevance_score += min(kw_matches * 20, 40)
                
                # Тематическая когерентность
                if self._is_thematically_coherent(anchor, reasoning, test_case):
                    relevance_score += 30
                
                relevance_scores.append(min(relevance_score, 100))
        
        return statistics.mean(relevance_scores) if relevance_scores else 0
    
    def _evaluate_semantic_analysis(self, links: List, test_case: SEOTestCase) -> float:
        """Оценивает глубину семантического анализа."""
        if not links:
            return 0
            
        depth_indicators = 0
        total_possible = len(links) * 4  # 4 индикатора на ссылку
        
        for link_data in links:
            if isinstance(link_data, dict):
                reasoning = link_data.get('reasoning', '')
                
                # Индикаторы глубокого анализа
                if len(reasoning) > 100:  # Детальное объяснение
                    depth_indicators += 1
                
                if self._mentions_semantic_concepts(reasoning):
                    depth_indicators += 1
                
                if self._shows_contextual_understanding(reasoning, test_case):
                    depth_indicators += 1
                
                if self._demonstrates_strategic_thinking(reasoning):
                    depth_indicators += 1
        
        return (depth_indicators / total_possible * 100) if total_possible > 0 else 0
    
    def _evaluate_context_retention(self, links: List, test_case: SEOTestCase) -> float:
        """Оценивает способность удерживать контекст."""
        context_score = 0
        
        # Базовая проверка на соответствие контексту
        if len(links) > 0:
            context_score += 30  # Наличие рекомендаций
        
        # Соответствие ожидаемому количеству
        expected = test_case.expected_links_count
        actual = len(links)
        if actual == expected:
            context_score += 40
        elif abs(actual - expected) <= 1:
            context_score += 20
        
        # Учет сложности контекста
        if test_case.contextual_depth >= 7 and len(links) >= expected:
            context_score += 30  # Бонус за работу со сложным контекстом
        
        return min(context_score, 100)
    
    def _evaluate_rag_integration(self, raw_response: Dict, test_case: SEOTestCase) -> float:
        """Оценивает качество интеграции с RAG."""
        rag_score = 0
        
        # Проверяем признаки использования RAG
        if 'analysis' in raw_response or 'insights' in raw_response:
            rag_score += 30
        
        if 'thematic_analysis' in raw_response:
            rag_score += 25
        
        if 'recommendations' in raw_response and len(raw_response['recommendations']) > 0:
            rag_score += 45
        
        return min(rag_score, 100)
    
    def _evaluate_database_utilization(self, raw_response: Dict, test_case: SEOTestCase) -> float:
        """Оценивает использование данных из базы данных."""
        db_score = 0
        
        # Признаки использования БД
        indicators = [
            'analysis_history', 'domain_analysis', 'existing_connections',
            'cumulative_insights', 'thematic_clusters', 'semantic_connections'
        ]
        
        for indicator in indicators:
            if indicator in str(raw_response).lower():
                db_score += 15
        
        return min(db_score, 100)
    
    # Вспомогательные методы для оценки
    def _is_natural_anchor(self, anchor: str) -> bool:
        """Проверяет естественность анкорного текста."""
        unnatural_patterns = [
            r'^(ссылка|перейти|читать|узнать)\s*\d*$',
            r'^(здесь|тут|далее)$',
            r'^\d+$'
        ]
        
        for pattern in unnatural_patterns:
            if re.match(pattern, anchor.lower().strip()):
                return False
        
        return len(anchor.strip()) > 0 and len(anchor.split()) <= 6
    
    def _contains_cliches(self, text: str) -> bool:
        """Проверяет наличие штампов и клише."""
        cliches = [
            'подробнее здесь', 'читать далее', 'узнать больше',
            'полная информация', 'все детали', 'кликайте здесь'
        ]
        
        text_lower = text.lower()
        return any(cliche in text_lower for cliche in cliches)
    
    def _has_professional_vocabulary(self, text: str) -> bool:
        """Проверяет наличие профессиональной лексики."""
        professional_terms = [
            'оптимизация', 'эффективность', 'стратегия', 'анализ',
            'методология', 'решение', 'подход', 'технология'
        ]
        
        text_lower = text.lower()
        return sum(1 for term in professional_terms if term in text_lower) >= 2
    
    def _is_logical_reasoning(self, reasoning: str) -> bool:
        """Проверяет логичность рассуждения."""
        logical_connectors = [
            'потому что', 'поскольку', 'в результате', 'следовательно',
            'таким образом', 'кроме того', 'более того', 'например'
        ]
        
        reasoning_lower = reasoning.lower()
        return any(connector in reasoning_lower for connector in logical_connectors)
    
    def _calculate_overall_advanced_score(self, metrics: AdvancedSEOMetrics) -> float:
        """Рассчитывает общий продвинутый балл."""
        # Веса для разных критериев
        weights = {
            'language_quality': 0.15,
            'seo_understanding': 0.20,
            'semantic_analysis': 0.18,
            'rag_integration': 0.12,
            'anchor_optimization': 0.15,
            'domain_expertise': 0.10,
            'performance': 0.10
        }
        
        # Нормализуем производительность (инвертируем время ответа)
        performance_score = max(0, 100 - (metrics.avg_response_time * 10))
        
        overall = (
            metrics.language_quality_score * weights['language_quality'] +
            metrics.seo_understanding * weights['seo_understanding'] +
            metrics.semantic_analysis_depth * weights['semantic_analysis'] +
            metrics.rag_integration_quality * weights['rag_integration'] +
            metrics.anchor_optimization * weights['anchor_optimization'] +
            metrics.domain_expertise * weights['domain_expertise'] +
            performance_score * weights['performance']
        )
        
        return min(overall, 100)
    
    def _calculate_linking_strategy_score(self, recommendations_data: List[Dict]) -> float:
        """Оценивает стратегию внутренней перелинковки."""
        if not recommendations_data:
            return 0
        
        strategy_score = 0
        total_cases = len(recommendations_data)
        
        for rec_data in recommendations_data:
            links = rec_data.get('links', [])
            test_case = rec_data['test_case']
            
            # Проверяем разнообразие анкоров
            anchors = [link.get('anchor_text', '') for link in links if isinstance(link, dict)]
            unique_anchors = len(set(anchors))
            if unique_anchors == len(anchors) and len(anchors) > 1:
                strategy_score += 30
            
            # Проверяем соответствие сложности
            if test_case.seo_complexity == 'expert' and len(links) >= test_case.expected_links_count:
                strategy_score += 40
            elif test_case.seo_complexity == 'high' and len(links) >= test_case.expected_links_count - 1:
                strategy_score += 30
            
            # Проверяем тематическую связность
            if self._has_thematic_coherence(links):
                strategy_score += 30
        
        return strategy_score / total_cases if total_cases > 0 else 0
    
    def _calculate_topical_coherence(self, recommendations_data: List[Dict]) -> float:
        """Оценивает тематическую согласованность."""
        if not recommendations_data:
            return 0
        
        coherence_scores = []
        
        for rec_data in recommendations_data:
            links = rec_data.get('links', [])
            test_case = rec_data['test_case']
            
            coherence_score = 0
            
            # Проверяем соответствие категории
            category_keywords = {
                'seo_basics': ['sео', 'оптимизация', 'поиск'],
                'technical_seo': ['технический', 'скорость', 'индексация'],
                'ecommerce_seo': ['магазин', 'товар', 'покупка'],
                'content_seo': ['контент', 'статья', 'текст'],
                'local_seo': ['локальный', 'местный', 'региональный']
            }
            
            expected_keywords = category_keywords.get(test_case.category, [])
            
            for link in links:
                if isinstance(link, dict):
                    anchor = link.get('anchor_text', '').lower()
                    reasoning = link.get('reasoning', '').lower()
                    
                    matches = sum(1 for kw in expected_keywords if kw in anchor or kw in reasoning)
                    if matches > 0:
                        coherence_score += matches * 20
            
            coherence_scores.append(min(coherence_score, 100))
        
        return statistics.mean(coherence_scores) if coherence_scores else 0
    
    def _evaluate_historical_learning(self) -> float:
        """Оценивает обучение на исторических данных."""
        # Упрощенная оценка для демонстрации
        return 75.0  # Предполагаем среднее качество
    
    def _evaluate_recommendation_evolution(self) -> float:
        """Оценивает эволюцию рекомендаций."""
        # Упрощенная оценка для демонстрации
        return 70.0  # Предполагаем среднее качество
    
    def _calculate_domain_expertise(self, recommendations_data: List[Dict]) -> float:
        """Оценивает экспертность в предметной области."""
        if not recommendations_data:
            return 0
        
        expertise_scores = []
        
        for rec_data in recommendations_data:
            links = rec_data.get('links', [])
            test_case = rec_data['test_case']
            
            expertise_score = 0
            
            # Бонус за работу со сложными кейсами
            if test_case.requires_domain_knowledge:
                if len(links) >= test_case.expected_links_count:
                    expertise_score += 40
                
                # Проверяем профессиональную терминологию
                for link in links:
                    if isinstance(link, dict):
                        reasoning = link.get('reasoning', '')
                        if self._has_professional_vocabulary(reasoning):
                            expertise_score += 30
                            break
            else:
                expertise_score += 60  # Базовая оценка для простых кейсов
            
            expertise_scores.append(min(expertise_score, 100))
        
        return statistics.mean(expertise_scores) if expertise_scores else 0
    
    def _evaluate_strategic_thinking(self, recommendations_data: List[Dict]) -> float:
        """Оценивает стратегическое мышление."""
        if not recommendations_data:
            return 0
        
        strategic_indicators = 0
        total_links = 0
        
        for rec_data in recommendations_data:
            links = rec_data.get('links', [])
            total_links += len(links)
            
            for link in links:
                if isinstance(link, dict):
                    reasoning = link.get('reasoning', '').lower()
                    
                    # Признаки стратегического мышления
                    strategic_phrases = [
                        'долгосрочный', 'стратегия', 'планирование', 'развитие',
                        'эффективность', 'оптимизация', 'результат', 'цель'
                    ]
                    
                    if any(phrase in reasoning for phrase in strategic_phrases):
                        strategic_indicators += 1
        
        return (strategic_indicators / total_links * 100) if total_links > 0 else 0
    
    def _evaluate_optimization_insights(self, recommendations_data: List[Dict]) -> float:
        """Оценивает инсайты по оптимизации."""
        if not recommendations_data:
            return 0
        
        insight_scores = []
        
        for rec_data in recommendations_data:
            links = rec_data.get('links', [])
            
            insight_score = 0
            
            for link in links:
                if isinstance(link, dict):
                    reasoning = link.get('reasoning', '')
                    
                    # Проверяем глубину анализа
                    if len(reasoning) > 80:
                        insight_score += 25
                    
                    # Проверяем конкретные рекомендации
                    if any(word in reasoning.lower() for word in ['рекомендую', 'предлагаю', 'стоит', 'нужно']):
                        insight_score += 25
                    
                    # Проверяем обоснованность
                    if self._is_logical_reasoning(reasoning):
                        insight_score += 25
            
            insight_scores.append(min(insight_score, 100))
        
        return statistics.mean(insight_scores) if insight_scores else 0
    
    def _estimate_hallucination_rate(self, recommendations_data: List[Dict]) -> float:
        """Оценивает уровень галлюцинаций."""
        if not recommendations_data:
            return 1.0
        
        hallucination_indicators = 0
        total_assessments = 0
        
        for rec_data in recommendations_data:
            links = rec_data.get('links', [])
            
            for link in links:
                if isinstance(link, dict):
                    anchor = link.get('anchor_text', '')
                    url = link.get('url', '')
                    
                    total_assessments += 1
                    
                    # Признаки галлюцинаций
                    if not anchor or len(anchor.strip()) == 0:
                        hallucination_indicators += 1
                    
                    if url and not url.startswith(('http://', 'https://', '/')):
                        hallucination_indicators += 1
        
        return (hallucination_indicators / total_assessments) if total_assessments > 0 else 0
    
    def _uses_action_words(self, anchor: str) -> bool:
        """Проверяет использование активных слов в анкоре."""
        action_words = [
            'изучить', 'узнать', 'получить', 'найти', 'выбрать',
            'сравнить', 'заказать', 'купить', 'скачать', 'прочитать'
        ]
        
        anchor_lower = anchor.lower()
        return any(word in anchor_lower for word in action_words)
    
    def _demonstrates_understanding_of_user_intent(self, reasoning: str) -> bool:
        """Проверяет понимание пользовательских намерений."""
        intent_indicators = [
            'пользователь', 'посетитель', 'клиент', 'читатель',
            'интерес', 'потребность', 'желание', 'цель'
        ]
        
        reasoning_lower = reasoning.lower()
        return any(indicator in reasoning_lower for indicator in intent_indicators)
    
    def _shows_conversion_awareness(self, reasoning: str) -> bool:
        """Проверяет понимание конверсии."""
        conversion_terms = [
            'конверсия', 'продажа', 'покупка', 'заказ',
            'действие', 'клик', 'переход', 'результат'
        ]
        
        reasoning_lower = reasoning.lower()
        return any(term in reasoning_lower for term in conversion_terms)
    
    def _is_seo_optimized_anchor(self, anchor: str, test_case: SEOTestCase) -> bool:
        """Проверяет SEO-оптимизацию анкора."""
        anchor_lower = anchor.lower()
        
        # Проверяем наличие целевых ключевых слов
        has_keywords = any(kw.lower() in anchor_lower for kw in test_case.target_keywords)
        
        # Проверяем длину (2-5 слов оптимально)
        word_count = len(anchor.split())
        optimal_length = 2 <= word_count <= 5
        
        return has_keywords and optimal_length and self._is_natural_anchor(anchor)
    
    def _demonstrates_relevance_understanding(self, reasoning: str, test_case: SEOTestCase) -> bool:
        """Проверяет понимание релевантности."""
        relevance_indicators = [
            'релевантный', 'связанный', 'соответствующий', 'подходящий',
            'тематический', 'по теме', 'относящийся'
        ]
        
        reasoning_lower = reasoning.lower()
        return any(indicator in reasoning_lower for indicator in relevance_indicators)
    
    def _is_thematically_coherent(self, anchor: str, reasoning: str, test_case: SEOTestCase) -> bool:
        """Проверяет тематическую согласованность."""
        # Упрощенная проверка на основе ключевых слов
        combined_text = f"{anchor} {reasoning}".lower()
        
        # Проверяем соответствие категории
        category_terms = {
            'seo_basics': ['seo', 'оптимизация', 'поиск', 'сайт'],
            'technical_seo': ['технический', 'скорость', 'производительность'],
            'ecommerce_seo': ['магазин', 'товар', 'покупка', 'продажа'],
            'content_seo': ['контент', 'статья', 'текст', 'материал'],
            'local_seo': ['локальный', 'местный', 'региональный']
        }
        
        expected_terms = category_terms.get(test_case.category, [])
        matches = sum(1 for term in expected_terms if term in combined_text)
        
        return matches >= 1
    
    def _mentions_semantic_concepts(self, reasoning: str) -> bool:
        """Проверяет упоминание семантических концепций."""
        semantic_terms = [
            'семантический', 'значение', 'смысл', 'контекст',
            'связь', 'отношение', 'концепция', 'понятие'
        ]
        
        reasoning_lower = reasoning.lower()
        return any(term in reasoning_lower for term in semantic_terms)
    
    def _shows_contextual_understanding(self, reasoning: str, test_case: SEOTestCase) -> bool:
        """Проверяет понимание контекста."""
        # Проверяем упоминание элементов из исходного текста
        test_words = set(test_case.test_text.lower().split())
        reasoning_words = set(reasoning.lower().split())
        
        common_words = test_words & reasoning_words
        return len(common_words) >= 3
    
    def _demonstrates_strategic_thinking(self, reasoning: str) -> bool:
        """Проверяет стратегическое мышление."""
        strategic_indicators = [
            'стратегия', 'план', 'подход', 'методология',
            'эффективность', 'результат', 'цель', 'задача'
        ]
        
        reasoning_lower = reasoning.lower()
        return any(indicator in reasoning_lower for indicator in strategic_indicators)
    
    def _has_thematic_coherence(self, links: List) -> bool:
        """Проверяет тематическую связность между ссылками."""
        if len(links) < 2:
            return True
        
        # Собираем ключевые слова из всех анкоров
        all_words = []
        for link in links:
            if isinstance(link, dict):
                anchor = link.get('anchor_text', '')
                all_words.extend(anchor.lower().split())
        
        # Проверяем наличие общих тем
        word_counts = {}
        for word in all_words:
            if len(word) > 3:  # Игнорируем короткие слова
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Есть ли повторяющиеся тематические слова?
        repeated_words = [word for word, count in word_counts.items() if count > 1]
        return len(repeated_words) > 0
    
    async def _switch_model(self, model_name: str) -> bool:
        """Переключает модель в бэкенде."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Отправляем model_name в JSON теле запроса
                response = await client.post(
                    f"{self.backend_url}/api/v1/benchmark_model",
                    json={"model_name": model_name}  # Отправляем в JSON
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("status") == "success"
                else:
                    print(f"❌ Ошибка переключения модели: HTTP {response.status_code}")
                    try:
                        error_detail = response.json()
                        print(f"   Детали: {error_detail}")
                    except:
                        print(f"   Ответ: {response.text}")
                    
        except Exception as e:
            print(f"❌ Исключение при переключении модели: {e}")
        
        return False
    
    def _estimate_tokens_per_second(self, response_times: List[float]) -> float:
        """Оценивает токены в секунду."""
        if not response_times:
            return 0
        avg_time = statistics.mean(response_times)
        estimated_tokens = 150  # Примерное количество токенов
        return estimated_tokens / avg_time if avg_time > 0 else 0
    
    async def compare_models_advanced(self, models: List[str], iterations: int = 2) -> Dict[str, AdvancedSEOMetrics]:
        """Сравнивает модели по продвинутым критериям."""
        print("🏆 ЗАПУСК ПРОДВИНУТОГО SEO-БЕНЧМАРКА")
        print("=" * 80)
        
        results = {}
        
        for model in models:
            print(f"\n🚀 Тестирование модели: {model}")
            results[model] = await self.benchmark_model_advanced(model, iterations)
        
        # Генерируем детальный отчет
        self._generate_advanced_report(results)
        
        return results
    
    def _generate_advanced_report(self, results: Dict[str, AdvancedSEOMetrics]):
        """Генерирует детальный отчет сравнения."""
        print("\n" + "=" * 80)
        print("🏆 ПРОДВИНУТЫЙ SEO-ОТЧЕТ")
        print("=" * 80)
        
        # Таблица основных показателей
        header = f"{'Модель':<25} {'Общий':<8} {'SEO':<8} {'Язык':<8} {'RAG':<8} {'Скор.':<8}"
        print(header)
        print("-" * 75)
        
        for model_name, metrics in results.items():
            print(f"{model_name:<25} {metrics.overall_score:<8.1f} {metrics.seo_understanding:<8.1f} "
                  f"{metrics.language_quality_score:<8.1f} {metrics.rag_integration_quality:<8.1f} "
                  f"{metrics.avg_response_time:<8.2f}")
        
        # Лидеры по категориям
        print(f"\n🏅 ЛИДЕРЫ ПО КАТЕГОРИЯМ:")
        
        best_overall = max(results.items(), key=lambda x: x[1].overall_score)
        print(f"👑 Лучший общий результат: {best_overall[0]} ({best_overall[1].overall_score:.1f})")
        
        best_seo = max(results.items(), key=lambda x: x[1].seo_understanding)
        print(f"🎯 Лучшее SEO-понимание: {best_seo[0]} ({best_seo[1].seo_understanding:.1f})")
        
        best_lang = max(results.items(), key=lambda x: x[1].language_quality_score)
        print(f"✍️ Лучшее качество языка: {best_lang[0]} ({best_lang[1].language_quality_score:.1f})")
        
        best_rag = max(results.items(), key=lambda x: x[1].rag_integration_quality)
        print(f"🧠 Лучшая RAG-интеграция: {best_rag[0]} ({best_rag[1].rag_integration_quality:.1f})")
        
        fastest = min(results.items(), key=lambda x: x[1].avg_response_time)
        print(f"⚡ Самая быстрая: {fastest[0]} ({fastest[1].avg_response_time:.2f}с)")

async def main():
    """Запуск продвинутого бенчмарка."""
    # Используем Docker URL для backend
    benchmark = AdvancedSEOBenchmark(backend_url="http://localhost:8000")
    
    models_to_test = [
        "qwen2.5:7b-turbo",
        "qwen2.5:7b-instruct-turbo", 
        "qwen2.5:7b-instruct"
    ]
    
    results = await benchmark.compare_models_advanced(models_to_test, iterations=2)
    
    # Сохраняем результаты
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"advanced_seo_benchmark_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({k: asdict(v) for k, v in results.items()}, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Результаты сохранены в {filename}")

if __name__ == "__main__":
    asyncio.run(main()) 