"""FastAPI-приложение для генерации внутренних ссылок."""

from __future__ import annotations

import asyncio
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

import httpx
import nltk
import numpy as np
import chromadb
import ollama
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import Integer, Text, JSON, select, DateTime, ARRAY, Float
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime

# Загрузка NLTK данных при старте
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Русские стоп-слова
RUSSIAN_STOP_WORDS = set(stopwords.words('russian'))


class WebSocketManager:
    """Менеджер WebSocket соединений для отслеживания прогресса."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Подключение нового клиента."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"🔌 WebSocket подключен: {client_id}")
    
    def disconnect(self, client_id: str):
        """Отключение клиента."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"🔌 WebSocket отключен: {client_id}")
    
    async def send_progress(self, client_id: str, message: dict):
        """Отправка прогресса конкретному клиенту."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                print(f"📊 Прогресс отправлен {client_id}: {message}")
            except Exception as e:
                print(f"❌ Ошибка отправки прогресса {client_id}: {e}")
    
    async def send_error(self, client_id: str, error: str, details: str = ""):
        """Отправка ошибки клиенту."""
        await self.send_progress(client_id, {
            "type": "error",
            "message": error,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_step(self, client_id: str, step: str, current: int, total: int, details: str = ""):
        """Отправка информации о текущем шаге."""
        await self.send_progress(client_id, {
            "type": "progress",
            "step": step,
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100) if total > 0 else 0,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_ollama_info(self, client_id: str, info: dict):
        """Отправка информации о работе Ollama."""
        await self.send_progress(client_id, {
            "type": "ollama",
            "info": info,
            "timestamp": datetime.now().isoformat()
        })


# Глобальный менеджер WebSocket
websocket_manager = WebSocketManager()

app = FastAPI()

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Base(DeclarativeBase):
    """Базовый класс моделей."""


class Recommendation(Base):
    """Модель сохраненной рекомендации."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    links: Mapped[list[str]] = mapped_column(JSON)


class WordPressPost(Base):
    """Модель статей WordPress сайта."""

    __tablename__ = "wordpress_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(Text)
    wp_post_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    excerpt: Mapped[str] = mapped_column(Text, nullable=True)
    link: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisHistory(Base):
    """Модель истории анализов WordPress сайтов."""

    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(Text)
    posts_count: Mapped[int] = mapped_column(Integer)
    recommendations_count: Mapped[int] = mapped_column(Integer) 
    recommendations: Mapped[list[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    summary: Mapped[str] = mapped_column(Text, nullable=True)


class ArticleEmbedding(Base):
    """Модель для хранения эмбеддингов статей."""

    __tablename__ = "article_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    domain: Mapped[str] = mapped_column(Text)
    wp_post_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    content_snippet: Mapped[str] = mapped_column(Text)
    link: Mapped[str] = mapped_column(Text)
    embedding_vector: Mapped[str] = mapped_column(Text)  # JSON строка с вектором
    themes: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RecommendRequest(BaseModel):
    """Запрос с текстом для генерации ссылок."""

    text: str


class WPRequest(BaseModel):
    """Запрос для анализа WordPress-сайта."""

    domain: str
    client_id: Optional[str] = None


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
# Оптимальная модель для SEO задач: qwen2.5:7b - отличный баланс качества/стабильности/ресурсов
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://seo_user:seo_pass@localhost/seo_db",
)

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Инициализация RAG-системы
chroma_client = None
tfidf_vectorizer = None

def initialize_rag_system():
    """Инициализирует TF-IDF векторизатор и векторную БД."""
    global chroma_client, tfidf_vectorizer
    try:
        print("🔧 Инициализация упрощенной RAG-системы...")
        # Используем TF-IDF вместо sentence-transformers
        tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8,
            stop_words='english'
        )
        
        # Инициализируем ChromaDB для векторного поиска
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        print("✅ Упрощенная RAG-система инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации RAG: {e}")
        chroma_client = None
        tfidf_vectorizer = None


