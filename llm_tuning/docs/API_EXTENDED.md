# 🚀 Расширенная API Документация

## 📋 Обзор

Этот документ описывает расширенные API эндпоинты LLM Tuning Microservice, включающие:

- 🧪 **A/B Тестирование** - сравнение производительности моделей
- ⚡ **Автоматическая оптимизация** - улучшение моделей
- 🎯 **Оценка качества** - анализ качества ответов
- 🏥 **Мониторинг здоровья** - состояние системы
- 📊 **Расширенная статистика** - детальная аналитика

---

## 🧪 A/B Тестирование

### Создание A/B теста

**POST** `/api/v1/ab-tests`

Создает новый A/B тест для сравнения производительности моделей.

#### Запрос

```json
{
  "name": "SEO Content Quality Test",
  "description": "Тестирование качества SEO контента между разными моделями",
  "model_id": 1,
  "variant_a": "llama2:7b",
  "variant_b": "llama2:13b",
  "traffic_split": 0.5,
  "test_duration_days": 7,
  "success_metrics": ["response_time", "quality_score", "user_satisfaction"],
  "minimum_sample_size": 1000
}
```

#### Ответ

```json
{
  "id": 1,
  "name": "SEO Content Quality Test",
  "description": "Тестирование качества SEO контента между разными моделями",
  "model_id": 1,
  "variant_a": "llama2:7b",
  "variant_b": "llama2:13b",
  "traffic_split": 0.5,
  "test_duration_days": 7,
  "success_metrics": ["response_time", "quality_score", "user_satisfaction"],
  "minimum_sample_size": 1000,
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-01-22T10:30:00Z"
}
```

### Список A/B тестов

**GET** `/api/v1/ab-tests`

Получает список всех A/B тестов с возможностью фильтрации.

#### Параметры запроса

- `skip` (int, опционально): Количество записей для пропуска
- `limit` (int, опционально): Максимальное количество записей
- `status` (string, опционально): Фильтр по статусу
- `model_id` (int, опционально): Фильтр по ID модели

#### Ответ

