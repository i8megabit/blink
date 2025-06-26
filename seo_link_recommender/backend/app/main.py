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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
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


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://seo_user:seo_pass@localhost/seo_db",
)

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Инициализация RAG-системы
embedding_model = None
chroma_client = None

def initialize_rag_system():
    """Инициализирует модель эмбеддингов и векторную БД."""
    global embedding_model, chroma_client
    try:
        print("🔧 Инициализация RAG-системы...")
        # Используем легкую, но качественную модель для русского языка
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Инициализируем ChromaDB для векторного поиска
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        print("✅ RAG-система инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации RAG: {e}")
        embedding_model = None
        chroma_client = None


def clean_text_simple(text: str) -> str:
    """Простая очистка русского текста."""
    # Удаляем HTML теги
    clean_text = BeautifulSoup(text, 'html.parser').get_text()
    
    # Токенизация
    tokens = word_tokenize(clean_text.lower(), language='russian')
    
    # Простая фильтрация без лемматизации
    filtered_tokens = []
    for token in tokens:
        if token.isalpha() and token not in RUSSIAN_STOP_WORDS and len(token) > 2:
            filtered_tokens.append(token)
    
    return ' '.join(filtered_tokens)


def extract_key_themes(posts: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """Извлекает ключевые темы из постов с помощью TF-IDF."""
    # Подготавливаем тексты для анализа
    texts = []
    for post in posts:
        title = post.get('title', '')
        content = post.get('content', '')
        combined_text = f"{title} {content}"
        cleaned = clean_text_simple(combined_text)
        texts.append(cleaned)
    
    if not texts:
        return {}
    
    # TF-IDF векторизация
    vectorizer = TfidfVectorizer(
        max_features=50,
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.8
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        # Получаем топ-5 ключевых слов для каждого поста
        themes = {}
        for i, post in enumerate(posts):
            post_vector = tfidf_matrix[i].toarray()[0]
            top_indices = post_vector.argsort()[-5:][::-1]
            top_keywords = [feature_names[idx] for idx in top_indices if post_vector[idx] > 0]
            themes[post['link']] = top_keywords
            
        return themes
    except Exception as e:
        print(f"❌ Ошибка TF-IDF анализа: {e}")
        return {}


def calculate_content_similarity(posts: List[Dict[str, str]]) -> Dict[tuple, float]:
    """Вычисляет семантическую близость между статьями."""
    if len(posts) < 2:
        return {}
    
    # Подготавливаем тексты
    texts = []
    for post in posts:
        title = post.get('title', '')
        content = post.get('content', '')
        combined_text = f"{title} {content}"
        cleaned = clean_text_simple(combined_text)
        texts.append(cleaned)
    
    try:
        # TF-IDF векторизация для вычисления сходства
        vectorizer = TfidfVectorizer(
            max_features=100,
            ngram_range=(1, 2), 
            min_df=1,
            max_df=0.9
        )
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Вычисляем косинусное сходство между всеми парами
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Сохраняем только значимые сходства (> 0.1)
        similarities = {}
        for i in range(len(posts)):
            for j in range(i + 1, len(posts)):
                sim_score = similarity_matrix[i][j]
                if sim_score > 0.1:  # Только значимые сходства
                    similarities[(i, j)] = sim_score
                    
        return similarities
        
    except Exception as e:
        print(f"❌ Ошибка вычисления сходства: {e}")
        return {}


def extract_semantic_clusters(posts: List[Dict[str, str]], themes: Dict[str, List[str]]) -> Dict[str, List[int]]:
    """Группирует статьи по семантическим кластерам."""
    clusters = {}
    
    # Анализируем ключевые слова для группировки
    keyword_to_posts = {}
    
    for i, post in enumerate(posts):
        post_themes = themes.get(post['link'], [])
        for theme in post_themes[:3]:  # Берем топ-3 темы
            if theme not in keyword_to_posts:
                keyword_to_posts[theme] = []
            keyword_to_posts[theme].append(i)
    
    # Создаем кластеры из пересекающихся тем
    for theme, post_indices in keyword_to_posts.items():
        if len(post_indices) >= 2:  # Минимум 2 статьи для кластера
            clusters[theme] = post_indices
    
    return clusters


class RAGDatabaseManager:
    """Менеджер для работы с RAG-системой и векторной БД."""
    
    def __init__(self):
        self.collection_name = "articles"
    
    async def create_article_embeddings(self, domain: str, posts: List[Dict]) -> None:
        """Создает эмбеддинги для статей и сохраняет в векторную БД."""
        if not embedding_model or not chroma_client:
            print("❌ RAG-система не инициализирована")
            return
            
        print(f"🔮 Создание эмбеддингов для {len(posts)} статей...")
        
        try:
            # Получаем или создаем коллекцию
            collection = chroma_client.get_or_create_collection(
                name=f"{domain}_articles",
                metadata={"description": f"Articles from {domain}"}
            )
            
            # Очищаем старые эмбеддинги для этого домена
            existing_ids = collection.get()["ids"]
            if existing_ids:
                collection.delete(ids=existing_ids)
            
            # Создаем эмбеддинги для всех статей
            texts_to_embed = []
            metadatas = []
            ids = []
            
            async with AsyncSessionLocal() as session:
                for i, post in enumerate(posts):
                    # Подготавливаем текст для эмбеддинга
                    title = post.get('title', '')
                    content = post.get('content', '')[:500]  # Первые 500 символов
                    combined_text = f"Заголовок: {title}\n\nСодержание: {content}"
                    
                    texts_to_embed.append(combined_text)
                    metadatas.append({
                        "title": title,
                        "link": post.get('link', ''),
                        "content_snippet": content,
                        "domain": domain,
                        "post_id": i
                    })
                    ids.append(f"{domain}_{i}")
                
                # Создаем эмбеддинги батчами
                embeddings = embedding_model.encode(texts_to_embed).tolist()
                
                # Сохраняем в ChromaDB
                collection.add(
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=texts_to_embed,
                    ids=ids
                )
                
                # Также сохраняем в PostgreSQL для бэкапа
                for i, (text, embedding, metadata) in enumerate(zip(texts_to_embed, embeddings, metadatas)):
                    article_embedding = ArticleEmbedding(
                        domain=domain,
                        wp_post_id=i,
                        title=metadata["title"],
                        content_snippet=metadata["content_snippet"],
                        link=metadata["link"],
                        embedding_vector=json.dumps(embedding),
                        themes=[]  # Заполним позже
                    )
                    session.add(article_embedding)
                
                await session.commit()
                
        except Exception as e:
            print(f"❌ Ошибка создания эмбеддингов: {e}")
        
        print(f"✅ Создано {len(posts)} эмбеддингов")
    
    def semantic_search(self, domain: str, query: str, n_results: int = 5) -> List[Dict]:
        """Выполняет семантический поиск по статьям."""
        if not embedding_model or not chroma_client:
            return []
        
        try:
            collection = chroma_client.get_collection(name=f"{domain}_articles")
            
            # Создаем эмбеддинг для запроса
            query_embedding = embedding_model.encode([query]).tolist()
            
            # Ищем похожие статьи
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                include=['metadatas', 'documents', 'distances']
            )
            
            # Форматируем результаты
            articles = []
            for i in range(len(results['ids'][0])):
                articles.append({
                    'title': results['metadatas'][0][i]['title'],
                    'link': results['metadatas'][0][i]['link'],
                    'content': results['metadatas'][0][i]['content_snippet'],
                    'similarity': 1 - results['distances'][0][i]  # Преобразуем distance в similarity
                })
            
            return articles
            
        except Exception as e:
            print(f"❌ Ошибка семантического поиска: {e}")
            return []
    
    def get_all_articles(self, domain: str) -> List[Dict]:
        """Получает все статьи домена для обзора."""
        if not chroma_client:
            return []
        
        try:
            collection = chroma_client.get_collection(name=f"{domain}_articles")
            results = collection.get(include=['metadatas'])
            
            articles = []
            for metadata in results['metadatas']:
                articles.append({
                    'title': metadata['title'],
                    'link': metadata['link'],
                    'content': metadata['content_snippet']
                })
            
            return articles
            
        except Exception as e:
            print(f"❌ Ошибка получения статей: {e}")
            return []


# Глобальный экземпляр RAG-менеджера
rag_manager = RAGDatabaseManager()


# Функции-инструменты для Ollama
OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_articles",
            "description": "Поиск статей по семантическому сходству с запросом",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Домен сайта для поиска"
                    },
                    "query": {
                        "type": "string", 
                        "description": "Запрос для поиска релевантных статей"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Количество статей для возврата (по умолчанию 5)"
                    }
                },
                "required": ["domain", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_articles_overview",
            "description": "Получить обзор всех статей сайта",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Домен сайта"
                    }
                },
                "required": ["domain"]
            }
        }
    }
]


