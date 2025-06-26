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
    content = data.get("response", "").strip()
    
    # Парсим ссылки из ответа
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    links = []
    for line in lines:
        # Извлекаем URL если есть в строке
        if line.startswith('/'):
            links.append(line.split()[0])
        elif '/article/' in line or '/articles/' in line:
            # Ищем ссылки в тексте
            parts = line.split()
            for part in parts:
                if part.startswith('/'):
                    links.append(part)
                    break
    
    return links[:5] if links else [f"/articles/{word}" for word in text.lower().split()[:3] if len(word) > 3]


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
