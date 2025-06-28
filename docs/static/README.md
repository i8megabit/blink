# 📚 SEO Link Recommender - Документация

Микросервис документации и управления версиями для SEO Link Recommender.

## 🚀 Возможности

- **Управление версиями** - централизованное хранение и получение информации о версиях
- **Документация** - автоматическое чтение и кэширование документации
- **FAQ система** - структурированные ответы на частые вопросы
- **Redis кэширование** - быстрый доступ к данным
- **REST API** - удобные эндпоинты для интеграции

## 🏗️ Архитектура

Микросервис построен на:
- **FastAPI** - современный веб-фреймворк для Python
- **Redis** - кэширование данных
- **Pydantic** - валидация данных
- **Markdown** - обработка документации

## 📋 API Эндпоинты

### Основные
- `GET /api/v1/health` - проверка здоровья сервиса
- `GET /api/v1/version` - информация о версии

### Документация
- `GET /api/v1/docs/readme` - README документация
- `GET /api/v1/docs/roadmap` - технический roadmap
- `GET /api/v1/docs/faq` - часто задаваемые вопросы
- `GET /api/v1/docs/about` - информация о проекте
- `GET /api/v1/docs/how-it-works` - как работает система

### Кэш
- `GET /api/v1/cache/stats` - статистика кэша
- `DELETE /api/v1/cache/clear` - очистка кэша

## 🔧 Настройка

### Переменные окружения
```bash
# Основные настройки
DEBUG=false
HOST=0.0.0.0
PORT=8001

# Redis настройки
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Кэширование
CACHE_TTL=3600
CACHE_PREFIX=docs:

# Пути к файлам
DOCS_PATH=/app/static
VERSION_FILE=/app/VERSION
README_FILE=/app/README.md

# CORS
CORS_ORIGINS=["http://localhost:3000","http://frontend:80"]
```

### Docker
```bash
# Сборка образа
docker build -t seo-docs .

# Запуск контейнера
docker run -p 8001:8001 seo-docs
```

## 📊 Мониторинг

### Health Check
```bash
curl http://localhost:8001/api/v1/health
```

### Статистика кэша
```bash
curl http://localhost:8001/api/v1/cache/stats
```

## 🔄 Кэширование

Все данные автоматически кэшируются в Redis с TTL 1 час. Для принудительного обновления используйте параметр `force_refresh=true`:

```bash
curl "http://localhost:8001/api/v1/version?force_refresh=true"
```

## 🧪 Тестирование

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск тестов
pytest

# Запуск с покрытием
pytest --cov=app
```

## 📝 Логирование

Сервис использует структурированное логирование с JSON форматом:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info",
  "logger": "app.main",
  "message": "Documentation service started successfully",
  "version": "1.0.0"
}
```

## 🔒 Безопасность

- CORS настройки для ограничения доступа
- Валидация всех входных данных
- Обработка ошибок без утечки информации
- Логирование всех операций

## 📈 Производительность

- Асинхронная обработка запросов
- Кэширование в Redis
- Оптимизированные запросы к файловой системе
- Минимальное использование памяти

## 🤝 Интеграция

Микросервис легко интегрируется в существующую инфраструктуру:

```javascript
// Пример интеграции во frontend
const response = await fetch('http://docs:8001/api/v1/docs/readme');
const data = await response.json();
```

## 📞 Поддержка

Для вопросов и предложений обращайтесь к команде разработки. 