# 📚 SEO Link Recommender - Микросервис Документации

Микросервис для управления документацией, версиями и FAQ системы SEO Link Recommender с Redis кэшированием.

## 🚀 Возможности

- **📖 Управление документацией** - автоматическое чтение и кэширование README, roadmap и других документов
- **🏷️ Управление версиями** - централизованное хранение информации о версиях
- **❓ FAQ система** - структурированные ответы на частые вопросы
- **⚡ Redis кэширование** - быстрый доступ к данным с TTL
- **🔧 REST API** - удобные эндпоинты для интеграции с frontend
- **📊 Мониторинг** - health checks и статистика кэша

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Docs Service  │    │     Redis       │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Cache)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Static Files  │
                       │   (Markdown)    │
                       └─────────────────┘
```

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

## 🔧 Быстрый старт

### Локальная разработка

```bash
# Клонирование репозитория
git clone <repository>
cd relink/docs

# Установка зависимостей
make install-dev

# Запуск в режиме разработки
make run

# Проверка здоровья
make health
```

### Docker

```bash
# Сборка образа
make build

# Запуск контейнера
make docker-run

# Проверка логов
make docker-logs
```

### Docker Compose

```bash
# Запуск всей инфраструктуры
cd ../
docker-compose up -d docs redis

# Проверка статуса
docker-compose ps
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
make test

# Тесты с покрытием
make test-cov

# Тесты в режиме наблюдения
make test-watch

# Проверка качества кода
make ci
```

## 📝 Логирование

Сервис использует структурированное логирование:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info",
  "logger": "app.main",
  "message": "Documentation service started successfully",
  "version": "1.0.0"
}
```

## 🔄 Кэширование

Все данные автоматически кэшируются в Redis с TTL 1 час:

```bash
# Принудительное обновление кэша
curl "http://localhost:8001/api/v1/version?force_refresh=true"

# Просмотр статистики кэша
make cache-stats

# Очистка кэша
make clear-cache
```

## 🔒 Безопасность

- **CORS** - настройки для ограничения доступа
- **Валидация** - все входные данные валидируются
- **Обработка ошибок** - безопасная обработка без утечки информации
- **Логирование** - все операции логируются

## 📈 Производительность

- **Асинхронность** - все операции асинхронные
- **Кэширование** - Redis для быстрого доступа
- **Оптимизация** - минимальное использование ресурсов
- **Мониторинг** - health checks и метрики

## 🤝 Интеграция с Frontend

### Пример использования в React

```typescript
// Хук для работы с документацией
const useDocumentation = () => {
  const [docs, setDocs] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchDocs = async (type: string) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8001/api/v1/docs/${type}`);
      const data = await response.json();
      setDocs(data.data);
    } catch (error) {
      console.error('Error fetching docs:', error);
    } finally {
      setLoading(false);
    }
  };

  return { docs, loading, fetchDocs };
};

// Компонент для отображения документации
const DocumentationView = ({ type }: { type: string }) => {
  const { docs, loading, fetchDocs } = useDocumentation();

  useEffect(() => {
    fetchDocs(type);
  }, [type]);

  if (loading) return <div>Загрузка...</div>;
  if (!docs) return <div>Документация не найдена</div>;

  return (
    <div>
      <h1>{docs.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: docs.content }} />
    </div>
  );
};
```

### Кнопки меню для интеграции

```typescript
// Компоненты кнопок меню
const DocumentationButton = () => (
  <button onClick={() => navigate('/docs/readme')}>
    📖 Документация
  </button>
);

const VersionButton = () => (
  <button onClick={() => navigate('/docs/version')}>
    🏷️ Версия
  </button>
);

const AboutButton = () => (
  <button onClick={() => navigate('/docs/about')}>
    ℹ️ О программе
  </button>
);

const HowItWorksButton = () => (
  <button onClick={() => navigate('/docs/how-it-works')}>
    🔧 Как это работает?
  </button>
);

const FAQButton = () => (
  <button onClick={() => navigate('/docs/faq')}>
    ❓ FAQ
  </button>
);
```

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

### Структура файлов

```
docs/
├── app/
│   ├── __init__.py
│   ├── config.py          # Конфигурация
│   ├── cache.py           # Redis кэш
│   ├── models.py          # Pydantic модели
│   ├── services.py        # Бизнес-логика
│   └── main.py           # FastAPI приложение
├── static/
│   └── README.md         # Документация
├── tests/
│   ├── test_docs_service.py
│   └── test_api.py
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── Makefile
└── README.md
```

## 📊 Мониторинг

### Health Check

```bash
curl http://localhost:8001/api/v1/health
```

Ответ:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "cache_status": "connected",
  "uptime": 3600.5
}
```

### Статистика кэша

```bash
curl http://localhost:8001/api/v1/cache/stats
```

Ответ:
```json
{
  "success": true,
  "message": "Cache statistics retrieved successfully",
  "data": {
    "connected": true,
    "total_keys": 5,
    "memory_used": "2.5MB",
    "connected_clients": 1,
    "uptime": 3600
  }
}
```

## 🚀 Деплой

### Docker Compose

```yaml
services:
  docs:
    build:
      context: .
      dockerfile: docs/Dockerfile
    ports:
      - "8001:8001"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docs-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: docs-service
  template:
    metadata:
      labels:
        app: docs-service
    spec:
      containers:
      - name: docs
        image: seo-docs:latest
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_HOST
          value: "redis-service"
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Запустите проверки: `make ci`
6. Создайте Pull Request

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/seo-team/seo-link-recommender/issues)
- **Документация**: [API Docs](http://localhost:8001/docs)
- **Команда**: seo-team@example.com

## 📄 Лицензия

MIT License - см. файл [LICENSE](../LICENSE) для деталей. 