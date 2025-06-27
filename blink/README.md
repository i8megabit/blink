# 🚀 reLink - AI-Powered SEO Platform v4.0.0

**Версия:** 4.0.0  
**Дата релиза:** 2024-12-19  
**Статус:** Production Ready

Интеллектуальная система для генерации внутренних ссылок с использованием AI и семантического анализа.

## 🎯 Возможности

- 🤖 **AI-генерация ссылок** с использованием Ollama
- 🧠 **Семантический анализ** контента
- 📊 **Тематическая кластеризация** статей
- 🔗 **Кумулятивный интеллект** - накопление знаний
- 📈 **A/B тестирование** моделей
- 🌐 **WordPress интеграция**
- ⚡ **Параллельные frontend** (Classic + Vite)
- 🏷️ **Система управления версиями** с автоматическими Git тегами

## 🚀 Быстрый старт

### Параллельный запуск (рекомендуется)
```bash
# Запуск обоих вариантов одновременно
cd seo_link_recommender
./run_parallel.sh
```

### Обычный запуск
```bash
# Classic вариант
docker-compose up --build

# Vite вариант
docker-compose -f docker-compose.vite.yml up --build
```

### Нативный GPU (максимальная производительность)
```bash
# Настройка нативного GPU
./scripts/native-gpu-setup.sh

# Запуск с GPU
docker-compose -f docker-compose.native-gpu.yml up
```

## 🌐 Доступ к приложению

| Сервис | URL | Описание |
|--------|-----|----------|
| 🎯 **Classic Frontend** | http://localhost:3000 | Стабильный интерфейс |
| ⚡ **Vite Frontend** | http://localhost:3001 | Современный интерфейс |
| 🔧 **Backend API** | http://localhost:8000 | FastAPI backend |
| 📚 **API Docs** | http://localhost:8000/docs | Swagger документация |
| 🧠 **Ollama** | http://localhost:11434 | LLM сервис |

## 🏷️ Управление версиями

```bash
# Показать версию
make version

# Установить новую версию
make set-version VERSION=3.0.18

# Создать релиз
make release-version VERSION=3.0.18
```

## 📚 Документация

**📖 [Полная документация](UNIFIED_DOCUMENTATION.md)** — все аспекты проекта в одном файле

### Быстрые ссылки
- [🚀 Быстрый старт](UNIFIED_DOCUMENTATION.md#-как-быстро-начать-работу)
- [🏗️ Архитектура](UNIFIED_DOCUMENTATION.md#️-архитектура-системы)
- [⚡ Производительность](UNIFIED_DOCUMENTATION.md#-производительность-и-оптимизация)
- [🔧 Управление версиями](UNIFIED_DOCUMENTATION.md#-управление-версиями)
- [🐳 Docker](UNIFIED_DOCUMENTATION.md#-docker-и-развертывание)
- [🧠 AI и ML](UNIFIED_DOCUMENTATION.md#-ai-и-машинное-обучение)

## 🧪 Тестирование

```bash
# Backend тесты
cd backend && python -m pytest tests/ -v

# Frontend тесты
cd frontend && npm test

# Интеграционные тесты
docker-compose exec backend python -m pytest tests/ -v
```

## 🔍 Мониторинг

```bash
# Проверка здоровья
curl http://localhost:8000/api/v1/health

# Статус Ollama
curl http://localhost:11434/api/tags

# Логи
docker-compose logs -f
```

## 🚀 Продакшн

```bash
# Публикация в Docker Hub
./scripts/publish-dockerhub.sh latest

# Продакшн конфигурация
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте feature branch
3. Внесите изменения с тестами
4. Создайте Pull Request

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

**📖 [Читать полную документацию](UNIFIED_DOCUMENTATION.md)** 