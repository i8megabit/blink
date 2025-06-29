"""
🗄️ Подключение к базе данных для всех микросервисов
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import structlog

from .config import get_settings

logger = structlog.get_logger()

# Базовый класс для моделей
Base = declarative_base()

# Глобальные переменные
_engine: Optional[create_async_engine] = None
_sessionmaker: Optional[async_sessionmaker] = None

def get_database_engine():
    """Получение движка базы данных"""
    global _engine
    
    if _engine is None:
        settings = get_settings()
        
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        
        logger.info("Database engine created", url=settings.DATABASE_URL)
    
    return _engine

def get_sessionmaker():
    """Получение фабрики сессий"""
    global _sessionmaker
    
    if _sessionmaker is None:
        engine = get_database_engine()
        _sessionmaker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Session maker created")
    
    return _sessionmaker

async def get_database() -> AsyncSession:
    """Получение сессии базы данных"""
    session_maker = get_sessionmaker()
    
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()

async def init_database():
    """Инициализация базы данных"""
    engine = get_database_engine()
    
    async with engine.begin() as conn:
        # Создание всех таблиц
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized")

async def close_database():
    """Закрытие соединений с базой данных"""
    global _engine, _sessionmaker
    
    if _engine:
        await _engine.dispose()
        _engine = None
    
    _sessionmaker = None
    
    logger.info("Database connections closed") 