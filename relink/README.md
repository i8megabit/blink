# 🚀 reLink - AI-Powered SEO Platform v4.1.1.019

**Версия:** 4.1.1.019  
**Дата релиза:** 2024-12-19  
**Статус:** Production Ready

Интеллектуальная система для генерации внутренних ссылок с использованием AI и семантического анализа.

## 📊 Метрики проекта

![Lines of Code](https://img.shields.io/badge/lines%20of%20code-13,834-brightgreen)
![Repository Size](https://img.shields.io/badge/repository%20size-4.7GB-blue)
![Files](https://img.shields.io/badge/files-138-blue)
![Python](https://img.shields.io/badge/python-3.11+-yellow)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue)
![Docker](https://img.shields.io/badge/docker-20.10+-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Apple Silicon](https://img.shields.io/badge/apple%20silicon-M4%20optimized-purple)
![Memory](https://img.shields.io/badge/memory-16GB-red)
![CPU Cores](https://img.shields.io/badge/CPU%20cores-10-orange)

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
- **Интеллектуальная маршрутизация** - автоматический выбор оптимальной модели
- **RAG-интеграция** - семантический поиск и контекстное обогащение
- **Кэширование** - Redis для ускорения повторных запросов
- **Мониторинг** - детальная аналитика производительности

### Поддерживаемые модели:
- **qwen2.5:7b-instruct-turbo** - основная модель для генерации
- **qwen2.5:14b-instruct** - для сложных аналитических задач
- **llama3.2:3b-instruct** - быстрые ответы
- **llama3.2:8b-instruct** - баланс скорости и качества

## 🏗️ Микросервисная архитектура

### Основные сервисы:
- **Backend** (FastAPI) - основная бизнес-логика
- **Frontend** (React + TypeScript) - пользовательский интерфейс
- **LLM Tuning** - оптимизация и настройка моделей
- **Monitoring** - мониторинг и алерты
- **Docs** - управление документацией
- **Testing** - автоматизированное тестирование

### Технологический стек:
- **Backend**: FastAPI, SQLAlchemy, Alembic, Redis
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **AI/ML**: Ollama, RAG, семантический анализ
- **DevOps**: Docker, Docker Compose, GitHub Actions
- **Monitoring**: Prometheus, Grafana, ELK Stack

## 🚀 Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Node.js 18+ (для разработки)
- Python 3.11+ (для разработки)

### Запуск в production
```bash
# Клонирование репозитория
git clone https://github.com/your-username/reLink.git
cd reLink

# Запуск всех сервисов
docker-compose up -d --build

# Проверка статуса
docker-compose ps
```

### Доступ к приложению
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Ollama**: http://localhost:11434
- **Monitoring**: http://localhost:9090
- **Documentation**: http://localhost:8001

## 🧪 Тестирование

### Unit тесты
```bash
cd frontend
npm test
```

### E2E тесты
```bash
cd frontend
npm run test:e2e
```

### Backend тесты
```bash
cd backend
pytest
```

## 📊 API Endpoints

### Основные endpoints
- `GET /api/v1/health` - Проверка здоровья сервиса
- `GET /api/v1/version` - Версия приложения
- `GET /api/v1/ollama_status` - Статус Ollama
- `GET /api/v1/domains` - Список доменов
- `GET /api/v1/analysis_history` - История анализов
- `GET /api/v1/benchmarks` - Список бенчмарков
- `GET /api/v1/settings` - Настройки приложения

### WebSocket endpoints
- `WS /ws/{client_id}` - WebSocket для real-time обновлений

## 🎯 Функциональность

### 🔍 Анализ WordPress сайтов
- Автоматическое извлечение статей
- Семантический анализ контента
- Выявление тематических кластеров
- Генерация внутренних ссылок

### 🤖 AI рекомендации
- Интеграция с Ollama LLM
- Контекстные рекомендации
- Семантический поиск
- Адаптивное обучение

### 📈 Бенчмарки и метрики
- Сравнение производительности моделей
- Web Vitals мониторинг
- SEO метрики
- Производительность API

### 📊 Визуализация
- Интерактивные графики
- Тематические карты
- Связи между статьями
- Статистика и аналитика

## 🔧 Конфигурация

### Переменные окружения
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db

# Ollama
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:7b-instruct-turbo

# API
ENVIRONMENT=production
GIT_COMMIT_HASH=abc123
```

### Настройка Ollama
```bash
# Установка модели
ollama pull qwen2.5:7b-instruct-turbo

# Проверка статуса
curl http://localhost:11434/api/tags
```

## 📈 Производительность

### Метрики
- **Bundle size**: 295KB (gzipped: 82KB)
- **Build time**: ~900ms
- **API response time**: < 100ms
- **Database queries**: оптимизированы с индексами

### Оптимизации
- Lazy loading компонентов
- Кэширование API ответов
- Оптимизированные изображения
- Tree shaking для уменьшения bundle

## 🤝 Контрибьюция

### Процесс разработки
1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Следуйте стандартам кода (ESLint, Prettier, TypeScript)
4. Напишите тесты для новой функциональности
5. Commit изменения (`git commit -m 'Add amazing feature'`)
6. Push в branch (`git push origin feature/amazing-feature`)
7. Откройте Pull Request

### Стандарты кода
- TypeScript для всего кода
- Tailwind CSS для стилей
- ESLint + Prettier для форматирования
- Тесты для всех компонентов
- Семантические коммиты

## 📄 Лицензия

Этот проект лицензирован под Apache License 2.0 - см. файл [LICENSE](LICENSE) для деталей.

### Разрешения
- ✅ Коммерческое использование
- ✅ Модификация
- ✅ Распространение
- ✅ Патентное использование
- ✅ Частное использование

### Условия
- ℹ️ Лицензия и авторские права
- ℹ️ Уведомление об изменениях
- ℹ️ Состояние файлов

## 🆘 Поддержка

### Документация
- [API Documentation](http://localhost:8000/docs) - Swagger UI
- [Component Library](http://localhost:6006) - Storybook (в разработке)

### Сообщество
- [Issues](https://github.com/your-username/reLink/issues) - Баг репорты и feature requests
- [Discussions](https://github.com/your-username/reLink/discussions) - Обсуждения
- [Wiki](https://github.com/your-username/reLink/wiki) - Дополнительная документация

### Контакты
- **TheFounder**: @eberil
- **Telegram**: @reLink_support
- **Discord**: [reLink Community](https://discord.gg/reLink)

## 🏆 Достижения

### Технические достижения
- ✅ 100% TypeScript покрытие
- ✅ Современный стек технологий
- ✅ Оптимизация для Apple Silicon
- ✅ Микрофронтенд архитектура
- ✅ Real-time обновления

### Пользовательские достижения
- ✅ Интуитивный интерфейс
- ✅ Быстрая загрузка
- ✅ Адаптивный дизайн
- ✅ Доступность (WCAG 2.1 AA)
- ✅ Профессиональный UX

---

*reLink - Мировая платформа для SEO-инженеров с AI и современными технологиями* 🚀 