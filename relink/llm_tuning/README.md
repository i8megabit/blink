# 🧠 LLM Tuning Microservice

Микросервис для управления и тюнинга LLM моделей с поддержкой RAG, маршрутизации и мониторинга производительности.

## 🚀 Возможности

- **Управление моделями**: Создание, обновление, удаление LLM моделей
- **Динамический тюнинг**: Fine-tuning моделей в реальном времени
- **RAG (Retrieval-Augmented Generation)**: Работа с документами и контекстными ответами
- **Умная маршрутизация**: Автоматический выбор оптимальной модели для запроса
- **Мониторинг**: Отслеживание производительности и метрик
- **Оптимизация**: Автоматическая оптимизация параметров моделей
- **REST API**: Полнофункциональный API для интеграции

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   Ollama API    │    │   PostgreSQL    │
│                 │◄──►│                 │    │                 │
│ - Models API    │    │ - Model Mgmt    │    │ - Models        │
│ - Routes API    │    │ - Generation    │    │ - Routes        │
│ - RAG API       │    │ - Tuning        │    │ - Sessions      │
│ - Tuning API    │    │ - Embeddings    │    │ - Documents     │
│ - Metrics API   │    │                 │    │ - Metrics       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cache   │    │   Vector Store  │    │   Monitoring    │
│                 │    │                 │    │                 │
│ - Route Cache   │    │ - Embeddings    │    │ - Prometheus    │
│ - Model Cache   │    │ - Similarity    │    │ - Grafana       │
│ - Session Cache │    │ - Search        │    │ - Logs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Требования

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Ollama (для работы с моделями)
- Docker & Docker Compose (опционально)

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd relink/llm_tuning
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Скопируйте файл конфигурации:

```bash
cp env.example .env
```

Отредактируйте `.env` файл:

```env
# Основные настройки
ENVIRONMENT=development
DEBUG=true
API_TITLE="LLM Tuning Microservice"
API_VERSION="1.0.0"

# База данных
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/llm_tuning

# Redis
REDIS_URL=redis://localhost:6379/0

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=30

# RAG
RAG_ENABLED=true
RAG_EMBEDDING_MODEL=nomic-embed-text
RAG_MAX_DOCUMENTS=1000

# Тюнинг
TUNING_ENABLED=true
TUNING_MAX_SESSIONS=10
TUNING_TIMEOUT=3600

# Маршрутизация
ROUTER_ENABLED=true
ROUTER_CACHE_TTL=300

# Мониторинг
MONITORING_ENABLED=true
MONITORING_LOG_LEVEL=INFO
```

### 4. Инициализация базы данных

```bash
# Создание таблиц
python -m app.create_tables

# Или с помощью Alembic
alembic upgrade head
```

### 5. Запуск Ollama

```bash
# Установка Ollama (если не установлен)
curl -fsSL https://ollama.ai/install.sh | sh

# Запуск Ollama
ollama serve

# Загрузка базовой модели
ollama pull llama2
```

## 🚀 Запуск

### Разработка

```bash
# Запуск в режиме разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Продакшн с Docker

```bash
# Сборка образа
docker build -t llm-tuning .

# Запуск с Docker Compose
docker-compose up -d
```

### Docker Compose (рекомендуется)

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f llm-tuning

# Остановка
docker-compose down
```

## 📚 API Документация

После запуска сервиса документация доступна по адресам:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 Основные Endpoints

### Модели

```bash
# Создание модели
POST /api/v1/models
{
  "name": "my-model",
  "base_model": "llama2",
  "provider": "ollama",
  "description": "Моя тюнированная модель"
}

# Список моделей
GET /api/v1/models

# Получение модели
GET /api/v1/models/{model_id}

# Обновление модели
PUT /api/v1/models/{model_id}

# Удаление модели
DELETE /api/v1/models/{model_id}
```

### Маршрутизация

```bash
# Создание маршрута
POST /api/v1/routes
{
  "name": "code-route",
  "model_id": 1,
  "strategy": "round_robin",
  "request_types": ["code"],
  "keywords": ["python", "javascript"]
}

# Маршрутизация запроса
POST /api/v1/route
{
  "request_type": "text",
  "content": "Напиши код для сортировки массива",
  "use_rag": false
}
```

### RAG

```bash
# Добавление документа
POST /api/v1/rag/documents
{
  "title": "Python Guide",
  "content": "Python - это язык программирования...",
  "source": "docs",
  "document_type": "guide"
}

# RAG запрос
POST /api/v1/rag/query
{
  "query": "Как использовать Python?",
  "model_name": "llama2",
  "use_context": true
}
```

### Тюнинг

