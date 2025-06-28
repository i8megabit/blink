# 🍎 LLM Tuning для Apple Silicon

Оптимизированный микросервис для работы с LLM моделями на Apple Silicon (M1/M2/M3) с поддержкой Metal Performance Shaders и ARM64 архитектуры.

## 🚀 Особенности для Apple Silicon

### ⚡ Оптимизации производительности
- **Metal Performance Shaders** - GPU ускорение через Metal API
- **Flash Attention** - оптимизированное внимание для трансформеров
- **Квантованные модели** - поддержка q8_0 для экономии памяти
- **Оптимизированные размеры батчей** - адаптированные под ARM64
- **Многопоточность** - эффективное использование ядер M1/M2/M3

### 🏗️ Архитектурные преимущества
- **ARM64 нативная сборка** - без эмуляции x86
- **Оптимизированные контейнеры** - linux/arm64 платформа
- **Эффективное управление памятью** - до 16GB для Ollama
- **Быстрая сеть** - оптимизированные Docker сети

## 📋 Системные требования

### Минимальные требования
- **macOS**: 12.0+ (Monterey)
- **Процессор**: Apple M1, M2 или M3
- **Память**: 16GB RAM
- **Свободное место**: 50GB
- **Docker**: 20.10+ с поддержкой ARM64

### Рекомендуемые требования
- **macOS**: 14.0+ (Sonoma)
- **Процессор**: Apple M2 Pro/Max или M3 Pro/Max
- **Память**: 32GB+ RAM
- **Свободное место**: 100GB+ SSD
- **Docker Desktop**: последняя версия

## 🛠️ Установка и настройка

### 1. Подготовка системы

```bash
# Проверка архитектуры
uname -m  # Должно быть arm64

# Проверка доступной памяти
sysctl hw.memsize | awk '{print $2/1024/1024/1024 " GB"}'

# Установка Docker Desktop для Apple Silicon
# Скачайте с https://www.docker.com/products/docker-desktop/
```

### 2. Клонирование и настройка

```bash
# Клонирование репозитория
git clone <repository-url>
cd relink/llm_tuning

# Копирование конфигурации для Apple Silicon
cp docker-compose.apple-silicon.yml docker-compose.yml
cp Makefile.apple-silicon Makefile

# Создание .env файла
cp .env.example .env
```

### 3. Настройка переменных окружения

```bash
# Редактирование .env файла
nano .env

# Ключевые настройки для Apple Silicon:
OLLAMA_METAL=1                    # Включить GPU ускорение
OLLAMA_FLASH_ATTENTION=1          # Оптимизированное внимание
OLLAMA_KV_CACHE_TYPE=q8_0         # Квантованные модели
OLLAMA_CONTEXT_LENGTH=4096        # Размер контекста
OLLAMA_BATCH_SIZE=512             # Размер батча
OLLAMA_NUM_PARALLEL=2             # Количество потоков
OLLAMA_MEM_FRACTION=0.9           # Доля памяти для Ollama
```

### 4. Запуск системы

```bash
# Сборка и запуск всех сервисов
make setup-prod

# Или пошагово:
make docker-build
make docker-run
make migrate
make monitor
```

## 🎯 Оптимизация для вашего Mac

### Настройка под разные модели

#### Apple M1 (8GB RAM)
```bash
# В .env файле:
OLLAMA_MEM_FRACTION=0.7           # 70% памяти
OLLAMA_CONTEXT_LENGTH=2048        # Меньший контекст
OLLAMA_BATCH_SIZE=256             # Меньший батч
OLLAMA_NUM_PARALLEL=1             # Один поток
```

#### Apple M2 (16GB RAM)
```bash
# В .env файле:
OLLAMA_MEM_FRACTION=0.8           # 80% памяти
OLLAMA_CONTEXT_LENGTH=4096        # Стандартный контекст
OLLAMA_BATCH_SIZE=512             # Стандартный батч
OLLAMA_NUM_PARALLEL=2             # Два потока
```

#### Apple M2 Pro/Max (32GB+ RAM)
```bash
# В .env файле:
OLLAMA_MEM_FRACTION=0.9           # 90% памяти
OLLAMA_CONTEXT_LENGTH=8192        # Больший контекст
OLLAMA_BATCH_SIZE=1024            # Больший батч
OLLAMA_NUM_PARALLEL=4             # Четыре потока
```

### Оптимизация Docker

```bash
# Настройка Docker Desktop
# Preferences -> Resources -> Advanced:
# - CPUs: 8 (или больше)
# - Memory: 16GB (или больше)
# - Swap: 2GB
# - Disk image size: 100GB

# Включение BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

## 🚀 Использование

### Основные команды

```bash
# Запуск всех сервисов
make docker-run

# Проверка здоровья
make health

# Просмотр логов
make docker-logs

# Остановка сервисов
make docker-stop

# Перезапуск
make restart
```

### Работа с моделями

```bash
# Проверка доступных моделей
make check-ollama

# Загрузка новых моделей
docker-compose exec ollama ollama pull qwen2.5:7b-turbo
docker-compose exec ollama ollama pull llama3.1:8b

