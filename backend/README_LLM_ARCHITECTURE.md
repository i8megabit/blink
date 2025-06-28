# 🧠 Централизованная LLM Архитектура reLink

## 📋 Обзор

Централизованная LLM архитектура reLink обеспечивает конкурентное использование одной модели Ollama всеми микросервисами платформы. Архитектура оптимизирована для Apple M4 и других систем с ограниченными ресурсами.

## 🏗️ Архитектура

### Основные компоненты

1. **CentralizedLLMArchitecture** - Центральный координатор
2. **ConcurrentOllamaManager** - Менеджер конкурентных запросов к Ollama
3. **DistributedRAGCache** - Распределенный кэш с Redis
4. **RequestPrioritizer** - Приоритизация запросов
5. **RAGMonitor** - Мониторинг и метрики

### Схема работы

```
Микросервисы → LLMIntegrationService → CentralizedLLMArchitecture
                                           ↓
                                    RequestPrioritizer
                                           ↓
                                    ConcurrentOllamaManager (семафор=2)
                                           ↓
                                    Ollama (qwen2.5:7b-instruct-turbo)
                                           ↓
                                    DistributedRAGCache
                                           ↓
                                    RAGMonitor
```

## 🚀 Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements_llm.txt
```

### Запуск Redis

```bash
docker run -d -p 6379:6379 redis:alpine
```

### Базовое использование

```python
from app.llm_integration import get_llm_integration_service

async def main():
    # Получаем сервис интеграции
    llm_service = await get_llm_integration_service()
    
    # Генерируем ответ
    response = await llm_service.generate_response(
        prompt="Привет, как дела?",
        max_tokens=100
    )
    
    print(response)

# Запуск
asyncio.run(main())
```

## 📊 Конфигурация

### Оптимизация для Apple M4

```python
from app.llm.concurrent_manager import OllamaConfig

config = OllamaConfig(
    max_concurrent_requests=2,  # Оптимизировано для M4
    request_timeout=300.0,
    keep_alive="2h",
    context_length=4096,
    batch_size=512,
    num_parallel=2
)
```

### Настройка приоритетов

```python
from app.llm.request_prioritizer import RequestPrioritizer

prioritizer = RequestPrioritizer()

# Уровни приоритетов
priorities = {
    "critical": 100,    # Критически важные
    "high": 80,         # Высокий приоритет
    "normal": 50,       # Обычный приоритет
    "low": 20,          # Низкий приоритет
    "background": 10    # Фоновые задачи
}
```

## 🔧 Интеграция с микросервисами

### Сервис тестирования

```python
from app.llm_integration import LLMIntegrationFactory

async def test_integration():
    llm_service = await get_llm_integration_service()
    factory = LLMIntegrationFactory(llm_service)
    
    # Интеграция с тестированием
    testing = factory.get_testing_integration()
    test_case = await testing.generate_test_case(
        "Функция валидации email",
        "unit"
    )
    
    return test_case
```

### Сервис диаграмм

```python
async def diagram_integration():
    llm_service = await get_llm_integration_service()
    factory = LLMIntegrationFactory(llm_service)
    
    # Интеграция с диаграммами
    diagram = factory.get_diagram_integration()
    description = await diagram.generate_diagram_description(
        {"nodes": ["A", "B"], "edges": [("A", "B")]},
        "flowchart"
    )
    
    return description
```

### Сервис мониторинга

```python
async def monitoring_integration():
    llm_service = await get_llm_integration_service()
    factory = LLMIntegrationFactory(llm_service)
    
    # Интеграция с мониторингом
    monitoring = factory.get_monitoring_integration()
    analysis = await monitoring.analyze_performance_data({
        "response_time": 2.5,
        "error_rate": 0.01,
        "throughput": 100
    })
    
    return analysis
```

## 📈 Мониторинг и метрики

### Получение метрик

```python
async def get_metrics():
    llm_service = await get_llm_integration_service()
    metrics = await llm_service.get_metrics()
    
    print(f"Всего запросов: {metrics['total_requests']}")
    print(f"Кэш-хиты: {metrics['cache_hits']}")
    print(f"Среднее время ответа: {metrics['avg_response_time']:.2f}s")
    print(f"Ошибки: {metrics['errors']}")
```

### Проверка здоровья

```python
async def health_check():
    llm_service = await get_llm_integration_service()
    health = await llm_service.health_check()
    
    if health["status"] == "healthy":
        print("✅ Система работает нормально")
    else:
        print(f"❌ Проблемы: {health}")
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest test_llm_architecture.py -v

# Только тесты архитектуры
pytest test_llm_architecture.py::TestCentralizedLLMArchitecture -v

# Тесты производительности
pytest test_llm_architecture.py::TestPerformance -v
```

### Тестирование производительности

```python
import asyncio
import time
from app.llm_integration import get_llm_integration_service

async def performance_test():
    llm_service = await get_llm_integration_service()
    
    # Тест конкурентных запросов
    start_time = time.time()
    
    tasks = []
    for i in range(10):
        task = llm_service.generate_response(f"Запрос {i}")
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    print(f"Обработано {len(responses)} запросов за {total_time:.2f}s")
    print(f"Среднее время: {total_time/len(responses):.2f}s на запрос")