```bash
# Создание сессии тюнинга
POST /api/v1/tuning/sessions
{
  "model_id": 1,
  "strategy": "instruction_tuning",
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.9
  },
  "training_data": [
    {
      "instruction": "Объясни концепцию",
      "input": "",
      "output": "Это концепция..."
    }
  ]
}

# Список сессий
GET /api/v1/tuning/sessions

# Статус сессии
GET /api/v1/tuning/sessions/{session_id}
```

### Метрики

```bash
# Запись метрик
POST /api/v1/metrics
{
  "model_id": 1,
  "response_time": 1.5,
  "tokens_generated": 100,
  "success_rate": 1.0
}

# Сводка метрик
GET /api/v1/metrics/summary?model_id=1&time_range=24h
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Конкретные тесты
pytest tests/test_main.py::TestModelsAPI

# Асинхронные тесты
pytest -v --asyncio-mode=auto
```

### Тестовые данные

```bash
# Создание тестовых данных
python scripts/create_test_data.py

# Очистка тестовых данных
python scripts/cleanup_test_data.py
```

## 📊 Мониторинг

### Health Check

```bash
curl http://localhost:8000/health
```

### Метрики Prometheus

```bash
# Включение метрик Prometheus
curl http://localhost:8000/metrics
```

### Логи

```bash
# Просмотр логов
tail -f logs/llm-tuning.log

# Фильтрация по уровню
grep "ERROR" logs/llm-tuning.log
```

## 🔒 Безопасность

### Аутентификация

```bash
# API Key аутентификация
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/models
```

### CORS

Настройка CORS в `config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://yourdomain.com"
]
```

### Rate Limiting

```python
# Настройка ограничений
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # секунды
```

## 🚀 Развертывание

### Docker

```bash
# Продакшн образ
docker build -f Dockerfile.prod -t llm-tuning:prod .

# Запуск
docker run -d \
  --name llm-tuning \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  llm-tuning:prod
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-tuning
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-tuning
  template:
    metadata:
      labels:
        app: llm-tuning
    spec:
      containers:
      - name: llm-tuning
        image: llm-tuning:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

### CI/CD

```yaml
# GitHub Actions
name: Deploy LLM Tuning

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and test
      run: |
        docker build -t llm-tuning .
        docker run --rm llm-tuning pytest
    - name: Deploy
      run: |
        docker push llm-tuning:latest
        kubectl apply -f k8s/
```

## 🔧 Конфигурация

### Настройки модели

```python
# config.py
class ModelConfig:
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TOP_P = 0.9
    DEFAULT_MAX_TOKENS = 1000
    SUPPORTED_PROVIDERS = ["ollama", "openai", "anthropic"]
```

### Настройки RAG

```python
class RAGConfig:
    EMBEDDING_MODEL = "nomic-embed-text"
    MAX_DOCUMENTS = 1000
    SIMILARITY_THRESHOLD = 0.7
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
```

### Настройки тюнинга

```python
class TuningConfig:
    MAX_SESSIONS = 10
    TIMEOUT = 3600
    VALIDATION_QUERIES = [
        "Привет, как дела?",
        "Объясни простыми словами",
        "Напиши код"
    ]
```

## 🐛 Отладка

### Логирование

```python
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Отладка Ollama

```bash
# Проверка статуса Ollama
curl http://localhost:11434/api/tags

# Тест генерации
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "llama2", "prompt": "Hello"}'
```

### Отладка базы данных

```bash
# Подключение к БД
psql -h localhost -U user -d llm_tuning

# Проверка таблиц
\dt

# Проверка данных
SELECT * FROM llm_models LIMIT 5;
```

## 📈 Производительность

### Оптимизация

```python
# Кэширование
CACHE_TTL = 300  # 5 минут
CACHE_MAX_SIZE = 1000

# Пул соединений
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 30

# Асинхронность
MAX_CONCURRENT_REQUESTS = 100
```

### Мониторинг производительности

```bash
# Профилирование
python -m cProfile -o profile.stats app/main.py

# Анализ профиля
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

## 🤝 Вклад в проект

### Установка для разработки

```bash
# Клонирование
git clone <repository-url>
cd llm-tuning

# Установка зависимостей для разработки
pip install -r requirements-dev.txt

# Установка pre-commit hooks
pre-commit install

# Запуск тестов
pytest
```

### Стиль кода

```bash
# Форматирование
black app/
isort app/

# Проверка стиля
flake8 app/
mypy app/
```

### Создание PR

1. Создайте ветку: `git checkout -b feature/new-feature`
2. Внесите изменения
3. Добавьте тесты
4. Запустите тесты: `pytest`
5. Создайте PR с описанием изменений

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

- **Документация**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: support@yourdomain.com

## 🔄 Changelog

### v1.0.0 (2024-01-01)
- 🎉 Первый релиз
- ✨ Управление моделями
- ✨ RAG система
- ✨ Динамический тюнинг
- ✨ Умная маршрутизация
- ✨ Мониторинг и метрики

---

**Создано с ❤️ для сообщества AI/ML разработчиков** 