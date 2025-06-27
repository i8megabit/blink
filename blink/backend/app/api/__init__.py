"""API модуль для приложения."""

from fastapi import APIRouter
from .auth import router as auth_router

# Создание основного API роутера
api_router = APIRouter(prefix="/api/v1")

# Подключение роутеров
api_router.include_router(auth_router) 