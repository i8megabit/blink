# 🔍 Микросервис Мониторинга reLink

Мощный, легкий и быстрый микросервис мониторинга для платформы reLink. Предоставляет комплексный мониторинг всех компонентов системы с богатой метрикой и реальным временем.

## 🚀 Возможности

### 📊 Сбор метрик
- **Системные метрики**: CPU, память, диск, сеть, нагрузка
- **База данных**: подключения, запросы, производительность
- **Кеш Redis**: hit rate, память, операции
- **Ollama LLM**: модели, время ответа, токены/сек
- **HTTP метрики**: запросы, ответы, ошибки

### 🚨 Система алертов
- Автоматическое обнаружение проблем
- Настраиваемые пороги для всех метрик
- Различные уровни важности (INFO, WARNING, ERROR, CRITICAL)
- Управление статусами алертов (активный, разрешенный, подтвержденный)

### 🏥 Проверка здоровья
- Мониторинг всех сервисов системы
- Автоматические проверки доступности
- Детальная диагностика компонентов
- Статусы: HEALTHY, DEGRADED, DOWN

### 📈 Дашборд
- Реальное время обновления данных
- Интеграция с фронтендом
- Исторические данные
- Визуализация трендов

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Monitoring    │    │   Redis Cache   │
│   (React)       │◄──►│   Service       │◄──►│   (Metrics)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (History)     │
                       └─────────────────┘
```

## 🛠️ Технологический стек

- **FastAPI** - современный веб-фреймворк
- **Redis** - кеширование и хранение метрик
- **PostgreSQL** - долгосрочное хранение данных
- **SQLAlchemy** - ORM для работы с БД
- **psutil** - системные метрики
- **aiohttp** - асинхронные HTTP запросы
- **Pydantic** - валидация данных
- **Prometheus** - экспорт метрик

## 📦 Установка и запуск

### Локальная разработка

```bash
# Клонирование репозитория
git clone <repository>
cd relink/monitoring

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Запуск сервиса
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker

```bash
# Сборка образа
docker build -t relink-monitoring .

# Запуск контейнера
docker run -d \
  --name monitoring \
  -p 8002:8002 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e REDIS_HOST=redis \
  -e OLLAMA_URL=http://ollama:11434 \
  relink-monitoring
```

### Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f monitoring
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql+asyncpg://seo_user:seo_pass@db:5432/seo_db` |
| `REDIS_HOST` | Хост Redis | `redis` |
| `REDIS_PORT` | Порт Redis | `6379` |
| `OLLAMA_URL` | URL Ollama API | `http://ollama:11434` |
| `COLLECT_INTERVAL` | Интервал сбора метрик (сек) | `30` |
| `RETENTION_DAYS` | Дни хранения данных | `30` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `CORS_ORIGINS` | Разрешенные CORS источники | `["http://localhost:3000"]` |

### Пороги алертов

```python
ALERT_THRESHOLDS = {
    "cpu_usage": 80.0,      # CPU > 80%
    "memory_usage": 85.0,   # Память > 85%
    "disk_usage": 90.0,     # Диск > 90%
    "response_time": 2.0,   # Время ответа > 2с
    "error_rate": 5.0       # Ошибки > 5%
}
```

## 📡 API Endpoints

### Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/` | Информация о сервисе |
| `GET` | `/health` | Проверка здоровья |
| `GET` | `/metrics` | Текущие метрики |
| `GET` | `/metrics/history` | История метрик |
| `GET` | `/alerts` | Список алертов |
| `POST` | `/alerts` | Создание алерта |
| `PUT` | `/alerts/{id}` | Обновление алерта |
| `GET` | `/services` | Статус сервисов |
| `GET` | `/dashboard` | Данные дашборда |
| `POST` | `/metrics/collect` | Принудительный сбор метрик |
| `GET` | `/prometheus` | Prometheus метрики |

### Примеры запросов

```bash
# Получение метрик
curl http://localhost:8002/metrics

# Получение алертов
curl http://localhost:8002/alerts

# Проверка здоровья
curl http://localhost:8002/health

# Создание алерта
curl -X POST http://localhost:8002/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High CPU Usage",
    "description": "CPU usage is 85%",
    "severity": "warning",
    "source": "system",
    "metric_name": "cpu_usage",
    "threshold": 80.0,
    "current_value": 85.0
  }'
```

## 📊 Метрики

