"""
LLM-агент для анализа контекста и генерации промптов
Интеллектуальный анализ контекста для улучшения рекомендаций
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from .types import LLMResponse
from .contextual_search import SearchResult
from ..llm_integration import LLMService


@dataclass
class ContextAnalysis:
    """Результат анализа контекста"""
    key_topics: List[str]
    potential_issues: List[str]
    improvement_opportunities: List[str]
    priority_directions: List[str]
    domain_specifics: Dict[str, Any]
    target_audience_insights: Dict[str, Any]
    technical_constraints: List[str]
    business_goals_alignment: Dict[str, float]
    content_gaps: List[str]
    competitive_advantages: List[str]
    risk_factors: List[str]
    implementation_roadmap: List[Dict[str, Any]]


@dataclass
class EnhancedPrompt:
    """Улучшенный промпт с контекстом"""
    base_prompt: str
    context_analysis: ContextAnalysis
    relevant_examples: List[Dict[str, Any]]
    specific_instructions: List[str]
    quality_criteria: Dict[str, Any]
    output_format: Dict[str, Any]
    constraints: List[str]


class ContextAnalysisAgent:
    """LLM-агент для анализа контекста и генерации промптов"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        
    async def analyze_context(self, context: Dict[str, Any]) -> ContextAnalysis:
        """Анализ контекста для улучшения рекомендаций"""
        
        analysis_prompt = self._build_analysis_prompt(context)
        
        try:
            response = await self.llm_service.generate_response(
                prompt=analysis_prompt,
                model="llama3.2:3b",  # Используем локальную модель для анализа
                temperature=0.3,
                max_tokens=2000
            )
            
            # Парсим ответ
            analysis_data = self._parse_analysis_response(response.content)
            
            # Создаем объект анализа
            context_analysis = ContextAnalysis(
                key_topics=analysis_data.get("key_topics", []),
                potential_issues=analysis_data.get("potential_issues", []),
                improvement_opportunities=analysis_data.get("improvement_opportunities", []),
                priority_directions=analysis_data.get("priority_directions", []),
                domain_specifics=analysis_data.get("domain_specifics", {}),
                target_audience_insights=analysis_data.get("target_audience_insights", {}),
                technical_constraints=analysis_data.get("technical_constraints", []),
                business_goals_alignment=analysis_data.get("business_goals_alignment", {}),
                content_gaps=analysis_data.get("content_gaps", []),
                competitive_advantages=analysis_data.get("competitive_advantages", []),
                risk_factors=analysis_data.get("risk_factors", []),
                implementation_roadmap=analysis_data.get("implementation_roadmap", [])
            )
            
            return context_analysis
            
        except Exception as e:
            print(f"Error in context analysis: {e}")
            # Возвращаем базовый анализ при ошибке
            return self._get_fallback_analysis(context)
    
    def _build_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Создание промпта для анализа контекста"""
        
        prompt = f"""
        Проанализируй следующий контекст и извлеки ключевую информацию для SEO-рекомендаций:
        
        ДОМЕН И КОНТЕНТ:
        - Домен: {context.get('domain', 'N/A')}
        - Тип контента: {context.get('content_type', 'N/A')}
        - Структура сайта: {context.get('site_structure', 'N/A')}
        
        МЕТРИКИ И ПРОИЗВОДИТЕЛЬНОСТЬ:
        - Текущие метрики: {json.dumps(context.get('metrics', {}), ensure_ascii=False, indent=2)}
        - Производительность: {context.get('performance', 'N/A')}
        
        ЦЕЛЕВАЯ АУДИТОРИЯ:
        - Аудитория: {context.get('target_audience', 'N/A')}
        - Демография: {context.get('demographics', 'N/A')}
        - Поведение: {context.get('user_behavior', 'N/A')}
        
        БИЗНЕС-ЦЕЛИ:
        - Цели: {', '.join(context.get('business_goals', []))}
        - KPI: {context.get('kpi', 'N/A')}
        - Конверсии: {context.get('conversion_goals', 'N/A')}
        
        ТЕХНИЧЕСКИЕ ОГРАНИЧЕНИЯ:
        - Ограничения: {', '.join(context.get('technical_constraints', []))}
        - Ресурсы: {context.get('available_resources', 'N/A')}
        - Временные рамки: {context.get('timeline', 'N/A')}
        
        КОНКУРЕНЦИЯ:
        - Конкуренты: {context.get('competitors', 'N/A')}
        - Рыночная позиция: {context.get('market_position', 'N/A')}
        
        ИСТОРИЧЕСКИЕ ДАННЫЕ:
        - Предыдущие результаты: {context.get('historical_performance', 'N/A')}
        - Успешные стратегии: {context.get('successful_strategies', 'N/A')}
        
        Извлеки следующую информацию и ответь в формате JSON:
        
        {{
            "key_topics": ["список ключевых тем и тематик"],
            "potential_issues": ["потенциальные проблемы SEO"],
            "improvement_opportunities": ["возможности для улучшения"],
            "priority_directions": ["приоритетные направления"],
            "domain_specifics": {{
                "industry": "отрасль",
                "content_style": "стиль контента",
                "user_intent": "намерения пользователей",
                "seasonal_factors": ["сезонные факторы"]
            }},
            "target_audience_insights": {{
                "pain_points": ["боли аудитории"],
                "motivations": ["мотивации"],
                "search_patterns": ["паттерны поиска"],
                "content_preferences": ["предпочтения в контенте"]
            }},
            "technical_constraints": ["технические ограничения"],
            "business_goals_alignment": {{
                "traffic_growth": 0.8,
                "conversion_optimization": 0.9,
                "brand_visibility": 0.7
            }},
            "content_gaps": ["пробелы в контенте"],
            "competitive_advantages": ["конкурентные преимущества"],
            "risk_factors": ["факторы риска"],
            "implementation_roadmap": [
                {{
                    "phase": "краткосрочные",
                    "priority": "high",
                    "effort": "low",
                    "impact": "medium",
                    "recommendations": ["конкретные рекомендации"]
                }}
            ]
        }}
        
        Будь конкретным и actionable. Фокусируйся на практических рекомендациях.
        """
        
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Парсинг ответа анализа контекста"""
        
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Пытаемся парсить весь ответ как JSON
                return json.loads(response)
        except json.JSONDecodeError:
            # Если не удалось распарсить JSON, извлекаем информацию по ключевым словам
            return self._extract_analysis_from_text(response)
    
    def _extract_analysis_from_text(self, text: str) -> Dict[str, Any]:
        """Извлечение анализа из текстового ответа"""
        
        analysis = {
            "key_topics": [],
            "potential_issues": [],
            "improvement_opportunities": [],
            "priority_directions": [],
            "domain_specifics": {},
            "target_audience_insights": {},
            "technical_constraints": [],
            "business_goals_alignment": {},
            "content_gaps": [],
            "competitive_advantages": [],
            "risk_factors": [],
            "implementation_roadmap": []
        }
        
        # Простое извлечение по ключевым словам
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Определяем секции
            if 'темы' in line.lower() or 'topics' in line.lower():
                current_section = 'key_topics'
            elif 'проблемы' in line.lower() or 'issues' in line.lower():
                current_section = 'potential_issues'
            elif 'возможности' in line.lower() or 'opportunities' in line.lower():
                current_section = 'improvement_opportunities'
            elif 'приоритеты' in line.lower() or 'priorities' in line.lower():
                current_section = 'priority_directions'
            elif line.startswith('-') or line.startswith('•'):
                # Добавляем элемент в текущую секцию
                item = line[1:].strip()
                if current_section and current_section in analysis:
                    if isinstance(analysis[current_section], list):
                        analysis[current_section].append(item)
        
        return analysis
    
    def _get_fallback_analysis(self, context: Dict[str, Any]) -> ContextAnalysis:
        """Базовый анализ при ошибке"""
        
        return ContextAnalysis(
            key_topics=[context.get('domain', 'general')],
            potential_issues=['basic SEO optimization needed'],
            improvement_opportunities=['content optimization', 'technical SEO'],
            priority_directions=['content quality', 'user experience'],
            domain_specifics={
                'industry': 'general',
                'content_style': 'informational',
                'user_intent': 'informational',
                'seasonal_factors': []
            },
            target_audience_insights={
                'pain_points': ['information finding'],
                'motivations': ['problem solving'],
                'search_patterns': ['question-based'],
                'content_preferences': ['detailed content']
            },
            technical_constraints=context.get('technical_constraints', []),
            business_goals_alignment={
                'traffic_growth': 0.5,
                'conversion_optimization': 0.5,
                'brand_visibility': 0.5
            },
            content_gaps=['comprehensive content needed'],
            competitive_advantages=['unique value proposition'],
            risk_factors=['competition', 'algorithm changes'],
            implementation_roadmap=[
                {
                    'phase': 'immediate',
                    'priority': 'high',
                    'effort': 'low',
                    'impact': 'medium',
                    'recommendations': ['basic SEO audit', 'content optimization']
                }
            ]
        )
    
    async def generate_enhanced_prompt(
        self,
        base_prompt: str,
        context_analysis: ContextAnalysis,
        relevant_docs: List[SearchResult],
        specific_requirements: Optional[Dict[str, Any]] = None
    ) -> EnhancedPrompt:
        """Генерация улучшенного промпта с контекстом"""
        
        # Форматируем релевантные примеры
        formatted_examples = self._format_relevant_docs(relevant_docs)
        
        # Создаем специфические инструкции
        specific_instructions = self._generate_specific_instructions(
            context_analysis, specific_requirements
        )
        
        # Определяем критерии качества
        quality_criteria = self._define_quality_criteria(context_analysis)
        
        # Определяем формат вывода
        output_format = self._define_output_format(specific_requirements)
        
        # Определяем ограничения
        constraints = self._define_constraints(context_analysis)
        
        # Создаем улучшенный промпт
        enhanced_prompt = EnhancedPrompt(
            base_prompt=base_prompt,
            context_analysis=context_analysis,
            relevant_examples=formatted_examples,
            specific_instructions=specific_instructions,
            quality_criteria=quality_criteria,
            output_format=output_format,
            constraints=constraints
        )
        
        return enhanced_prompt
    
    def _format_relevant_docs(self, relevant_docs: List[SearchResult]) -> List[Dict[str, Any]]:
        """Форматирование релевантных документов"""
        
        formatted_docs = []
        
        for doc in relevant_docs[:5]:  # Берем топ-5
            formatted_doc = {
                'content': doc.content[:500] + '...' if len(doc.content) > 500 else doc.content,
                'quality_score': doc.quality_score,
                'relevance_score': doc.relevance_score,
                'category': doc.metadata.get('category', 'general'),
                'tags': doc.metadata.get('tags', []),
                'implementation_difficulty': doc.metadata.get('implementation_difficulty', 'medium'),
                'estimated_impact': doc.metadata.get('estimated_impact', 'medium')
            }
            formatted_docs.append(formatted_doc)
        
        return formatted_docs
    
    def _generate_specific_instructions(
        self,
        context_analysis: ContextAnalysis,
        specific_requirements: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Генерация специфических инструкций"""
        
        instructions = [
            "Используй контекст анализа для персонализации рекомендаций",
            "Опирайся на релевантные примеры, но адаптируй под текущий случай",
            "Учитывай специфику домена и типа контента",
            "Предоставь конкретные, actionable рекомендации",
            "Объясни логику каждой рекомендации"
        ]
        
        # Добавляем специфические инструкции на основе анализа
        if context_analysis.priority_directions:
            instructions.append(f"Фокусируйся на приоритетных направлениях: {', '.join(context_analysis.priority_directions)}")
        
        if context_analysis.technical_constraints:
            instructions.append(f"Учитывай технические ограничения: {', '.join(context_analysis.technical_constraints)}")
        
        if context_analysis.target_audience_insights.get('pain_points'):
            pain_points = context_analysis.target_audience_insights['pain_points']
            instructions.append(f"Решай боли аудитории: {', '.join(pain_points)}")
        
        # Добавляем требования пользователя
        if specific_requirements:
            if specific_requirements.get('focus_on_conversion'):
                instructions.append("Приоритет конверсионной оптимизации")
            if specific_requirements.get('technical_focus'):
                instructions.append("Фокус на технических аспектах SEO")
            if specific_requirements.get('content_focus'):
                instructions.append("Фокус на контентной оптимизации")
        
        return instructions
    
    def _define_quality_criteria(self, context_analysis: ContextAnalysis) -> Dict[str, Any]:
        """Определение критериев качества"""
        
        return {
            'relevance': {
                'domain_alignment': 0.9,
                'audience_match': 0.8,
                'goal_alignment': 0.9
            },
            'actionability': {
                'specificity': 0.9,
                'implementation_clarity': 0.8,
                'measurability': 0.7
            },
            'uniqueness': {
                'originality': 0.7,
                'differentiation': 0.8,
                'competitive_edge': 0.6
            },
            'feasibility': {
                'resource_requirements': 0.8,
                'timeline_realism': 0.7,
                'technical_feasibility': 0.9
            }
        }
    
    def _define_output_format(self, specific_requirements: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Определение формата вывода"""
        
        base_format = {
            'structure': 'organized_sections',
            'include_explanations': True,
            'include_priorities': True,
            'include_metrics': True
        }
        
        if specific_requirements:
            if specific_requirements.get('detailed_format'):
                base_format['structure'] = 'detailed_analysis'
                base_format['include_implementation_steps'] = True
                base_format['include_cost_estimates'] = True
            
            if specific_requirements.get('simple_format'):
                base_format['structure'] = 'simple_list'
                base_format['include_explanations'] = False
        
        return base_format
    
    def _define_constraints(self, context_analysis: ContextAnalysis) -> List[str]:
        """Определение ограничений"""
        
        constraints = [
            "Рекомендации должны быть реалистичными и выполнимыми",
            "Учитывай доступные ресурсы и временные рамки",
            "Избегай дублирования существующих рекомендаций",
            "Фокусируйся на долгосрочной стратегии"
        ]
        
        # Добавляем специфические ограничения
        if context_analysis.technical_constraints:
            constraints.extend(context_analysis.technical_constraints)
        
        if context_analysis.risk_factors:
            constraints.append(f"Минимизируй риски: {', '.join(context_analysis.risk_factors)}")
        
        return constraints
    
    def build_final_prompt(self, enhanced_prompt: EnhancedPrompt) -> str:
        """Сборка финального промпта"""
        
        prompt_parts = [
            enhanced_prompt.base_prompt,
            "",
            "КОНТЕКСТ АНАЛИЗА:",
            json.dumps({
                'key_topics': enhanced_prompt.context_analysis.key_topics,
                'priority_directions': enhanced_prompt.context_analysis.priority_directions,
                'target_audience': enhanced_prompt.context_analysis.target_audience_insights,
                'domain_specifics': enhanced_prompt.context_analysis.domain_specifics
            }, indent=2, ensure_ascii=False),
            "",
            "РЕЛЕВАНТНЫЕ ПРИМЕРЫ:",
            json.dumps(enhanced_prompt.relevant_examples, indent=2, ensure_ascii=False),
            "",
            "СПЕЦИФИЧЕСКИЕ ИНСТРУКЦИИ:",
            "\n".join(f"- {instruction}" for instruction in enhanced_prompt.specific_instructions),
            "",
            "КРИТЕРИИ КАЧЕСТВА:",
            json.dumps(enhanced_prompt.quality_criteria, indent=2, ensure_ascii=False),
            "",
            "ФОРМАТ ВЫВОДА:",
            json.dumps(enhanced_prompt.output_format, indent=2, ensure_ascii=False),
            "",
            "ОГРАНИЧЕНИЯ:",
            "\n".join(f"- {constraint}" for constraint in enhanced_prompt.constraints)
        ]
        
        return "\n".join(prompt_parts)
    
    async def validate_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        context_analysis: ContextAnalysis
    ) -> Dict[str, Any]:
        """Валидация рекомендаций на соответствие контексту"""
        
        validation_results = {
            'overall_score': 0.0,
            'context_alignment': 0.0,
            'actionability': 0.0,
            'uniqueness': 0.0,
            'feasibility': 0.0,
            'issues': [],
            'suggestions': []
        }
        
        total_score = 0.0
        valid_recommendations = 0
        
        for rec in recommendations:
            rec_score = 0.0
            
            # Проверяем соответствие контексту
            context_alignment = self._check_context_alignment(rec, context_analysis)
            rec_score += context_alignment * 0.3
            
            # Проверяем actionable
            actionability = self._check_actionability(rec)
            rec_score += actionability * 0.25
            
            # Проверяем уникальность
            uniqueness = self._check_uniqueness(rec, recommendations)
            rec_score += uniqueness * 0.2
            
            # Проверяем выполнимость
            feasibility = self._check_feasibility(rec, context_analysis)
            rec_score += feasibility * 0.25
            
            total_score += rec_score
            valid_recommendations += 1
        
        if valid_recommendations > 0:
            validation_results['overall_score'] = total_score / valid_recommendations
        
        return validation_results
    
    def _check_context_alignment(
        self,
        recommendation: Dict[str, Any],
        context_analysis: ContextAnalysis
    ) -> float:
        """Проверка соответствия контексту"""
        
        score = 0.0
        
        # Проверяем соответствие приоритетным направлениям
        if any(direction in recommendation.get('content', '').lower() 
               for direction in context_analysis.priority_directions):
            score += 0.3
        
        # Проверяем соответствие целевой аудитории
        if any(pain_point in recommendation.get('content', '').lower() 
               for pain_point in context_analysis.target_audience_insights.get('pain_points', [])):
            score += 0.3
        
        # Проверяем соответствие доменной специфике
        if any(topic in recommendation.get('content', '').lower() 
               for topic in context_analysis.key_topics):
            score += 0.2
        
        # Проверяем соответствие бизнес-целям
        if any(goal in recommendation.get('content', '').lower() 
               for goal in context_analysis.business_goals_alignment.keys()):
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_actionability(self, recommendation: Dict[str, Any]) -> float:
        """Проверка actionable рекомендаций"""
        
        content = recommendation.get('content', '').lower()
        
        # Проверяем наличие конкретных действий
        action_words = ['добавить', 'изменить', 'улучшить', 'оптимизировать', 'настроить', 'исправить']
        action_count = sum(1 for word in action_words if word in content)
        
        # Проверяем наличие измеримых результатов
        metric_words = ['увеличить', 'уменьшить', 'улучшить', 'повысить', 'снизить']
        metric_count = sum(1 for word in metric_words if word in content)
        
        return min((action_count + metric_count) / 10, 1.0)
    
    def _check_uniqueness(
        self,
        recommendation: Dict[str, Any],
        all_recommendations: List[Dict[str, Any]]
    ) -> float:
        """Проверка уникальности рекомендации"""
        
        content = recommendation.get('content', '').lower()
        
        # Подсчитываем схожесть с другими рекомендациями
        similarity_count = 0
        for other_rec in all_recommendations:
            if other_rec != recommendation:
                other_content = other_rec.get('content', '').lower()
                # Простая проверка схожести по ключевым словам
                common_words = set(content.split()) & set(other_content.split())
                if len(common_words) > 5:  # Если много общих слов
                    similarity_count += 1
        
        # Чем меньше схожести, тем выше уникальность
        uniqueness = max(0, 1 - (similarity_count / len(all_recommendations)))
        return uniqueness
    
    def _check_feasibility(
        self,
        recommendation: Dict[str, Any],
        context_analysis: ContextAnalysis
    ) -> float:
        """Проверка выполнимости рекомендации"""
        
        content = recommendation.get('content', '').lower()
        score = 1.0
        
        # Проверяем соответствие техническим ограничениям
        for constraint in context_analysis.technical_constraints:
            if constraint.lower() in content:
                score -= 0.2  # Штраф за нарушение ограничений
        
        # Проверяем сложность реализации
        difficulty_words = ['сложно', 'трудно', 'требует', 'необходимо', 'обязательно']
        difficulty_count = sum(1 for word in difficulty_words if word in content)
        score -= difficulty_count * 0.1
        
        return max(score, 0.0) 