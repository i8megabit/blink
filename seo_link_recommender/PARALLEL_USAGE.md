# 🚀 Параллельные варианты фронтенда SEO Link Recommender

## 📋 Обзор

Проект теперь поддерживает запуск двух вариантов фронтенда одновременно:

- **Classic Frontend** (порт 3000) - классическая версия
- **Vite Frontend** (порт 3001) - современная версия с Vite

## 🎯 Доступные URL

### Основные сервисы
- **Classic Frontend**: http://localhost:3000
- **Vite Frontend**: http://localhost:3001  
- **Backend API**: http://localhost:8000
- **Ollama API**: http://localhost:11434
- **Traefik Dashboard**: http://localhost:8080

### API Endpoints
- **Health Check**: http://localhost:8000/api/v1/health
- **Domains**: http://localhost:8000/api/v1/domains
- **Analysis History**: http://localhost:8000/api/v1/analysis_history
- **Ollama Status**: http://localhost:8000/api/v1/ollama_status

## 🚀 Запуск

### Параллельный запуск (рекомендуется)
```bash
# Запуск всех сервисов
docker-compose -f docker-compose.parallel.yml up -d

# Просмотр логов
docker-compose -f docker-compose.parallel.yml logs -f

# Остановка
docker-compose -f docker-compose.parallel.yml down
```

### Классический запуск
```bash
# Только Classic Frontend
docker-compose up -d

# Только Vite Frontend  
docker-compose -f docker-compose.vite.yml up -d
```

## 🔧 Управление

### Проверка статуса
```bash
# Статус всех контейнеров
docker-compose -f docker-compose.parallel.yml ps

# Логи конкретного сервиса
docker-compose -f docker-compose.parallel.yml logs frontend-classic
docker-compose -f docker-compose.parallel.yml logs frontend-vite
docker-compose -f docker-compose.parallel.yml logs backend
docker-compose -f docker-compose.parallel.yml logs ollama
```

### Перезапуск сервисов
```bash
# Перезапуск конкретного сервиса
docker-compose -f docker-compose.parallel.yml restart frontend-classic
docker-compose -f docker-compose.parallel.yml restart frontend-vite

# Перезапуск всех сервисов
docker-compose -f docker-compose.parallel.yml restart
```

## 🧪 Тестирование

### Проверка доступности
```bash
# Проверка Classic Frontend
curl -s http://localhost:3000 | head -5

# Проверка Vite Frontend
curl -s http://localhost:3001 | head -5

# Проверка Backend API
curl -s http://localhost:8000/api/v1/health

# Проверка Ollama
curl -s http://localhost:11434/api/tags | jq '.models | length'
```

## 📊 Мониторинг

### Traefik Dashboard
- URL: http://localhost:8080
- Показывает маршруты и статус сервисов

### Ollama Status
- Проверка моделей: http://localhost:11434/api/tags
- Статус через API: http://localhost:8000/api/v1/ollama_status

## 🔍 Отладка

### Проблемы с Classic Frontend
```bash
# Проверка логов
docker-compose -f docker-compose.parallel.yml logs frontend-classic

# Пересборка образа
docker-compose -f docker-compose.parallel.yml build frontend-classic
```

### Проблемы с Vite Frontend
```bash
# Проверка логов
docker-compose -f docker-compose.parallel.yml logs frontend-vite

# Пересборка образа
docker-compose -f docker-compose.parallel.yml build frontend-vite
```

### Проблемы с Backend
```bash
# Проверка логов
docker-compose -f docker-compose.parallel.yml logs backend

# Проверка подключения к БД
docker-compose -f docker-compose.parallel.yml exec backend python -c "import asyncio; from app.main import AsyncSessionLocal; print('DB OK')"
```

## 🎨 Различия между вариантами

### Classic Frontend (порт 3000)
- Классическая архитектура
- Стабильная работа
- Подходит для production

### Vite Frontend (порт 3001)
- Современная архитектура с Vite
- Быстрая разработка
- Hot Module Replacement
- Оптимизированная сборка

## 📝 Примечания

- Оба фронтенда используют один и тот же Backend API
- Ollama оптимизирован для Apple M4 с CPU-ускорением
- Все данные сохраняются в PostgreSQL
- Модели Ollama кэшируются в `./ollama_models/`

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose -f docker-compose.parallel.yml logs`
2. Убедитесь, что порты не заняты: `lsof -i :3000,3001,8000,11434`
3. Перезапустите сервисы: `docker-compose -f docker-compose.parallel.yml restart` 