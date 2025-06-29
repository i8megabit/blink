# 🔧 Backend - FastAPI микросервис reLink

Основной backend микросервис reLink построен на FastAPI с интеграцией LLM, RAG и микросервисной архитектуры.

## 🚀 Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запуск через Docker
docker build -t relink-backend .
docker run -p 8000:8000 relink-backend
```

## 🏗️ Архитектура

### Технологический стек
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL** - основная база данных
- **Redis** - кеширование и очереди
- **Ollama** - локальные LLM модели
- **ChromaDB** - векторная база данных

### Структура проекта
```
app/
├── api/                 # API роуты
│   ├── auth.py         # Аутентификация
│   └── routes.py       # Основные роуты
├── llm/                # LLM интеграция
│   ├── router.py       # LLM роутер
│   ├── integration.py  # Интеграция с моделями
│   └── rag/            # RAG система
├── models.py           # Модели данных
├── database.py         # Подключение к БД
├── config.py           # Конфигурация
└── main.py             # Точка входа
```

## 🎯 Основные функции

### SEO Анализ
- Анализ WordPress сайтов
- Генерация SEO рекомендаций
- Визуализация внутренних ссылок
- Экспорт результатов

### LLM Интеграция
- Маршрутизация запросов к оптимальным моделям
- RAG система для контекстного поиска
- Анализ эффективности ответов
- Автоматическая оптимизация

### Микросервисы
- Нативная интеграция с другими сервисами
- API Gateway функциональность
- Мониторинг и метрики
- Автоматическое масштабирование

## 🔧 Разработка

### Команды разработки
```bash
# Запуск в режиме разработки
uvicorn app.main:app --reload

# Запуск тестов
pytest

# Запуск тестов с покрытием
pytest --cov=app

# Линтинг
flake8 app/
black app/
isort app/
```

### Миграции базы данных
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

# Запуск тестов с подробным выводом
pytest -v
```

### Интеграционные тесты
```bash
# Тесты с реальной базой данных
pytest tests/integration/

# Тесты API
pytest tests/api/
```

### LLM тесты
```bash
# Тесты LLM интеграции
pytest tests/test_llm_integration.py

# Тесты RAG системы
pytest tests/test_rag_system.py
```

## 🐳 Docker

### Сборка образа
```bash
# Сборка образа
docker build -t relink-backend .

# Запуск контейнера
docker run -p 8000:8000 relink-backend
```

### Docker Compose
```bash
# Запуск с зависимостями
docker-compose up backend
```

## 📊 API Документация

### Swagger UI
- **Локально**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Основные эндпоинты
- `GET /health` - проверка здоровья
- `GET /api/v1/analyze` - анализ сайта
- `POST /api/v1/recommendations` - генерация рекомендаций
- `GET /api/v1/visualization` - визуализация связей

## 🔒 Безопасность

### Аутентификация
- JWT токены
- OAuth2 с Password flow
- API ключи для сервисов

### Валидация
- Pydantic модели
- Автоматическая валидация входных данных
- Санитизация пользовательского ввода

## 📊 Мониторинг

### Метрики
- Prometheus метрики
- OpenTelemetry трейсинг
- Структурированное логирование

### Health Checks
- Проверка подключения к БД
- Проверка Redis
- Проверка LLM сервисов

## 🔗 Интеграции

### LLM Router
- Автоматическая маршрутизация запросов
- Анализ эффективности моделей
- Оптимизация выбора модели

### RAG System
- Векторный поиск
- Контекстное извлечение
- Автоматическое обновление базы знаний

### Микросервисы
- Service discovery
- Load balancing
- Circuit breaker паттерн

## 🚀 Деплой

### Продакшен
```bash
# Сборка для продакшена
docker build -t relink-backend:prod .

# Запуск с переменными окружения
docker run -e DATABASE_URL=... relink-backend:prod
```

### CI/CD
- Автоматическая сборка при push
- Тестирование перед деплоем
- Blue-green деплой
- Автоматический rollback

## 📚 Документация

- [API документация](http://localhost:8000/docs)
- [LLM архитектура](README_LLM_ARCHITECTURE.md)
- [Техническая документация](../docs/)

## 🤝 Вклад в проект

1. Следуйте [правилам кодирования](../docs/CODING_STANDARDS.md)
2. Пишите тесты для новых функций
3. Обновляйте API документацию
4. Проверяйте безопасность

---

**Backend reLink** - мощный API для SEO-инженеров 🔧 