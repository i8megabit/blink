# 🧠 LLM Tuning - Настройка и оптимизация LLM

Микросервис для настройки, оптимизации и управления LLM моделями в платформе reLink.

## 🚀 Быстрый старт

```bash
# Запуск через Docker Compose
docker-compose up -d

# Локальная разработка
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# Запуск тестов
pytest tests/
```

## 🏗️ Архитектура

### Технологический стек
- **FastAPI** - веб-фреймворк для API
- **Ollama** - локальные LLM модели
- **ChromaDB** - векторная база данных
- **SQLAlchemy** - ORM для работы с БД
- **Alembic** - миграции базы данных
- **Prometheus** - мониторинг метрик

### Структура проекта
```
app/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Подключение к БД
├── models.py            # Модели данных
├── services.py          # Бизнес-логика
├── rag_service.py       # RAG система
├── svg_generator_service.py  # Генерация SVG
├── schemas.py           # Pydantic схемы
├── exceptions.py        # Обработка исключений
├── middleware.py        # Middleware
└── utils.py             # Утилиты

benchmarks/
├── performance_test.py  # Тесты производительности
├── run_benchmarks.sh    # Скрипт запуска тестов
└── README.md            # Документация тестов

tests/
├── test_main.py         # Основные тесты
└── test_extended_api.py # Расширенные API тесты
```

## 🎯 Основные функции

### Управление моделями
- Загрузка и развертывание LLM моделей
- Оптимизация параметров моделей
- Мониторинг производительности
- Автоматическое масштабирование

### Fine-tuning
- Настройка моделей под специфические задачи
- Обучение на доменных данных
- Валидация качества моделей
- Экспорт оптимизированных моделей

### RAG интеграция
- Векторный поиск документов
- Контекстное извлечение информации
- Автоматическое обновление базы знаний
- Оптимизация запросов

### Анализ производительности
- Бенчмарки моделей
- Сравнение эффективности
- Анализ ресурсов
- Рекомендации по оптимизации

## 🔧 Разработка

### Команды разработки
```bash
# Запуск сервиса
uvicorn app.main:app --reload --port 8002

# Запуск тестов
pytest tests/ -v

# Запуск бенчмарков
./benchmarks/run_benchmarks.sh

# Миграции БД
alembic upgrade head
```

### Создание миграций
```bash
# Создание миграции
alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

## 🧪 Тестирование

### Unit тесты
```bash
# Запуск всех тестов
pytest

# Запуск конкретного теста
pytest tests/test_main.py::test_health_check

# Запуск с покрытием
pytest --cov=app tests/
```

### Бенчмарки производительности
```bash
# Запуск бенчмарков
python benchmarks/performance_test.py

# Сравнение моделей
python benchmarks/performance_test.py --compare

# Генерация отчета
python benchmarks/performance_test.py --report
```

## 🐳 Docker

### Сборка образа
```bash
# Сборка образа
docker build -t relink-llm-tuning .

# Запуск контейнера
docker run -p 8002:8002 relink-llm-tuning
```

### Docker Compose
```bash
# Запуск с зависимостями
docker-compose up -d

# Просмотр логов
docker-compose logs -f llm-tuning
```

## 📊 API Документация

### Swagger UI
- **Локально**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

### Основные эндпоинты
- `GET /health` - проверка здоровья
- `POST /models/load` - загрузка модели
- `POST /models/tune` - настройка модели
- `GET /models/performance` - метрики производительности
- `POST /rag/query` - RAG запросы

## 🔍 RAG Система

### Векторный поиск
```python
from app.rag_service import RAGService

# Инициализация RAG
rag = RAGService()

# Добавление документов
rag.add_documents(documents)

# Поиск по запросу
results = rag.query("Ваш запрос")
```

### Контекстное извлечение
- Автоматическое извлечение релевантной информации
- Ранжирование результатов
- Фильтрация по домену
- Кэширование запросов

## 📈 Мониторинг и метрики

### Prometheus метрики
- Время ответа моделей
- Использование ресурсов
- Количество запросов
- Ошибки и исключения

### Grafana дашборды
- Производительность моделей
- Использование ресурсов
- Тренды качества
- Алерты и уведомления

## 🔗 Интеграции

### Ollama
- Автоматическое обнаружение моделей
- Управление версиями
- Оптимизация параметров
- Мониторинг состояния

### ChromaDB
- Векторное хранение
- Семантический поиск
- Автоматическая индексация
- Масштабирование

## 🚀 Деплой

### Продакшен
```bash
# Сборка продакшен образа
docker build -t relink-llm-tuning:prod .

# Запуск с переменными окружения
docker run -e DATABASE_URL=... relink-llm-tuning:prod
```

### CI/CD
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging

## 📚 Дополнительная документация

- [API документация](https://api.relink.dev)
- [RAG система](app/rag_service.py)
- [Бенчмарки](benchmarks/README.md) 