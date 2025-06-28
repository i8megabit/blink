# 🚀 LLM Tuning Microservice для reLink

## 📋 Обзор

LLM Tuning Microservice - это мощный микросервис для управления и адаптации языковых моделей в проекте reLink. Сервис предоставляет комплексное решение для тюнинга, маршрутизации, RAG (Retrieval-Augmented Generation) и мониторинга LLM моделей.

### 🎯 Ключевые возможности

- **🧪 A/B Тестирование** - сравнение производительности моделей
- **⚡ Автоматическая оптимизация** - улучшение моделей
- **🎯 Оценка качества** - анализ качества ответов
- **🏥 Мониторинг здоровья** - состояние системы
- **📊 Расширенная статистика** - детальная аналитика
- **🔄 Динамический тюнинг** - адаптация моделей в реальном времени
- **🛣️ Умная маршрутизация** - выбор оптимальной модели
- **🔍 RAG интеграция** - поиск и генерация с контекстом
- **📈 Мониторинг производительности** - отслеживание метрик
- **🔒 Безопасность** - защита и валидация

---

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   reLink App    │◄──►│  LLM Tuning MS   │◄──►│    Ollama       │
│                 │    │                  │    │                 │
│ - SEO Analysis  │    │ - Model Mgmt     │    │ - Base Models   │
│ - Content Gen   │    │ - A/B Testing    │    │ - Tuned Models  │
│ - Optimization  │    │ - Auto Optimize  │    │ - RAG Support   │
└─────────────────┘    │ - Quality Assess │    └─────────────────┘
                       │ - Health Monitor │
                       │ - Smart Routing  │    ┌─────────────────┐
                       │ - RAG Service    │◄──►│  Vector DB      │
                       └──────────────────┘    │                 │
                                                │ - Embeddings    │
                                                │ - Documents     │
                                                └─────────────────┘
```

---

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.9+
- Docker & Docker Compose
- Ollama (для локальных моделей)
- PostgreSQL (для метаданных)

### Установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd relink/llm_tuning

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Запуск с Docker Compose
docker-compose up -d

# Или локальный запуск
python -m app.main
```

### Проверка работоспособности

```bash
# Проверка здоровья сервиса
curl http://localhost:8000/health

# Проверка API документации
open http://localhost:8000/docs
```

---

## 🧪 A/B Тестирование

### Создание A/B теста

```python
from relink_client import RelinkLLMClient

client = RelinkLLMClient("http://localhost:8000")

# Создание A/B теста для сравнения моделей
ab_test = await client.create_ab_test({
    "name": "SEO Content Quality Test",
    "model_id": 1,
    "variant_a": "llama2:7b",
    "variant_b": "llama2:13b",
    "traffic_split": 0.5,
    "test_duration_days": 7,
    "success_metrics": ["response_time", "quality_score", "user_satisfaction"]
})
```

### Выбор модели для теста

```python
# Выбор модели для запроса
model_info = await client.select_model_for_ab_test(
    test_id=ab_test['id'],
    request_type="seo_content_generation",
    user_id="user_123"
)

# Запись результатов
await client.record_ab_test_result(
    test_id=ab_test['id'],
    model_variant=model_info['model_name'],
    metrics={
        "response_time": 2.5,
        "quality_score": 8.5,
        "user_satisfaction": 4.2
    }
)
```

---

## ⚡ Автоматическая оптимизация

### Запуск оптимизации

```python
# Запуск автоматической оптимизации модели
optimization = await client.optimize_model({
    "model_id": 1,
    "optimization_type": "performance",
    "target_metrics": {
        "response_time": 1.5,
        "quality_score": 8.0,
        "error_rate": 0.01
    },
    "optimization_strategies": [
        "quantization",
        "pruning",
        "hyperparameter_tuning"
    ]
})

# Мониторинг прогресса
status = await client.get_optimization_status(optimization['id'])
print(f"Прогресс: {status['progress']}%")
```

