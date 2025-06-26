"""Простое приложение FastAPI с эндпоинтом проверки состояния."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Проверка работоспособности."""
    return {"status": "ok"}
