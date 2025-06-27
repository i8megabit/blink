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
        response = await ac.post("/api/v1/wp_index", json={"domain": domain})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["domain"] == domain