# Оптимизация моделей
make optimize-models
```

### Мониторинг и отладка

```bash
# Запуск мониторинга
make monitor

# Проверка производительности
make performance-test

# Нагрузочное тестирование
make load-test

# Просмотр статистики
make status
```

## 📊 Мониторинг

### Доступные интерфейсы

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger**: http://localhost:16686
- **API Docs**: http://localhost:8001/docs
- **ChromaDB**: http://localhost:8000

### Ключевые метрики

```bash
# Проверка использования ресурсов
docker stats llm-tuning-apple-silicon

# Проверка логов Ollama
docker-compose logs -f ollama

# Проверка метрик API
curl http://localhost:8001/health
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Недостаточно памяти
```bash
# Симптомы: 503 ошибки, медленная работа
# Решение:
make docker-stop
# Увеличьте OLLAMA_MEM_FRACTION в .env
# Уменьшите OLLAMA_CONTEXT_LENGTH
make docker-run
```

#### 2. Медленная работа моделей
```bash
# Проверка настроек Metal:
docker-compose exec ollama env | grep OLLAMA_METAL
# Должно быть OLLAMA_METAL=1

# Проверка использования GPU:
docker stats llm-tuning-ollama-apple-silicon
# CPU может показывать 100% даже при GPU использовании
```

#### 3. Проблемы с ChromaDB
```bash
# Перезапуск ChromaDB:
docker-compose restart chromadb

# Проверка логов:
docker-compose logs chromadb
```

#### 4. Проблемы с сетью
```bash
# Проверка Docker сети:
docker network ls
docker network inspect llm-tuning_llm-tuning-network

# Пересоздание сети:
docker-compose down
docker network prune
docker-compose up -d
```

### Диагностика производительности

```bash
# Полная диагностика
make apple-silicon-optimize

# Проверка всех сервисов
make health

# Тест производительности
make performance-test

# Анализ логов
make logs-tail
```

## 🎛️ Продвинутая настройка

### Кастомные модели

```bash
# Создание кастомной модели
docker-compose exec ollama ollama create mymodel -f Modelfile

# Пример Modelfile:
FROM qwen2.5:7b-turbo
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
SYSTEM "Ты эксперт по SEO и веб-аналитике."
```

### Оптимизация для продакшена

```bash
# Настройка продакшн среды
make setup-prod

# Настройка резервного копирования
make backup

# Мониторинг в продакшне
make monitor
```

### Интеграция с основным проектом

```bash
# Настройка интеграции с reLink
# В основном проекте добавьте:

# .env
LLM_TUNING_URL=http://localhost:8001
LLM_TUNING_API_KEY=apple-silicon-api-key-2024

# docker-compose.yml
llm-tuning:
  external: true
  name: llm-tuning_llm-tuning
```

## 📈 Бенчмарки и производительность

### Ожидаемая производительность

| Модель | Контекст | Время ответа | Память |
|--------|----------|--------------|--------|
| qwen2.5:7b-turbo | 4096 | 2-5 сек | 8-12GB |
| llama3.1:8b | 4096 | 3-7 сек | 10-14GB |
| mistral:7b | 4096 | 2-4 сек | 7-11GB |

### Оптимизация под ваши задачи

```bash
# Для быстрых ответов:
OLLAMA_BATCH_SIZE=1024
OLLAMA_NUM_PARALLEL=4
OLLAMA_CONTEXT_LENGTH=2048

# Для качественных ответов:
OLLAMA_BATCH_SIZE=256
OLLAMA_NUM_PARALLEL=2
OLLAMA_CONTEXT_LENGTH=8192
```

## 🔒 Безопасность

### Настройки безопасности

```bash
# В .env файле:
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
RATE_LIMIT_PER_MINUTE=100
ENABLE_API_KEYS=true

# Настройка файрвола:
sudo pfctl -e
sudo pfctl -f /etc/pf.conf
```

### Мониторинг безопасности

```bash
# Проверка логов безопасности
docker-compose logs | grep -i "error\|warning\|security"

# Аудит API запросов
curl -H "X-API-Key: your-key" http://localhost:8001/api/v1/models
```

## 📚 Дополнительные ресурсы

### Полезные ссылки

- [Ollama для Apple Silicon](https://ollama.ai/download/mac)
- [Docker Desktop для Mac](https://www.docker.com/products/docker-desktop/)
- [Metal Performance Shaders](https://developer.apple.com/metal/pytorch/)
- [ARM64 оптимизации](https://developer.apple.com/documentation/metal)

### Сообщество

- [GitHub Issues](https://github.com/your-repo/issues)
- [Discord](https://discord.gg/your-server)
- [Telegram](https://t.me/your-channel)

## 🤝 Поддержка

Если у вас возникли проблемы или вопросы:

1. Проверьте раздел [Устранение неполадок](#устранение-неполадок)
2. Запустите диагностику: `make apple-silicon-optimize`
3. Создайте issue в GitHub с логами: `make logs-tail`
4. Обратитесь в сообщество

---

**🍎 Оптимизировано для Apple Silicon - Быстро, Эффективно, Надежно!** 