async def execute_tool_call(tool_name: str, arguments: Dict) -> str:
    """Выполняет вызов инструмента RAG-системы."""
    try:
        if tool_name == "search_articles":
            domain = arguments.get("domain")
            query = arguments.get("query") 
            count = arguments.get("count", 5)
            
            articles = rag_manager.semantic_search(domain, query, count)
            
            if not articles:
                return f"Не найдено статей по запросу '{query}' на домене {domain}"
            
            result = f"Найдено {len(articles)} статей по запросу '{query}':\n\n"
            for i, article in enumerate(articles, 1):
                result += f"{i}. {article['title']}\n"
                result += f"   Ссылка: {article['link']}\n"
                result += f"   Содержание: {article['content'][:100]}...\n"
                result += f"   Релевантность: {article['similarity']:.3f}\n\n"
            
            return result
            
        elif tool_name == "get_all_articles_overview":
            domain = arguments.get("domain")
            articles = rag_manager.get_all_articles(domain)
            
            if not articles:
                return f"Не найдено статей на домене {domain}"
            
            result = f"Обзор всех {len(articles)} статей на домене {domain}:\n\n"
            for i, article in enumerate(articles, 1):
                result += f"{i}. {article['title']}\n"
                result += f"   {article['content'][:80]}...\n\n"
            
            return result
        
        else:
            return f"Неизвестный инструмент: {tool_name}"
            
    except Exception as e:
        return f"Ошибка выполнения инструмента {tool_name}: {e}"


