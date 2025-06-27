# 🚀 SEO Link Recommender

Интеллектуальная система для генерации внутренних ссылок с использованием AI и семантического анализа.

## 🎯 Возможности

- 🤖 **AI-генерация ссылок** с использованием Ollama
- 🧠 **Семантический анализ** контента
- 📊 **Тематическая кластеризация** статей
- 🔗 **Кумулятивный интеллект** - накопление знаний
- 📈 **A/B тестирование** моделей
- 🌐 **WordPress интеграция**
- ⚡ **Параллельные frontend** (Classic + Vite)

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

## 🌐 Доступ к приложениям

### Параллельный режим
| Сервис | URL | Описание |
|--------|-----|----------|
| 🎯 **Classic Frontend** | http://localhost:3000 | Обычный вариант |
| ⚡ **Vite Frontend** | http://localhost:3001 | Современный вариант |
| 🔧 **Backend API** | http://localhost:8000 | FastAPI backend |
| 🧠 **Ollama** | http://localhost:11434 | LLM сервис |

### Обычный режим
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Ollama: http://localhost:11434

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Frontend      │
│   (Classic)     │    │   (Vite)        │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┼───┐
                                 │   │
                    ┌─────────────▼───▼─────────────┐
                    │         Backend               │
                    │      (FastAPI + SQLAlchemy)   │
                    └─────────────┬─────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌────────▼────────┐    ┌──────────▼──────────┐    ┌───────▼────────┐
│   PostgreSQL    │    │      Ollama         │    │   ChromaDB     │
│   (Database)    │    │   (LLM Models)      │    │   (Vector DB)  │
└─────────────────┘    └─────────────────────┘    └─────────────────┘
```

## 🔧 Технологии

### Backend
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД
- **PostgreSQL** - основная база данных
- **ChromaDB** - векторная база данных
- **Ollama** - локальные LLM модели

### Frontend
- **React** - пользовательский интерфейс
- **TypeScript** - типизированный JavaScript
- **Tailwind CSS** - стилизация
- **Vite** - современный сборщик (опционально)

### AI/ML
- **Qwen2.5:7b** - основная LLM модель
- **TF-IDF** - векторизация текста
- **Кластеризация** - тематическая группировка
- **Семантический анализ** - понимание контекста

## 📊 Основные функции

### 1. Индексация WordPress
```bash
# Анализ WordPress сайта
curl -X POST http://localhost:8000/api/v1/wp_index \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'
```

### 2. Генерация рекомендаций
```bash
# Получение рекомендаций
curl -X POST http://localhost:8000/api/v1/wp_index \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "comprehensive": true}'
```

### 3. Мониторинг Ollama
```bash
# Проверка статуса
curl http://localhost:8000/api/v1/ollama_status
```

## 🧠 AI Возможности

### Семантический анализ
- Извлечение ключевых концепций
- Тематическая кластеризация
- Оценка связности контента

### Кумулятивный интеллект
- Накопление знаний о связях
- Эволюция рекомендаций
- Анализ успешности внедрения

### A/B тестирование моделей
- Сравнение производительности
- Оценка качества рекомендаций
- Оптимизация параметров

## 🚀 Производительность

### Оптимизация для Apple M4
- **OLLAMA_METAL=1** - использование Metal Performance Shaders
- **OLLAMA_FLASH_ATTENTION=1** - ускорение внимания
- **OLLAMA_KV_CACHE_TYPE=q8_0** - квантованный кэш
- **16GB памяти** для Ollama
- **8 CPU cores** для максимальной производительности

### Мониторинг ресурсов
```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Логи Ollama
docker-compose logs -f ollama
```

## 🔍 Отладка

### Проблемы с запуском
```bash
# Проверка портов
lsof -i :3000
lsof -i :8000
lsof -i :11434

# Очистка Docker
docker system prune -f
docker volume prune -f
```

### Проблемы с Ollama
```bash
# Проверка моделей
curl http://localhost:11434/api/tags

# Перезапуск Ollama
docker-compose restart ollama
```

### Логи приложения
```bash
# Все логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 📚 Документация

- [Параллельный запуск](PARALLEL_SETUP.md)
- [Быстрый старт](QUICK_START.md)
- [GPU руководство](GPU_GUIDE.md)
- [UI архитектура](UI_ARCHITECTURE_RULES.md)

## 🛠️ Разработка

### Установка зависимостей
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Запуск в режиме разработки
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend (Classic)
cd frontend
npm run dev

# Frontend (Vite)
cd frontend
npm run dev:vite
```

### Тестирование
```bash
# Backend тесты
cd backend
pytest

# Frontend тесты
cd frontend
npm test
```

## 📈 Мониторинг и аналитика

### Метрики производительности
- Время генерации рекомендаций
- Использование памяти и CPU
- Качество рекомендаций
- Успешность внедрения

### Логирование
- Структурированные логи
- Мониторинг ошибок
- Трассировка запросов
- Аналитика использования

## 🔒 Безопасность

- Изоляция контейнеров
- Безопасные переменные окружения
- Валидация входных данных
- Логирование безопасности

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

- Создайте Issue для багов
- Обсудите в Discussions
- Обратитесь к документации

---

**🎉 Готово!** Теперь у вас есть мощная система для генерации внутренних ссылок с использованием AI. 