### Системные метрики
- `cpu_usage` - Использование CPU (%)
- `memory_usage` - Использование памяти (%)
- `disk_usage` - Использование диска (%)
- `network_in/out` - Сетевой трафик (байт/с)
- `load_average` - Средняя нагрузка системы

### Метрики базы данных
- `active_connections` - Активные подключения
- `total_connections` - Общее количество подключений
- `query_time` - Время выполнения запросов
- `slow_queries` - Количество медленных запросов
- `errors` - Количество ошибок

### Метрики кеша
- `hit_rate` - Процент попаданий в кеш
- `miss_rate` - Процент промахов кеша
- `memory_usage` - Использование памяти кеша
- `keys_count` - Количество ключей
- `evictions` - Количество вытеснений

### Метрики Ollama
- `model` - Название модели
- `response_time` - Время ответа (сек)
- `tokens_per_second` - Токенов в секунду
- `memory_usage` - Использование памяти модели
- `requests_per_minute` - Запросов в минуту
- `errors` - Количество ошибок

## 🚨 Алерты

### Уровни важности
- **INFO** - Информационные сообщения
- **WARNING** - Предупреждения
- **ERROR** - Ошибки
- **CRITICAL** - Критические проблемы

### Статусы алертов
- **ACTIVE** - Активный алерт
- **RESOLVED** - Разрешенный алерт
- **ACKNOWLEDGED** - Подтвержденный алерт

### Автоматические алерты
- Высокое использование CPU (>80%)
- Высокое использование памяти (>85%)
- Высокое использование диска (>90%)
- Медленные запросы к БД (>2с)
- Низкий hit rate кеша (<80%)
- Ошибки Ollama

## 🔍 Мониторинг

### Проверка здоровья сервисов
- **PostgreSQL** - подключение и выполнение запросов
- **Redis** - ping и базовые операции
- **Ollama** - проверка API и моделей

### Логирование
- Структурированные логи в JSON формате
- Различные уровни логирования
- Ротация логов
- Централизованный сбор логов

## 🧪 Тестирование

```bash
# Запуск тестов
pytest

# Запуск с покрытием
pytest --cov=app

# Запуск конкретного теста
pytest tests/test_metrics.py::test_system_metrics
```

## 📈 Производительность

### Оптимизации
- Асинхронная обработка запросов
- Кеширование метрик в Redis
- Периодический сбор метрик
- Эффективные SQL запросы
- Сжатие данных

### Метрики производительности
- Время ответа API < 100ms
- Потребление памяти < 100MB
- CPU использование < 10%
- Доступность > 99.9%

## 🔒 Безопасность

- Валидация всех входных данных
- CORS настройки
- Rate limiting
- Логирование безопасности
- Безопасные подключения к БД

## 🤝 Интеграция

### С фронтендом
- REST API для получения данных
- WebSocket для real-time обновлений
- CORS настройки для кросс-доменных запросов

### С другими сервисами
- Prometheus для экспорта метрик
- Grafana для визуализации
- AlertManager для уведомлений
- ELK Stack для логов

## 📝 Разработка

### Структура проекта
```
monitoring/
├── app/
│   ├── __init__.py
│   ├── main.py          # Основное приложение
│   ├── config.py        # Конфигурация
│   ├── models.py        # Pydantic модели
│   └── services.py      # Бизнес-логика
├── tests/               # Тесты
├── Dockerfile           # Docker образ
├── requirements.txt     # Зависимости
└── README.md           # Документация
```

### Добавление новых метрик
1. Создать модель в `models.py`
2. Добавить метод сбора в `MetricsCollector`
3. Обновить API эндпоинты
4. Добавить тесты

### Добавление новых алертов
1. Определить пороговые значения в конфигурации
2. Добавить проверку в `AlertService`
3. Создать соответствующие алерты
4. Протестировать логику

## 🚀 Развертывание

### Production
```bash
# Сборка production образа
docker build -t relink-monitoring:prod .

# Запуск с production настройками
docker run -d \
  --name monitoring-prod \
  -p 8002:8002 \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=WARNING \
  relink-monitoring:prod
```

### Мониторинг в production
- Health checks каждые 30 секунд
- Автоматический restart при сбоях
- Логирование в stdout/stderr
- Метрики в Prometheus формате

## 📞 Поддержка

- Документация API: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`
- Health check: `http://localhost:8002/health`
- Prometheus metrics: `http://localhost:8002/prometheus`

## 📄 Лицензия

MIT License - см. файл LICENSE в корне проекта. 