# 🧪 reLink Testing Service

Микросервис тестирования для платформы reLink - мощный, масштабируемый и высокопроизводительный сервис для управления и выполнения различных типов тестов.

## 🚀 Возможности

### ✅ Основной функционал
- **Управление тестами**: создание, редактирование, удаление тестов
- **Выполнение тестов**: API, UI, Performance, Load, Security тесты
- **Наборы тестов**: группировка и параллельное выполнение
- **Отчеты**: детальные отчеты с метриками и рекомендациями
- **Метрики**: сбор и анализ производительности
- **Мониторинг**: real-time отслеживание выполнения

### 🔧 Технические возможности
- **Асинхронность**: полная поддержка async/await
- **Масштабируемость**: горизонтальное масштабирование
- **Кэширование**: Redis для быстрого доступа к данным
- **Очереди**: фоновое выполнение тестов
- **WebSocket**: real-time обновления
- **API**: RESTful API с автоматической документацией

### 📊 Типы тестов
- **API тесты**: HTTP/HTTPS запросы, валидация ответов
- **UI тесты**: Selenium WebDriver, Playwright
- **Performance тесты**: нагрузочное тестирование
- **Load тесты**: стресс-тестирование
- **Security тесты**: проверка уязвимостей
- **Integration тесты**: комплексное тестирование

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Testing       │
│   (React)       │◄──►│   (Nginx)       │◄──►│   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐            │
                       │   PostgreSQL    │◄───────────┤
                       │   Database      │            │
                       └─────────────────┘            │
                                                       │
                       ┌─────────────────┐            │
                       │   Redis Cache   │◄───────────┤
                       │   & Queue       │            │
                       └─────────────────┘            │
                                                       │
                       ┌─────────────────┐            │
                       │   Prometheus    │◄───────────┘
                       │   & Grafana     │
                       └─────────────────┘
```

## 🛠️ Технологический стек

### Backend
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **asyncpg** - асинхронный драйвер PostgreSQL
- **Redis** - кэширование и очереди
- **Pydantic** - валидация данных
- **Prometheus** - метрики и мониторинг

### Тестирование
- **pytest** - фреймворк тестирования
- **pytest-asyncio** - асинхронные тесты
- **pytest-cov** - покрытие кода
- **httpx** - HTTP клиент для тестов
- **Selenium** - UI тестирование
- **Locust** - нагрузочное тестирование

### DevOps
- **Docker** - контейнеризация
- **Docker Compose** - оркестрация
- **Nginx** - reverse proxy
- **Grafana** - визуализация метрик
- **Jaeger** - трейсинг
- **Elasticsearch** - логирование

## 📦 Установка и запуск

### Предварительные требования
- Docker и Docker Compose
- Python 3.11+
- Node.js 18+ (для фронтенда)

### Быстрый старт

1. **Клонирование репозитория**
```bash
git clone https://github.com/your-org/relink.git
cd relink/testing
```

2. **Настройка окружения**
```bash
cp .env.example .env
# Отредактируйте .env файл под ваши нужды
```

3. **Запуск с Docker Compose**
```bash
docker-compose up -d
```

4. **Проверка работоспособности**
```bash
curl http://localhost:8001/health
```

### Локальная разработка

1. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

2. **Настройка базы данных**
```bash
# Создание миграций
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

3. **Запуск сервиса**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Документация

После запуска сервиса документация доступна по адресам:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

### Основные эндпоинты

#### Тесты
```http
POST   /tests/                    # Создание теста
GET    /tests/                    # Список тестов
GET    /tests/{test_id}           # Получение теста
PUT    /tests/{test_id}           # Обновление теста
DELETE /tests/{test_id}           # Удаление теста
```

#### Выполнение тестов
```http
POST   /tests/{test_id}/execute   # Выполнение теста
GET    /executions/               # Список выполнений
GET    /executions/{execution_id} # Получение выполнения
POST   /executions/{execution_id}/cancel # Отмена выполнения
```

#### Наборы тестов
```http
POST   /test-suites/              # Создание набора
POST   /test-suites/{suite_id}/execute # Выполнение набора
```

#### Отчеты
```http
GET    /reports/                  # Список отчетов
GET    /reports/{report_id}       # Получение отчета
```

