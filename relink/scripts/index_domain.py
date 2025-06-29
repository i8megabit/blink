#!/usr/bin/env python3
"""
Скрипт индексации домена dagorod.ru
Извлекает посты, внутренние ссылки и SEO данные
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Set
import json
from datetime import datetime
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainIndexer:
    """Индексатор домена для извлечения SEO данных"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls: Set[str] = set()
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

async def main():
    """Основная функция"""
    domain = "https://dagorod.ru"
    
    indexer = DomainIndexer(domain)
    
    try:
        # Индексируем домен
        report = await indexer.index_domain()
        
        # Сохраняем результат
        with open('dagorod_index.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Индексация завершена!")
        print(f"📊 Обработано постов: {report['posts_count']}")
        print(f"🔗 Внутренних ссылок: {report['internal_links_count']}")
        print(f"📄 Результат сохранен в: dagorod_index.json")
        
        return report
        
    except Exception as e:
        print(f"❌ Ошибка при индексации: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main()) 