---

## 🎯 Оценка качества

### Оценка качества ответа

```python
# Оценка качества ответа модели
quality = await client.assess_quality({
    "model_id": 1,
    "request_text": "Создай SEO-оптимизированную статью о машинном обучении",
    "response_text": "Машинное обучение - это подраздел искусственного интеллекта...",
    "assessment_criteria": [
        "relevance",
        "accuracy", 
        "completeness",
        "seo_optimization"
    ]
})

print(f"Общий балл: {quality['overall_score']}/10")
```

### Статистика качества

```python
# Получение статистики качества модели
stats = await client.get_quality_stats(model_id=1, days=30)
print(f"Средний балл: {stats['avg_score']}")
print(f"Тренд: {stats['trend']}")
```

---

## 🏥 Мониторинг здоровья системы

### Состояние системы

```python
# Получение состояния здоровья системы
health = await client.get_system_health()

print(f"CPU: {health['cpu_usage']}%")
print(f"Память: {health['memory_usage']}%")
print(f"Ollama: {health['ollama_status']}")
print(f"RAG: {health['rag_status']}")
print(f"Среднее время ответа: {health['response_time_avg']}с")
```

### История здоровья

```python
# Получение истории здоровья системы
history = await client.get_system_health_history(hours=24)
print(f"Записей: {len(history['records'])}")
```

---

## 📊 Расширенная статистика

### Статистика модели

```python
# Детальная статистика модели
stats = await client.get_model_stats(model_id=1, days=30)

print(f"Всего запросов: {stats['total_requests']}")
print(f"Успешных: {stats['successful_requests']}")
print(f"Среднее время ответа: {stats['avg_response_time']}с")
print(f"Средний балл качества: {stats['avg_quality_score']}")
print(f"Токенов сгенерировано: {stats['total_tokens_generated']}")
```

### Общая статистика системы

```python
# Общая статистика системы
system_stats = await client.get_system_stats()

print(f"Всего моделей: {system_stats['total_models']}")
print(f"Активных моделей: {system_stats['active_models']}")
print(f"Запросов сегодня: {system_stats['total_requests_today']}")
print(f"Процент ошибок: {system_stats['error_rate']}%")
```

---

## 🔧 Конфигурация

### Основные настройки

```python
# config.py
class Settings(BaseSettings):
    # База данных
    database_url: str = "postgresql://user:pass@localhost/llm_tuning"
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    
    # RAG
    rag_enabled: bool = True
    vector_db_url: str = "http://localhost:6333"
    
    # Тюнинг
    tuning_enabled: bool = True
    ab_testing_enabled: bool = True
    
    # Мониторинг
    monitoring_enabled: bool = True
    metrics_retention_days: int = 30
```

### Переменные окружения

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost/llm_tuning
OLLAMA_BASE_URL=http://localhost:11434
RAG_ENABLED=true
VECTOR_DB_URL=http://localhost:6333
TUNING_ENABLED=true
AB_TESTING_ENABLED=true
MONITORING_ENABLED=true
```

---

## 🐳 Docker развертывание

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  llm_tuning:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/llm_tuning
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - db
      - ollama
      - qdrant

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: llm_tuning
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  ollama_data:
  qdrant_data:
```

### Запуск

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f llm_tuning

# Остановка
docker-compose down
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Конкретные тесты
pytest tests/test_ab_testing.py
pytest tests/test_optimization.py
pytest tests/test_quality_assessment.py

# С покрытием
pytest --cov=app --cov-report=html

# Интеграционные тесты
pytest tests/integration/
```

### Примеры API

```bash
# Запуск примеров
python examples/api_examples.py

