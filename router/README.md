# 🧠 LLM Router - Интеллектуальная маршрутизация запросов

## 🎯 Описание

LLM Router - это микросервис для интеллектуальной маршрутизации запросов к оптимальным языковым моделям. Сервис анализирует входящие запросы и автоматически выбирает наиболее подходящую модель на основе сложности задачи, приоритета и доступных ресурсов.

## 🚀 Возможности

- **Интеллектуальный выбор модели** - автоматический анализ запросов для выбора оптимальной модели
- **Пакетная обработка** - одновременная обработка множественных запросов
- **Анализ эффективности** - оценка качества результатов и рекомендации по улучшению
- **Мониторинг производительности** - отслеживание метрик и производительности
- **Интеграция с RAG** - использование векторной базы данных для контекста
- **Нативная интеграция с Ollama** - прямое взаимодействие с локальными моделями

## 🏗️ Архитектура

### Основные компоненты

1. **Route Analyzer** - анализ запросов для выбора модели
2. **Model Selector** - выбор оптимальной модели
3. **Batch Processor** - пакетная обработка запросов
4. **Effectiveness Analyzer** - анализ эффективности результатов
5. **Performance Monitor** - мониторинг производительности

### Поддерживаемые модели

- `qwen2.5:7b-instruct-turbo` - быстрые простые задачи
- `qwen2.5:14b-instruct` - сбалансированные задачи
- `qwen2.5:32b-instruct` - сложные качественные задачи

## 📡 API Endpoints

### POST `/api/v1/route`
Маршрутизация запроса к оптимальной модели

**Request:**
```json
{
  "prompt": "Ваш запрос к модели",
  "model": "qwen2.5:14b-instruct",  // опционально
  "context": {"key": "value"},      // опционально
  "service": "seo-analyzer",        // опционально
  "priority": "normal"              // low, normal, high, critical
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "model_used": "qwen2.5:14b-instruct",
  "response": "Ответ от модели",
  "confidence": 0.95,
  "latency": 1.2,
  "cost_estimate": 0.002,
  "metadata": {
    "method": "direct_ollama",
    "model_selection_reason": "medium_prompt_balanced_model"
  }
}
```

### POST `/api/v1/route/batch`
Пакетная маршрутизация запросов

**Request:**
```json
[
  {
    "prompt": "Первый запрос",
    "model": null,
    "context": {},
    "service": "test-service"
  },
  {
    "prompt": "Второй запрос",
    "model": null,
    "context": {},
    "service": "test-service"
  }
]
```

**Response:**
```json
{
  "batch_id": "uuid",
  "total_requests": 2,
  "successful_results": [...],
  "failed_results": [...],
  "batch_latency": 2.5
}
```

### GET `/api/v1/models`
Получение списка доступных моделей

**Response:**
```json
[
  {
    "name": "qwen2.5:7b-instruct-turbo",
    "description": "Быстрая модель для простых задач",
    "capabilities": ["text-generation", "fast-inference", "basic-qa"],
    "avg_latency": 0.5,
    "avg_cost": 0.001,
    "availability": 1.0
  }
]
```

### POST `/api/v1/analyze`
Анализ эффективности результата

**Request:**
```json
{
  "request_id": "uuid",
  "result": {
    "request_id": "uuid",
    "model_used": "qwen2.5:7b-instruct-turbo",
    "response": "Ответ от модели",
    "confidence": 0.85,
    "latency": 1.2,
    "cost_estimate": 0.002,
    "metadata": {}
  },
  "original_request": {
    "prompt": "Исходный запрос",
    "model": null,
    "context": {},
    "service": "test-service"
  }
}
```

**Response:**
```json
{
  "request_id": "uuid",
  "model_used": "qwen2.5:7b-instruct-turbo",
  "effectiveness_score": 0.87,
  "quality_metrics": {
    "relevance_score": 0.9,
    "completeness_score": 0.85,
    "coherence_score": 0.88,
    "length_appropriate": true
  },
  "recommendations": [
    "Consider using a larger model for better quality"
  ]
}
```

## 🔧 Установка и запуск

### Локальная разработка

```bash
# Клонирование репозитория
git clone <repository-url>
cd router

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервиса
python -m app.main
```

### Docker

```bash
# Сборка образа
docker build -t eberil/relink-router:latest .

# Запуск контейнера
docker run -p 8004:8004 eberil/relink-router:latest
```

### Docker Compose

```bash
# Запуск с полной инфраструктурой
docker-compose up -d
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Конкретный тест
pytest tests/test_main.py::test_route_request_success -v

# С покрытием
pytest tests/ --cov=app --cov-report=html
```

### Тестовые сценарии

1. **Маршрутизация коротких запросов** - проверка выбора быстрых моделей
2. **Маршрутизация длинных запросов** - проверка выбора качественных моделей
3. **Пакетная обработка** - проверка параллельной обработки
4. **Обработка ошибок** - проверка graceful degradation
5. **Анализ эффективности** - проверка метрик качества

## 📊 Мониторинг

### Метрики Prometheus

- `service_requests_total` - общее количество запросов
- `service_request_duration_seconds` - время выполнения запросов
- `service_active_connections` - активные соединения

### Health Check

```bash
curl http://localhost:8004/health
```

### Swagger UI

```
http://localhost:8004/docs
```

## 🔗 Интеграция

### С другими микросервисами

Router интегрируется с:

- **RAG Service** - для получения контекста
- **Ollama** - для генерации ответов
- **Monitoring** - для метрик
- **Database** - для логирования

### Конфигурация

```bash
# Переменные окружения
SERVICE_NAME=router
SERVICE_PORT=8004
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
REDIS_HOST=redis
REDIS_PORT=6379
OLLAMA_URL=http://ollama:11434
```

## 🚀 Производительность

### Ожидаемые метрики

- **Latency**: < 2 секунд для 95% запросов
- **Throughput**: > 100 RPS
- **Availability**: 99.9%
- **Error Rate**: < 1%

### Оптимизации

1. **Кеширование** - кеширование результатов частых запросов
2. **Пакетная обработка** - группировка запросов для эффективности
3. **Асинхронность** - неблокирующая обработка
4. **Connection pooling** - переиспользование соединений

## 🔒 Безопасность

- Валидация входных данных
- Rate limiting
- Аутентификация (планируется)
- Логирование всех операций

## 📈 Планы развития

- [ ] Интеграция с внешними LLM API
- [ ] Машинное обучение для выбора модели
- [ ] A/B тестирование моделей
- [ ] Автоматическое масштабирование
- [ ] Расширенная аналитика

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License