class SmartRAGManager:
    """Умный RAG-менеджер с TF-IDF векторизацией."""
    
    def __init__(self):
        self.domain_collections = {}
        self.domain_articles = {}  # Кеш статей для TF-IDF
    
    async def create_domain_knowledge_base(self, domain: str, posts: List[Dict]) -> bool:
        """Создает базу знаний для конкретного домена с TF-IDF."""
        if not chroma_client:
            print("❌ RAG-система не инициализирована")
            return False
            
        try:
            print(f"🔮 Создание TF-IDF базы знаний для домена {domain}...")
            
            # Очищаем имя коллекции для ChromaDB
            collection_name = domain.replace(".", "_").replace("-", "_")
            
            # Удаляем старую коллекцию если есть
            try:
                old_collection = chroma_client.get_collection(name=collection_name)
                chroma_client.delete_collection(name=collection_name)
                print(f"🗑️ Удалена старая коллекция {collection_name}")
            except:
                pass
            
            # Создаем новую коллекцию
            collection = chroma_client.create_collection(
                name=collection_name,
                metadata={"domain": domain, "created_at": datetime.now().isoformat()}
            )
            
            # Подготавливаем тексты для TF-IDF
            documents = []
            metadatas = []
            ids = []
            
            for i, post in enumerate(posts):
                # Проверяем, что статья принадлежит нашему домену
                if domain.lower() not in post.get('link', '').lower():
                    continue
                
                title = post.get('title', '')[:200]
                content = post.get('content', '')[:800]
                
                # Создаем текст для векторизации
                full_text = f"{title} {content}"
                
                documents.append(full_text)
                metadatas.append({
                    "title": title,
                    "link": post.get('link', ''),
                    "content_snippet": content[:200],
                    "domain": domain,
                    "post_index": i
                })
                ids.append(f"{collection_name}_{i}")
            
            if not documents:
                print(f"❌ Нет статей для домена {domain}")
                return False
            
            # Вычисляем TF-IDF векторы для всех документов
            vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                min_df=1,
                stop_words='english'
            )
            
            tfidf_matrix = vectorizer.fit_transform(documents)
            
            # Конвертируем разреженную матрицу в плотную для ChromaDB
            dense_embeddings = tfidf_matrix.toarray().tolist()
            
            # Добавляем в коллекцию
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=dense_embeddings
            )
            
            self.domain_collections[domain] = collection_name
            self.domain_articles[domain] = posts  # Кешируем для поиска
            
            print(f"✅ TF-IDF база знаний создана: {len(documents)} статей для {domain}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания базы знаний: {e}")
            return False
    
    def get_domain_articles_overview(self, domain: str, limit: int = 20) -> List[Dict]:
        """Получает обзор статей домена с ограничением."""
        if domain not in self.domain_collections:
            return []
        
        try:
            collection = chroma_client.get_collection(name=self.domain_collections[domain])
            results = collection.get(
                limit=limit,
                include=['metadatas']
            )
            
            articles = []
            for metadata in results['metadatas']:
                # Дополнительная проверка домена
                if domain.lower() in metadata['link'].lower():
                    articles.append({
                        'title': metadata['title'],
                        'link': metadata['link'],
                        'content': metadata['content_snippet'],
                        'domain': metadata['domain']
                    })
            
            print(f"📋 Получено {len(articles)} статей для обзора")
            return articles
            
        except Exception as e:
            print(f"❌ Ошибка получения обзора: {e}")
            return []


# Глобальный RAG-менеджер
rag_manager = SmartRAGManager()


async def generate_links(text: str) -> list[str]:
    """Запрашивает Ollama для генерации простых ссылок."""
    prompt = (
        "Предложи до пяти внутренних ссылок для следующего текста на русском языке. "
        "Каждую ссылку выведи с новой строки в формате /article/название-статьи, "
        "основываясь на ключевых словах из текста. "
        "Не добавляй лишние символы или объяснения. "
        f"Текст: {text}"
    )
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
    response.raise_for_status()
    data = response.json()
    lines = [line.strip("- \n") for line in data.get("response", "").splitlines()]
    links = [line for line in lines if line]
    return links[:5]