async def generate_links(text: str) -> list[str]:
    """Запрашивает Ollama для генерации ссылок."""
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
    """Загружает список постов с WordPress сайта и сохраняет в БД."""
    print(f"🌐 Загружаю посты с сайта {domain}")
    
    # Сначала очищаем старые посты этого домена
    async with AsyncSessionLocal() as session:
        await session.execute(
            select(WordPressPost).where(WordPressPost.domain == domain)
        )
        await session.commit()
    
    url = f"https://{domain}/wp-json/wp/v2/posts?per_page=100"  # Загружаем до 100 статей
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="Сайт недоступен или не WordPress")
    data = response.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Некорректный ответ WordPress")
    
    posts = []
    async with AsyncSessionLocal() as session:
        for item in data:
            try:
                # Извлекаем полное содержимое
                content = item.get("content", {}).get("rendered", "")
                excerpt = item.get("excerpt", {}).get("rendered", "")
                
                # Очищаем HTML
                clean_content = BeautifulSoup(content, 'html.parser').get_text()
                clean_excerpt = BeautifulSoup(excerpt, 'html.parser').get_text() if excerpt else ""
                
                # Сохраняем в БД
                wp_post = WordPressPost(
                    domain=domain,
                    wp_post_id=item["id"],
                    title=item["title"]["rendered"],
                    content=clean_content,
                    excerpt=clean_excerpt,
                    link=item["link"]
                )
                session.add(wp_post)
                
                # Для возврата берем краткую версию
                short_content = clean_content[:500] if clean_content else clean_excerpt[:500]
                posts.append({
                    "title": item["title"]["rendered"], 
                    "link": item["link"],
                    "content": short_content.strip()
                })
                
                print(f"💾 Сохранен пост: {item['title']['rendered']}")
                
            except Exception as exc:
                print(f"❌ Ошибка обработки поста {item.get('id', 'unknown')}: {exc}")
                continue
        
        await session.commit()
        print(f"✅ Сохранено {len(posts)} постов в БД")
    
    return posts


