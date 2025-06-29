# 📊 Monitoring - Мониторинг и алерты reLink

Система мониторинга и алертов для платформы reLink с интеграцией Prometheus, Grafana и кастомных метрик.

## 🚀 Быстрый старт

```bash
# Запуск через Docker Compose
docker-compose up -d

# Локальная разработка
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003

# Запуск тестов
pytest tests/
```

## 🏗️ Архитектура

### Технологический стек
- **FastAPI** - веб-фреймворк для API
- **Prometheus** - сбор метрик
- **Grafana** - визуализация данных
- **SQLAlchemy** - ORM для работы с БД
- **Redis** - кэширование и очереди
- **AlertManager** - управление алертами

### Структура проекта
```
app/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Подключение к БД
├── models.py            # Модели данных
├── services.py          # Бизнес-логика
├── monitoring.py        # Основной мониторинг
└── api/
    └── routes.py        # API роуты

tests/
├── test_api.py          # API тесты
└── test_services.py     # Тесты сервисов

prometheus.yml           # Конфигурация Prometheus
```

## 🎯 Основные функции

### Сбор метрик
- Системные метрики (CPU, память, диск)
- Прикладные метрики (API, база данных)
- Бизнес-метрики (пользователи, транзакции)
- Кастомные метрики для специфических задач

### Визуализация
- Дашборды Grafana
- Реал-тайм графики
- Исторические данные
- Сравнительная аналитика

### Алерты
- Автоматические уведомления
- Настраиваемые пороги
- Эскалация инцидентов
- Интеграция с внешними системами

### Аналитика
- Тренды производительности
- Прогнозирование проблем
- Анализ инцидентов
- Отчеты и экспорт

## 🔧 Разработка

### Команды разработки
```bash
# Запуск сервиса
uvicorn app.main:app --reload --port 8003

# Запуск тестов
pytest tests/ -v

# Запуск с покрытием
pytest --cov=app tests/

# Линтинг
flake8 app/
black app/
isort app/
```

### Создание метрик
```python
from app.monitoring import MetricsCollector

# Инициализация коллектора
collector = MetricsCollector()

# Создание кастомной метрики
collector.create_counter("api_requests_total", "Total API requests")
collector.create_gauge("active_users", "Number of active users")
collector.create_histogram("response_time", "API response time")
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

# Тесты API
pytest tests/api/
```

## 🐳 Docker

### Сборка образа
```bash
# Сборка образа
docker build -t relink-monitoring .

# Запуск контейнера
docker run -p 8003:8003 relink-monitoring
```

### Docker Compose
```bash
# Запуск с зависимостями
docker-compose up -d

# Просмотр логов
docker-compose logs -f monitoring
```

## 📊 API Документация

### Swagger UI
- **Локально**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

### Основные эндпоинты
- `GET /health` - проверка здоровья
- `GET /metrics` - метрики Prometheus
- `GET /alerts` - активные алерты
- `POST /alerts/configure` - настройка алертов

## 📈 Prometheus метрики

### Системные метрики
```yaml
# CPU и память
node_cpu_seconds_total
node_memory_MemAvailable_bytes
node_filesystem_avail_bytes

# Сеть
node_network_receive_bytes_total
node_network_transmit_bytes_total
```

### Прикладные метрики
```yaml
# API метрики
http_requests_total
http_request_duration_seconds
http_requests_in_flight

# База данных
db_connections_active
db_queries_total
db_query_duration_seconds
```

### Бизнес-метрики
```yaml
# Пользователи
active_users_total
user_registrations_total
user_sessions_total

# Транзакции
transactions_total
transaction_amount_total
transaction_success_rate
```

## 🎨 Grafana дашборды

### Системный мониторинг
- Обзор системы
- Использование ресурсов
- Сетевой трафик
- Дисковые операции

### Прикладной мониторинг
- API производительность
- Ошибки и исключения
- Время ответа
- Пропускная способность

### Бизнес-аналитика
- Активные пользователи
- Транзакции
- Конверсия
- Тренды роста

## 🔔 Алерты

### Настройка алертов
```yaml
# prometheus.yml
groups:
  - name: system_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for 5 minutes"
```

### Уведомления
- Email уведомления
- Slack интеграция
- Telegram бот
- Webhook уведомления

## 🔗 Интеграции

### Prometheus
- Автоматический сбор метрик
- Service discovery
- Scraping конфигурация
- Хранение временных рядов

### Grafana
- Визуализация метрик
- Дашборды
- Алерты
- Экспорт данных

### AlertManager
- Управление алертами
- Группировка уведомлений
- Эскалация
- Интеграция с внешними системами

## 🚀 Деплой

### Продакшен
```bash
# Сборка продакшен образа
docker build -t relink-monitoring:prod .

# Запуск с переменными окружения
docker run -e DATABASE_URL=... relink-monitoring:prod
```

### CI/CD
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging

## 📚 Дополнительная документация

- [API документация](https://api.relink.dev)
- [Prometheus конфигурация](prometheus.yml)
- [Grafana дашборды](grafana/dashboards/) 