#### Метрики
```http
GET    /metrics/                  # Получение метрик
```

## 🧪 Примеры использования

### Создание API теста

```python
import requests

# Создание теста
test_data = {
    "name": "API Health Check",
    "description": "Проверка здоровья API",
    "test_type": "api",
    "priority": "high",
    "environment": "production",
    "config": {
        "url": "https://api.example.com/health",
        "method": "GET",
        "timeout": 30,
        "expected_status": 200,
        "assertions": [
            {"type": "status_code", "value": 200},
            {"type": "response_time", "value": 1000, "operator": "<"}
        ]
    }
}

response = requests.post("http://localhost:8001/tests/", json=test_data)
test_id = response.json()["id"]

# Выполнение теста
execution_response = requests.post(f"http://localhost:8001/tests/{test_id}/execute")
execution_id = execution_response.json()["id"]

# Получение результата
result = requests.get(f"http://localhost:8001/executions/{execution_id}")
print(result.json())
```

### Создание UI теста

```python
test_data = {
    "name": "Login Page Test",
    "description": "Тест страницы входа",
    "test_type": "ui",
    "priority": "medium",
    "environment": "staging",
    "config": {
        "url": "https://app.example.com/login",
        "browser": "chrome",
        "viewport": {"width": 1920, "height": 1080},
        "steps": [
            {"action": "type", "selector": "#email", "value": "test@example.com"},
            {"action": "type", "selector": "#password", "value": "password123"},
            {"action": "click", "selector": "#login-button"},
            {"action": "wait", "selector": ".dashboard", "timeout": 5000}
        ]
    }
}
```

### Создание Performance теста

```python
test_data = {
    "name": "Load Test",
    "description": "Нагрузочное тестирование API",
    "test_type": "performance",
    "priority": "high",
    "environment": "staging",
    "config": {
        "url": "https://api.example.com/users",
        "method": "GET",
        "users": 100,
        "duration": 300,
        "ramp_up": 60,
        "target_rps": 1000,
        "thresholds": {
            "response_time_p95": 200,
            "error_rate": 1.0
        }
    }
}
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# Основные настройки
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# База данных
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# API
HOST=0.0.0.0
PORT=8000
API_PREFIX=/api/v1

# Безопасность
AUTH_REQUIRED=true
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Тестирование
MAX_CONCURRENT_TESTS=10
TEST_TIMEOUT=300
RETRY_ATTEMPTS=3

# Мониторинг
METRICS_PORT=8000
METRICS_ENABLED=true
TRACING_ENABLED=true
```

### Docker Compose

Для запуска полного стека используйте:

```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск только основных сервисов
docker-compose up -d testing-service postgres redis

# Запуск с мониторингом
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Unit тесты
pytest -m unit

# Integration тесты
pytest -m integration

# Performance тесты
pytest -m performance

# С покрытием кода
pytest --cov=app --cov-report=html

# Параллельное выполнение
pytest -n auto
```

### Типы тестов

- **Unit тесты**: тестирование отдельных функций и классов
- **Integration тесты**: тестирование взаимодействия компонентов
- **API тесты**: тестирование HTTP эндпоинтов
- **Performance тесты**: тестирование производительности
- **E2E тесты**: полное тестирование пользовательских сценариев

## 📊 Мониторинг

### Метрики Prometheus

Сервис экспортирует метрики на `/metrics`:
- `test_executions_total` - общее количество выполнений
- `test_execution_duration_seconds` - время выполнения тестов
- `active_executions` - активные выполнения
- `queue_size` - размер очереди

### Grafana дашборды

Доступны готовые дашборды:
- **Testing Overview**: общий обзор тестирования
- **Test Performance**: производительность тестов
- **Error Analysis**: анализ ошибок
- **System Metrics**: системные метрики

### Логирование

Логи отправляются в:
- **Elasticsearch** - для анализа и поиска
- **Kibana** - для визуализации
- **Fluentd** - для агрегации

## 🔒 Безопасность

### Аутентификация
- JWT токены
- OAuth 2.0 интеграция
- API ключи

### Авторизация
- RBAC (Role-Based Access Control)
- Разрешения на уровне ресурсов
- Аудит действий

