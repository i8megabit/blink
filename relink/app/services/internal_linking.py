"""
🔗 Сервис внутренней перелинковки
"""

import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os

from ..models import (
    InternalLink, Post, InternalLinkAnalysis, PostAnalysis,
    SEOAnalysisResult, Recommendation, FocusArea, Priority
)

logger = logging.getLogger(__name__)

class InternalLinkingService:
    """Сервис анализа и оптимизации внутренних ссылок"""
    
    def __init__(self):
        self.indexed_data: Dict[str, Any] = {}
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def index_domain(self, domain: str) -> Dict[str, Any]:
        """Индексация домена"""
        logger.info(f"Начинаем индексацию домена: {domain}")
        
        try:
            # Проверяем кеш
            cache_file = os.path.join(self.cache_dir, f"{domain}_index.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.indexed_data[domain] = json.load(f)
                logger.info(f"Загружены кешированные данные для {domain}")
                return self.indexed_data[domain]
            
            # Запускаем индексацию
            base_url = f"https://{domain}"
            indexer = DomainIndexer(base_url)
            result = await indexer.index_domain()
            
            # Сохраняем в кеш
            self.indexed_data[domain] = result
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Индексация {domain} завершена. Обработано {result['posts_count']} постов")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка индексации {domain}: {e}")
            raise
    
    async def get_indexing_status(self, domain: str) -> Dict[str, Any]:
        """Получение статуса индексации"""
        cache_file = os.path.join(self.cache_dir, f"{domain}_index.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                "status": "completed",
                "domain": domain,
                "posts_count": data.get("posts_count", 0),
                "internal_links_count": data.get("internal_links_count", 0),
                "indexed_at": data.get("indexed_at", ""),
                "last_updated": datetime.fromtimestamp(os.path.getmtime(cache_file)).isoformat()
            }
        else:
            return {
                "status": "not_indexed",
                "domain": domain,
                "message": "Домен не проиндексирован"
            }
    
    async def analyze_domain(
        self, 
        domain: str, 
        include_posts: bool = True,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Анализ домена"""
        logger.info(f"Анализируем домен: {domain}")
        
        # Убеждаемся, что домен проиндексирован
        if domain not in self.indexed_data:
            await self.index_domain(domain)
        
        data = self.indexed_data[domain]
        
        analysis = {
            "domain": domain,
            "total_posts": data["posts_count"],
            "total_internal_links": data["internal_links_count"],
            "seo_data": data["seo_data"],
            "internal_links_analysis": await self._analyze_internal_links(data),
        }
        
        if include_posts:
            analysis["posts_analysis"] = await self._analyze_posts(data["posts"])
        
        if include_recommendations:
            analysis["recommendations"] = await self._generate_basic_recommendations(data)
        
        return analysis
    
    async def _analyze_internal_links(self, data: Dict[str, Any]) -> InternalLinkAnalysis:
        """Анализ внутренних ссылок"""
        internal_links = data.get("internal_links", [])
        posts = data.get("posts", [])
        
        # Собираем все ссылки
        all_links = []
        for post in posts:
            all_links.extend(post.get("internal_links", []))
        
        # Анализируем распределение
        link_distribution = {}
        for link in all_links:
            link_type = self._determine_link_type(link)
            link_distribution[link_type] = link_distribution.get(link_type, 0) + 1
        
        # Находим страницы без входящих ссылок
        all_targets = set()
        for link in all_links:
            all_targets.add(link["to_url"])
        
        all_sources = set()
        for link in all_links:
            all_sources.add(link["from_url"])
        
        orphan_pages = list(all_sources - all_targets)
        
        # Самые ссылаемые страницы
        target_counts = {}
        for link in all_links:
            target = link["to_url"]
            target_counts[target] = target_counts.get(target, 0) + 1
        
        most_linked = sorted(target_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_linked_pages = [
            {"url": url, "incoming_links": count} 
            for url, count in most_linked
        ]
        
        return InternalLinkAnalysis(
            total_links=len(all_links),
            unique_targets=len(all_targets),
            orphan_pages=orphan_pages,
            most_linked_pages=most_linked_pages,
            link_distribution=link_distribution
        )
    
    async def _analyze_posts(self, posts: List[Dict[str, Any]]) -> List[PostAnalysis]:
        """Анализ постов"""
        post_analyses = []
        
        for post in posts:
            # Рассчитываем SEO оценку
            seo_score = await self._calculate_seo_score(post)
            
            # Находим проблемы
            issues = await self._identify_post_issues(post)
            
            analysis = PostAnalysis(
                url=post["url"],
                title=post["title"],
                word_count=post["word_count"],
                internal_links_count=len(post.get("internal_links", [])),
                seo_score=seo_score,
                issues=issues
            )
            post_analyses.append(analysis)
        
        return post_analyses
    
    async def _calculate_seo_score(self, post: Dict[str, Any]) -> float:
        """Расчет SEO оценки поста"""
        score = 0.0
        
        # Оценка заголовка (0-25 баллов)
        title = post.get("title", "")
        if title:
            if 30 <= len(title) <= 60:
                score += 25
            elif 20 <= len(title) <= 70:
                score += 15
            else:
                score += 5
        
        # Оценка контента (0-30 баллов)
        word_count = post.get("word_count", 0)
        if word_count >= 300:
            score += 30
        elif word_count >= 150:
            score += 20
        elif word_count >= 50:
            score += 10
        
        # Оценка внутренних ссылок (0-25 баллов)
        internal_links = post.get("internal_links", [])
        if 2 <= len(internal_links) <= 5:
            score += 25
        elif len(internal_links) > 5:
            score += 15
        elif len(internal_links) == 1:
            score += 10
        
        # Оценка meta description (0-20 баллов)
        seo_data = post.get("seo_data", {})
        meta_desc = seo_data.get("meta_description", "")
        if meta_desc:
            if 120 <= len(meta_desc) <= 160:
                score += 20
            elif 100 <= len(meta_desc) <= 180:
                score += 15
            else:
                score += 5
        
        return min(score, 100.0)
    
    async def _identify_post_issues(self, post: Dict[str, Any]) -> List[str]:
        """Выявление проблем в посте"""
        issues = []
        
        title = post.get("title", "")
        if not title:
            issues.append("Отсутствует заголовок")
        elif len(title) < 30:
            issues.append("Заголовок слишком короткий")
        elif len(title) > 60:
            issues.append("Заголовок слишком длинный")
        
        word_count = post.get("word_count", 0)
        if word_count < 300:
            issues.append("Недостаточно контента (менее 300 слов)")
        
        internal_links = post.get("internal_links", [])
        if len(internal_links) == 0:
            issues.append("Отсутствуют внутренние ссылки")
        elif len(internal_links) > 10:
            issues.append("Слишком много внутренних ссылок")
        
        seo_data = post.get("seo_data", {})
        if not seo_data.get("meta_description"):
            issues.append("Отсутствует meta description")
        
        return issues
    
    async def _determine_link_type(self, link: Dict[str, Any]) -> str:
        """Определение типа ссылки"""
        anchor_text = link.get("anchor_text", "").lower()
        
        if any(word in anchor_text for word in ["читать", "подробнее", "далее"]):
            return "cta"
        elif any(word in anchor_text for word in ["главная", "о нас", "контакты"]):
            return "navigation"
        elif any(word in anchor_text for word in ["связанные", "похожие", "рекомендуем"]):
            return "related"
        else:
            return "content"
    
    async def _generate_basic_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация базовых рекомендаций"""
        recommendations = []
        
        posts = data.get("posts", [])
        internal_links = data.get("internal_links", [])
        
        # Анализ контента
        short_posts = [p for p in posts if p.get("word_count", 0) < 300]
        if short_posts:
            recommendations.append({
                "type": "content_optimization",
                "priority": "high",
                "title": "Увеличить объем контента",
                "description": f"Найдено {len(short_posts)} постов с недостаточным объемом контента",
                "action": "Добавить больше релевантного контента в короткие посты"
            })
        
        # Анализ внутренних ссылок
        posts_without_links = [p for p in posts if not p.get("internal_links")]
        if posts_without_links:
            recommendations.append({
                "type": "internal_linking",
                "priority": "medium",
                "title": "Добавить внутренние ссылки",
                "description": f"Найдено {len(posts_without_links)} постов без внутренних ссылок",
                "action": "Добавить релевантные внутренние ссылки в посты"
            })
        
        # Анализ заголовков
        bad_titles = [p for p in posts if len(p.get("title", "")) < 30 or len(p.get("title", "")) > 60]
        if bad_titles:
            recommendations.append({
                "type": "on_page_seo",
                "priority": "medium",
                "title": "Оптимизировать заголовки",
                "description": f"Найдено {len(bad_titles)} постов с неоптимальными заголовками",
                "action": "Оптимизировать заголовки (30-60 символов)"
            })
        
        return recommendations
    
    async def generate_recommendations(
        self, 
        domain: str, 
        focus_areas: List[FocusArea] = None,
        priority: Priority = Priority.MEDIUM
    ) -> List[Dict[str, Any]]:
        """Генерация SEO рекомендаций"""
        logger.info(f"Генерируем рекомендации для {domain}")
        
        if domain not in self.indexed_data:
            await self.index_domain(domain)
        
        data = self.indexed_data[domain]
        recommendations = []
        
        # Базовые рекомендации
        basic_recs = await self._generate_basic_recommendations(data)
        recommendations.extend(basic_recs)
        
        # Специфичные рекомендации по областям фокуса
        if focus_areas:
            for area in focus_areas:
                area_recs = await self._generate_area_recommendations(data, area)
                recommendations.extend(area_recs)
        
        # Фильтрация по приоритету
        if priority != Priority.LOW:
            recommendations = [r for r in recommendations if r.get("priority") != "low"]
        
        return recommendations
    
    async def _generate_area_recommendations(self, data: Dict[str, Any], area: FocusArea) -> List[Dict[str, Any]]:
        """Генерация рекомендаций по конкретной области"""
        recommendations = []
        
        if area == FocusArea.INTERNAL_LINKING:
            # Анализ структуры внутренних ссылок
            internal_links = data.get("internal_links", [])
            if len(internal_links) < 10:
                recommendations.append({
                    "type": "internal_linking",
                    "priority": "high",
                    "title": "Улучшить структуру внутренних ссылок",
                    "description": "Недостаточно внутренних ссылок для эффективной навигации",
                    "action": "Создать стратегию внутренней перелинковки"
                })
        
        elif area == FocusArea.CONTENT_OPTIMIZATION:
            # Анализ контента
            posts = data.get("posts", [])
            avg_word_count = sum(p.get("word_count", 0) for p in posts) / len(posts) if posts else 0
            
            if avg_word_count < 500:
                recommendations.append({
                    "type": "content_optimization",
                    "priority": "medium",
                    "title": "Улучшить качество контента",
                    "description": f"Средний объем контента ({avg_word_count:.0f} слов) ниже рекомендуемого",
                    "action": "Увеличить объем и качество контента"
                })
        
        elif area == FocusArea.TECHNICAL_SEO:
            # Технические рекомендации
            seo_data = data.get("seo_data", {})
            if not seo_data.get("meta_description"):
                recommendations.append({
                    "type": "technical_seo",
                    "priority": "high",
                    "title": "Добавить meta description",
                    "description": "Отсутствует meta description на главной странице",
                    "action": "Добавить уникальный meta description"
                })
        
        return recommendations
    
    async def get_internal_links(self, domain: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение внутренних ссылок домена"""
        if domain not in self.indexed_data:
            await self.index_domain(domain)
        
        data = self.indexed_data[domain]
        return data.get("internal_links", [])[:limit]
    
    async def get_posts(self, domain: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение постов домена"""
        if domain not in self.indexed_data:
            await self.index_domain(domain)
        
        data = self.indexed_data[domain]
        return data.get("posts", [])[:limit]
    
    async def analyze_seo_content(
        self, 
        url: str, 
        title: str, 
        content: str, 
        meta_description: str = None
    ) -> Dict[str, Any]:
        """Анализ SEO контента"""
        analysis = {
            "url": url,
            "title_analysis": await self._analyze_title(title),
            "content_analysis": await self._analyze_content(content),
            "meta_description_analysis": await self._analyze_meta_description(meta_description) if meta_description else None,
            "overall_score": 0.0,
            "recommendations": []
        }
        
        # Рассчитываем общую оценку
        scores = []
        if analysis["title_analysis"]:
            scores.append(analysis["title_analysis"]["score"])
        if analysis["content_analysis"]:
            scores.append(analysis["content_analysis"]["score"])
        if analysis["meta_description_analysis"]:
            scores.append(analysis["meta_description_analysis"]["score"])
        
        if scores:
            analysis["overall_score"] = sum(scores) / len(scores)
        
        # Генерируем рекомендации
        analysis["recommendations"] = await self._generate_content_recommendations(analysis)
        
        return analysis
    
    async def _analyze_title(self, title: str) -> Dict[str, Any]:
        """Анализ заголовка"""
        score = 0.0
        issues = []
        
        if not title:
            issues.append("Отсутствует заголовок")
        else:
            length = len(title)
            if length < 30:
                score = 30
                issues.append("Заголовок слишком короткий")
            elif 30 <= length <= 60:
                score = 100
            elif length <= 70:
                score = 80
            else:
                score = 40
                issues.append("Заголовок слишком длинный")
        
        return {
            "score": score,
            "length": len(title),
            "issues": issues,
            "recommendation": "Оптимальная длина: 30-60 символов"
        }
    
    async def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Анализ контента"""
        score = 0.0
        issues = []
        
        if not content:
            issues.append("Отсутствует контент")
        else:
            word_count = len(content.split())
            if word_count < 300:
                score = 30
                issues.append("Недостаточно контента")
            elif word_count < 500:
                score = 60
            elif word_count < 1000:
                score = 80
            else:
                score = 100
        
        return {
            "score": score,
            "word_count": len(content.split()) if content else 0,
            "issues": issues,
            "recommendation": "Рекомендуемый объем: 500+ слов"
        }
    
    async def _analyze_meta_description(self, meta_description: str) -> Dict[str, Any]:
        """Анализ meta description"""
        score = 0.0
        issues = []
        
        if not meta_description:
            issues.append("Отсутствует meta description")
        else:
            length = len(meta_description)
            if length < 120:
                score = 40
                issues.append("Meta description слишком короткий")
            elif 120 <= length <= 160:
                score = 100
            elif length <= 180:
                score = 80
            else:
                score = 60
                issues.append("Meta description слишком длинный")
        
        return {
            "score": score,
            "length": len(meta_description),
            "issues": issues,
            "recommendation": "Оптимальная длина: 120-160 символов"
        }
    
    async def _generate_content_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций по контенту"""
        recommendations = []
        
        title_analysis = analysis.get("title_analysis")
        if title_analysis and title_analysis.get("issues"):
            recommendations.extend(title_analysis["issues"])
        
        content_analysis = analysis.get("content_analysis")
        if content_analysis and content_analysis.get("issues"):
            recommendations.extend(content_analysis["issues"])
        
        meta_analysis = analysis.get("meta_description_analysis")
        if meta_analysis and meta_analysis.get("issues"):
            recommendations.extend(meta_analysis["issues"])
        
        return recommendations
    
    async def get_dashboard_data(self, domain: str) -> Dict[str, Any]:
        """Получение данных для дашборда"""
        if domain not in self.indexed_data:
            await self.index_domain(domain)
        
        data = self.indexed_data[domain]
        posts = data.get("posts", [])
        
        # Анализируем посты
        post_analyses = await self._analyze_posts(posts)
        
        # Рассчитываем среднюю SEO оценку
        avg_seo_score = sum(p.seo_score for p in post_analyses) / len(post_analyses) if post_analyses else 0
        
        # Топ посты
        top_posts = sorted(post_analyses, key=lambda x: x.seo_score, reverse=True)[:5]
        
        # Топ рекомендации
        recommendations = await self._generate_basic_recommendations(data)
        top_recommendations = [r for r in recommendations if r.get("priority") == "high"][:3]
        
        return {
            "total_posts": len(posts),
            "total_internal_links": data.get("internal_links_count", 0),
            "average_seo_score": avg_seo_score,
            "top_posts": [p.dict() for p in top_posts],
            "top_recommendations": top_recommendations,
            "recent_activity": [
                {
                    "type": "indexing",
                    "timestamp": data.get("indexed_at", ""),
                    "description": f"Индексация завершена: {len(posts)} постов"
                }
            ]
        }
    
    async def export_analysis_json(self, domain: str) -> str:
        """Экспорт анализа в JSON"""
        if domain not in self.indexed_data:
            await self.index_domain(domain)
        
        data = self.indexed_data[domain]
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    async def export_analysis_csv(self, domain: str) -> str:
        """Экспорт анализа в CSV"""
        if domain not in self.indexed_data:
            await self.index_domain(domain)
        
        data = self.indexed_data[domain]
        posts = data.get("posts", [])
        
        # Создаем CSV
        csv_lines = ["URL,Title,Word Count,Internal Links,SEO Score"]
        
        for post in posts:
            seo_score = await self._calculate_seo_score(post)
            csv_lines.append(
                f'"{post["url"]}","{post["title"]}",{post["word_count"]},'
                f'{len(post.get("internal_links", []))},{seo_score:.1f}'
            )
        
        return "\n".join(csv_lines)

class DomainIndexer:
    """Индексатор домена для извлечения SEO данных"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls: set = set()
        self.posts: List[Dict[str, Any]] = []
        self.internal_links: List[Dict[str, Any]] = []
        self.seo_data: Dict[str, Any] = {}
        
    async def index_domain(self) -> Dict[str, Any]:
        """Полная индексация домена"""
        logger.info(f"Начинаем индексацию домена: {self.base_url}")
        
        try:
            # Получаем главную страницу
            main_page = await self.fetch_page(self.base_url)
            if not main_page:
                raise Exception("Не удалось получить главную страницу")
            
            # Извлекаем SEO данные главной страницы
            self.seo_data = await self.extract_seo_data(main_page, self.base_url)
            
            # Ищем ссылки на посты
            post_urls = await self.find_post_urls(main_page)
            logger.info(f"Найдено {len(post_urls)} постов для индексации")
            
            # Индексируем каждый пост
            for url in post_urls[:10]:  # Ограничиваем для тестирования
                post_data = await self.index_post(url)
                if post_data:
                    self.posts.append(post_data)
            
            # Анализируем внутренние ссылки
            await self.analyze_internal_links()
            
            # Создаем отчет
            report = {
                "domain": self.domain,
                "base_url": self.base_url,
                "indexed_at": datetime.now().isoformat(),
                "seo_data": self.seo_data,
                "posts_count": len(self.posts),
                "posts": self.posts,
                "internal_links_count": len(self.internal_links),
                "internal_links": self.internal_links,
                "visited_urls_count": len(self.visited_urls)
            }
            
            logger.info(f"Индексация завершена. Обработано {len(self.posts)} постов")
            return report
            
        except Exception as e:
            logger.error(f"Ошибка при индексации: {e}")
            raise
    
    async def fetch_page(self, url: str) -> str:
        """Получение страницы"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        self.visited_urls.add(url)
                        return await response.text()
                    else:
                        logger.warning(f"Ошибка {response.status} для {url}")
                        return ""
        except Exception as e:
            logger.error(f"Ошибка при получении {url}: {e}")
            return ""
    
    async def extract_seo_data(self, html: str, url: str) -> Dict[str, Any]:
        """Извлечение SEO данных со страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Мета-теги
        title = soup.find('title')
        description = soup.find('meta', attrs={'name': 'description'})
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        
        # Open Graph
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        og_description = soup.find('meta', attrs={'property': 'og:description'})
        og_image = soup.find('meta', attrs={'property': 'og:image'})
        
        # Структурированные данные
        structured_data = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except:
                pass
        
        # Заголовки
        headers = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            headers[f'h{i}'] = [h.get_text(strip=True) for h in h_tags]
        
        # Изображения
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                images.append({
                    'src': urljoin(url, src),
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        
        return {
            'url': url,
            'title': title.get_text(strip=True) if title else '',
            'meta_description': description.get('content', '') if description else '',
            'meta_keywords': keywords.get('content', '') if keywords else '',
            'og_title': og_title.get('content', '') if og_title else '',
            'og_description': og_description.get('content', '') if og_description else '',
            'og_image': og_image.get('content', '') if og_image else '',
            'structured_data': structured_data,
            'headers': headers,
            'images': images,
            'word_count': len(soup.get_text().split()),
            'links_count': len(soup.find_all('a'))
        }
    
    async def find_post_urls(self, html: str) -> List[str]:
        """Поиск ссылок на посты"""
        soup = BeautifulSoup(html, 'html.parser')
        post_urls = []
        
        # Ищем ссылки, которые могут быть постами
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                
                # Проверяем, что это внутренняя ссылка
                if urlparse(full_url).netloc == self.domain:
                    # Ищем паттерны постов
                    if any(pattern in full_url.lower() for pattern in [
                        '/post/', '/article/', '/blog/', '/news/',
                        '/2024/', '/2023/', '/2022/', '/2021/',
                        '.html', '.php'
                    ]):
                        post_urls.append(full_url)
        
        return list(set(post_urls))  # Убираем дубликаты
    
    async def index_post(self, url: str) -> Dict[str, Any]:
        """Индексация отдельного поста"""
        logger.info(f"Индексируем пост: {url}")
        
        html = await self.fetch_page(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Извлекаем SEO данные
        seo_data = await self.extract_seo_data(html, url)
        
        # Ищем основной контент
        content = ""
        content_selectors = [
            'article', '.post-content', '.entry-content', 
            '.content', '.main-content', '#content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True)
                break
        
        if not content:
            content = soup.get_text(strip=True)
        
        # Извлекаем дату публикации
        publish_date = ""
        date_selectors = [
            '.publish-date', '.post-date', '.entry-date',
            'time[datetime]', '.date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                publish_date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                break
        
        # Ищем внутренние ссылки в посте
        internal_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)
                if urlparse(full_url).netloc == self.domain:
                    internal_links.append({
                        'from_url': url,
                        'to_url': full_url,
                        'anchor_text': link.get_text(strip=True),
                        'title': link.get('title', '')
                    })
        
        return {
            'url': url,
            'title': seo_data['title'],
            'content': content[:1000] + "..." if len(content) > 1000 else content,
            'publish_date': publish_date,
            'word_count': seo_data['word_count'],
            'internal_links': internal_links,
            'seo_data': seo_data
        }
    
    async def analyze_internal_links(self):
        """Анализ внутренних ссылок"""
        link_map = {}
        
        # Собираем все внутренние ссылки
        for post in self.posts:
            for link in post.get('internal_links', []):
                to_url = link['to_url']
                if to_url not in link_map:
                    link_map[to_url] = []
                link_map[to_url].append({
                    'from_url': link['from_url'],
                    'anchor_text': link['anchor_text'],
                    'title': link['title']
                })
        
        # Создаем структуру внутренних ссылок
        for to_url, links in link_map.items():
            self.internal_links.append({
                'target_url': to_url,
                'incoming_links': links,
                'incoming_links_count': len(links)
            })
        
        # Сортируем по количеству входящих ссылок
        self.internal_links.sort(key=lambda x: x['incoming_links_count'], reverse=True) 