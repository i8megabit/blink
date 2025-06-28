#!/usr/bin/env python3
"""
Скрипт для создания таблиц в базе данных
"""

import asyncio

async def create_tables():
    """Создаёт все таблицы в базе данных"""
    try:
        from app.database import engine
        from app.models import Base
        
        print("Создаю таблицы в базе данных...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Таблицы созданы успешно!")
        
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_tables()) 