async def fetch_and_store_wp_posts(domain: str) -> list[dict[str, str]]:
    """Загружает статьи WordPress и сохраняет в БД с дедупликацией."""
    print(f"🌐 Загружаю посты с сайта {domain}")
    
    # Очищаем старые посты этого домена
    async with AsyncSessionLocal() as session:
        await session.execute(
            select(WordPressPost).where(WordPressPost.domain == domain)
        )
        await session.commit()
    
    url = f"https://{domain}/wp-json/wp/v2/posts?per_page=50"  # Ограничиваем до 50 для производительности
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="Сайт недоступен или не WordPress")
    data = response.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Некорректный ответ WordPress")
    
    posts = []
    seen_urls = set()  # Для дедупликации по URL
    seen_titles = set()  # Для дедупликации по заголовкам
    
    async with AsyncSessionLocal() as session:
        for item in data:
            try:
                # Извлекаем содержимое
                content = item.get("content", {}).get("rendered", "")
                excerpt = item.get("excerpt", {}).get("rendered", "")
                
                # Очищаем HTML
                clean_content = BeautifulSoup(content, 'html.parser').get_text()
                clean_excerpt = BeautifulSoup(excerpt, 'html.parser').get_text() if excerpt else ""
                
                # Проверяем, что ссылка принадлежит нашему домену
                post_link = item["link"]
                if domain.lower() not in post_link.lower():
                    print(f"⚠️ Пропускаю статью с чужого домена: {post_link}")
                    continue
                
                # Дедупликация по URL
                if post_link in seen_urls:
                    print(f"⚠️ Дубликат URL пропущен: {post_link}")
                    continue
                seen_urls.add(post_link)
                
                # Дедупликация по заголовку
                title = item["title"]["rendered"]
                title_normalized = title.lower().strip()
                if title_normalized in seen_titles:
                    print(f"⚠️ Дубликат заголовка пропущен: {title}")
                    continue
                seen_titles.add(title_normalized)
                
                # Сохраняем в БД
                wp_post = WordPressPost(
                    domain=domain,
                    wp_post_id=item["id"],
                    title=title,
                    content=clean_content,
                    excerpt=clean_excerpt,
                    link=post_link
                )
                session.add(wp_post)
                
                # Для RAG берем больше контекста
                posts.append({
                    "title": title, 
                    "link": post_link,
                    "content": clean_content[:800].strip()  # Первые 800 символов
                })
                
                print(f"💾 Сохранен уникальный пост: {title}")
                
            except Exception as exc:
                print(f"❌ Ошибка обработки поста {item.get('id', 'unknown')}: {exc}")
                continue
        
        await session.commit()
        print(f"✅ Сохранено {len(posts)} уникальных постов из домена {domain}")
    
    return posts


