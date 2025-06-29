# reLink - Сервис анализа и оптимизации внутренних ссылок

Сервис для автоматического анализа внутренних ссылок, генерации SEO рекомендаций и оптимизации контента на основе AI/ML технологий.

## 🚀 Возможности

- **Индексация доменов** - автоматическое извлечение постов и внутренних ссылок
- **SEO анализ** - комплексная оценка контента и технических аспектов
- **Генерация рекомендаций** - AI-powered рекомендации по улучшению
- **Анализ внутренних ссылок** - выявление проблем и возможностей
- **Дашборд** - визуализация данных и метрик
- **Экспорт данных** - поддержка JSON и CSV форматов

## 🏗️ Архитектура

```
relink/
├── app/
│   ├── api/           # FastAPI роуты
│   ├── services/      # Бизнес-логика
│   ├── models.py      # Pydantic модели
│   └── main.py        # Точка входа
├── scripts/           # Скрипты индексации
├── cache/             # Кеш индексации
├── Dockerfile         # Контейнеризация
└── requirements.txt   # Зависимости
```

## 🛠️ Технологии

- **FastAPI** - современный веб-фреймворк
- **BeautifulSoup** - парсинг HTML
- **aiohttp** - асинхронные HTTP запросы
- **Pydantic** - валидация данных
- **SQLAlchemy** - работа с БД
- **Redis** - кеширование
- **Ollama** - LLM интеграция

## 📦 Установка и запуск

### Через Docker Compose (рекомендуется)

```bash
# Запуск всех сервисов
make up

# Проверка здоровья
make health

# Анализ dagorod.ru
make analyze-dagorod
```

### Локальная разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервиса
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## 🔌 API Эндпоинты

### Основные эндпоинты

#### `POST /api/v1/index-domain`
Индексация домена для анализа

```bash
curl -X POST http://localhost:8001/api/v1/index-domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "dagorod.ru"}'
```

#### `POST /api/v1/analyze-domain`
Анализ домена и внутренних ссылок

```bash
curl -X POST http://localhost:8001/api/v1/analyze-domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "dagorod.ru",
    "include_posts": true,
    "include_recommendations": true
  }'
```

#### `POST /api/v1/generate-recommendations`
Генерация SEO рекомендаций

```bash
curl -X POST http://localhost:8001/api/v1/generate-recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "dagorod.ru",
    "focus_areas": ["internal_linking", "content_optimization"],
    "priority": "high"
  }'
```

#### `GET /api/v1/dashboard/{domain}`
Получение данных для дашборда

```bash
curl http://localhost:8001/api/v1/dashboard/dagorod.ru
```

### Специальные эндпоинты

#### `POST /api/v1/analyze-dagorod`
Полный анализ dagorod.ru (включает индексацию, анализ и рекомендации)

```bash
curl -X POST http://localhost:8001/api/v1/analyze-dagorod
```

#### `GET /api/v1/posts/{domain}`
Получение проиндексированных постов

```bash
curl "http://localhost:8001/api/v1/posts/dagorod.ru?limit=10"
```

#### `GET /api/v1/internal-links/{domain}`
Получение анализа внутренних ссылок

```bash
curl "http://localhost:8001/api/v1/internal-links/dagorod.ru?limit=20"
```

## 📊 Примеры использования

### 1. Полный анализ домена

```python
import requests

# Индексируем домен
index_response = requests.post(
    "http://localhost:8001/api/v1/index-domain",
    json={"domain": "dagorod.ru"}
)

# Анализируем
analysis_response = requests.post(
    "http://localhost:8001/api/v1/analyze-domain",
    json={
        "domain": "dagorod.ru",
        "include_posts": True,
        "include_recommendations": True
    }
)

# Генерируем рекомендации
recommendations_response = requests.post(
    "http://localhost:8001/api/v1/generate-recommendations",
    json={
        "domain": "dagorod.ru",
        "focus_areas": ["internal_linking", "content_optimization", "technical_seo"],
        "priority": "high"
    }
)

print("Анализ завершен!")
print(f"Постов проанализировано: {analysis_response.json()['analysis']['total_posts']}")
print(f"Рекомендаций сгенерировано: {len(recommendations_response.json()['recommendations'])}")
```

