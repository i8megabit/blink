# ⚡ Benchmark - Тестирование производительности reLink

Система тестирования производительности для платформы reLink с комплексными бенчмарками всех компонентов.

## 🚀 Быстрый старт

```bash
# Запуск через Docker Compose
docker-compose up -d

# Локальная разработка
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005

# Запуск тестов
pytest tests/
```

## 🏗️ Архитектура

### Технологический стек
- **FastAPI** - веб-фреймворк для API
- **Locust** - нагрузочное тестирование
- **pytest-benchmark** - бенчмарки производительности
- **SQLAlchemy** - ORM для работы с БД
- **Redis** - кэширование результатов
- **Prometheus** - сбор метрик

### Структура проекта
```
app/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Подключение к БД
├── models.py            # Модели данных
├── services.py          # Бизнес-логика
├── benchmark.py         # Основные бенчмарки
└── api/
    └── routes.py        # API роуты

tests/
├── test_api.py          # API тесты
├── test_benchmark_service.py  # Тесты бенчмарков
└── test_main.py         # Основные тесты

scripts/
└── run_benchmarks.sh    # Скрипт запуска бенчмарков
```

## 🎯 Основные функции

### Нагрузочное тестирование
- Тестирование API эндпоинтов
- Симуляция пользовательских сценариев
- Измерение пропускной способности
- Анализ времени ответа

### Бенчмарки производительности
- CPU и память
- Сетевая производительность
- База данных
- Кэширование

### Стресс-тестирование
- Максимальная нагрузка
- Долгосрочное тестирование
- Тестирование отказоустойчивости
- Восстановление после сбоев

### Анализ результатов
- Детальные отчеты
- Графики производительности
- Сравнение версий
- Рекомендации по оптимизации

## 🔧 Разработка

### Команды разработки
```bash
# Запуск сервиса
uvicorn app.main:app --reload --port 8005

# Запуск тестов
pytest tests/ -v

# Запуск бенчмарков
python -m pytest tests/ --benchmark-only

# Запуск нагрузочных тестов
locust -f locustfile.py
```

### Создание бенчмарков
```python
from app.benchmark import BenchmarkService

# Инициализация сервиса
benchmark = BenchmarkService()

# Создание бенчмарка API
benchmark.create_api_benchmark(
    endpoint="/api/v1/analyze",
    method="POST",
    data={"url": "https://example.com"}
)

# Создание бенчмарка базы данных
benchmark.create_db_benchmark(
    query="SELECT * FROM users",
    iterations=1000
)
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

### Бенчмарки
```bash
# Запуск всех бенчмарков
pytest --benchmark-only

# Запуск конкретного бенчмарка
pytest tests/test_benchmark_service.py::test_api_performance --benchmark-only

# Сравнение с предыдущими результатами
pytest --benchmark-only --benchmark-compare
```

## 🐳 Docker

### Сборка образа
```bash
# Сборка образа
docker build -t relink-benchmark .

# Запуск контейнера
docker run -p 8005:8005 relink-benchmark
```

### Docker Compose
```bash
# Запуск с зависимостями
docker-compose up -d

# Просмотр логов
docker-compose logs -f benchmark
```

## 📊 API Документация

### Swagger UI
- **Локально**: http://localhost:8005/docs
- **ReDoc**: http://localhost:8005/redoc

### Основные эндпоинты
- `GET /health` - проверка здоровья
- `POST /benchmark/run` - запуск бенчмарка
- `GET /benchmark/results` - результаты бенчмарков
- `GET /benchmark/reports` - отчеты производительности

## 📈 Типы бенчмарков

### API бенчмарки
```python
# Тестирование эндпоинтов
benchmark.test_api_endpoint(
    url="/api/v1/analyze",
    method="POST",
    data={"url": "https://example.com"},
    iterations=1000,
    concurrent_users=10
)
```

### База данных бенчмарки
```python
# Тестирование запросов
benchmark.test_database_query(
    query="SELECT * FROM users WHERE active = true",
    iterations=1000,
    connection_pool_size=10
)
```

### Системные бенчмарки
```python
# Тестирование CPU
benchmark.test_cpu_performance(
    iterations=1000,
    complexity="high"
)

# Тестирование памяти
benchmark.test_memory_usage(
    data_size="1GB",
    iterations=100
)
```

## 📊 Метрики производительности

### Время ответа
- Среднее время ответа
- 95-й процентиль
- 99-й процентиль
- Максимальное время ответа

### Пропускная способность
- Запросов в секунду
- Одновременных пользователей
- Обработанных транзакций

### Ресурсы
- Использование CPU
- Использование памяти
- Сетевой трафик
- Дисковые операции

## 📋 Отчеты

### Детальные отчеты
```python
# Генерация отчета
report = benchmark.generate_report(
    test_name="api_performance",
    format="html"
)

# Экспорт результатов
benchmark.export_results(
    format="json",
    filename="benchmark_results.json"
)
```

### Сравнительные отчеты
```python
# Сравнение версий
comparison = benchmark.compare_versions(
    version1="v1.0.0",
    version2="v1.1.0",
    tests=["api", "database", "system"]
)
```

## 🔗 Интеграции

### Locust
- Нагрузочное тестирование
- Пользовательские сценарии
- Распределенное тестирование
- Веб-интерфейс

### Prometheus
- Сбор метрик
- Мониторинг производительности
- Алерты
- Исторические данные

### Grafana
- Визуализация результатов
- Дашборды производительности
- Тренды и аналитика
- Экспорт отчетов

## 🚀 Деплой

### Продакшен
```bash
# Сборка продакшен образа
docker build -t relink-benchmark:prod .

# Запуск с переменными окружения
docker run -e DATABASE_URL=... relink-benchmark:prod
```

### CI/CD
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging

## 📚 Дополнительная документация

- [API документация](https://api.relink.dev)
- [Locust конфигурация](locustfile.py)
- [Бенчмарки](app/benchmark.py)