async def generate_rag_recommendations(domain: str, client_id: Optional[str] = None) -> list[dict[str, str]]:
    """Генерирует рекомендации используя RAG-подход с векторной БД."""
    print(f"🚀 Запуск RAG-анализа для домена {domain} (client: {client_id})")
    
    try:
        # Шаг 1: Загрузка статей из БД
        if client_id:
            await websocket_manager.send_step(client_id, "Загрузка статей", 1, 7, "Получение статей из базы данных...")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WordPressPost).where(WordPressPost.domain == domain)
            )
            db_posts = result.scalars().all()
        
        if not db_posts:
            error_msg = "❌ Нет статей для RAG-анализа"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg, f"Не найдено статей для домена {domain}")
            return []
        
        print(f"📊 Загружено {len(db_posts)} статей из БД")
        
        # Преобразуем в формат для RAG
        posts_data = []
        for post in db_posts:
            posts_data.append({
                "title": post.title,
                "link": post.link,
                "content": post.content[:1000]  # Первые 1000 символов
            })
        
        # Шаг 2: Создание векторной базы
        if client_id:
            await websocket_manager.send_step(client_id, "Создание векторной базы", 2, 7, "Обработка статей для векторного поиска...")
        
        success = await rag_manager.create_domain_knowledge_base(domain, posts_data)
        if not success:
            error_msg = "❌ Не удалось создать базу знаний"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg, "Ошибка создания TF-IDF векторов")
            return []
        
        # Шаг 3: Получение обзора статей
        if client_id:
            await websocket_manager.send_step(client_id, "Анализ контента", 3, 7, "Выбор наиболее релевантных статей...")
        
        articles = rag_manager.get_domain_articles_overview(domain, limit=8)  # Увеличиваем для качества
        if not articles:
            error_msg = "❌ Не найдены статьи в базе знаний"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg, "Пустая векторная база знаний")
            return []
        
        print(f"📋 Выбрано {len(articles)} статей для анализа")
        
        # Шаг 4: Подготовка улучшенного промпта
        if client_id:
            await websocket_manager.send_step(client_id, "Подготовка ИИ", 4, 7, "Создание контекста для Ollama...")
        
        # Создаем более качественный промпт
        articles_context = ""
        for i, article in enumerate(articles, 1):
            title = article['title'][:80]
            content_snippet = article['content'][:150] if article.get('content') else ""
            articles_context += f"Статья {i}: {title}\nURL: {article['link']}\nКратко: {content_snippet}...\n\n"
        
        # Промпт, оптимизированный для qwen2.5 - четкие инструкции и структура
        qwen_optimized_prompt = f"""# SEO АНАЛИЗ САЙТА {domain}

## КОНТЕКСТ ({len(articles)} статей):
{articles_context}

## ЦЕЛЬ:
Создать 5-7 внутренних SEO-ссылок для улучшения внутренней перелинковки сайта.

## ФОРМАТ ОТВЕТА:
```
ИСТОЧНИК -> ЦЕЛЬ | анкор-текст | обоснование связи
```

## ТРЕБОВАНИЯ:
1. Анкор: естественный текст 3-8 слов, содержит ключевые слова
2. Обоснование: логическая связь между статьями (8-15 слов)
3. Используй ТОЛЬКО URL из списка выше
4. Создавай тематически связанные ссылки
5. Избегай повторения одних и тех же URL

## ПРИМЕР:
```
{articles[0]['link']} -> {articles[1]['link'] if len(articles) > 1 else articles[0]['link']} | читайте подробное руководство | статьи дополняют друг друга по теме
```

## ТВОЙ ОТВЕТ:
```"""

        # Шаг 5: Запрос к Ollama
        if client_id:
            await websocket_manager.send_step(client_id, "Запрос к Ollama", 5, 7, "Отправка контекста в ИИ...")
            # Отправляем детали запроса
            await websocket_manager.send_ollama_info(client_id, {
                "status": "starting",
                "model": OLLAMA_MODEL,
                "model_info": "qwen2.5:7b - оптимизированная для SEO",
                "articles_count": len(articles),
                "prompt_length": len(qwen_optimized_prompt),
                "timeout": 45,
                "settings": "temperature=0.2, ctx=4096, predict=350"
            })
        
        print("🤖 Отправляю оптимизированный запрос для qwen2.5...")
        print(f"📝 Размер промпта: {len(qwen_optimized_prompt)} символов")
        
        # Оптимальные настройки для qwen2.5:7b - баланс качества/стабильности/скорости
        start_time = datetime.now()
        async with httpx.AsyncClient(timeout=45.0) as client:  # Сокращаем таймаут для qwen - быстрее работает
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": qwen_optimized_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,    # Немного больше креативности для qwen
                        "num_ctx": 4096,       # qwen2.5 хорошо работает с большим контекстом
                        "num_predict": 350,    # Оптимальное количество токенов для SEO
                        "top_p": 0.8,         # qwen лучше работает с более высоким top_p
                        "top_k": 50,          # Ограничиваем выбор токенов для стабильности
                        "repeat_penalty": 1.15, # qwen склонна к повторениям
                        "seed": 42,           # Фиксированное зерно для воспроизводимости
                        "stop": ["\n\nРЕЗУЛЬТАТ:", "КОНЕЦ", "---", "```"]
                    }
                },
                timeout=45
            )
        
        request_time = (datetime.now() - start_time).total_seconds()
        
        if client_id:
            await websocket_manager.send_ollama_info(client_id, {
                "status": "completed",
                "response_code": response.status_code,
                "request_time": f"{request_time:.1f}s",
                "response_length": len(response.text) if response.status_code == 200 else 0
            })
        
        if response.status_code != 200:
            error_msg = f"❌ Ollama вернула код {response.status_code}"
            print(error_msg)
            if client_id:
                await websocket_manager.send_error(client_id, error_msg, f"HTTP статус: {response.status_code}")
            return []
        
        data = response.json()
        content = data.get("response", "")
        print(f"📝 Получен ответ от Ollama: {len(content)} символов за {request_time:.1f}с")
        
        # Шаг 6: Обработка результатов
        if client_id:
            await websocket_manager.send_step(client_id, "Обработка ответа", 6, 7, "Парсинг рекомендаций от ИИ...")
        
        recommendations = parse_ollama_recommendations(content, domain, articles)
        
        # Шаг 7: Финализация
        if client_id:
            await websocket_manager.send_step(client_id, "Завершение", 7, 7, f"Готово! Получено {len(recommendations)} рекомендаций")
        
        print(f"✅ RAG-анализ завершен: {len(recommendations)} рекомендаций за {request_time:.1f}с")
        return recommendations[:15]  # Топ-15 для баланса качества и производительности
        
    except Exception as e:
        error_msg = f"❌ Ошибка RAG-анализа: {e}"
        print(error_msg)
        if client_id:
            await websocket_manager.send_error(client_id, "Критическая ошибка анализа", str(e))
        return []


