# 🚀 reLink Docker BuildKit Setup

## Автоматическое использование BuildKit и профессионального скрипта сборки

Этот документ описывает, как настроить автоматическое использование BuildKit и профессионального скрипта сборки в проекте reLink.

## 📋 Что настроено

### 1. **Makefile** - Основной интерфейс
```bash
# Сборка с BuildKit
make build                    # Сборка всех сервисов
make build-no-cache          # Сборка без кеша
make build-service SERVICE=backend  # Сборка конкретного сервиса

# Управление сервисами
make up                      # Запуск сервисов
make down                    # Остановка сервисов
make restart                 # Перезапуск сервисов

# Мониторинг
make logs                    # Просмотр логов
make health                  # Проверка здоровья
make analyze                 # Анализ образов

# Быстрые команды
make quick-start             # Полный цикл запуска
make dev                     # Режим разработки
make prod                    # Продакшн режим
```

### 2. **Shell Aliases** - Быстрые команды
```bash
# Основные команды
relink-build                 # Сборка с BuildKit
relink-up                    # Запуск сервисов
relink-down                  # Остановка сервисов
relink-logs                  # Просмотр логов
relink-health                # Проверка здоровья

# Быстрые команды
relink-quick                 # Быстрый старт
relink-dev                   # Режим разработки
relink-prod                  # Продакшн режим

# Docker Compose с BuildKit
dcb                          # docker-compose build с BuildKit
dcu                          # docker-compose up с BuildKit
dcd                          # docker-compose down
```

### 3. **Docker Compose** - Автоматический BuildKit
- Все сервисы автоматически используют BuildKit
- Настройки загружаются из `config/docker.env`
- Глобальные настройки для всех сервисов

### 4. **Профессиональный скрипт** - Полный контроль
```bash
./scripts/professional-build.sh build        # Сборка
./scripts/professional-build.sh quick-start  # Быстрый старт
./scripts/professional-build.sh dev          # Режим разработки
./scripts/professional-build.sh prod         # Продакшн
```

## 🚀 Быстрый старт

### Установка алиасов
```bash
# Установить алиасы в shell
./scripts/setup-aliases.sh install

# Загрузить алиасы в текущую сессию
source scripts/relink-aliases.sh
```

### Первый запуск
```bash
# Вариант 1: Через Makefile
make quick-start

# Вариант 2: Через алиасы
relink-quick

# Вариант 3: Через скрипт
./scripts/professional-build.sh quick-start
```

## 📁 Структура файлов

```
relink/
├── Makefile                          # Основной интерфейс
├── config/
│   ├── docker-compose.yml           # Docker Compose с BuildKit
│   └── docker.env                   # Настройки BuildKit
├── scripts/
│   ├── professional-build.sh        # Профессиональный скрипт
│   ├── setup-aliases.sh             # Установка алиасов
│   └── relink-aliases.sh            # Файл алиасов
└── DOCKER_BUILDKIT_SETUP.md         # Эта документация
```

## 🔧 Настройки BuildKit

### Автоматические настройки
```bash
# config/docker.env
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
COMPOSE_FILE=config/docker-compose.yml
DOCKER_BUILDKIT_INLINE_CACHE=1
DOCKER_BUILDKIT_MAX_PARALLELISM=4
```

### Docker Compose настройки
```yaml
# config/docker-compose.yml
x-buildkit: &buildkit
  DOCKER_BUILDKIT: 1
  COMPOSE_DOCKER_CLI_BUILD: 1

services:
  backend:
    build:
      args:
        <<: *buildkit
```

## 🎯 Рекомендуемые команды

### Для разработки
```bash
# Быстрый старт
relink-quick

# Режим разработки (пересборка + логи)
relink-dev

# Сборка конкретного сервиса
relink-build backend

# Просмотр логов
relink-logs backend
```

### Для продакшна
```bash
# Продакшн развертывание
relink-prod

# Проверка здоровья
relink-health

# Анализ образов
relink-analyze
```

### Для отладки
```bash
# Остановка сервисов
relink-down

# Перезапуск
relink-restart

# Очистка Docker
relink-clean
```

## 🔍 Мониторинг

### Проверка статуса
```bash
# Статус сервисов
relink-status

# Процессы Docker
relink-ps

# Логи в реальном времени
relink-logs
```

### Анализ производительности
```bash
# Анализ образов
relink-analyze

# Проверка здоровья
relink-health

# Использование ресурсов
docker system df
```

## 🛠️ Устранение неполадок

### Проблемы с BuildKit
```bash
# Проверка версии Docker
docker --version

# Принудительное включение BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Пересборка без кеша
relink-build-nc
```

### Проблемы с алиасами
```bash
# Переустановка алиасов
./scripts/setup-aliases.sh remove
./scripts/setup-aliases.sh install

# Ручная загрузка
source scripts/relink-aliases.sh
```

### Очистка системы
```bash
# Очистка Docker
relink-clean

# Принудительная очистка
relink-clean-force

# Полная пересборка
relink-build-nc
```

## 📊 Преимущества настройки

### 1. **Автоматизация**
- BuildKit включается автоматически
- Профессиональный скрипт используется по умолчанию
- Настройки загружаются из файлов

### 2. **Производительность**
- Параллельная сборка слоев
- Кеширование между сборками
- Оптимизированные образы

### 3. **Удобство**
- Короткие команды через алиасы
- Единый интерфейс через Makefile
- Автоматические проверки здоровья

### 4. **Надежность**
- Проверка зависимостей
- Автоматическая очистка
- Мониторинг состояния

## 🎉 Результат

Теперь вместо сложных команд:
```bash
# Было
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -f config/docker-compose.yml build --pull

# Стало
relink-build
# или
make build
```

Все команды автоматически используют BuildKit и профессиональный скрипт сборки! 🚀 