# 🚀 Параллельный запуск SEO Link Recommender

## 📋 Обзор

Этот режим позволяет запустить **оба варианта frontend** одновременно:
- 🎯 **Classic** (обычный) - порт 3000
- ⚡ **Vite** (современный) - порт 3001

## 🎯 Преимущества параллельного запуска

1. **A/B тестирование** - сравнение производительности
2. **Разработка** - одновременная работа с обоими вариантами
3. **Демонстрация** - показ различий между подходами
4. **Миграция** - постепенный переход с Classic на Vite

## 🚀 Быстрый запуск

### Автоматический запуск
```bash
# Из корневой директории проекта
cd seo_link_recommender
./run_parallel.sh
```

### Ручной запуск
```bash
# Запуск с очисткой
./run_parallel.sh --clean

# Или через docker-compose
docker-compose -f docker-compose.parallel.yml up --build -d
```

## 🌐 Доступ к приложениям

После запуска будут доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| 🎯 **Classic Frontend** | http://localhost:3000 | Обычный вариант |
| ⚡ **Vite Frontend** | http://localhost:3001 | Современный вариант |
| 🔧 **Backend API** | http://localhost:8000 | FastAPI backend |
| 🧠 **Ollama** | http://localhost:11434 | LLM сервис |
| 📊 **Traefik Dashboard** | http://localhost:8080 | Прокси панель |

### Traefik маршрутизация
- Classic: http://localhost/classic
- Vite: http://localhost/vite

## 🔧 Архитектура

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Frontend      │
│   Classic       │    │   Vite          │
│   :3000         │    │   :3001         │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┼───┐
                                 │   │
                    ┌─────────────▼───▼─────────────┐
                    │         Traefik               │
                    │         :80/:443              │
                    └─────────────┬─────────────────┘
                                  │
                    ┌─────────────▼─────────────────┐
                    │         Backend               │
                    │         :8000                 │
                    └─────────────┬─────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌────────▼────────┐    ┌──────────▼──────────┐    ┌───────▼────────┐
│   PostgreSQL    │    │      Ollama         │    │   ChromaDB     │
│   :5432         │    │      :11434         │    │   (внутренний)  │
└─────────────────┘    └─────────────────────┘    └─────────────────┘
```

## 📊 Мониторинг

### Проверка статуса
```bash
# Статус всех контейнеров
docker-compose -f docker-compose.parallel.yml ps

# Логи всех сервисов
docker-compose -f docker-compose.parallel.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.parallel.yml logs -f frontend-classic
docker-compose -f docker-compose.parallel.yml logs -f frontend-vite
```

### Health checks
```bash
# Backend
curl http://localhost:8000/api/v1/health

# Ollama
curl http://localhost:11434/api/tags

# Frontend Classic
curl http://localhost:3000

# Frontend Vite
curl http://localhost:3001
```

## 🛠️ Управление

### Остановка
```bash
# Graceful остановка
docker-compose -f docker-compose.parallel.yml down

# Принудительная остановка
docker-compose -f docker-compose.parallel.yml down --remove-orphans
```

### Перезапуск
```bash
# Перезапуск всех сервисов
docker-compose -f docker-compose.parallel.yml restart

# Перезапуск конкретного сервиса
docker-compose -f docker-compose.parallel.yml restart frontend-classic
```

### Обновление
```bash
# Пересборка и обновление
docker-compose -f docker-compose.parallel.yml up --build -d
```

## 🔍 Отладка

### Проблемы с Classic Frontend
```bash
# Проверка логов
docker-compose -f docker-compose.parallel.yml logs frontend-classic

# Вход в контейнер
docker-compose -f docker-compose.parallel.yml exec frontend-classic sh
```

### Проблемы с Vite Frontend
```bash
# Проверка логов
docker-compose -f docker-compose.parallel.yml logs frontend-vite

# Вход в контейнер
docker-compose -f docker-compose.parallel.yml exec frontend-vite sh
```

### Проблемы с Backend
```bash
# Проверка логов
docker-compose -f docker-compose.parallel.yml logs backend

# Вход в контейнер
docker-compose -f docker-compose.parallel.yml exec backend sh
```

## 📈 Производительность

### Ресурсы для Apple M4
- **Memory**: 16GB (Ollama) + 2GB (остальные сервисы)
- **CPU**: 8 cores (Ollama) + 2 cores (остальные)
- **Storage**: ~10GB для моделей + 2GB для приложения

### Оптимизации
- Ollama оптимизирован для Apple Silicon
- Frontend контейнеры используют Alpine Linux
- Traefik обеспечивает эффективную маршрутизацию

## 🔄 Миграция между вариантами

### Classic → Vite
1. Запустите параллельный режим
2. Протестируйте Vite на http://localhost:3001
3. Убедитесь в совместимости
4. Переключитесь на Vite

### Vite → Classic
1. Если возникли проблемы с Vite
2. Используйте Classic как fallback
3. Анализируйте различия в логах

## 🚨 Устранение неполадок

### Порт занят
```bash
# Проверка занятых портов
lsof -i :3000
lsof -i :3001
lsof -i :8000

# Остановка процессов
sudo kill -9 <PID>
```

### Проблемы с Docker
```bash
# Очистка Docker
docker system prune -f
docker volume prune -f

# Перезапуск Docker
sudo systemctl restart docker
```

### Проблемы с Ollama
```bash
# Проверка моделей
curl http://localhost:11434/api/tags

# Перезапуск Ollama
docker-compose -f docker-compose.parallel.yml restart ollama
```

## 📝 Логи и отладка

### Структура логов
```
frontend-classic_1  | [nginx] Access logs
frontend-vite_1     | [nginx] Access logs
backend_1           | [FastAPI] Application logs
ollama_1            | [Ollama] Model loading logs
db_1                | [PostgreSQL] Database logs
traefik_1           | [Traefik] Routing logs
```

### Полезные команды
```bash
# Логи в реальном времени
docker-compose -f docker-compose.parallel.yml logs -f --tail=100

# Логи с временными метками
docker-compose -f docker-compose.parallel.yml logs -f -t

# Логи конкретного сервиса
docker-compose -f docker-compose.parallel.yml logs -f backend
```

## 🎯 Следующие шаги

1. **Тестирование** - сравните производительность
2. **Разработка** - выберите предпочтительный вариант
3. **Оптимизация** - настройте под ваши нужды
4. **Документация** - обновите README проекта

---

**🎉 Готово!** Теперь у вас запущены оба варианта frontend параллельно для сравнения и тестирования. 