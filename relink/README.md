# 🚀 reLink - AI-Powered SEO Platform v4.1.1.019

**Версия:** 4.1.1.019  
**Дата релиза:** 2024-12-19  
**Статус:** Production Ready

Интеллектуальная система для генерации внутренних ссылок с использованием AI и семантического анализа.

## 📊 Метрики проекта

![Lines of Code](https://img.shields.io/badge/lines%20of%20code-17,951-brightgreen)
![Files](https://img.shields.io/badge/files-97-blue)
![Python](https://img.shields.io/badge/python-3.11+-yellow)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue)
![Docker](https://img.shields.io/badge/docker-20.10+-orange)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 Возможности

- 🤖 **AI-генерация ссылок** с использованием Ollama
- 🧠 **Семантический анализ** контента
- 📊 **Тематическая кластеризация** статей
- 🔗 **Кумулятивный интеллект** - накопление знаний
- 📈 **A/B тестирование** моделей
- 🌐 **WordPress интеграция**
- ⚡ **Параллельные frontend** (Classic + Vite)
- 🏷️ **Система управления версиями** с автоматическими Git тегами

## 🧠 LLM-маршрутизатор и RAG-подход

### Архитектурное решение
Все микросервисы reLink, взаимодействующие с Ollama, используют **единый LLM-маршрутизатор**, основанный на проверенном RAG-подходе, разработанном в сервисе SEO-рекомендаций.

### Ключевые принципы:
- **Единая точка входа** - все запросы к LLM проходят через `llm_router.py`
- **RAG-подход** - Retrieval-Augmented Generation для улучшения качества ответов
- **Конкурентная обработка** - семафоры и очереди для стабильности Ollama
- **Кэширование** - Redis для оптимизации повторных запросов
- **Мониторинг** - детальная аналитика всех LLM-взаимодействий

### Модель и бенчмарки
**Основная модель:** Qwen2.5-Instruct (Qwen2.5-7B-Instruct)
- **Версия:** Turbo (оптимизированная для скорости)
- **Контекст:** 32K токенов
- **Квантование:** Q4_K_M для оптимизации памяти
- **Производительность:** ~24 секунды на сложный запрос (SEO-анализ)

### Бенчмарк-результаты:
- **SEO-рекомендации:** 24.04s (сложный анализ)
- **Генерация диаграмм:** ~15-20s (SVG + оптимизация)
- **Бенчмарк-анализ:** ~10-15s (метрики + сравнения)
- **Стабильность:** 99.8% успешных запросов

### Микросервисы с LLM-интеграцией:
1. **SEO-рекомендации** (первопроходец RAG-подхода)
2. **Генерация диаграмм** (SVG + архитектурные схемы)
3. **Бенчмарк-анализ** (сравнение производительности)
4. **LLM-тюнинг** (оптимизация промптов)

### Конфигурация Ollama для Apple Silicon:
```bash
OLLAMA_METAL=1                    # Использование Metal Performance Shaders
OLLAMA_FLASH_ATTENTION=1          # Ускорение внимания
OLLAMA_KV_CACHE_TYPE=q8_0         # Оптимизация кэша
OLLAMA_CONTEXT_LENGTH=32768       # Контекст 32K
OLLAMA_BATCH_SIZE=512             # Размер батча
OLLAMA_NUM_PARALLEL=2             # Параллельные запросы
OLLAMA_MEM_FRACTION=0.9           # Использование памяти
```

## 🚀 Быстрый старт

### Параллельный запуск (рекомендуется)
```bash
# Запуск обоих вариантов одновременно
cd relink
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