```json
[
  {
    "id": 1,
    "name": "SEO Content Quality Test",
    "status": "active",
    "variant_a": "llama2:7b",
    "variant_b": "llama2:13b",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### Получение A/B теста

**GET** `/api/v1/ab-tests/{test_id}`

Получает детальную информацию о конкретном A/B тесте.

#### Ответ

```json
{
  "id": 1,
  "name": "SEO Content Quality Test",
  "description": "Тестирование качества SEO контента между разными моделями",
  "model_id": 1,
  "variant_a": "llama2:7b",
  "variant_b": "llama2:13b",
  "traffic_split": 0.5,
  "test_duration_days": 7,
  "success_metrics": ["response_time", "quality_score", "user_satisfaction"],
  "minimum_sample_size": 1000,
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-01-22T10:30:00Z",
  "results": {
    "variant_a_stats": {
      "total_requests": 500,
      "avg_response_time": 2.1,
      "avg_quality_score": 8.2,
      "success_rate": 0.98
    },
    "variant_b_stats": {
      "total_requests": 500,
      "avg_response_time": 3.5,
      "avg_quality_score": 8.8,
      "success_rate": 0.97
    },
    "statistical_significance": true,
    "winner": "variant_b"
  }
}
```

### Обновление A/B теста

**PUT** `/api/v1/ab-tests/{test_id}`

Обновляет параметры A/B теста.

#### Запрос

```json
{
  "name": "Updated SEO Content Quality Test",
  "traffic_split": 0.6,
  "test_duration_days": 14
}
```

### Выбор модели для A/B теста

**POST** `/api/v1/ab-tests/{test_id}/select-model`

Выбирает модель для запроса в рамках A/B теста.

#### Запрос

```json
{
  "request_type": "seo_content_generation",
  "user_id": "user_123"
}
```

#### Ответ

```json
{
  "model_name": "llama2:13b",
  "variant": "variant_b",
  "test_id": 1
}
```

### Запись результатов A/B теста

**POST** `/api/v1/ab-tests/{test_id}/record-result`

Записывает результаты выполнения запроса для A/B теста.

#### Запрос

```json
{
  "model_variant": "llama2:13b",
  "metrics": {
    "response_time": 2.5,
    "quality_score": 8.5,
    "user_satisfaction": 4.2,
    "tokens_generated": 150,
    "tokens_processed": 50,
    "success": true
  }
}
```

---

## ⚡ Автоматическая оптимизация

### Запуск оптимизации

**POST** `/api/v1/optimization`

Запускает автоматическую оптимизацию модели.

#### Запрос

```json
{
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
}
```

#### Ответ

```json
{
  "id": 1,
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
  ],
  "status": "running",
  "progress": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T12:30:00Z"
}
```

### Получение статуса оптимизации

**GET** `/api/v1/optimization/{optimization_id}`

Получает текущий статус и прогресс оптимизации.

#### Ответ

```json
{
  "id": 1,
  "model_id": 1,
  "optimization_type": "performance",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T12:25:00Z",
  "improvements": {
    "response_time": {
      "before": 3.2,
      "after": 1.8,
      "improvement": 43.75
    },
    "quality_score": {
      "before": 7.5,
      "after": 8.2,
      "improvement": 9.33
    },
    "error_rate": {
      "before": 0.05,
      "after": 0.02,
      "improvement": 60.0
    }
  },
  "optimized_model_name": "llama2:7b-optimized-v1",
  "applied_strategies": [
    "quantization",
    "hyperparameter_tuning"
  ]
}
```

---

## 🎯 Оценка качества

### Оценка качества ответа

**POST** `/api/v1/quality/assess`

Оценивает качество ответа модели по различным критериям.

#### Запрос

```json
{
  "model_id": 1,
  "request_text": "Создай SEO-оптимизированную статью о машинном обучении",
  "response_text": "Машинное обучение - это подраздел искусственного интеллекта...",
  "context_documents": [
    "Машинное обучение использует алгоритмы для анализа данных...",
    "Основные типы ML: supervised, unsupervised, reinforcement learning..."
  ],
  "assessment_criteria": [
    "relevance",
    "accuracy",
    "completeness",
    "seo_optimization"
  ]
}
```

#### Ответ

```json
{
  "id": 1,
  "model_id": 1,
  "request_text": "Создай SEO-оптимизированную статью о машинном обучении",
  "response_text": "Машинное обучение - это подраздел искусственного интеллекта...",
  "overall_score": 8.5,
  "detailed_scores": {
    "relevance": 9.0,
    "accuracy": 8.5,
    "completeness": 8.0,
    "seo_optimization": 8.5
  },
  "assessment_criteria": [
    "relevance",
    "accuracy",
    "completeness",
    "seo_optimization"
  ],
  "assessed_at": "2024-01-15T10:30:00Z",
  "assessor": "automated"
}
```

### Статистика качества модели

**GET** `/api/v1/quality/stats/{model_id}`

Получает статистику качества модели за указанный период.

#### Параметры запроса

- `days` (int, опционально): Количество дней для анализа (по умолчанию 30)

#### Ответ

```json
{
  "model_id": 1,
  "model_name": "llama2:7b",
  "avg_score": 8.2,
  "total_assessments": 150,
  "score_distribution": {
    "excellent": 45,
    "good": 60,
    "average": 30,
    "poor": 15
  },
  "trend": "improving",
  "trend_data": [
    {
      "date": "2024-01-01",
      "avg_score": 7.8,
      "assessments": 5
    },
    {
      "date": "2024-01-02",
      "avg_score": 8.1,
      "assessments": 7
    }
  ],
  "criteria_performance": {
    "relevance": 8.5,
    "accuracy": 8.0,
    "completeness": 7.8,
    "seo_optimization": 8.3
  }
}
```

---

## 🏥 Мониторинг здоровья системы

### Состояние здоровья системы

**GET** `/api/v1/health/system`

Получает текущее состояние здоровья системы.

#### Ответ

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 23.4,
  "ollama_status": "healthy",
  "rag_status": "healthy",
  "response_time_avg": 2.1,
  "error_rate": 0.02,
  "total_requests": 1250,
  "active_models": 3,
  "active_routes": 5,
  "alerts": [
    {
      "level": "warning",
      "message": "Memory usage is high",
      "timestamp": "2024-01-15T10:25:00Z"
    }
  ],
  "overall_status": "healthy"
}
```

### История здоровья системы

**GET** `/api/v1/health/system/history`

Получает историю состояния здоровья системы.

#### Параметры запроса

- `hours` (int, опционально): Количество часов для анализа (по умолчанию 24)

#### Ответ

```json
{
  "records": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "disk_usage": 23.4,
      "ollama_status": "healthy",
      "rag_status": "healthy",
      "response_time_avg": 2.1,
      "error_rate": 0.02,
      "alerts_count": 1
    },
    {
      "timestamp": "2024-01-15T09:30:00Z",
      "cpu_usage": 42.1,
      "memory_usage": 65.3,
      "disk_usage": 23.4,
      "ollama_status": "healthy",
      "rag_status": "healthy",
      "response_time_avg": 2.0,
      "error_rate": 0.01,
      "alerts_count": 0
    }
  ]
}
```

