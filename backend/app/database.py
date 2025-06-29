"""
Модуль для работы с базой данных
Поддерживает асинхронные операции с SQLAlchemy
"""

import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData
import logging
import inspect

from .config import get_settings

logger = logging.getLogger(__name__)

# Базовый URL для подключения к базе данных
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/relink_db"
)

# Создание асинхронного движка
def get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database.url or DEFAULT_DATABASE_URL,
        echo=settings.database.echo,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

engine = get_engine()

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Базовый класс для моделей
Base = declarative_base()

# Метаданные для управления схемой
metadata = MetaData()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения асинхронной сессии базы данных
    Используется в FastAPI endpoints
    """
    stack = inspect.stack()
    caller = stack[1]
    print(f"[DEBUG get_db] Called from: {caller.filename}:{caller.lineno} - {caller.function}")
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Инициализация базы данных - создание всех таблиц"""
    try:
        async with engine.begin() as conn:
            # Создание всех таблиц
            await conn.run_sync(Base.metadata.create_all)
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise


async def close_db():
    """Закрытие соединений с базой данных"""
    try:
        await engine.dispose()
        logger.info("Соединения с базой данных закрыты")
    except Exception as e:
        logger.error(f"Ошибка закрытия соединений с БД: {e}")
        raise


async def check_db_connection() -> bool:
    """Проверка подключения к базе данных"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return False


async def get_db_info() -> dict:
    """Получение информации о базе данных"""
    try:
        async with AsyncSessionLocal() as session:
            # Получение версии PostgreSQL
            result = await session.execute("SELECT version()")
            version = result.scalar()
            
            # Получение количества таблиц
            result = await session.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = result.scalar()
            
            return {
                "status": "connected",
                "version": version,
                "table_count": table_count,
                "url": settings.database.url.replace(settings.database.password, "***") if settings.database.password else settings.database.url
            }
    except Exception as e:
        logger.error(f"Ошибка получения информации о БД: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# Утилиты для работы с транзакциями
class DatabaseTransaction:
    """Контекстный менеджер для транзакций"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._transaction = None
    
    async def __aenter__(self):
        self._transaction = await self.session.begin()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self._transaction.rollback()
            logger.error(f"Транзакция откачена: {exc_val}")
        else:
            await self._transaction.commit()
            logger.debug("Транзакция зафиксирована")


async def execute_in_transaction(session: AsyncSession, operation):
    """
    Выполнение операции в транзакции
    Автоматический rollback при ошибке
    """
    async with DatabaseTransaction(session):
        return await operation(session)


# Утилиты для миграций
async def create_tables():
    """Создание всех таблиц"""
    await init_db()


async def drop_tables():
    """Удаление всех таблиц (только для разработки!)"""
    if settings.is_production():
        raise ValueError("Удаление таблиц запрещено в продакшене!")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Все таблицы удалены")
    except Exception as e:
        logger.error(f"Ошибка удаления таблиц: {e}")
        raise


# Утилиты для тестирования
async def reset_test_db():
    """Сброс тестовой базы данных"""
    if not settings.is_testing():
        raise ValueError("Сброс БД разрешен только в тестовой среде!")
    
    try:
        await drop_tables()
        await create_tables()
        logger.info("Тестовая база данных сброшена")
    except Exception as e:
        logger.error(f"Ошибка сброса тестовой БД: {e}")
        raise


# Экспорт для обратной совместимости
RelinkDatabase = {
    "get_db": get_db,
    "init_db": init_db,
    "close_db": close_db,
    "check_db_connection": check_db_connection,
    "get_db_info": get_db_info,
    "create_tables": create_tables,
    "drop_tables": drop_tables,
    "reset_test_db": reset_test_db,
}

# Функции для работы с пользователями
async def get_user_by_username(session: AsyncSession, username: str):
    """Получение пользователя по имени пользователя."""
    from .models import User
    from sqlalchemy import select
    
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_email(session: AsyncSession, email: str):
    """Получение пользователя по email."""
    from .models import User
    from sqlalchemy import select
    
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, username: str, email: str, hashed_password: str, full_name: str = None):
    """Создание нового пользователя."""
    from .models import User
    
    logger.info(f"Creating user: {username} with full_name: {full_name}")
    
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    logger.info(f"User {username} created with ID: {user.id}")
    
    return user

# Функции для работы с доменами
async def get_domains_by_user(session: AsyncSession, user_id: int):
    """Получение доменов пользователя."""
    from .models import Domain
    from sqlalchemy import select
    
    result = await session.execute(
        select(Domain).where(Domain.owner_id == user_id, Domain.is_active == True)
    )
    return result.scalars().all()

async def create_domain(session: AsyncSession, name: str, display_name: str, owner_id: int, description: str = None):
    """Создание нового домена."""
    from .models import Domain
    
    domain = Domain(
        name=name,
        display_name=display_name,
        owner_id=owner_id,
        description=description
    )
    session.add(domain)
    await session.commit()
    await session.refresh(domain)
    return domain 