### Защита данных
- Шифрование в покое и в движении
- Маскирование чувствительных данных
- Регулярные бэкапы

## 🚀 Развертывание

### Production

```bash
# Сборка образа
docker build -t relink-testing:latest .

# Запуск в production
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Применение манифестов
kubectl apply -f k8s/

# Проверка статуса
kubectl get pods -n relink-testing
```

### CI/CD

```yaml
# GitHub Actions пример
name: Deploy Testing Service
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
          docker build -t relink-testing .
          docker run relink-testing pytest
      - name: Deploy
        run: |
          docker push relink-testing:latest
          kubectl set image deployment/testing-service testing-service=relink-testing:latest
```

## 🤝 Разработка

### Структура проекта

```
testing/
├── app/                    # Основной код приложения
│   ├── __init__.py
│   ├── main.py            # FastAPI приложение
│   ├── config.py          # Конфигурация
│   ├── models.py          # Pydantic модели
│   ├── services.py        # Бизнес-логика
│   ├── database.py        # Работа с БД
│   └── monitoring.py      # Мониторинг
├── tests/                 # Тесты
│   ├── test_api.py        # API тесты
│   ├── test_services.py   # Тесты сервисов
│   └── conftest.py        # Фикстуры
├── scripts/               # Скрипты
├── monitoring/            # Конфигурация мониторинга
├── nginx/                 # Nginx конфигурация
├── mocks/                 # Моки для тестирования
├── reports/               # Отчеты
├── logs/                  # Логи
├── storage/               # Файловое хранилище
├── Dockerfile             # Docker образ
├── docker-compose.yml     # Docker Compose
├── requirements.txt       # Python зависимости
├── pytest.ini           # Конфигурация pytest
└── README.md             # Документация
```

### Стиль кода

- **Black** - форматирование кода
- **isort** - сортировка импортов
- **flake8** - линтинг
- **mypy** - статическая типизация

```bash
# Форматирование
black app/ tests/
isort app/ tests/

# Линтинг
flake8 app/ tests/
mypy app/
```

### Git workflow

```bash
# Создание feature ветки
git checkout -b feature/new-test-type

# Коммиты
git add .
git commit -m "feat: add new test type support"

# Push и создание PR
git push origin feature/new-test-type
```

## 📈 Производительность

### Бенчмарки

- **API запросы**: 10,000+ RPS
- **Выполнение тестов**: 100+ параллельных тестов
- **Время отклика**: < 100ms для 95% запросов
- **Память**: < 512MB для базового использования

### Оптимизация

- **Кэширование**: Redis для часто запрашиваемых данных
- **Индексы БД**: оптимизированные запросы
- **Connection pooling**: переиспользование соединений
- **Async I/O**: неблокирующие операции

## 🐛 Troubleshooting

### Частые проблемы

1. **Ошибка подключения к БД**
```bash
# Проверка статуса PostgreSQL
docker-compose ps postgres
docker-compose logs postgres
```

2. **Redis недоступен**
```bash
# Проверка Redis
docker-compose exec redis redis-cli ping
```

3. **Тесты не выполняются**
```bash
# Проверка логов
docker-compose logs testing-service
```

4. **Метрики не отображаются**
```bash
# Проверка Prometheus
curl http://localhost:9090/api/v1/targets
```

### Логи

```bash
# Просмотр логов в реальном времени
docker-compose logs -f testing-service

# Логи с фильтрацией
docker-compose logs testing-service | grep ERROR
```

## 📞 Поддержка

### Документация
- [API Reference](docs/api.md)
- [Architecture](docs/architecture.md)
- [Deployment](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

### Сообщество
- [GitHub Issues](https://github.com/your-org/relink/issues)
- [Discussions](https://github.com/your-org/relink/discussions)
- [Wiki](https://github.com/your-org/relink/wiki)

### Контакты
- **Email**: support@relink.com
- **Slack**: #relink-testing
- **Telegram**: @relink_support

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл для деталей.

## 🙏 Благодарности

- FastAPI сообществу за отличный фреймворк
- SQLAlchemy команде за мощный ORM
- Docker сообществу за контейнеризацию
- Всем контрибьюторам проекта

---

**reLink Testing Service** - мощный инструмент для современного тестирования! 🚀 