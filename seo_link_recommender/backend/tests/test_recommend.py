import pytest
import respx
import httpx
from httpx import AsyncClient, ASGITransport

from seo_link_recommender.backend.app.main import app


@pytest.mark.asyncio
@respx.mock
async def test_recommend() -> None:
    respx.post("http://localhost:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "- https://a.ru\n- https://b.ru"})
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/recommend", json={"text": "test"})
    assert response.status_code == 200
    assert response.json() == {"links": ["https://a.ru", "https://b.ru"]}