```

## 🔒 Безопасность

### Rate Limiting

```python
from app.llm.request_prioritizer import RequestPrioritizer

prioritizer = RequestPrioritizer()

# Проверка лимитов пользователя
can_process = prioritizer.can_process_request(
    user_id=123,
    user_tier="standard"  # premium, standard, basic, free
)

if not can_process:
    raise Exception("Превышен лимит запросов")
```

### Приоритизация

```python
# Критические запросы обрабатываются первыми
critical_request = LLMRequest(
    id="critical-1",
    prompt="Срочный запрос",
    priority="critical"
)

# Фоновые задачи обрабатываются последними
background_request = LLMRequest(
    id="bg-1", 
    prompt="Фоновая задача",
    priority="background"
)
```

## 🚨 Устранение неполадок

### Проблемы с подключением к Ollama

```python
async def troubleshoot_ollama():
    llm_service = await get_llm_integration_service()
    health = await llm_service.health_check()
    
    if health["ollama_status"]["status"] != "healthy":
        print("❌ Проблемы с Ollama:")
        print(f"   - {health['ollama_status']['error']}")
        print("🔧 Решения:")
        print("   1. Проверьте, что Ollama запущен")
        print("   2. Проверьте модель qwen2.5:7b-instruct-turbo")
        print("   3. Проверьте порт 11434")
```

### Проблемы с Redis

```python
async def troubleshoot_redis():
    from app.llm.distributed_cache import DistributedRAGCache
    
    cache = DistributedRAGCache()
    health = await cache.health_check()
    
    if health["status"] != "healthy":
        print("❌ Проблемы с Redis:")
        print(f"   - {health['error']}")
        print("🔧 Решения:")
        print("   1. Запустите Redis: docker run -d -p 6379:6379 redis:alpine")
        print("   2. Проверьте подключение к localhost:6379")
```

### Оптимизация производительности

```python
async def optimize_performance():
    llm_service = await get_llm_integration_service()
    metrics = await llm_service.get_metrics()
    
    # Анализ метрик
    if metrics["avg_response_time"] > 5.0:
        print("⚠️ Медленные ответы")
        print("🔧 Рекомендации:")
        print("   - Уменьшите max_tokens")
        print("   - Используйте кэширование")
        print("   - Проверьте нагрузку на систему")
    
    if metrics["cache_hit_rate"] < 0.5:
        print("⚠️ Низкий hit rate кэша")
        print("🔧 Рекомендации:")
        print("   - Увеличьте TTL кэша")
        print("   - Добавьте больше документов в базу знаний")
```

## 📚 API Reference

### CentralizedLLMArchitecture

```python
class CentralizedLLMArchitecture:
    async def start() -> None
    async def stop() -> None
    async def submit_request(request: LLMRequest) -> str
    async def get_response(request_id: str) -> Optional[LLMResponse]
    def get_metrics() -> Dict[str, Any]
    async def health_check() -> Dict[str, Any]
```

### LLMIntegrationService

```python
class LLMIntegrationService:
    async def initialize(redis_url: str = "redis://localhost:6379") -> None
    async def shutdown() -> None
    async def generate_response(prompt: str, **kwargs) -> str
    async def get_embedding(text: str) -> List[float]
    async def search_knowledge_base(query: str, limit: int = 5) -> List[str]
    async def get_metrics() -> Dict[str, Any]
    async def health_check() -> Dict[str, Any]
```

### LLMRequest

```python
@dataclass
class LLMRequest:
    id: str
    prompt: str
    model_name: str = "qwen2.5:7b-instruct-turbo"
    priority: str = "normal"
    max_tokens: int = 100
    temperature: float = 0.7
    use_rag: bool = True
    user_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## 🔄 Миграция с старой архитектуры

### Обновление существующего кода

```python
# Старый код
from app.llm_router import generate_seo_recommendations

# Новый код
from app.llm_integration import get_llm_integration_service

async def new_approach():
    llm_service = await get_llm_integration_service()
    response = await llm_service.generate_response(
        prompt="SEO рекомендации",
        priority="high"
    )
    return response
```

### Совместимость

Старые функции (`generate_seo_recommendations`, `generate_diagram`, etc.) продолжают работать, но теперь используют новую централизованную архитектуру.

## 📈 Планы развития

### Краткосрочные (1-2 недели)
- [x] Базовая централизованная архитектура
- [x] Конкурентный доступ к Ollama
- [x] Распределенное кэширование
- [x] Приоритизация запросов
- [ ] Векторная база знаний
- [ ] Автоматическая оптимизация

### Среднесрочные (1-2 месяца)
- [ ] Поддержка множественных моделей
- [ ] A/B тестирование конфигураций
- [ ] Автоматическое масштабирование
- [ ] Интеграция с внешними LLM API

### Долгосрочные (3-6 месяцев)
- [ ] Распределенная архитектура
- [ ] Машинное обучение для оптимизации
- [ ] Поддержка мультимодальных моделей
- [ ] Интеграция с Kubernetes

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📞 Поддержка

- **Документация**: [README_LLM_ARCHITECTURE.md](README_LLM_ARCHITECTURE.md)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**reLink Centralized LLM Architecture** - Эффективное использование Ollama для всех микросервисов платформы 🚀 