### 2. Мониторинг индексации

```python
import time
import requests

# Запускаем индексацию
requests.post(
    "http://localhost:8001/api/v1/index-domain",
    json={"domain": "dagorod.ru"}
)

# Проверяем статус
while True:
    status = requests.get("http://localhost:8001/api/v1/indexing-status/dagorod.ru").json()
    print(f"Статус: {status['status']}")
    
    if status['status'] == 'completed':
        print("Индексация завершена!")
        break
    
    time.sleep(5)
```

### 3. Экспорт результатов

```python
import requests

# Экспорт в JSON
json_data = requests.get(
    "http://localhost:8001/api/v1/export-analysis/dagorod.ru?format=json"
).content

with open("dagorod_analysis.json", "wb") as f:
    f.write(json_data)

# Экспорт в CSV
csv_data = requests.get(
    "http://localhost:8001/api/v1/export-analysis/dagorod.ru?format=csv"
).content

with open("dagorod_analysis.csv", "wb") as f:
    f.write(csv_data)
```

## 🔍 Анализ dagorod.ru

Сервис специально оптимизирован для анализа домена dagorod.ru. Вот что он делает:

### 1. Индексация
- Извлекает все посты и страницы
- Анализирует внутренние ссылки
- Собирает SEO метаданные
- Определяет структуру сайта

### 2. Анализ
- Оценивает качество контента
- Анализирует распределение ссылок
- Выявляет "сиротские" страницы
- Рассчитывает SEO оценки

### 3. Рекомендации
- Генерирует AI-powered рекомендации
- Фокусируется на внутренней перелинковке
- Предлагает улучшения контента
- Дает технические советы

## 📈 Метрики и мониторинг

### Основные метрики
- **Количество постов** - общее число проиндексированных страниц
- **Внутренние ссылки** - количество и качество связей
- **SEO оценки** - средняя оценка постов
- **Проблемы** - выявленные недостатки

### Мониторинг
```bash
# Проверка здоровья
make health

# Просмотр логов
make logs-relink

# Статус сервисов
make monitor
```

## 🧪 Тестирование

### Автоматические тесты
```bash
# Запуск всех тестов
make test

# Тестирование relink
make test-relink
```

### Ручное тестирование
```bash
# Проверка эндпоинтов
curl http://localhost:8001/api/v1/health
curl http://localhost:8001/api/v1/endpoints

# Тест анализа
make analyze-dagorod
```

## 🔧 Конфигурация

### Переменные окружения
```bash
# Основные настройки
LOG_LEVEL=INFO
CACHE_DIR=./cache
MAX_POSTS_PER_DOMAIN=100

# База данных
DATABASE_URL=postgresql://user:pass@localhost/relink

# Redis
REDIS_URL=redis://localhost:6379

# LLM
OLLAMA_URL=http://localhost:11434
```

### Настройка производительности
```yaml
# docker-compose.yml
services:
  relink:
    environment:
      - MAX_WORKERS=4
      - CONCURRENT_REQUESTS=10
      - CACHE_TTL=3600
```

## 🚀 Производительность

### Оптимизация для MacBook Pro M4 16GB
- **Параллельная индексация** - до 10 одновременных запросов
- **Кеширование** - Redis для быстрого доступа к данным
- **Асинхронная обработка** - non-blocking операции
- **Оптимизированные запросы** - минимизация нагрузки на целевые сайты

### Метрики производительности
```bash
# Проверка производительности
make performance

# Мониторинг ресурсов
make monitor
```

## 🐛 Отладка

### Включение отладки
```bash
# Режим отладки
make debug

# Детальные логи
LOG_LEVEL=DEBUG make up
```

### Частые проблемы
1. **Таймауты при индексации** - увеличьте `REQUEST_TIMEOUT`
2. **Ошибки парсинга** - проверьте структуру HTML
3. **Проблемы с памятью** - уменьшите `MAX_POSTS_PER_DOMAIN`

## 📚 Документация API

Полная документация API доступна по адресу:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 📞 Поддержка

- **Issues**: GitHub Issues
- **Документация**: `/docs` папка
- **Примеры**: `/examples` папка

---

**reLink** - умный анализ внутренних ссылок для лучшего SEO! 🚀 