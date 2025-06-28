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
async def test_analysis_history() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Проверяем историю анализов
        resp = await ac.get("/api/v1/analysis_history")
    assert resp.status_code == 200
    data = resp.json()
    assert "history" in data
    assert isinstance(data["history"], list)
