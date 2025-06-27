#!/usr/bin/env python3
"""
Скрипт для создания первой миграции Alembic
"""

# Устанавливаем переменные окружения ДО любых импортов
import os
os.environ['DB_PASSWORD'] = 'G7p!x2Qw9z$Lk8vR3s@T1uY6b#N4eW5c'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'relink_db'
os.environ['DB_USER'] = 'postgres'

import sys
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_settings():
    """Тестирует загрузку настроек"""
    try:
        from app.config import get_settings, reload_settings
        # Очищаем кэш настроек
        reload_settings()
        settings = get_settings()
        print(f"DB URL: {settings.database.sync_url}")
        print(f"DB Password: {settings.database.password}")
        return True
    except Exception as e:
        print(f"Ошибка загрузки настроек: {e}")
        return False

def create_migration():
    """Создаёт первую миграцию"""
    try:
        # Сначала тестируем настройки
        if not test_settings():
            return
        
        from alembic import command
        from alembic.config import Config
        
        # Создаём конфигурацию Alembic
        alembic_cfg = Config("alembic.ini")
        
        # Создаём миграцию
        print("Создаю миграцию...")
        command.revision(alembic_cfg, autogenerate=True, message="Initial migration")
        
        print("Миграция создана успешно!")
        
    except Exception as e:
        print(f"Ошибка при создании миграции: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_migration() 