async def generate_wp_recommendations_from_db(domain: str, progress_callback=None) -> list[dict[str, str]]:
    """Получает качественные рекомендации по перелинковке с глубоким анализом содержания."""
    print(f"🔍 Запуск улучшенного анализа для домена {domain}")
    
    # Загружаем посты из БД
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(WordPressPost).where(WordPressPost.domain == domain).order_by(WordPressPost.created_at.desc())
        )
        db_posts = result.scalars().all()
    
    if not db_posts:
        print("❌ Не найдены посты в БД для анализа")
        return []
    
    print(f"📚 Найдено {len(db_posts)} постов в БД")
    
    # Ограничиваем количество статей для качественного анализа
    limited_posts = db_posts[:min(len(db_posts), 30)]  # Фокус на качестве, а не количестве
    print(f"🎯 Анализируем {len(limited_posts)} статей для максимального качества")
    
    # Подготавливаем данные для глубокого анализа
    posts_for_analysis = []
    for post in limited_posts:
        # Больше контекста для анализа
        content_preview = post.content[:1000] if post.content else post.excerpt[:1000] if post.excerpt else ""
        posts_for_analysis.append({
            "title": post.title,
            "link": post.link,
            "content": content_preview.strip(),
            "full_content": post.content  # Полный текст для детального анализа
        })
    
    # Этап 1: Глубокий анализ тем и ключевых слов
    print("🧠 Этап 1: Семантический анализ контента...")
    if progress_callback:
        progress_callback("Анализ тем и ключевых слов", 1, 4)
    
    themes = extract_key_themes(posts_for_analysis)
    similarities = calculate_content_similarity(posts_for_analysis)
    clusters = extract_semantic_clusters(posts_for_analysis, themes)
    
    print(f"📊 Найдено {len(clusters)} тематических кластеров")
    print(f"📊 Вычислено {len(similarities)} семантических связей")
    
    # Этап 2: Интеллектуальная генерация рекомендаций
    print("🤖 Этап 2: Генерация качественных рекомендаций...")
    if progress_callback:
        progress_callback("Генерация рекомендаций через ИИ", 2, 4)
    
    all_recommendations = []
    
    # Обрабатываем меньшими порциями для лучшего качества
    batch_size = 8  # Меньший размер для более детального анализа
    total_batches = min(len(limited_posts) // batch_size + 1, 5)  # Максимум 5 батчей
    
    for batch_num in range(total_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(limited_posts))
        batch_posts = limited_posts[batch_start:batch_end]
        
        if len(batch_posts) < 2:  # Нужно минимум 2 статьи для связей
            continue
        
        print(f"🔄 Обработка батча {batch_num + 1}/{total_batches}: {len(batch_posts)} статей")
        
        # Создаем расширенное описание статей для ИИ
        detailed_posts = []
        for i, post in enumerate(batch_posts):
            global_idx = batch_start + i + 1
            post_themes = themes.get(post.link, [])[:4]  # Топ-4 темы
            themes_str = ", ".join(post_themes) if post_themes else "общие темы"
            
            # Краткое содержание (первые 150 символов)
            content_snippet = post.content[:150].replace('\n', ' ').strip()
            if len(post.content) > 150:
                content_snippet += "..."
            
            detailed_posts.append({
                'index': global_idx,
                'title': post.title,
                'themes': themes_str,
                'content_snippet': content_snippet,
                'link': post.link
            })
        
        # Продвинутый промпт с детальными инструкциями
        prompt = f"""Ты - эксперт по SEO и внутренней перелинковке. Проанализируй следующие статьи и создай КАЧЕСТВЕННЫЕ рекомендации по внутренним ссылкам.

СТАТЬИ ДЛЯ АНАЛИЗА:
"""
        
        for post_data in detailed_posts:
            prompt += f"""
{post_data['index']}. "{post_data['title']}"
Ключевые темы: {post_data['themes']}
Содержание: {post_data['content_snippet']}
"""
        
        prompt += f"""

ЗАДАЧА: Создай 5-7 высококачественных рекомендаций по внутренним ссылкам между этими статьями.

ТРЕБОВАНИЯ К КАЧЕСТВУ:
- Анализируй СЕМАНТИЧЕСКУЮ СВЯЗЬ между темами статей
- Рекомендации должны быть ЛОГИЧНЫМИ и ПОЛЕЗНЫМИ для пользователя
- Анкор-текст должен быть ЕСТЕСТВЕННЫМ и информативным
- Объяснение должно содержать ДЕТАЛЬНОЕ ОБОСНОВАНИЕ связи

ФОРМАТ ОТВЕТА (строго соблюдай):
N1->N2|анкор-текст|подробное объяснение почему эта ссылка полезна и логична

ПРИМЕРЫ КАЧЕСТВЕННЫХ РЕКОМЕНДАЦИЙ:
1->3|как правильно выбрать район для покупки квартиры|Обе статьи освещают вопросы недвижимости: первая рассказывает о процессе покупки, а третья детально разбирает критерии выбора локации, что является логичным продолжением для читателя, принимающего решение о покупке
2->4|методы эффективного изучения английского языка|Тематическая связь через образовательный контент: вторая статья о самообразовании естественно ведет к конкретным методикам изучения языков, предоставляя читателю практические инструменты для реализации планов по саморазвитию

ВАЖНО: 
- НЕ создавай поверхностные связи типа "схожие темы"
- Каждое объяснение должно быть КОНКРЕТНЫМ и РАЗВЕРНУТЫМ
- Анкор должен точно описывать содержание целевой статьи
- Ссылка должна приносить РЕАЛЬНУЮ ПОЛЬЗУ читателю

АНАЛИЗИРУЙ И СОЗДАВАЙ РЕКОМЕНДАЦИИ:"""

        try:
            print(f"🤖 Отправляю детальный запрос в Ollama (батч {batch_num + 1})...")
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # Увеличили таймаут
                resp = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": OLLAMA_MODEL, 
                        "prompt": prompt, 
                        "stream": False,
                        "options": {
                            "num_ctx": 4096,        # Больше контекста для качественного анализа
                            "temperature": 0.4,     # Баланс между креативностью и точностью
                            "top_p": 0.7,          # Более разнообразные ответы
                            "repeat_penalty": 1.1,  # Избегаем повторений
                            "num_predict": 800      # Больше места для детальных объяснений
                        }
                    },
                    timeout=120,
                )
            
            if resp.status_code != 200:
                print(f"❌ Ollama вернула код {resp.status_code}, пропускаем батч")
                continue
                
            content = resp.json().get("response", "")
            print(f"🤖 Получен развернутый ответ: {len(content)} символов")
            
            # Улучшенный парсинг рекомендаций
            batch_recommendations = 0
            for line in content.splitlines():
                line = line.strip()
                if not line or "->" not in line or "|" not in line:
                    continue
                    
                try:
                    # Парсинг: N1->N2|анкор|детальное объяснение
                    parts = line.split("|", 2)
                    if len(parts) < 3:
                        continue
                        
                    link_part = parts[0].strip()
                    anchor = parts[1].strip()
                    detailed_comment = parts[2].strip()
                    
                    # Проверяем качество комментария
                    if len(detailed_comment) < 30:  # Слишком короткий комментарий
                        print(f"⚠️ Пропускаю рекомендацию с коротким комментарием: {line[:50]}...")
                        continue
                    
                    if "->" in link_part:
                        src_part, dst_part = link_part.split("->", 1)
                        
                        # Извлекаем индексы
                        src_match = re.search(r'\d+', src_part)
                        dst_match = re.search(r'\d+', dst_part)
                        
                        if src_match and dst_match:
                            src_idx = int(src_match.group())
                            dst_idx = int(dst_match.group())
                            
                            # Проверяем валидность индексов
                            src_global = src_idx - 1
                            dst_global = dst_idx - 1
                            
                            if (0 <= src_global < len(limited_posts) and 
                                0 <= dst_global < len(limited_posts) and 
                                src_global != dst_global):
                                
                                # Улучшаем анкор если нужно
                                if len(anchor) < 10:  # Слишком короткий анкор
                                    anchor = f"подробнее о {limited_posts[dst_global].title.split()[0]}"
                                
                                # Добавляем рекомендацию
                                recommendation = {
                                    "from": limited_posts[src_global].link, 
                                    "to": limited_posts[dst_global].link, 
                                    "anchor": anchor,
                                    "comment": detailed_comment
                                }
                                
                                all_recommendations.append(recommendation)
                                batch_recommendations += 1
                                print(f"✅ Качественная рекомендация {len(all_recommendations)}: {src_idx}->{dst_idx}")
                                print(f"   Анкор: {anchor[:50]}...")
                                print(f"   Обоснование: {detailed_comment[:100]}...")
                        
                except Exception as parse_error:
                    print(f"❌ Ошибка парсинга: {parse_error}")
                    continue
            
            print(f"📊 Батч {batch_num + 1} завершен: добавлено {batch_recommendations} качественных рекомендаций")
            
            # Пауза для разгрузки Ollama
            if batch_num < total_batches - 1:
                print("⏳ Пауза 4 секунды для качественной обработки...")
                await asyncio.sleep(4)
                    
        except Exception as e:
            print(f"❌ Ошибка обработки батча {batch_num + 1}: {e}")
            continue
    
    # Этап 3: Постобработка и улучшение рекомендаций
    print("🔧 Этап 3: Постобработка и фильтрация...")
    if progress_callback:
        progress_callback("Постобработка рекомендаций", 3, 4)
    
    # Фильтруем дубликаты и низкокачественные рекомендации
    unique_recommendations = []
    seen_pairs = set()
    
    for rec in all_recommendations:
        pair_key = (rec["from"], rec["to"])
        if pair_key not in seen_pairs:
            # Проверяем качество
            if (len(rec["anchor"]) >= 10 and 
                len(rec["comment"]) >= 30 and
                "схожие темы" not in rec["comment"].lower() and
                "общие темы" not in rec["comment"].lower()):
                
                unique_recommendations.append(rec)
                seen_pairs.add(pair_key)
    
    # Этап 4: Финализация
    print("🎯 Этап 4: Финализация результатов...")
    if progress_callback:
        progress_callback("Финализация", 4, 4)
    
    # Ограничиваем количество для поддержания качества
    final_recommendations = unique_recommendations[:50] 
    
    print(f"🎉 Создано {len(final_recommendations)} высококачественных рекомендаций")
    print(f"📊 Средняя длина объяснения: {sum(len(r['comment']) for r in final_recommendations) // len(final_recommendations) if final_recommendations else 0} символов")
    
    return final_recommendations


