# 🧠 Интеллектуальная система оптимизации reLink

## Обзор

Интеллектуальная система оптимизации reLink - это революционная система, которая использует **RAG (Retrieval-Augmented Generation)** и **LLM** для автоматического определения оптимальной конфигурации для вашего ПК. Система анализирует характеристики вашего оборудования, историю производительности и использует базу знаний для принятия интеллектуальных решений об оптимизации.

## 🎯 Основные возможности

### 1. Автоопределение системных характеристик
- **Анализ процессора**: Apple Silicon M1/M2/M4, Intel, AMD
- **Определение GPU**: NVIDIA, AMD, Apple Silicon GPU
- **Анализ памяти**: объем RAM, тип памяти
- **Платформа**: macOS, Linux, Windows

### 2. LLM-рекомендации для оптимизации
- **Интеллектуальный анализ**: LLM анализирует характеристики системы
- **Контекстные решения**: учитывает историю производительности
- **Адаптивные параметры**: автоматическая настройка всех параметров Ollama

### 3. RAG-подход к принятию решений
- **База знаний**: содержит информацию о производительности разных систем
- **Семантический поиск**: находит релевантные знания для вашей системы
- **Контекстное обогащение**: использует найденные знания для принятия решений

### 4. Адаптивная оптимизация
- **Мониторинг производительности**: отслеживает время ответа и успешность
- **Автоматическая адаптация**: переоптимизирует при ухудшении производительности
- **История оптимизаций**: сохраняет все изменения для анализа

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Интеллектуальная система                 │
├─────────────────────────────────────────────────────────────┤
│  🔍 SystemAnalyzer                                          │
│  ├── analyze_system()      # Анализ характеристик          │
│  ├── optimize_config()     # LLM-оптимизация               │
│  ├── record_performance()  # Мониторинг производительности │
│  └── _analyze_and_adapt()  # Адаптивная оптимизация        │
├─────────────────────────────────────────────────────────────┤
│  🧠 LLM Router                                             │
│  ├── _make_ollama_request() # Интеллектуальные запросы     │
│  ├── process_request()      # Полный pipeline              │
│  └── get_stats()           # Статистика                    │
├─────────────────────────────────────────────────────────────┤
│  📚 База знаний                                            │
│  ├── Apple Silicon M1/M2/M4                                │
│  ├── NVIDIA GPU                                            │
│  ├── AMD GPU                                               │
│  └── CPU-only системы                                      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Быстрый старт

### 1. Запуск системы

```bash
# Запуск backend с интеллектуальной оптимизацией
cd relink/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Проверка оптимизации

```bash
# Получение отчета об оптимизации
curl http://localhost:8000/api/v1/optimization/report

# Получение переменных окружения
curl http://localhost:8000/api/v1/optimization/environment

# Принудительная оптимизация
curl -X POST http://localhost:8000/api/v1/optimization/trigger
```

### 3. Тестирование системы

```bash
# Запуск тестового скрипта
cd relink/backend
python test_intelligent_optimization.py
```

## 📊 API Endpoints

### GET `/api/v1/optimization/report`
Получение полного отчета об интеллектуальной оптимизации.

**Ответ:**
```json
{
  "system_specs": {
    "platform": "Darwin",
    "architecture": "arm64",
    "cpu_count": 8,
    "memory_gb": 16.0,
    "gpu_available": true,
    "gpu_type": "Apple Silicon GPU",
    "apple_silicon": true,
    "m1_m2_m4": true
  },
  "optimized_config": {
    "model": "qwen2.5:7b-instruct-turbo",
    "num_gpu": 1,
    "num_thread": 8,
    "batch_size": 1024,
    "f16_kv": true,
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_length": 8192,
    "keep_alive": "2h",
    "request_timeout": 300,
    "semaphore_limit": 8,
    "cache_ttl": 3600
  },
  "performance_history": {
    "total_records": 15,
    "recent_avg_response_time": 1.85,
    "recent_success_rate": 0.93
  },
  "optimization_status": {
    "llm_recommendations_applied": true,
    "adaptive_optimization_active": true,
    "performance_monitoring": true,
    "knowledge_base_entries": 6,
    "last_optimization": "2024-01-15T10:30:00"
  }
}
```

### GET `/api/v1/optimization/environment`
Получение оптимизированных переменных окружения для Ollama.

**Ответ:**
```json
{
  "environment_variables": {
    "OLLAMA_HOST": "0.0.0.0",
    "OLLAMA_ORIGINS": "*",
    "OLLAMA_KEEP_ALIVE": "2h",
    "OLLAMA_CONTEXT_LENGTH": "8192",
    "OLLAMA_BATCH_SIZE": "1024",
    "OLLAMA_NUM_PARALLEL": "8",
    "REQUEST_TIMEOUT": "300",
    "OLLAMA_METAL": "1",
    "OLLAMA_FLASH_ATTENTION": "1",
    "OLLAMA_KV_CACHE_TYPE": "q8_0",
    "OLLAMA_MEM_FRACTION": "0.9"
  },
  "optimization_applied": true,
  "recommended_ollama_command": "OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS=* ollama serve"
}
```

### POST `/api/v1/optimization/trigger`
Принудительный запуск оптимизации.

**Ответ:**
```json
{
  "message": "Оптимизация успешно запущена",
  "new_config": {
    "model": "qwen2.5:7b-instruct-turbo",
    "num_gpu": 1,
    "num_thread": 8,
    "batch_size": 1024,
    "context_length": 8192,
    "semaphore_limit": 8
  },
  "optimization_timestamp": "2024-01-15T10:30:00"
}
```

## 🔧 Конфигурация

### Системные требования

- **Python 3.8+**
- **Ollama** с поддержкой модели `qwen2.5:7b-instruct-turbo`
- **Минимум 8GB RAM** (рекомендуется 16GB+)
- **Apple Silicon M1/M2/M4** (оптимально) или **NVIDIA GPU**

### Переменные окружения

```bash
# Основные настройки
OLLAMA_URL=http://localhost:11434
OLLAMA_HOST=0.0.0.0
OLLAMA_ORIGINS=*