def parse_ollama_recommendations(text: str, domain: str, articles: List[Dict]) -> List[Dict]:
    """Парсит рекомендации из ответа Ollama с проверкой домена."""
    recommendations = []
    
    # Создаем множество валидных URL для домена
    valid_urls = set()
    for article in articles:
        url = article['link']
        if domain.lower() in url.lower():
            valid_urls.add(url)
    
    print(f"🔍 Валидные URL для домена {domain}: {len(valid_urls)}")
    
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        
        if '->' in line and '|' in line:
            try:
                parts = line.split('|', 2)
                if len(parts) < 3:
                    continue
                
                link_part = parts[0].strip()
                anchor = parts[1].strip()
                comment = parts[2].strip()
                
                # Проверяем качество
                if len(anchor) < 5 or len(comment) < 40:
                    continue
                
                if '->' in link_part:
                    source, target = link_part.split('->', 1)
                    source = source.strip()
                    target = target.strip()
                    
                    # Проверяем, что URL принадлежат нашему домену
                    if (source in valid_urls and 
                        target in valid_urls and 
                        source != target and
                        domain.lower() in source.lower() and
                        domain.lower() in target.lower()):
                        
                        recommendations.append({
                            "from": source,
                            "to": target,
                            "anchor": anchor,
                            "comment": comment
                        })
                        print(f"✅ Валидная рекомендация: {source[:50]}... -> {target[:50]}...")
                    else:
                        print(f"⚠️ Отклонена рекомендация: неподходящие URL или домен")
                        
            except Exception as e:
                print(f"❌ Ошибка парсинга строки: {e}")
                continue
    
    return recommendations


@app.on_event("startup")
async def on_startup() -> None:
    """Создает таблицы и инициализирует RAG-систему при запуске."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Инициализируем RAG-систему
    initialize_rag_system()


@app.post("/api/v1/test")
async def test(req: RecommendRequest) -> dict[str, str]:
    """Тестовый endpoint."""
    return {"message": f"Получен текст: {req.text[:50]}..."}


@app.post("/api/v1/recommend")
async def recommend(req: RecommendRequest) -> dict[str, list[str]]:
    """Возвращает простые рекомендации ссылок."""
    links = await generate_links(req.text)

    async with AsyncSessionLocal() as session:
        rec = Recommendation(text=req.text, links=links)
        session.add(rec)
        await session.commit()
    return {"links": links}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket эндпоинт для отслеживания прогресса."""
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            # Ожидаем сообщения от клиента (поддержание соединения)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)


