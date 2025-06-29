# 🔧 Bootstrap - Общая основа для микросервисов reLink

Общая основа и утилиты для всех микросервисов платформы reLink, обеспечивающая стандартизированную инициализацию и общие функции.

## 🚀 Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Импорт в микросервис
from bootstrap import config, database, logging, monitoring
```

## 🏗️ Архитектура

### Технологический стек
- **Python 3.11+** - основной язык
- **SQLAlchemy** - ORM для работы с БД
- **Redis** - кэширование и очереди
- **Logging** - структурированное логирование
- **Monitoring** - метрики и мониторинг
- **Ollama** - интеграция с LLM

### Структура проекта
```
bootstrap/
├── __init__.py          # Основной модуль
├── config.py            # Конфигурация
├── database.py          # Подключение к БД
├── cache.py             # Кэширование
├── logging.py           # Логирование
├── monitoring.py        # Мониторинг
├── ollama_client.py     # Ollama клиент
├── llm_router.py        # LLM роутер
└── rag_service.py       # RAG сервис
```

## 🎯 Основные функции

### Конфигурация
- Централизованное управление настройками
- Переменные окружения
- Валидация конфигурации
- Различные профили (dev, staging, prod)

### База данных
- Подключение к PostgreSQL
- Миграции Alembic
- Connection pooling
- Транзакции и rollback

### Кэширование
- Redis интеграция
- Кэширование запросов
- Управление TTL
- Инвалидация кэша

### Логирование
- Структурированные логи
- Различные уровни логирования
- Ротация логов
- Централизованный сбор

### Мониторинг
- Prometheus метрики
- Health checks
- Performance monitoring
- Алерты и уведомления

## 🔧 Разработка

### Импорт в микросервис
```python
# Основные компоненты
from bootstrap import config, database, logging, monitoring

# Инициализация
config.init()
database.init()
logging.init()
monitoring.init()
```

### Использование конфигурации
```python
from bootstrap.config import get_config

# Получение настроек
db_url = get_config("DATABASE_URL")
redis_url = get_config("REDIS_URL")
log_level = get_config("LOG_LEVEL", default="INFO")
```

### Работа с базой данных
```python
from bootstrap.database import get_session, get_engine

# Получение сессии
with get_session() as session:
    # Выполнение запросов
    users = session.query(User).all()

# Получение движка
engine = get_engine()
```

### Кэширование
```python
from bootstrap.cache import cache

# Сохранение в кэш
await cache.set("user:123", user_data, ttl=3600)

# Получение из кэша
user_data = await cache.get("user:123")

# Удаление из кэша
await cache.delete("user:123")
```

## 🧪 Тестирование

### Unit тесты
```bash
# Запуск тестов
pytest tests/

# Запуск с покрытием
pytest --cov=bootstrap tests/
```

### Интеграционные тесты
```bash
# Тесты с реальными сервисами
pytest tests/integration/
```

## 📊 Конфигурация

### Переменные окружения
```bash
# База данных
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=json

# Мониторинг
PROMETHEUS_PORT=9090
HEALTH_CHECK_PORT=8080

# Ollama
OLLAMA_URL=http://localhost:11434
```

### Профили конфигурации
```python
# config.py
class Config:
    # Development
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    
    # Production
    DEBUG = False
    LOG_LEVEL = "WARNING"
    DATABASE_POOL_SIZE = 20
```

## 🔗 Интеграции

### PostgreSQL
- Подключение и пул соединений
- Миграции Alembic
- Транзакции и rollback
- Мониторинг производительности

### Redis
- Кэширование данных
- Очереди сообщений
- Распределенные блокировки
- Pub/Sub механизмы

### Prometheus
- Сбор метрик
- Health checks
- Мониторинг производительности
- Алерты

### Ollama
- Интеграция с LLM моделями
- Управление моделями
- Генерация текста
- Анализ эффективности

## 🚀 Деплой

### Установка в микросервис
```bash
# Добавление в requirements.txt
bootstrap @ git+https://github.com/your-repo/relink.git#subdirectory=bootstrap

# Или локальная установка
pip install -e ./bootstrap
```

### Инициализация в микросервисе
```python
# main.py
from bootstrap import init_bootstrap

# Инициализация всех компонентов
init_bootstrap()

# Запуск приложения
app = FastAPI()
```

## 📚 Дополнительная документация

- [Конфигурация](config.py)
- [База данных](database.py)
- [Кэширование](cache.py)
- [Логирование](logging.py)
- [Мониторинг](monitoring.py) 