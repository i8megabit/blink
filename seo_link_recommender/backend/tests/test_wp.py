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
async def test_wp_recommend() -> None:
    domain = "example.com"
    respx.get("https://example.com/wp-json/wp/v2/posts?per_page=100").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"title": {"rendered": "Post1"}, "link": "https://example.com/post1"},
                {"title": {"rendered": "Post2"}, "link": "https://example.com/post2"},
            ],
        )
    )
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(
            200,
            json={"response": "https://example.com/post1 -> https://example.com/post2 | anchor"},
        )
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/wp_recommend", json={"domain": domain})
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommendations"][0]["from"] == "https://example.com/post1"