# Apple Silicon оптимизации
OLLAMA_METAL=1
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0
OLLAMA_MEM_FRACTION=0.9

# Производительность
OLLAMA_KEEP_ALIVE=2h
OLLAMA_CONTEXT_LENGTH=8192
OLLAMA_BATCH_SIZE=1024
OLLAMA_NUM_PARALLEL=8
REQUEST_TIMEOUT=300
```

## 📈 Мониторинг производительности

### Метрики отслеживания

- **Время ответа**: среднее время обработки запросов
- **Процент успеха**: доля успешных запросов
- **Использование токенов**: количество токенов на запрос
- **Использование ресурсов**: CPU, GPU, память

### Адаптивная оптимизация

Система автоматически переоптимизируется при:
- Время ответа > 5 секунд
- Процент успеха < 80%
- Ухудшение производительности на 20%+

## 🧪 Тестирование

### Запуск тестов

```bash
# Тестирование интеллектуальной системы
python test_intelligent_optimization.py

# Тестирование API
curl http://localhost:8000/api/v1/optimization/report

# Тестирование производительности
ab -n 100 -c 10 http://localhost:8000/api/v1/health
```

### Примеры тестов

```python
import asyncio
from app.llm_router import system_analyzer, llm_router

async def test_optimization():
    # Анализ системы
    specs = await system_analyzer.analyze_system()
    print(f"Система: {specs.platform} {specs.architecture}")
    
    # Оптимизация
    config = await system_analyzer.optimize_config()
    print(f"Оптимизированная конфигурация: {config}")
    
    # Тест производительности
    await system_analyzer.record_performance(1.5, True, 100)
    
    # Отчет
    report = await system_analyzer.get_optimization_report()
    print(f"Отчет: {report}")

asyncio.run(test_optimization())
```

## 🔍 Отладка

### Логирование

```python
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Логи оптимизации
logger.info("🧠 LLM recommendation: Apple Silicon optimization applied")
logger.info("⚙️ Optimized config: GPU=1, threads=8, batch=1024")
logger.info("📊 Performance: avg_time=1.85s, success_rate=93%")
```

### Диагностика проблем

1. **Проверка Ollama**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Проверка оптимизации**:
   ```bash
   curl http://localhost:8000/api/v1/optimization/report
   ```

3. **Проверка переменных окружения**:
   ```bash
   curl http://localhost:8000/api/v1/optimization/environment
   ```

## 🚀 Производительность

### Ожидаемые результаты

- **Apple Silicon M1/M2/M4**: 1-2 секунды на запрос
- **NVIDIA GPU**: 1-3 секунды на запрос
- **CPU-only**: 3-5 секунд на запрос

### Оптимизации

- **GPU acceleration**: использование Metal/CUDA
- **Batch processing**: обработка нескольких запросов одновременно
- **Memory optimization**: эффективное использование памяти
- **Context optimization**: оптимальный размер контекста

## 🔮 Будущие улучшения

- **Машинное обучение**: предсказание оптимальных параметров
- **A/B тестирование**: автоматическое тестирование конфигураций
- **Распределенная оптимизация**: оптимизация для кластеров
- **Пользовательские профили**: сохранение предпочтений пользователей

## 📚 Дополнительные ресурсы

- [Документация Ollama](https://ollama.ai/docs)
- [Apple Silicon оптимизации](https://developer.apple.com/metal/)
- [RAG подход](https://arxiv.org/abs/2005.11401)
- [LLM оптимизации](https://huggingface.co/docs/transformers/performance)

---

**🧠 Интеллектуальная система оптимизации reLink** - революция в автоматической настройке LLM систем! 🚀 