# 🧠 LLM Tuning Microservice

## 🎯 Миссия
Мощный микросервис для управления LLM моделями в reLink - маршрутизатор, RAG-нативный оркестратор и динамический тюнер производительности.

## 🏗️ Архитектура

### Core Components
- **Model Router** - умная маршрутизация запросов к оптимальным моделям
- **RAG Engine** - нативная интеграция с векторными БД и контекстом
- **Dynamic Tuner** - ZooKeeper-подобное управление конфигурацией в реальном времени
- **Performance Monitor** - мониторинг и оптимизация качества ответов
- **Fine-tuning Pipeline** - адаптация моделей на лету

### Key Features
- 🚀 **Ultra-fast** routing (< 10ms latency)
- 🧠 **RAG-native** с ChromaDB/Weaviate
- ⚡ **Dynamic tuning** без остановки Ollama
- 📊 **Real-time metrics** и A/B тестирование
- 🔄 **Auto-scaling** моделей по нагрузке
- 🎯 **Context-aware** выбор оптимальной модели

## 🛠️ Технологический стек
- **FastAPI** + **Pydantic** - современный API
- **SQLAlchemy** + **Alembic** - работа с БД
- **Redis** - кэширование и очереди
- **ChromaDB/Weaviate** - векторные БД
- **Prometheus** + **Grafana** - мониторинг
- **Docker** + **Kubernetes** - контейнеризация

## 🚀 Быстрый старт
```bash
# Запуск микросервиса
make llm-tuning-up

# Проверка статуса
make llm-tuning-status

# Логи
make llm-tuning-logs
```

## 📊 API Endpoints
- `POST /api/v1/route` - маршрутизация запросов
- `POST /api/v1/rag/query` - RAG запросы
- `PUT /api/v1/tune` - динамическая настройка
- `GET /api/v1/models/status` - статус моделей
- `POST /api/v1/fine-tune` - файнтюнинг

## 🎯 Интеграция
- **Frontend** - React компоненты для управления
- **Database** - PostgreSQL для метаданных
- **Ollama** - управление моделями
- **Other Microservices** - единая точка входа для LLM 