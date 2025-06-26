import os
import importlib
import pytest
import respx
import httpx
from httpx import AsyncClient, ASGITransport

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
if os.path.exists("test.db"):
    os.remove("test.db")
from seo_link_recommender.backend.app import main
importlib.reload(main)
app = main.app
import asyncio
asyncio.get_event_loop().run_until_complete(main.on_startup())

@pytest.mark.asyncio
@respx.mock
async def test_history() -> None:
    transport = ASGITransport(app=app)
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "- https://a.ru"})
    )
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # insert a record
        await ac.post("/api/v1/recommend", json={"text": "text"})
        # fetch history
        resp = await ac.get("/api/v1/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["text"] == "text"