@app.post("/api/v1/wp_recommend")
async def wp_recommend(req: WPRequest) -> dict[str, list[dict[str, str]]]:
    """RAG-анализ WordPress сайта с векторной базой данных."""
    try:
        if req.client_id:
            await websocket_manager.send_step(req.client_id, "Начало анализа", 0, 3, "Инициализация анализа WordPress...")
        
        # Этап 1: Загружаем и сохраняем посты
        if req.client_id:
            await websocket_manager.send_step(req.client_id, "Загрузка WordPress", 1, 3, "Получение статей с сайта...")
        
        posts = await fetch_and_store_wp_posts(req.domain)
        
        # Этап 2: Генерируем рекомендации через RAG
        if req.client_id:
            await websocket_manager.send_step(req.client_id, "RAG анализ", 2, 3, "Запуск интеллектуального анализа...")
        
        recs = await generate_rag_recommendations(req.domain, req.client_id)
        
        # Этап 3: Сохраняем историю
        if req.client_id:
            await websocket_manager.send_step(req.client_id, "Сохранение", 3, 3, "Сохранение результатов...")
        
        summary = f"RAG-анализ {req.domain}: {len(posts)} статей, {len(recs)} качественных рекомендаций"
        
        async with AsyncSessionLocal() as session:
            analysis = AnalysisHistory(
                domain=req.domain,
                posts_count=len(posts),
                recommendations_count=len(recs),
                recommendations=recs,
                summary=summary
            )
            session.add(analysis)
            await session.commit()
        
        if req.client_id:
            await websocket_manager.send_progress(req.client_id, {
                "type": "complete",
                "message": "Анализ завершен успешно!",
                "recommendations_count": len(recs),
                "posts_count": len(posts),
                "timestamp": datetime.now().isoformat()
            })
        
        return {"recommendations": recs}
        
    except Exception as e:
        error_msg = f"Ошибка анализа WordPress: {str(e)}"
        print(f"❌ {error_msg}")
        
        if req.client_id:
            await websocket_manager.send_error(req.client_id, "Критическая ошибка", error_msg)
        
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Проверка работоспособности."""
    return {"status": "ok"}


@app.get("/api/v1/recommendations")
async def list_recommendations() -> list[dict[str, object]]:
    """Возвращает все сохраненные рекомендации."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Recommendation).order_by(Recommendation.id.desc())
        )
        items = [
            {"id": rec.id, "text": rec.text, "links": rec.links}
            for rec in result.scalars()
        ]
    return items


@app.get("/api/v1/analysis_history")
async def list_analysis_history() -> list[dict[str, object]]:
    """Возвращает историю анализов WordPress сайтов."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisHistory).order_by(AnalysisHistory.created_at.desc())
        )
        items = [
            {
                "id": analysis.id,
                "domain": analysis.domain,
                "posts_count": analysis.posts_count,
                "recommendations_count": analysis.recommendations_count,
                "summary": analysis.summary,
                "created_at": analysis.created_at.isoformat(),
                "recommendations": analysis.recommendations
            }
            for analysis in result.scalars()
        ]
    return items


@app.get("/api/v1/analysis_history/{analysis_id}")
async def get_analysis_details(analysis_id: int) -> dict[str, object]:
    """Возвращает детали конкретного анализа."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisHistory).where(AnalysisHistory.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise HTTPException(status_code=404, detail="Анализ не найден")
        
        return {
            "id": analysis.id,
            "domain": analysis.domain,
            "posts_count": analysis.posts_count,
            "recommendations_count": analysis.recommendations_count,
            "summary": analysis.summary,
            "created_at": analysis.created_at.isoformat(),
            "recommendations": analysis.recommendations
        }


@app.delete("/api/v1/clear_data")
async def clear_all_data() -> dict[str, str]:
    """Очистка всех данных в базе данных (только для разработки)."""
    try:
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # Используем raw SQL для очистки - более надежно
            await session.execute(text("DELETE FROM analysis_history"))
            await session.execute(text("DELETE FROM article_embeddings")) 
            await session.execute(text("DELETE FROM wordpress_posts"))
            await session.execute(text("DELETE FROM recommendations"))
            
            # Сброс последовательностей (автоинкремент)
            await session.execute(text("ALTER SEQUENCE analysis_history_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE article_embeddings_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE wordpress_posts_id_seq RESTART WITH 1"))
            await session.execute(text("ALTER SEQUENCE recommendations_id_seq RESTART WITH 1"))
            
            await session.commit()
        
        # Очищаем ChromaDB
        try:
            if chroma_client:
                # Получаем все коллекции и удаляем их
                collections = chroma_client.list_collections()
                for collection in collections:
                    chroma_client.delete_collection(name=collection.name)
                    print(f"🗑️ Удалена ChromaDB коллекция: {collection.name}")
                
                # Очищаем кеш RAG менеджера
                rag_manager.domain_collections.clear()
                rag_manager.domain_articles.clear()
                print("🗑️ Очищен кеш RAG менеджера")
        except Exception as chroma_error:
            print(f"⚠️ Ошибка очистки ChromaDB: {chroma_error}")
        
        print("🧹 Все данные успешно очищены")
        return {"status": "ok", "message": "Все данные очищены"}
        
    except Exception as e:
        print(f"❌ Ошибка очистки данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки: {str(e)}")


@app.get("/")
async def root():
    """Редирект на фронтенд."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:3000")
