"""
Модуль для работы с базой данных микросервиса тестирования reLink.
Поддерживает PostgreSQL для основных данных и Redis для кэширования.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import json
import uuid

from .config import settings

logger = logging.getLogger(__name__)

# Базовый класс для SQLAlchemy моделей
Base = declarative_base()

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.redis_client = None
        self._connection_pool = None
    
    async def initialize(self):
        """Инициализация подключений к базам данных"""
        try:
            # Инициализация PostgreSQL
            if settings.DATABASE_URL:
                self.engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DEBUG,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_pre_ping=True
                )
                
                self.session_factory = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                
                # Создание таблиц
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                
                logger.info("✅ PostgreSQL подключение установлено")
            
            # Инициализация Redis
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=settings.REDIS_MAX_CONNECTIONS
                )
                
                # Проверка подключения
                await self.redis_client.ping()
                logger.info("✅ Redis подключение установлено")
            
            # Инициализация пула подключений для asyncpg (для сложных запросов)
            if settings.DATABASE_URL:
                self._connection_pool = await asyncpg.create_pool(
                    settings.DATABASE_URL,
                    min_size=5,
                    max_size=20
                )
                logger.info("✅ Пул подключений asyncpg создан")
                
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    async def close(self):
        """Закрытие подключений к базам данных"""
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("🔌 PostgreSQL подключение закрыто")
            
            if self.redis_client:
                await self.redis_client.close()
                logger.info("🔌 Redis подключение закрыто")
            
            if self._connection_pool:
                await self._connection_pool.close()
                logger.info("🔌 Пул подключений asyncpg закрыт")
                
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия подключений: {e}")
    
    @asynccontextmanager
    async def get_session(self):
        """Получение сессии базы данных"""
        if not self.session_factory:
            raise RuntimeError("База данных не инициализирована")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Выполнение SQL запроса через asyncpg"""
        if not self._connection_pool:
            raise RuntimeError("Пул подключений не инициализирован")
        
        async with self._connection_pool.acquire() as conn:
            try:
                if params:
                    result = await conn.fetch(query, **params)
                else:
                    result = await conn.fetch(query)
                
                return [dict(row) for row in result]
            except Exception as e:
                logger.error(f"Ошибка выполнения запроса: {e}")
                raise
    
    async def execute_transaction(self, queries: List[Dict]) -> List[Any]:
        """Выполнение транзакции с несколькими запросами"""
        if not self._connection_pool:
            raise RuntimeError("Пул подключений не инициализирован")
        
        async with self._connection_pool.acquire() as conn:
            async with conn.transaction():
                results = []
                for query_data in queries:
                    query = query_data["query"]
                    params = query_data.get("params", {})
                    
                    if query.strip().upper().startswith("SELECT"):
                        result = await conn.fetch(query, **params)
                        results.append([dict(row) for row in result])
                    else:
                        result = await conn.execute(query, **params)
                        results.append(result)
                
                return results
    
    # Redis методы
    async def cache_get(self, key: str) -> Optional[Any]:
        """Получение данных из кэша"""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Ошибка получения из кэша: {e}")
            return None
    
    async def cache_set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Сохранение данных в кэш"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.setex(
                key,
                expire,
                json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш: {e}")
            return False
    
    async def cache_delete(self, key: str) -> bool:
        """Удаление данных из кэша"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {e}")
            return False
    
    async def cache_exists(self, key: str) -> bool:
        """Проверка существования ключа в кэше"""
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Ошибка проверки кэша: {e}")
            return False
    
    async def cache_invalidate_pattern(self, pattern: str) -> int:
        """Инвалидация кэша по паттерну"""
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Ошибка инвалидации кэша: {e}")
            return 0

# SQLAlchemy модели
class TestModel(Base):
    """Модель теста в базе данных"""
    __tablename__ = "tests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    test_type = Column(String, nullable=False)
    status = Column(String, default="active")
    priority = Column(String, default="medium")
    environment = Column(String, default="development")
    config = Column(JSON)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class TestExecutionModel(Base):
    """Модель выполнения теста в базе данных"""
    __tablename__ = "test_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id = Column(String, ForeignKey("tests.id"), nullable=False)
    status = Column(String, default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration = Column(Integer)  # в секундах
    result = Column(JSON)
    error_message = Column(Text)
    logs = Column(Text)
    metrics = Column(JSON)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

class TestSuiteModel(Base):
    """Модель набора тестов в базе данных"""
    __tablename__ = "test_suites"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    test_ids = Column(JSON)  # список ID тестов
    config = Column(JSON)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class TestReportModel(Base):
    """Модель отчета о тестировании в базе данных"""
    __tablename__ = "test_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String, ForeignKey("test_executions.id"), nullable=False)
    report_type = Column(String, default="detailed")
    content = Column(JSON)
    summary = Column(Text)
    recommendations = Column(JSON)
    created_at = Column(DateTime, default=func.now())

# Глобальный экземпляр базы данных
_db_instance: Optional[Database] = None

async def get_database() -> Database:
    """Получение глобального экземпляра базы данных"""
    global _db_instance
    
    if _db_instance is None:
        _db_instance = Database()
        await _db_instance.initialize()
    
    return _db_instance

async def close_database():
    """Закрытие глобального экземпляра базы данных"""
    global _db_instance
    
    if _db_instance:
        await _db_instance.close()
        _db_instance = None

# Утилиты для работы с данными
class DatabaseUtils:
    """Утилиты для работы с базой данных"""
    
    @staticmethod
    def generate_id() -> str:
        """Генерация уникального ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Форматирование даты и времени"""
        return dt.isoformat() if dt else None
    
    @staticmethod
    def parse_datetime(dt_str: str) -> datetime:
        """Парсинг строки даты и времени"""
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except ValueError:
            return datetime.now()
    
    @staticmethod
    def sanitize_sql_identifier(identifier: str) -> str:
        """Очистка SQL идентификатора от потенциально опасных символов"""
        import re
        # Удаляем все символы кроме букв, цифр и подчеркиваний
        return re.sub(r'[^a-zA-Z0-9_]', '', identifier)
    
    @staticmethod
    def build_where_clause(filters: Dict[str, Any]) -> tuple:
        """Построение WHERE условия для SQL запроса"""
        conditions = []
        params = {}
        
        for key, value in filters.items():
            if value is not None:
                safe_key = DatabaseUtils.sanitize_sql_identifier(key)
                param_name = f"param_{safe_key}"
                conditions.append(f"{safe_key} = :{param_name}")
                params[param_name] = value
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params

# Миграции базы данных
class DatabaseMigrations:
    """Класс для управления миграциями базы данных"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create_migrations_table(self):
        """Создание таблицы для отслеживания миграций"""
        query = """
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.db.execute_query(query)
    
    async def get_applied_migrations(self) -> List[str]:
        """Получение списка примененных миграций"""
        query = "SELECT version FROM migrations ORDER BY applied_at;"
        result = await self.db.execute_query(query)
        return [row["version"] for row in result]
    
    async def apply_migration(self, version: str, name: str, sql: str):
        """Применение миграции"""
        try:
            await self.db.execute_query(sql)
            
            insert_query = """
            INSERT INTO migrations (version, name) VALUES (:version, :name);
            """
            await self.db.execute_query(insert_query, {
                "version": version,
                "name": name
            })
            
            logger.info(f"✅ Миграция {version} ({name}) применена")
        except Exception as e:
            logger.error(f"❌ Ошибка применения миграции {version}: {e}")
            raise
    
    async def run_migrations(self):
        """Запуск всех миграций"""
        await self.create_migrations_table()
        
        applied_migrations = await self.get_applied_migrations()
        
        # Список миграций (в порядке применения)
        migrations = [
            {
                "version": "001",
                "name": "Initial schema",
                "sql": """
                -- Миграция уже применена через SQLAlchemy модели
                """
            }
        ]
        
        for migration in migrations:
            if migration["version"] not in applied_migrations:
                await self.apply_migration(
                    migration["version"],
                    migration["name"],
                    migration["sql"]
                )

# Инициализация при запуске
async def initialize_database():
    """Инициализация базы данных при запуске приложения"""
    try:
        db = await get_database()
        
        # Запуск миграций
        migrations = DatabaseMigrations(db)
        await migrations.run_migrations()
        
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise 