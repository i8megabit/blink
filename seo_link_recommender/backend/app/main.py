"""FastAPI-приложение для генерации внутренних ссылок."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class RecommendRequest(BaseModel):
    """Запрос с текстом для генерации ссылок."""

    text: str


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


async def generate_links(text: str) -> list[str]:
    """Запрашивает Ollama для генерации ссылок."""
    prompt = (
        "Предложи до пяти внутренних ссылок для следующего текста. "
        "Выведи каждый URL с новой строки без лишних символов: "
        f"{text}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=30,
        )
    response.raise_for_status()
    data = response.json()
    lines = [line.strip("- \n") for line in data.get("response", "").splitlines()]
    return [line for line in lines if line]


@app.post("/api/v1/recommend")
async def recommend(req: RecommendRequest) -> dict[str, list[str]]:
    """Возвращает рекомендации ссылок от Ollama."""
    try:
        links = await generate_links(req.text)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"links": links}


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Проверка работоспособности."""
    return {"status": "ok"}


frontend_path = Path(__file__).resolve().parents[2] / "frontend"
if frontend_path.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_path), html=True),
        name="frontend",
    )
