# 🛣️ Router - Маршрутизация запросов reLink

Микросервис маршрутизации для платформы reLink, обеспечивающий умное распределение запросов между сервисами.

## 🚀 Быстрый старт

```bash
# Запуск через Docker Compose
docker-compose up -d

# Локальная разработка
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004

# Запуск тестов
pytest tests/
```

## 🏗️ Архитектура

### Технологический стек
- **FastAPI** - веб-фреймворк для API
- **SQLAlchemy** - ORM для работы с БД
- **Redis** - кэширование и очереди
- **Prometheus** - мониторинг метрик
- **Consul** - service discovery
- **Load Balancer** - распределение нагрузки

### Структура проекта
```
app/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Подключение к БД
├── models.py            # Модели данных
├── services.py          # Бизнес-логика
├── router.py            # Основная маршрутизация
└── api/
    └── routes.py        # API роуты

tests/
├── test_api.py          # API тесты
└── test_services.py     # Тесты сервисов
```

## 🎯 Основные функции

### Умная маршрутизация
- Автоматическое обнаружение сервисов
- Балансировка нагрузки
- Маршрутизация по типу запроса
- Приоритизация сервисов

### Service Discovery
- Автоматическое обнаружение новых сервисов
- Мониторинг состояния сервисов
- Удаление недоступных сервисов
- Обновление маршрутов в реальном времени

### Load Balancing
- Round-robin распределение
- Weighted round-robin
- Least connections
- Health-based routing

### Мониторинг
- Метрики производительности
- Статистика запросов
- Ошибки и исключения
- Время ответа сервисов

## 🔧 Разработка

### Команды разработки
```bash
# Запуск сервиса
uvicorn app.main:app --reload --port 8004

# Запуск тестов
pytest tests/ -v

# Запуск с покрытием
pytest --cov=app tests/

# Линтинг
flake8 app/
black app/
isort app/
```

### Создание маршрутов
```python
from app.router import RouterService

# Инициализация роутера
router = RouterService()

# Добавление сервиса
router.add_service("backend", "http://backend:8000", weight=1)
router.add_service("llm", "http://llm-tuning:8002", weight=2)

# Настройка маршрута
router.set_route("/api/v1/analyze", "backend")
router.set_route("/api/v1/llm", "llm")
```

## 🧪 Тестирование

### Unit тесты
```bash
# Запуск всех тестов
pytest

# Запуск конкретного теста
pytest tests/test_api.py::test_health_check

# Запуск с покрытием
pytest --cov=app tests/
```

### Интеграционные тесты
```bash
# Тесты с реальными сервисами
pytest tests/integration/

# Тесты маршрутизации
pytest tests/test_router.py
```

## 🐳 Docker

### Сборка образа
```bash
# Сборка образа
docker build -t relink-router .

# Запуск контейнера
docker run -p 8004:8004 relink-router
```

### Docker Compose
```bash
# Запуск с зависимостями
docker-compose up -d

# Просмотр логов
docker-compose logs -f router
```

## 📊 API Документация

### Swagger UI
- **Локально**: http://localhost:8004/docs
- **ReDoc**: http://localhost:8004/redoc

### Основные эндпоинты
- `GET /health` - проверка здоровья
- `GET /services` - список сервисов
- `POST /services` - добавление сервиса
- `GET /routes` - список маршрутов
- `POST /routes` - настройка маршрута

## 🔍 Service Discovery

### Автоматическое обнаружение
```python
from app.services import ServiceDiscovery

# Инициализация discovery
discovery = ServiceDiscovery()

# Регистрация сервиса
discovery.register_service("backend", "http://backend:8000")

# Получение списка сервисов
services = discovery.get_services()

# Проверка здоровья
health = discovery.check_health("backend")
```

### Конфигурация
```yaml
# consul.yml
services:
  - name: backend
    address: backend
    port: 8000
    tags: ["api", "core"]
    health_check:
      path: /health
      interval: 30s
      timeout: 5s
```

## ⚖️ Load Balancing

### Алгоритмы балансировки
- **Round Robin** - поочередное распределение
- **Weighted Round Robin** - с учетом весов
- **Least Connections** - по наименьшему количеству соединений
- **Health-based** - только здоровые сервисы

### Настройка весов
```python
# Настройка весов сервисов
router.set_service_weight("backend", 1)
router.set_service_weight("backend-replica", 2)
router.set_service_weight("backend-backup", 0.5)
```

## 📈 Мониторинг и метрики

### Prometheus метрики
- Количество запросов по сервисам
- Время ответа сервисов
- Ошибки маршрутизации
- Состояние сервисов

### Grafana дашборды
- Обзор маршрутизации
- Производительность сервисов
- Ошибки и исключения
- Тренды нагрузки

## 🔗 Интеграции

### Consul
- Service discovery
- Health checks
- Key-value store
- Distributed locking

### Prometheus
- Сбор метрик
- Мониторинг производительности
- Алерты
- Исторические данные

### Redis
- Кэширование маршрутов
- Сессии пользователей
- Очереди сообщений
- Распределенные блокировки

## 🚀 Деплой

### Продакшен
```bash
# Сборка продакшен образа
docker build -t relink-router:prod .

# Запуск с переменными окружения
docker run -e DATABASE_URL=... relink-router:prod
```

### CI/CD
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging

## 📚 Дополнительная документация

- [API документация](https://api.relink.dev)
- [Service Discovery](app/services.py)
- [Load Balancing](app/router.py)