async def generate_wp_recommendations_with_rag(domain: str, progress_callback=None) -> list[dict[str, str]]:
    """Генерирует рекомендации используя RAG-систему с прямым доступом Ollama к БД."""
    print(f"🤖 Запуск RAG-анализа для домена {domain}")
    
    if progress_callback:
        progress_callback("Инициализация RAG-системы", 1, 6)
    
    # Загружаем посты из БД
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(WordPressPost).where(WordPressPost.domain == domain).order_by(WordPressPost.created_at.desc())
        )
        db_posts = result.scalars().all()
    
    if not db_posts:
        print("❌ Не найдены посты в БД для RAG-анализа")
        return []
    
    print(f"📚 Найдено {len(db_posts)} постов для RAG-анализа")
    
    # Преобразуем в формат для эмбеддингов
    posts_for_rag = []
    for post in db_posts:
        posts_for_rag.append({
            "title": post.title,
            "link": post.link,
            "content": post.content[:1000]  # Больше контекста для RAG
        })
    
    # Этап 1: Создаем эмбеддинги
    if progress_callback:
        progress_callback("Создание векторных эмбеддингов", 2, 6)
    
    await rag_manager.create_article_embeddings(domain, posts_for_rag)
    
    # Этап 2: Интеллектуальный анализ с использованием RAG
    if progress_callback:
        progress_callback("Анализ через RAG-систему", 3, 6)
    
    print("🧠 Запуск интеллектуального анализа с RAG...")
    
    # Создаем мастер-промпт для Ollama с доступом к инструментам
    master_prompt = f"""Ты - эксперт по SEO и внутренней перелинковке с доступом к векторной базе данных статей сайта {domain}.

У тебя есть следующие инструменты для работы с базой данных:
1. search_articles - поиск статей по семантическому сходству
2. get_all_articles_overview - получение обзора всех статей

ЗАДАЧА: Проанализируй все статьи сайта {domain} и создай высококачественные рекомендации по внутренним ссылкам.

ПЛАН ДЕЙСТВИЙ:
1. Сначала получи обзор всех статей сайта
2. Определи основные тематические кластеры
3. Для каждого кластера найди статьи, которые логично связать между собой
4. Создай детальные рекомендации с обоснованиями

Начни с получения обзора всех статей сайта {domain}."""

    try:
        if progress_callback:
            progress_callback("Инициализация диалога с Ollama", 4, 6)
        
        print("🤖 Запуск RAG-диалога с Ollama...")
        
        # Используем Ollama Python клиент для работы с инструментами
        messages = [
            {
                "role": "system",
                "content": "Ты эксперт по SEO с доступом к инструментам поиска в базе данных статей."
            },
            {
                "role": "user", 
                "content": master_prompt
            }
        ]
        
        all_recommendations = []
        conversation_steps = 0
        max_steps = 5  # Максимум итераций диалога
        
        while conversation_steps < max_steps:
            if progress_callback:
                progress_callback(f"RAG-диалог: шаг {conversation_steps + 1}", 4 + conversation_steps, 6)
            
            print(f"🔄 RAG-диалог: шаг {conversation_steps + 1}")
            
            # Отправляем запрос в Ollama
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                tools=OLLAMA_TOOLS if conversation_steps == 0 else None,  # Инструменты только на первом шаге
                options={
                    "temperature": 0.4,
                    "num_ctx": 8192,  # Большой контекст для RAG
                    "num_predict": 1000
                }
            )
            
            assistant_message = response['message']
            messages.append(assistant_message)
            
            # Проверяем, есть ли вызовы инструментов
            if 'tool_calls' in assistant_message:
                print(f"🔧 Обнаружены вызовы инструментов: {len(assistant_message['tool_calls'])}")
                
                for tool_call in assistant_message['tool_calls']:
                    tool_name = tool_call['function']['name']
                    arguments = tool_call['function']['arguments']
                    
                    print(f"📞 Вызов инструмента: {tool_name} с аргументами: {arguments}")
                    
                    # Выполняем вызов инструмента
                    tool_result = await execute_tool_call(tool_name, arguments)
                    
                    # Добавляем результат в диалог
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call.get('id', 'tool_1')
                    })
                
                # Продолжаем диалог после использования инструментов
                if conversation_steps == 0:
                    messages.append({
                        "role": "user",
                        "content": """Отлично! Теперь проанализируй статьи и создай 15-20 качественных рекомендаций по внутренним ссылкам.

Формат ответа:
ССЫЛКА_ИСТОЧНИК -> ССЫЛКА_ЦЕЛЬ | анкор-текст | детальное обоснование

Требования:
- Анкор должен быть естественным и информативным
- Обоснование должно объяснять, почему эта связь логична и полезна для пользователя
- Минимум 50 символов в обосновании
- Никаких общих фраз типа "схожие темы" или "связанные статьи\""""
                    })
            
            else:
                # Если нет вызовов инструментов, парсим рекомендации
                content = assistant_message.get('content', '')
                print(f"📝 Получен ответ: {len(content)} символов")
                
                # Парсим рекомендации из ответа
                recommendations = parse_rag_recommendations(content, posts_for_rag)
                all_recommendations.extend(recommendations)
                
                if recommendations:
                    print(f"✅ Извлечено {len(recommendations)} рекомендаций из RAG-ответа")
                
                # Если получили рекомендации, можем завершить
                if len(all_recommendations) >= 10:
                    break
            
            conversation_steps += 1
        
        # Этап 3: Постобработка RAG-рекомендаций
        if progress_callback:
            progress_callback("Постобработка RAG-рекомендаций", 6, 6)
        
        print("🔧 Постобработка RAG-рекомендаций...")
        
        # Убираем дубликаты и фильтруем по качеству
        unique_recommendations = []
        seen_pairs = set()
        
        for rec in all_recommendations:
            pair_key = (rec["from"], rec["to"])
            if pair_key not in seen_pairs and len(rec["comment"]) >= 30:
                unique_recommendations.append(rec)
                seen_pairs.add(pair_key)
        
        print(f"🎉 RAG-анализ завершен: {len(unique_recommendations)} уникальных рекомендаций")
        return unique_recommendations[:30]  # Топ-30 рекомендаций
        
    except Exception as e:
        print(f"❌ Ошибка RAG-анализа: {e}")
        # Откатываемся к обычному методу
        return await generate_wp_recommendations_from_db(domain, progress_callback)


