import os
import importlib
import pytest
import respx
import httpx
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
import json
import sys
import asyncio

# Настройка тестового окружения
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["OLLAMA_URL"] = "http://localhost:11434"
os.environ["SECRET_KEY"] = "test-secret-key"

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.main import app


@pytest.mark.asyncio
@respx.mock
async def test_wp_index() -> None:
    domain = "example.com"
    respx.get("https://example.com/wp-json/wp/v2/posts?per_page=50").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 1, "title": {"rendered": "Post1"}, "link": "https://example.com/post1", "content": {"rendered": "content1"}},
                {"id": 2, "title": {"rendered": "Post2"}, "link": "https://example.com/post2", "content": {"rendered": "content2"}},
            ],
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/wp_index", json={"domain": domain})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["domain"] == domain