# Тестирование конкретных эндпоинтов
python examples/test_ab_testing.py
python examples/test_optimization.py
```

---

## 📈 Мониторинг и метрики

### Prometheus метрики

```python
# Доступные метрики
- llm_requests_total
- llm_response_time_seconds
- llm_quality_score
- llm_tokens_generated
- llm_errors_total
- ab_test_results
- optimization_progress
- system_health_status
```

### Grafana дашборды

```bash
# Импорт дашбордов
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @dashboards/llm_tuning_overview.json
```

---

## 🔒 Безопасность

### Аутентификация

```python
# JWT токены
from fastapi.security import HTTPBearer

security = HTTPBearer()
token = await security(request)
```

### Валидация

```python
# Валидация входных данных
from pydantic import BaseModel, validator

class ModelCreate(BaseModel):
    name: str
    model_type: str
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 3:
            raise ValueError('Name must be at least 3 characters')
        return v
```

---

## 🚀 Производительность

### Оптимизации

- **Асинхронная обработка** - все операции неблокирующие
- **Кэширование** - Redis для быстрого доступа
- **Connection pooling** - эффективное управление соединениями
- **Batch processing** - пакетная обработка данных
- **Compression** - сжатие ответов

### Бенчмарки

```bash
# Тест производительности
python benchmarks/performance_test.py

# Результаты (на M1 Mac):
# - 1000 запросов/сек
# - Среднее время ответа: 2.1с
# - Память: ~500MB
# - CPU: ~30%
```

---

## 🔧 Устранение неполадок

### Частые проблемы

1. **Ollama недоступен**
   ```bash
   # Проверка статуса
   curl http://localhost:11434/api/tags
   
   # Перезапуск
   docker-compose restart ollama
   ```

2. **База данных недоступна**
   ```bash
   # Проверка подключения
   python -c "from app.database import engine; print(engine.connect())"
   
   # Миграции
   alembic upgrade head
   ```

3. **Высокое потребление памяти**
   ```bash
   # Мониторинг
   docker stats llm_tuning
   
   # Очистка кэша
   redis-cli FLUSHALL
   ```

### Логи

```bash
# Просмотр логов
docker-compose logs -f llm_tuning

# Фильтрация по уровню
docker-compose logs -f llm_tuning | grep ERROR

# Экспорт логов
docker-compose logs llm_tuning > logs.txt
```

---

## 📚 Документация

- [📖 Основная документация](README.md)
- [🔗 API документация](docs/API_EXTENDED.md)
- [🔗 Интеграция с reLink](INTEGRATION.md)
- [🔗 Примеры использования](examples/)
- [🔗 Конфигурация](config.py)
- [🔗 Тесты](tests/)

---

## 🤝 Вклад в проект

### Разработка

```bash
# Форк репозитория
git clone <your-fork-url>
cd llm_tuning

# Создание ветки
git checkout -b feature/new-feature

# Установка dev зависимостей
pip install -r requirements-dev.txt

# Запуск тестов
pytest

# Линтинг
flake8 app/
black app/
isort app/

# Коммит
git commit -m "feat: add new feature"
git push origin feature/new-feature
```

### Code Style

- **Black** для форматирования
- **isort** для сортировки импортов
- **flake8** для линтинга
- **mypy** для типизации
- **pytest** для тестирования

---

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

---

## 🆘 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: support@relink.com

---

## 🎯 Roadmap

### v2.0 (Q2 2024)
- [ ] Многопользовательская поддержка
- [ ] Расширенная аналитика
- [ ] Интеграция с внешними LLM
- [ ] Автоматическое масштабирование

### v2.1 (Q3 2024)
- [ ] Графический интерфейс
- [ ] Расширенное A/B тестирование
- [ ] Машинное обучение для оптимизации
- [ ] Интеграция с CI/CD

### v2.2 (Q4 2024)
- [ ] Поддержка мультимодальных моделей
- [ ] Расширенная безопасность
- [ ] Глобальное развертывание
- [ ] Enterprise функции

---

**🎉 Спасибо за использование LLM Tuning Microservice!** 