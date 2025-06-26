from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_links_endpoint():
    payload = {
        "text": "",
        "pages": [
            {"title": "Page1", "url": "/1", "keywords": ["a"]},
            {"title": "Page2", "url": "/2", "keywords": ["b"]},
        ],
        "target_keywords": ["a"],
        "max_links": 1,
    }
    response = client.post("/api/v1/links/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["links"]) == 1
