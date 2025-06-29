# 🚀 РУКОВОДСТВО ПО МОНИТОРИНГУ И ПРОФИЛИРОВАНИЮ RELINK

## 📋 СОДЕРЖАНИЕ

1. [Обзор системы](#обзор-системы)
2. [Настройка мониторинга](#настройка-мониторинга)
3. [Использование скрипта мониторинга](#использование-скрипта-мониторинга)
4. [Логирование на фронтенде](#логирование-на-фронтенде)
5. [Логирование на бэкенде](#логирование-на-бэкенде)
6. [Диагностика проблем](#диагностика-проблем)
7. [Рекомендации по оптимизации](#рекомендации-по-оптимизации)

---

## 🎯 ОБЗОР СИСТЕМЫ

### Что было добавлено

1. **Улучшенный Docker Compose** с:
   - Политиками перезапуска (`restart: unless-stopped`)
   - Ресурсными лимитами для всех сервисов
   - Улучшенными health checks с `start_period`
   - Ротацией логов с ограничением размера
   - Условными зависимостями (`condition: service_healthy`)

2. **Расширенная система логирования на фронтенде**:
   - Детальное профилирование запросов
   - Мониторинг производительности браузера
   - Перехват глобальных ошибок
   - Визуальный компонент для отображения логов

3. **Расширенная система мониторинга на бэкенде**:
   - Профилирование запросов с метриками
   - Мониторинг системных ресурсов
   - Middleware для автоматического профилирования
   - Контекстные менеджеры для операций

4. **Скрипт диагностики** для анализа проблем с контейнерами

---

## ⚙️ НАСТРОЙКА МОНИТОРИНГА

### 1. Переменные окружения

#### Для фронтенда (frontend/env.development):
```bash
# Включение отладки и профилирования
VITE_REACT_APP_DEBUG=true
VITE_REACT_APP_ENABLE_PROFILING=true
VITE_REACT_APP_ENABLE_DETAILED_LOGGING=true

# API настройки
VITE_REACT_APP_API_BASE_URL=http://localhost:8004
VITE_REACT_APP_WS_BASE_URL=ws://localhost:8004
```

#### Для бэкенда (в docker-compose.yml):
```yaml
environment:
  - DEBUG=true
  - LOG_LEVEL=DEBUG
  - ENABLE_PROFILING=true
  - ENABLE_DETAILED_LOGGING=true
  - ENABLE_REQUEST_PROFILING=true
  - ENABLE_PERFORMANCE_MONITORING=true
```

### 2. Запуск с мониторингом

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов в реальном времени
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## 🔍 ИСПОЛЬЗОВАНИЕ СКРИПТА МОНИТОРИНГА

### Основные команды

```bash
# Полный анализ системы
./scripts/monitor_containers.sh

# Анализ логов конкретного контейнера
./scripts/monitor_containers.sh logs relink-backend 100

# Проверка health endpoints
./scripts/monitor_containers.sh health

# Проверка системных ресурсов
./scripts/monitor_containers.sh resources

# Проверка сетевых соединений
./scripts/monitor_containers.sh network

# Получение рекомендаций
./scripts/monitor_containers.sh recommendations
```

### Примеры вывода

#### Статус контейнеров:
```
📊 СТАТУС КОНТЕЙНЕРОВ
====================
NAMES               STATUS              PORTS                    SIZE
relink-backend      Up 2 minutes        0.0.0.0:8004->8004/tcp   45.2MB
relink-frontend     Up 2 minutes        0.0.0.0:3000->3000/tcp   156MB
relink-chromadb     Up 2 minutes        0.0.0.0:8006->8000/tcp   2.1GB
```

#### Health checks:
```
🏥 HEALTH CHECKS
===============
✅ Router: OK
✅ Benchmark: OK
✅ Relink: OK
✅ Backend: OK
✅ LLM Tuning: OK
✅ Monitoring: OK
```

---

## 🖥️ ЛОГИРОВАНИЕ НА ФРОНТЕНДЕ

### Использование логгера

```typescript
import { useLogger } from '@/utils/logger';

function MyComponent() {
  const logger = useLogger('MyComponent');
  
  // Простое логирование
  logger.info('Компонент загружен');
  
  // Логирование с данными
  logger.debug('Получены данные', { 
    count: 42, 
    timestamp: new Date() 
  });
  
  // Профилирование запроса
  const requestId = logger.startRequestProfiling('/api/data', 'GET');
  try {
    const response = await fetch('/api/data');
    logger.endRequestProfiling(requestId, response.status, response.data);
  } catch (error) {
    logger.error('Ошибка запроса', { error });
  }
}
```

### Компонент ConsoleLogger

Автоматически отображается в правом нижнем углу при включенном детальном логировании:

- **Показать/Скрыть логи** - кнопка переключения
- **Очистить логи** - удаление всех записей
- **Экспорт логов** - сохранение в JSON файл
- **Статистика** - счетчики запросов, ошибок, предупреждений

### Что логируется автоматически

1. **Глобальные ошибки JavaScript**
2. **Необработанные отклонения промисов**
3. **Ошибки загрузки ресурсов**
4. **Метрики производительности** (Web Vitals)
5. **Использование памяти** (если доступно)
6. **Все console.log/warn/error вызовы**

---

## 🔧 ЛОГИРОВАНИЕ НА БЭКЕНДЕ

### Автоматическое профилирование

Все HTTP запросы автоматически профилируются middleware:

```python
# В логах вы увидите:
🚀 Начало профилирования запроса
  request_id: req_1703123456789_abc123
  method: POST
  url: /api/v1/seo/analyze
  memory_before: 45.2%
  cpu_before: 12.3%

✅ Завершение профилирования запроса
  request_id: req_1703123456789_abc123
  status_code: 200
  duration: 1.234s
  memory_delta: +2.1%
  cpu_delta: +5.7%
```

### Ручное профилирование операций

```python
from app.monitoring import monitor_operation, profile_function

# Контекстный менеджер
async with monitor_operation("analyze_domain", {"domain": "example.com"}) as op_id:
    # Ваш код здесь
    result = await analyze_domain(domain)
    return result

# Декоратор
@profile_function("generate_recommendations")
async def generate_recommendations(posts: List[dict]):
    # Функция автоматически профилируется
    pass
```

### Получение метрик

```python
# Текущие метрики
metrics = await get_metrics()

# Статус здоровья
health = await get_health_status()
```

---

## 🔍 ДИАГНОСТИКА ПРОБЛЕМ

### 1. Контейнеры рестартуются

```bash
# Проверка статуса
docker-compose ps

# Анализ логов проблемного контейнера
./scripts/monitor_containers.sh logs relink-backend 100

# Проверка ресурсов
./scripts/monitor_containers.sh resources
```

### 2. Медленные ответы

```bash
# Проверка health endpoints
./scripts/monitor_containers.sh health

# Анализ логов с профилированием
docker-compose logs -f backend | grep "duration\|slow"

# Проверка системных ресурсов
./scripts/monitor_containers.sh resources
```

### 3. Ошибки в браузере

1. Откройте консоль разработчика (F12)
2. Найдите компонент ConsoleLogger в правом нижнем углу
3. Нажмите "Показать логи"
4. Изучите детали ошибок с контекстом

### 4. Проблемы с сетью

```bash
# Проверка портов
./scripts/monitor_containers.sh network

# Проверка доступности сервисов
curl -f http://localhost:8004/health
curl -f http://localhost:3000
```

---

## ⚡ РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ

### 1. Настройка ресурсов

Если контейнеры падают из-за нехватки ресурсов:

```yaml
# В docker-compose.yml увеличьте лимиты
deploy:
  resources:
    limits:
      memory: 2G  # Увеличьте с 1G
      cpus: '1.0' # Увеличьте с 0.5
    reservations:
      memory: 1G  # Увеличьте с 512M
      cpus: '0.5' # Увеличьте с 0.25
```

### 2. Оптимизация health checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
  interval: 60s    # Увеличьте с 30s
  timeout: 20s     # Увеличьте с 10s
  retries: 5       # Увеличьте с 3
  start_period: 120s # Увеличьте с 60s
```

### 3. Настройка логирования

Для продакшена отключите детальное логирование:

```yaml
environment:
  - DEBUG=false
  - LOG_LEVEL=INFO
  - ENABLE_PROFILING=false
  - ENABLE_DETAILED_LOGGING=false
```

### 4. Мониторинг в реальном времени

```bash
# Мониторинг ресурсов контейнеров
docker stats

# Логи в реальном времени
docker-compose logs -f

# Мониторинг через Prometheus
open http://localhost:9090
```

---

## 🚨 ЧАСТЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

### 1. Контейнер не запускается

**Симптомы**: `Exit code 1`, `Container exited`

**Решение**:
```bash
# Проверьте логи
docker-compose logs [service_name]

# Проверьте зависимости
docker-compose ps

# Пересоберите образ
docker-compose build --no-cache [service_name]
```

### 2. Health check не проходит

**Симптомы**: `unhealthy`, `starting`

**Решение**:
```bash
# Увеличьте start_period в docker-compose.yml
# Проверьте endpoint в health check
curl -f http://localhost:[port]/health

# Проверьте зависимости сервиса
```

### 3. Высокое использование ресурсов

**Симптомы**: Медленные ответы, контейнеры падают

**Решение**:
```bash
# Проверьте ресурсы
./scripts/monitor_containers.sh resources

# Увеличьте лимиты в docker-compose.yml
# Оптимизируйте код
# Добавьте кэширование
```

### 4. Ошибки в браузере

**Симптомы**: Белый экран, ошибки в консоли

**Решение**:
1. Откройте консоль разработчика
2. Найдите ConsoleLogger компонент
3. Изучите логи с деталями
4. Проверьте API endpoints

---

## 📊 МЕТРИКИ И АНАЛИТИКА

### Доступные метрики

1. **Системные**:
   - CPU использование
   - Память (использованная/доступная)
   - Дисковое пространство
   - Сетевой трафик

2. **Приложения**:
   - Количество запросов
   - Время ответа
   - Процент ошибок
   - Активные соединения

3. **Производительность**:
   - Медленные запросы (>2s)
   - Использование памяти по запросам
   - CPU нагрузка по операциям

### Экспорт данных

```bash
# Экспорт логов фронтенда
# Используйте кнопку "Экспорт" в ConsoleLogger

# Экспорт метрик бэкенда
curl http://localhost:8004/metrics > metrics.json

# Экспорт логов контейнеров
docker-compose logs > all_logs.txt
```

---

## 🎯 ЗАКЛЮЧЕНИЕ

Новая система мониторинга предоставляет:

✅ **Автоматическое профилирование** всех запросов и операций  
✅ **Детальное логирование** с контекстом и метриками  
✅ **Визуальный интерфейс** для анализа логов в браузере  
✅ **Диагностические инструменты** для выявления проблем  
✅ **Рекомендации** по оптимизации и исправлению  

Используйте эти инструменты для:
- Быстрого выявления проблем
- Оптимизации производительности
- Улучшения стабильности системы
- Профилирования пользовательского опыта

---

## 📞 ПОДДЕРЖКА

При возникновении проблем:

1. Запустите диагностику: `./scripts/monitor_containers.sh`
2. Изучите логи: `docker-compose logs -f [service]`
3. Проверьте ресурсы: `./scripts/monitor_containers.sh resources`
4. Обратитесь к этому руководству

**Удачного мониторинга! 🚀** 