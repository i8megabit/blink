import os
import importlib
import pytest
import respx
import httpx
from httpx import AsyncClient, ASGITransport

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
if os.path.exists("test.db"):
    os.remove("test.db")

# Исправляем импорт для локального запуска
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.app import main
importlib.reload(main)
app = main.app
import asyncio
asyncio.get_event_loop().run_until_complete(main.on_startup())

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
