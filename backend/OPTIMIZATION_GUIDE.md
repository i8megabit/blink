# 🚀 Руководство по оптимизациям reLink

## 📋 Обзор

Система оптимизаций reLink включает в себя три основных компонента:

1. **🧠 Интеллектуальный роутер моделей** - автоматический выбор оптимальной модели Qwen
2. **🗄️ Продвинутый сервис ChromaDB** - оптимизированное хранение и поиск
3. **⚙️ Менеджер оптимизаций** - центральное управление всеми оптимизациями

## 🧠 Интеллектуальный роутер моделей

### Основные возможности

- **Автоматический выбор модели** на основе сложности задачи
- **Мониторинг ресурсов** системы в реальном времени
- **Адаптивная производительность** с учетом статистики использования
- **Fallback механизмы** при недоступности моделей

### Поддерживаемые модели

| Модель | Тип | Размер | Назначение | Время ответа |
|--------|-----|--------|------------|--------------|
| qwen2.5:0.5b | FAST_RESPONSE | 0.5B | Быстрые ответы | ~2 сек |
| qwen2.5:1.5b | HIGH_QUALITY | 1.5B | Высокое качество | ~5 сек |
| qwen2.5:3b | CODE_GENERATION | 3B | Генерация кода | ~8 сек |
| qwen2.5:7b | ANALYSIS | 7B | Анализ и размышления | ~15 сек |
| qwen2.5:14b | EXPERT | 14B | Экспертные задачи | ~30 сек |

### Уровни сложности задач

- **SIMPLE** - простые запросы (< 20 слов)
- **MEDIUM** - средняя сложность (20-100 слов)
- **COMPLEX** - сложные задачи (100-300 слов)
- **EXPERT** - экспертный уровень (> 300 слов)

### Пример использования

```python
from app.llm.intelligent_model_router import IntelligentModelRouter

# Создание роутера
router = IntelligentModelRouter()

# Обработка запроса
result = await router.route_request(
    prompt="Проанализируй производительность системы",
    context="Дополнительный контекст",
    preferred_model=None  # Автоматический выбор
)

print(f"Использована модель: {result['model_used']}")
print(f"Время ответа: {result['response_time']:.2f} сек")
```

## 🗄️ Продвинутый сервис ChromaDB

### Основные возможности

- **Автоматическое шардирование** коллекций
- **Интеллектуальное кеширование** с Redis и локальным кешем
- **Компрессия данных** для экономии места
- **Мониторинг производительности** в реальном времени

### Конфигурация

```python
from app.llm.advanced_chromadb_service import AdvancedChromaDBService

service = AdvancedChromaDBService(
    persist_directory="./chroma_db",
    redis_url="redis://localhost:6379",
    max_cache_size=1000,
    enable_compression=True,
    enable_sharding=True,
    shard_size_threshold=50000
)
```

### Операции с коллекциями

```python
# Создание коллекции
collection = await service.create_collection("my_collection")

# Добавление документов
ids = await service.add_documents(
    collection_name="my_collection",
    documents=["Документ 1", "Документ 2"],
    metadatas=[{"type": "text"}, {"type": "code"}]
)

# Поиск документов
results = await service.query(
    collection_name="my_collection",
    query_texts=["поисковый запрос"],
    n_results=10
)
```

### Шардирование

Система автоматически создает шарды при достижении порога в 50,000 документов:

- **Автоматическое распределение** документов по шардам
- **Параллельные запросы** к шардам
- **Объединение результатов** с ранжированием

## ⚙️ Менеджер оптимизаций

### Уровни оптимизации

- **BASIC** - базовая оптимизация (1 модель)
- **STANDARD** - стандартная оптимизация (2 модели)
- **ADVANCED** - продвинутая оптимизация (3 модели)
- **EXPERT** - экспертная оптимизация (4 модели)

### Инициализация

```python
from app.llm.optimization_manager import OptimizationManager, OptimizationLevel

manager = OptimizationManager(
    optimization_level=OptimizationLevel.ADVANCED,
    auto_optimize=True,
    optimization_interval=300  # 5 минут
)

# Запуск менеджера
await manager.start()
```

### Обработка запросов

```python
# Комплексная обработка с ChromaDB и LLM
result = await manager.process_request(
    prompt="Анализ производительности",
    context="Контекст системы",
    collection_name="knowledge_base",
    query_texts=["производительность", "оптимизация"],
    n_results=5,
    preferred_model="qwen2.5:3b"
)
```

### Мониторинг

```python
# Состояние системы
health = await manager.get_system_health()
print(f"CPU: {health.cpu_usage}%")
print(f"Memory: {health.memory_usage}%")

# Метрики оптимизации
metrics = manager.get_optimization_metrics()
print(f"Скор оптимизации: {metrics.optimization_score:.2f}")
print(f"Hit rate кеша: {metrics.cache_hit_rate:.2f}")
```

## 🌐 API эндпоинты

### Основные эндпоинты

#### Проверка здоровья
```bash
GET /api/v1/optimization/health
```

#### Получение метрик
```bash
GET /api/v1/optimization/metrics
```

#### Запуск оптимизации
```bash
POST /api/v1/optimization/optimize
```

#### Обработка запроса
```bash
POST /api/v1/optimization/process
{
    "prompt": "Анализ системы",
    "context": "Дополнительный контекст",
    "collection_name": "knowledge_base",
    "query_texts": ["анализ", "система"],
    "n_results": 5
}
```