---

## 📊 Расширенная статистика

### Статистика модели

**GET** `/api/v1/stats/models/{model_id}`

Получает детальную статистику модели за указанный период.

#### Параметры запроса

- `days` (int, опционально): Количество дней для анализа (по умолчанию 30)

#### Ответ

```json
{
  "model_id": 1,
  "model_name": "llama2:7b",
  "total_requests": 2500,
  "successful_requests": 2450,
  "failed_requests": 50,
  "avg_response_time": 2.1,
  "avg_quality_score": 8.2,
  "total_tokens_generated": 125000,
  "total_tokens_processed": 45000,
  "error_rate": 0.02,
  "last_used": "2024-01-15T10:30:00Z",
  "performance_trend": [
    {
      "date": "2024-01-01",
      "requests": 85,
      "avg_response_time": 2.3,
      "success_rate": 0.98
    },
    {
      "date": "2024-01-02",
      "requests": 92,
      "avg_response_time": 2.1,
      "success_rate": 0.99
    }
  ]
}
```

### Общая статистика системы

**GET** `/api/v1/stats/system`

Получает общую статистику системы.

#### Ответ

```json
{
  "total_models": 5,
  "active_models": 3,
  "total_routes": 8,
  "active_routes": 6,
  "total_documents": 1500,
  "total_requests_today": 1250,
  "avg_response_time": 2.1,
  "error_rate": 0.02,
  "system_health": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.4,
    "ollama_status": "healthy",
    "rag_status": "healthy",
    "overall_status": "healthy"
  },
  "top_models": [
    {
      "model_id": 1,
      "model_name": "llama2:7b",
      "total_requests": 500,
      "avg_response_time": 1.8,
      "avg_quality_score": 8.5
    },
    {
      "model_id": 2,
      "model_name": "llama2:13b",
      "total_requests": 450,
      "avg_response_time": 3.2,
      "avg_quality_score": 8.8
    }
  ]
}
```

---

## 🔧 Коды ошибок

### Общие ошибки

| Код | Описание |
|-----|----------|
| 400 | Неверный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещен |
| 404 | Ресурс не найден |
| 422 | Ошибка валидации |
| 500 | Внутренняя ошибка сервера |

### Специфичные ошибки

| Код | Описание |
|-----|----------|
| 4001 | A/B тест не найден |
| 4002 | Недостаточно данных для A/B теста |
| 4003 | Модель не найдена |
| 4004 | Оптимизация не найдена |
| 4005 | Ошибка оценки качества |
| 4006 | Система недоступна |

---

## 📝 Примеры использования

### Python с aiohttp

```python
import aiohttp
import asyncio

async def create_ab_test():
    async with aiohttp.ClientSession() as session:
        test_data = {
            "name": "SEO Content Quality Test",
            "model_id": 1,
            "variant_a": "llama2:7b",
            "variant_b": "llama2:13b",
            "traffic_split": 0.5
        }
        
        async with session.post(
            "http://localhost:8000/api/v1/ab-tests",
            json=test_data
        ) as response:
            return await response.json()

# Запуск
result = asyncio.run(create_ab_test())
print(result)
```

### cURL

```bash
# Создание A/B теста
curl -X POST "http://localhost:8000/api/v1/ab-tests" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SEO Content Quality Test",
    "model_id": 1,
    "variant_a": "llama2:7b",
    "variant_b": "llama2:13b",
    "traffic_split": 0.5
  }'

# Получение состояния здоровья
curl -X GET "http://localhost:8000/api/v1/health/system"

# Статистика модели
curl -X GET "http://localhost:8000/api/v1/stats/models/1?days=30"
```

---

## 🚀 Интеграция с reLink

Для интеграции с основным приложением reLink используйте `relink_client.py`:

```python
from relink_client import RelinkLLMClient

client = RelinkLLMClient("http://localhost:8000")

# Создание A/B теста
ab_test = await client.create_ab_test({
    "name": "SEO Content Quality Test",
    "model_id": 1,
    "variant_a": "llama2:7b",
    "variant_b": "llama2:13b"
})

# Оценка качества
quality = await client.assess_quality(
    model_id=1,
    request_text="Создай SEO статью",
    response_text="SEO статья о..."
)

# Мониторинг здоровья
health = await client.get_system_health()
```

---

## 📚 Дополнительные ресурсы

- [Основная документация](README.md)
- [Интеграция с reLink](INTEGRATION.md)
- [Примеры использования](examples/)
- [Конфигурация](config.py)
- [Тесты](tests/) 