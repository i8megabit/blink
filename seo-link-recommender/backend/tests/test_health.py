import sys
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport

sys.path.append(str(Path(__file__).resolve().parents[1] / "app"))
from main import app


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
