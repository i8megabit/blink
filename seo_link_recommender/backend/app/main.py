"""FastAPI-приложение для генерации внутренних ссылок."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import Integer, Text, JSON, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

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


async def fetch_wp_posts(domain: str) -> list[dict[str, str]]:
    """Загружает список постов с WordPress сайта с содержимым."""
    url = f"https://{domain}/wp-json/wp/v2/posts?per_page=6"  # Еще меньше постов
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
    if response.status_code >= 400:
        raise HTTPException(status_code=400, detail="Сайт недоступен или не WordPress")
    data = response.json()
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Некорректный ответ WordPress")
    posts = []
    for item in data:
        try:
            # Берем только заголовок - без содержимого для минимизации промпта
            posts.append({
                "title": item["title"]["rendered"], 
                "link": item["link"]
            })
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Не удалось разобрать данные") from exc
    return posts


async def generate_wp_recommendations(posts: list[dict[str, str]]) -> list[dict[str, str]]:
    """Получает рекомендации по перелинковке статей через Ollama с максимальной оптимизацией."""
    print(f"🔍 Генерация рекомендаций для {len(posts)} постов")
    
    # Обрабатываем все посты за один раз, но с минимальным промптом
    
    # Создаем максимально компактный список
    listing = "\n".join(f"{i+1}. {p['title']}" for i, p in enumerate(posts))
    print(f"📝 Список статей:\n{listing}")
    
    # Супер-компактный промпт с четкими инструкциями
    prompt = f"""Статьи о переезде:
{listing}

Создай 8 внутренних ссылок между статьями. Формат: НОМЕР1 -> НОМЕР2 | анкор_на_русском

Примеры:
1 -> 3 | сравнение городов для переезда
2 -> 5 | подробнее о переезде
4 -> 1 | обзор города

Твои ссылки:"""

    print(f"🤖 Отправляю промпт в Ollama: {prompt[:200]}...")

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL, 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {
                        "num_batch": 32,      # Еще меньше batch
                        "num_ctx": 2048,      # Минимальный контекст
                        "temperature": 0.3,   # Меньше креативности
                        "top_p": 0.5,         # Более фокусированные ответы
                        "repeat_penalty": 1.1
                    }
                },
                timeout=90,
            )
        resp.raise_for_status()
        content = resp.json().get("response", "")
        print(f"🤖 Ответ Ollama: {content}")
        
        recommendations = []
        for line in content.splitlines():
            if "->" not in line:
                continue
            try:
                src_part, rest = line.split("->", 1)
                if "|" in rest:
                    dst_part, anchor = rest.split("|", 1)
                else:
                    dst_part, anchor = rest, ""
                
                # Очищаем от лишних символов (точки, пробелы)
                src_clean = src_part.strip().rstrip('.')
                dst_clean = dst_part.strip().rstrip('.')
                
                # Извлекаем только числа
                import re
                src_match = re.search(r'\d+', src_clean)
                dst_match = re.search(r'\d+', dst_clean)
                
                if src_match and dst_match:
                    src_num = int(src_match.group()) - 1
                    dst_num = int(dst_match.group()) - 1
                    
                    if 0 <= src_num < len(posts) and 0 <= dst_num < len(posts) and src_num != dst_num:
                        recommendations.append({
                            "from": posts[src_num]['link'], 
                            "to": posts[dst_num]['link'], 
                            "anchor": anchor.strip().strip('"')
                        })
                        print(f"✅ Добавлена рекомендация: {posts[src_num]['link']} -> {posts[dst_num]['link']}")
                else:
                    print(f"❌ Не найдены номера в строке: '{line}'")
            except (ValueError, IndexError) as e:
                print(f"❌ Ошибка парсинга строки '{line}': {e}")
                continue
                
    except Exception as e:
        print(f"❌ Ошибка генерации рекомендаций: {e}")
        # Возвращаем хотя бы базовые рекомендации
        recommendations = []
        for i in range(min(5, len(posts)-1)):
            recommendations.append({
                "from": posts[i]['link'],
                "to": posts[i+1]['link'], 
                "anchor": f"читать далее о {posts[i+1]['title'][:30]}..."
            })
    
    print(f"📊 Итого сгенерировано {len(recommendations)} рекомендаций")
    return recommendations[:15]  # Ограничиваем до 15 рекомендаций


@app.on_event("startup")
async def on_startup() -> None:
    """Создает таблицы при запуске."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
    posts = await fetch_wp_posts(req.domain)
    recs = await generate_wp_recommendations(posts)
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


@app.get("/")
async def root():
    """Редирект на фронтенд."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:3000")


# Убираем StaticFiles mount так как фронтенд теперь на отдельном порту
