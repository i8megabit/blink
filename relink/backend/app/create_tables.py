#!/usr/bin/env python3
"""
Скрипт для создания таблиц в базе данных
"""

import asyncio
import os

# Устанавливаем переменные окружения
os.environ['DB_PASSWORD'] = 'G7p!x2Qw9z$Lk8vR3s@T1uY6b#N4eW5c'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'relink_db'
os.environ['DB_USER'] = 'postgres'

async def create_tables():
    """Создаёт все таблицы в базе данных"""
    try:
        from database import engine
        from models import Base
        
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