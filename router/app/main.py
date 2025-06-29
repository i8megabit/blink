"""
router - Микросервис reLink
LLM Router - интеллектуальная маршрутизация запросов к оптимальным моделям
"""

from fastapi import FastAPI
from bootstrap.main import create_app, add_service_routes
from bootstrap.config import get_settings

# Создание приложения с бутстрапом
app = create_app(
    title="router",
    description="LLM Router - интеллектуальная маршрутизация запросов к оптимальным моделям",
    version="1.0.0"
)

# Добавление роутов сервиса
from app.api import router
add_service_routes(app, router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8004,
        reload=settings.DEBUG
    )
