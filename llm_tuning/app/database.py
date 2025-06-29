"""
Настройка базы данных для LLM Tuning микросервиса
Обеспечивает асинхронное подключение к PostgreSQL
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from .config import settings

logger = logging.getLogger(__name__)

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем асинхронный движок базы данных
engine = create_async_engine(
    getattr(settings, 'DATABASE_URL', None) or settings.database.url,
    echo=settings.debug,
    poolclass=NullPool if getattr(settings, 'is_testing', lambda: False)() else None,
    pool_size=getattr(settings, 'DB_POOL_SIZE', 20),
    max_overflow=getattr(settings, 'DB_MAX_OVERFLOW', 40),
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии базы данных
    Используется в FastAPI для внедрения зависимостей
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка в сессии БД: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Инициализация базы данных"""
    try:
        # Создаем все таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("База данных инициализирована успешно")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")
        raise


async def close_db():
    """Закрытие соединений с базой данных"""
    try:
        await engine.dispose()
        logger.info("Соединения с БД закрыты")
    except Exception as e:
        logger.error(f"Ошибка при закрытии БД: {e}")


async def check_db_connection() -> bool:
    """Проверка подключения к базе данных"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return False


async def get_db_stats() -> dict:
    """Получение статистики базы данных"""
    try:
        async with AsyncSessionLocal() as session:
            # Получаем количество записей в основных таблицах
            from .models import LLMModel, ModelRoute, TuningSession, PerformanceMetrics
            
            models_count = await session.scalar(
                "SELECT COUNT(*) FROM llm_models"
            )
            routes_count = await session.scalar(
                "SELECT COUNT(*) FROM model_routes"
            )
            sessions_count = await session.scalar(
                "SELECT COUNT(*) FROM tuning_sessions"
            )
            metrics_count = await session.scalar(
                "SELECT COUNT(*) FROM performance_metrics"
            )
            
            return {
                "models_count": models_count or 0,
                "routes_count": routes_count or 0,
                "sessions_count": sessions_count or 0,
                "metrics_count": metrics_count or 0,
                "status": "connected"
            }
            
    except Exception as e:
        logger.error(f"Ошибка при получении статистики БД: {e}")
        return {
            "status": "error",
            "error": str(e)
        } 