def parse_rag_recommendations(text: str, posts: List[Dict]) -> List[Dict]:
    """Парсит рекомендации из RAG-ответа Ollama."""
    recommendations = []
    
    # Создаем словарь для быстрого поиска статей по заголовкам
    title_to_link = {}
    for post in posts:
        title_to_link[post['title'].lower()] = post['link']
    
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        
        # Ищем строки с рекомендациями
        if '->' in line and '|' in line:
            try:
                # Парсим формат: URL1 -> URL2 | анкор | обоснование
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    link_part = parts[0].strip()
                    anchor = parts[1].strip()
                    comment = parts[2].strip()
                    
                    if '->' in link_part:
                        source_part, target_part = link_part.split('->', 1)
                        source = source_part.strip()
                        target = target_part.strip()
                        
                        # Пытаемся найти полные URL или заголовки
                        source_url = find_article_url(source, title_to_link, posts)
                        target_url = find_article_url(target, title_to_link, posts)
                        
                        if source_url and target_url and source_url != target_url:
                            recommendations.append({
                                "from": source_url,
                                "to": target_url,
                                "anchor": anchor,
                                "comment": comment
                            })
                            
            except Exception as e:
                print(f"❌ Ошибка парсинга RAG-строки '{line}': {e}")
                continue
    
    return recommendations


