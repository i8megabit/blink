# 📊 Метрики и ресурсы проекта reLink

> Документация по автоматизации метрик и управлению ресурсами для Apple Silicon M4

## 🎯 Обзор

Проект reLink теперь включает автоматизированные инструменты для:
- 📊 **Автоматическое обновление метрик** в README.md
- 🚀 **Расчет лимитов ресурсов** для всех микросервисов
- 🍎 **Оптимизация для Apple Silicon M4**
- 🔧 **Удобное управление** через Makefile

---

## 📊 Автоматические метрики

### Обновление метрик

```bash
# Автоматическое обновление метрик
make metrics

# Или напрямую
python3 update_metrics.py
```

### Что обновляется

- **Строки кода**: Подсчет всех `.py`, `.ts`, `.tsx`, `.js`, `.jsx` файлов
- **Размер репозитория**: Общий размер проекта
- **Количество файлов**: Подсчет файлов исходного кода
- **CPU**: Количество ядер процессора
- **Память**: Общий объем RAM
- **Apple Silicon**: Оптимизация для M4

### GitHub Actions

Метрики автоматически обновляются:
- 🕐 **Каждое воскресенье** в 00:00 UTC
- 🔄 **При push** в main ветку
- 🖱️ **Ручной запуск** через GitHub Actions

---

## 🚀 Управление ресурсами

### Расчет лимитов

```bash
# Расчет лимитов ресурсов
make resources

# Или напрямую
python3 resource_limits.py
```

### Распределение ресурсов для Apple Silicon M4

| Сервис | CPU (cores) | RAM (Mi) | Приоритет | Описание |
|--------|-------------|----------|-----------|----------|
| 🔴 backend | 0.7-1.4 | 867-1734 | Высокий | FastAPI backend |
| 🟡 frontend | 0.3-0.7 | 433-867 | Средний | React frontend |
| 🔴 llm_tuning | 1.0-2.1 | 1734-3469 | Высокий | LLM tuning |
| 🟢 monitoring | 0.2-0.3 | 433-867 | Низкий | Prometheus/Grafana |
| 🟢 docs | 0.2-0.3 | 216-433 | Низкий | Документация |
| 🟡 testing | 0.3-0.7 | 433-867 | Средний | Тестирование |
| 🔴 ollama | 0.7-1.4 | 2602-5204 | Высокий | Ollama LLM |
| 🟡 redis | 0.2-0.3 | 216-433 | Средний | Redis кэш |
| 🔴 postgres | 0.3-0.7 | 433-867 | Высокий | PostgreSQL |

### Генерируемые конфигурации

1. **Docker Compose** (`docker-compose.resources.yml`)
2. **Kubernetes** (`kubernetes-deployments.yml`)
3. **Prometheus** (`prometheus.yml`)
4. **Алерты** (`resource_alerts.yml`)

---

## 🍎 Оптимизация для Apple Silicon

### Переменные окружения

```bash
# Автоматическая настройка
make apple-setup

# Ручная настройка
export OLLAMA_METAL=1                    # GPU ускорение
export OLLAMA_FLASH_ATTENTION=1          # Ускорение внимания
export OLLAMA_KV_CACHE_TYPE=q8_0         # Оптимизация памяти
export OLLAMA_CONTEXT_LENGTH=4096        # Длина контекста
export OLLAMA_BATCH_SIZE=512             # Размер батча
export OLLAMA_NUM_PARALLEL=2             # Параллелизм
```

### Рекомендации для M4

1. **GPU ускорение**: Всегда используйте `OLLAMA_METAL=1`
2. **Память**: Выделите 6GB для Ollama
3. **CPU**: Используйте 2 ядра для LLM операций
4. **Кэширование**: Включите Redis для снижения нагрузки

---

## 🔧 Makefile команды

### Основные команды

```bash
# Справка
make help

# Информация о проекте
make info

# Метрики и ресурсы
make metrics          # Обновить метрики
make resources        # Рассчитать ресурсы

# Сборка и запуск
make build           # Собрать образы
make build-native    # Сборка для Apple Silicon
make up              # Запустить сервисы
make up-native       # Запуск с оптимизацией
make down            # Остановить сервисы

# Разработка
make dev             # Режим разработки
make watch           # Режим наблюдения
make test            # Запустить тесты
make lint            # Проверить код
make format          # Форматировать код

# Мониторинг
make status          # Статус сервисов
make logs            # Логи сервисов
make monitor         # Открыть мониторинг
make check-health    # Проверить здоровье

# Управление
make clean           # Очистить Docker
make backup          # Резервная копия
make restore         # Восстановить данные
make update          # Обновить зависимости
```

### Специальные команды

```bash
# Apple Silicon
make apple-setup     # Настройка для M4

# Безопасность
make security        # Проверка безопасности

# Производительность
make performance     # Тесты производительности

# Документация
make docs            # Генерация документации
```

---

## 📈 Мониторинг ресурсов

### Prometheus метрики

Автоматически генерируются алерты для:
- **CPU > 80%** от лимита
- **Memory > 80%** от лимита
- **Доступность сервисов**

### Grafana дашборды

Рекомендуемые дашборды:
1. **Общий обзор**: Использование CPU/RAM по сервисам
2. **Ollama мониторинг**: Производительность LLM
3. **Системные метрики**: Температура, вентиляторы
4. **Сетевые метрики**: Трафик между сервисами

---

## 🛠️ Устранение неполадок

### Проблемы с метриками

```bash
# Проверить права доступа
ls -la update_metrics.py
chmod +x update_metrics.py

# Проверить зависимости
python3 -c "import yaml, subprocess"

# Ручной запуск с отладкой
python3 -u update_metrics.py
```

### Проблемы с ресурсами

```bash
# Проверить системную информацию
sysctl -n hw.ncpu
sysctl -n hw.memsize

# Проверить Docker
docker system df
docker stats

# Проверить конфигурации
cat docker-compose.resources.yml
cat kubernetes-deployments.yml
```

### Проблемы с Apple Silicon

```bash
# Проверить архитектуру
uname -m

# Проверить переменные окружения
env | grep OLLAMA

# Проверить Metal
system_profiler SPDisplaysDataType
```

---

## 📚 Дополнительные ресурсы

### Документация

- [Apple Silicon Optimization](https://developer.apple.com/documentation/metal)
- [Ollama Documentation](https://ollama.ai/docs)
- [Docker for Apple Silicon](https://docs.docker.com/desktop/mac/apple-silicon/)
- [Kubernetes Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

### Полезные команды

```bash
# Мониторинг в реальном времени
htop
docker stats
kubectl top pods

# Анализ производительности
python3 -m cProfile -o profile.stats script.py
python3 -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"

# Проверка памяти
vm_stat
memory_pressure
```

---

## 🎯 Заключение

Новые инструменты обеспечивают:

✅ **Автоматизацию** обновления метрик  
✅ **Оптимизацию** для Apple Silicon M4  
✅ **Удобное управление** через Makefile  
✅ **Мониторинг** ресурсов в реальном времени  
✅ **Масштабируемость** для всех микросервисов  

Используйте `make help` для получения полного списка команд! 