#### Управление конфигурацией
```bash
# Установка уровня оптимизации
POST /api/v1/optimization/config/level
{
    "level": "advanced"
}

# Включение автооптимизации
POST /api/v1/optimization/config/auto-optimize
{
    "enabled": true
}
```

### Управление кешами

```bash
# Статус кешей
GET /api/v1/optimization/cache/status

# Очистка кешей
POST /api/v1/optimization/cache/clear
```

### Отчеты о производительности

```bash
# Детальный отчет
GET /api/v1/optimization/performance/report
```

## 🧪 Тестирование

### Запуск тестов

```bash
cd backend
python test_optimizations.py
```

### Тестовые сценарии

1. **Тест роутера моделей** - проверка выбора оптимальной модели
2. **Тест ChromaDB** - проверка шардирования и кеширования
3. **Тест менеджера** - проверка комплексной оптимизации
4. **Тест API** - проверка эндпоинтов
5. **Бенчмарк** - тестирование производительности

## 📊 Мониторинг и метрики

### Ключевые метрики

- **Время ответа** - среднее время обработки запросов
- **Hit rate кеша** - эффективность кеширования
- **Утилизация моделей** - распределение нагрузки
- **Эффективность ресурсов** - использование CPU и памяти

### Алерты

Система автоматически генерирует алерты при:

- Высоком использовании CPU (> 80%)
- Высоком использовании памяти (> 85%)
- Низком hit rate кеша (< 50%)
- Высоком уровне ошибок (> 10%)

## 🔧 Конфигурация

### Переменные окружения

```bash
# ChromaDB
CHROMADB_PERSIST_DIR=./chroma_db
CHROMADB_REDIS_URL=redis://localhost:6379

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# Оптимизации
OPTIMIZATION_LEVEL=advanced
AUTO_OPTIMIZE=true
OPTIMIZATION_INTERVAL=300
```

### Docker Compose

```yaml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
      
  backend:
    build: .
    environment:
      - CHROMADB_REDIS_URL=redis://redis:6379
      - OLLAMA_BASE_URL=http://ollama:11434
      - OPTIMIZATION_LEVEL=advanced
    depends_on:
      - redis
      - ollama

volumes:
  ollama_data:
```

## 🚀 Лучшие практики

### 1. Выбор уровня оптимизации

- **BASIC** - для разработки и тестирования
- **STANDARD** - для небольших проектов
- **ADVANCED** - для продакшена
- **EXPERT** - для высоконагруженных систем

### 2. Настройка кеширования

```python
# Оптимальные настройки для продакшена
service = AdvancedChromaDBService(
    max_cache_size=5000,  # Больше кеш для высокой нагрузки
    enable_compression=True,
    enable_sharding=True,
    shard_size_threshold=25000  # Меньший порог для быстрого шардирования
)
```

### 3. Мониторинг производительности

```python
# Регулярная проверка метрик
async def monitor_performance():
    while True:
        metrics = manager.get_optimization_metrics()
        if metrics.optimization_score < 0.7:
            await manager.optimize_system()
        await asyncio.sleep(300)
```

### 4. Обработка ошибок

```python
try:
    result = await manager.process_request(prompt="Запрос")
except Exception as e:
    # Fallback к базовой модели
    result = await manager.model_router.route_request(
        prompt="Запрос",
        preferred_model="qwen2.5:0.5b"
    )
```

## 🔍 Диагностика проблем

### Частые проблемы

1. **Медленные ответы**
   - Проверьте доступность Ollama
   - Увеличьте размер кеша
   - Проверьте уровень оптимизации

2. **Высокое использование памяти**
   - Уменьшите размер кеша
   - Включите компрессию
   - Очистите кеши

3. **Ошибки ChromaDB**
   - Проверьте доступность Redis
   - Проверьте права доступа к директории
   - Перезапустите сервис

### Логи и отладка

```python
import logging

# Включение детального логирования
logging.basicConfig(level=logging.DEBUG)

# Логирование конкретных компонентов
logging.getLogger('app.llm.intelligent_model_router').setLevel(logging.DEBUG)
logging.getLogger('app.llm.advanced_chromadb_service').setLevel(logging.DEBUG)
```

## 📈 Производительность

### Ожидаемые результаты

- **Время ответа**: 2-30 секунд в зависимости от модели
- **Hit rate кеша**: 70-90% при правильной настройке
- **Использование памяти**: 1-16 GB в зависимости от моделей
- **Пропускная способность**: 10-100 запросов/мин

### Оптимизация для Apple Silicon

Система автоматически оптимизируется для Apple Silicon:

- Использование GPU слоев (35 слоев)
- Оптимальное количество CPU потоков
- Эффективное управление памятью

## 🔄 Обновления и миграции

### Обновление конфигурации

```python
# Динамическое обновление уровня оптимизации
await manager.set_optimization_level(OptimizationLevel.EXPERT)

# Обновление интервала оптимизации
manager.optimization_interval = 600  # 10 минут
```

### Миграция данных

```python
# Экспорт данных ChromaDB
await service.export_collection("old_collection", "backup.json")

# Импорт в новую систему
await service.import_collection("new_collection", "backup.json")
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи системы
2. Запустите тесты: `python test_optimizations.py`
3. Проверьте состояние сервисов: `GET /api/v1/optimization/health`
4. Обратитесь к документации API: `GET /docs`

---

**🎉 Поздравляем!** Вы успешно настроили систему оптимизаций reLink. Система автоматически оптимизирует производительность и обеспечивает высокое качество ответов. 