def find_article_url(text: str, title_to_link: Dict, posts: List[Dict]) -> Optional[str]:
    """Находит URL статьи по тексту (заголовку или частичному совпадению)."""
    text_lower = text.lower().strip()
    
    # Если это уже URL
    if text.startswith('http'):
        return text
    
    # Поиск по точному совпадению заголовка
    if text_lower in title_to_link:
        return title_to_link[text_lower]
    
    # Поиск по частичному совпадению
    for title, link in title_to_link.items():
        if text_lower in title or title in text_lower:
            return link
    
    # Поиск по ключевым словам
    text_words = text_lower.split()
    for post in posts:
        title_words = post['title'].lower().split()
        if len(set(text_words) & set(title_words)) >= 2:  # Минимум 2 общих слова
            return post['link']
    
    return None


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
    """Возвращает рекомендации ссылок от Ollama и сохраняет их."""
    links = await generate_links(req.text)

    async with AsyncSessionLocal() as session:
        rec = Recommendation(text=req.text, links=links)
        session.add(rec)
        await session.commit()
    return {"links": links}


@app.post("/api/v1/wp_recommend")
async def wp_recommend(req: WPRequest) -> dict[str, list[dict[str, str]]]:
    """Анализирует WordPress-сайт и выдает рекомендации по перелинковке."""
    # Этап 1: Загружаем и сохраняем посты в БД
    posts = await fetch_and_store_wp_posts(req.domain)
    
    # Этап 2: Генерируем рекомендации используя данные из БД
    recs = await generate_wp_recommendations_from_db(req.domain)
    
    # Этап 3: Сохраняем историю анализа
    summary = f"Проанализирован сайт {req.domain}: найдено {len(posts)} статей, создано {len(recs)} рекомендаций"
    
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
    
    return {"recommendations": recs}


@app.post("/api/v1/wp_recommend_rag")
async def wp_recommend_rag(req: WPRequest) -> dict[str, list[dict[str, str]]]:
    """RAG-анализ WordPress-сайта с прямым доступом Ollama к векторной БД."""
    # Этап 1: Загружаем и сохраняем посты в БД  
    posts = await fetch_and_store_wp_posts(req.domain)
    
    # Этап 2: Генерируем рекомендации через RAG-систему
    recs = await generate_wp_recommendations_with_rag(req.domain)
    
    # Этап 3: Сохраняем историю RAG-анализа
    summary = f"RAG-анализ сайта {req.domain}: найдено {len(posts)} статей, создано {len(recs)} RAG-рекомендаций"
    
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
    
    return {"recommendations": recs}


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


@app.get("/")
async def root():
    """Редирект на фронтенд."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:3000")


# Убираем StaticFiles mount так как фронтенд теперь на отдельном порту
