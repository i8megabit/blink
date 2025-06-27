"""Модуль для работы с базой данных."""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .models import Base

# Конфигурация базы данных
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/blink_db"
)

# Создание асинхронного движка
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Логирование SQL запросов
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Создание фабрики сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии базы данных."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """Инициализация базы данных."""
    async with engine.begin() as conn:
        # Создание всех таблиц
        await conn.run_sync(Base.metadata.create_all)
        print("✅ База данных инициализирована")

async def close_db() -> None:
    """Закрытие соединений с базой данных."""
    await engine.dispose()
    print("🔌 Соединения с базой данных закрыты")

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
    
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
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