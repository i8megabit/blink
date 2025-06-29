# 🔧 Scripts - Утилиты и автоматизация reLink

Коллекция скриптов и утилит для автоматизации разработки, развертывания и мониторинга платформы reLink.

## 🚀 Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск основных утилит
make help

# Проверка системы
./scripts/check_ollama.sh
```

## 🏗️ Архитектура

### Технологический стек
- **Python 3.11+** - основной язык скриптов
- **Bash** - системные утилиты
- **Docker** - контейнеризация
- **Make** - автоматизация команд
- **Git** - управление версиями

### Структура проекта
```
scripts/
├── check_ollama.sh           # Проверка Ollama
├── create-microservice.sh    # Создание микросервиса
├── detect-architecture.sh    # Определение архитектуры
├── monitor_ollama_startup.sh # Мониторинг Ollama
├── native-gpu-setup.sh       # Настройка GPU
├── professional-build.sh     # Профессиональная сборка
├── publish-dockerhub.sh      # Публикация в Docker Hub
├── relink-aliases.sh         # Алиасы команд
├── setup-aliases.sh          # Настройка алиасов
├── switch-mode.sh            # Переключение режимов
├── smart_docker_cache.py     # Умный кэш Docker
├── test_coverage_analyzer.py # Анализ покрытия тестов
├── update_metrics.py         # Обновление метрик
├── version_manager.py        # Управление версиями
└── resource_limits.py        # Управление ресурсами
```

## 🎯 Основные функции

### Автоматизация разработки
- Создание новых микросервисов
- Настройка окружения разработки
- Управление зависимостями
- Автоматическое тестирование

### DevOps утилиты
- Сборка и публикация образов
- Мониторинг системы
- Управление ресурсами
- Автоматическое развертывание

### Анализ и мониторинг
- Анализ покрытия тестов
- Мониторинг производительности
- Обновление метрик
- Отчеты о состоянии системы

## 🔧 Разработка

### Команды разработки
```bash
# Создание нового микросервиса
./scripts/create-microservice.sh my-service 8000 "Описание сервиса"

# Проверка системы
./scripts/check_ollama.sh

# Настройка GPU
./scripts/native-gpu-setup.sh

# Переключение режимов
./scripts/switch-mode.sh dev
```

### Python утилиты
```bash
# Анализ покрытия тестов
python scripts/test_coverage_analyzer.py

# Обновление метрик
python scripts/update_metrics.py

# Управление версиями
python scripts/version_manager.py

# Умный кэш Docker
python scripts/smart_docker_cache.py
```

## 🐳 Docker утилиты

### Сборка образов
```bash
# Профессиональная сборка
./scripts/professional-build.sh

# Публикация в Docker Hub
./scripts/publish-dockerhub.sh

# Умный кэш
python scripts/smart_docker_cache.py
```

### Мониторинг контейнеров
```bash
# Мониторинг Ollama
./scripts/monitor_ollama_startup.sh

# Управление ресурсами
python scripts/resource_limits.py
```

## 🔍 Анализ и отчеты

### Анализ покрытия тестов
```bash
# Запуск анализатора
python scripts/test_coverage_analyzer.py

# Генерация отчета
python scripts/test_coverage_analyzer.py --report
```

### Обновление метрик
```bash
# Обновление всех метрик
python scripts/update_metrics.py

# Обновление конкретной метрики
python scripts/update_metrics.py --metric performance
```

## 🚀 Автоматизация

### Make команды
```bash
# Справка по командам
make help

# Быстрый старт
make up

# Остановка системы
make down

# Пересборка
make rebuild

# Очистка
make clean
```

### Алиасы команд
```bash
# Настройка алиасов
./scripts/setup-aliases.sh

# Использование алиасов
relink-up
relink-down
relink-logs
relink-status
```

## 📊 Мониторинг

### Системные метрики
- Использование CPU и памяти
- Состояние Docker контейнеров
- Производительность сети
- Дисковое пространство

### Прикладные метрики
- Время ответа API
- Количество запросов
- Ошибки и исключения
- Покрытие тестами

## 🔒 Безопасность

### Проверки безопасности
- Сканирование уязвимостей
- Проверка зависимостей
- Анализ конфигурации
- Мониторинг доступа

### Аудит системы
- Логирование действий
- Отслеживание изменений
- Анализ производительности
- Отчеты о безопасности

## 🚀 Деплой

### Автоматическое развертывание
```bash
# Развертывание в staging
./scripts/deploy.sh staging

# Развертывание в продакшен
./scripts/deploy.sh production

# Откат изменений
./scripts/rollback.sh
```

### CI/CD интеграция
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging
- Уведомления о статусе

## 📚 Дополнительная документация

- [Makefile](Makefile) - команды автоматизации
- [Docker утилиты](docker-buildkit.env) - настройка Docker
- [Системные утилиты](relink-aliases.sh) - алиасы команд

# 🛠 Скрипты управления Ollama на Apple M4

## 📋 Обзор скриптов

| Скрипт | Назначение | Использование |
|--------|------------|---------------|
| `switch-mode.sh` | 🔄 Переключатель режимов | Основной скрипт для всех операций |
| `native-gpu-setup.sh` | ⚡ Настройка GPU | Первоначальная настройка нативной Ollama |
| `check_ollama.sh` | 🔍 Проверка состояния | Диагностика Ollama |
| `monitor_ollama_startup.sh` | 📊 Мониторинг запуска | Отслеживание запуска контейнера |

---

## 🚀 Основные команды

### Переключатель режимов (главный скрипт):
```bash
./scripts/switch-mode.sh status     # Проверить статус
./scripts/switch-mode.sh container  # Запуск контейнеров (основной)
./scripts/switch-mode.sh native     # Запуск нативного GPU
./scripts/switch-mode.sh stop       # Остановить все
```

### Первоначальная настройка GPU (только один раз):
```bash
./scripts/native-gpu-setup.sh       # Установка и настройка
```

---

## 🔧 Режимы работы

### 📦 Контейнерный режим (по умолчанию)
- **Запуск:** `docker-compose up` или `./scripts/switch-mode.sh container`
- **Порты:** 8000 (backend), 3000 (frontend), 11434 (ollama)
- **Производительность:** ~15-25 tok/s
- **Память:** 8-12GB
- **Преимущества:** Стабильный, изолированный, простой

### ⚡ Нативный GPU режим (резервный)
- **Запуск:** `./scripts/switch-mode.sh native`
- **Порты:** 8001 (backend), 3001 (frontend), 11434 (ollama)
- **Производительность:** ~40-60 tok/s  
- **Память:** 12-16GB
- **Преимущества:** Максимальная скорость, Metal Performance Shaders

---

## 💾 Общие модели

Все режимы используют **общую папку моделей**:
```
data/ollama_models/
├── models/           # Сами модели
├── blobs/           # Blob данные
└── manifests/       # Метаданные
```

**Преимущества:**
- ✅ Модели скачиваются один раз
- ✅ Быстрое переключение режимов
- ✅ Экономия дискового пространства
- ✅ Синхронизация кастомных моделей

---

## 🎯 Типичные сценарии

### 🏠 Ежедневная работа:
```bash
docker-compose up
# Доступ: http://localhost:8000
```

### 🔥 Демонстрация/бенчмарк:
```bash
./scripts/switch-mode.sh native
# Доступ: http://localhost:8001  
```

### 🔄 Переключение туда-обратно:
```bash
# В GPU режим
./scripts/switch-mode.sh native

# Обратно в контейнеры  
./scripts/switch-mode.sh container
```

### 🛑 Полная остановка:
```bash
./scripts/switch-mode.sh stop
```

---

## 🔍 Диагностика

### Проверить что работает:
```bash
./scripts/switch-mode.sh status
```

### Детальная диагностика:
```bash
./scripts/check_ollama.sh
```

### Мониторинг запуска:
```bash
./scripts/monitor_ollama_startup.sh
```

### Логи нативной Ollama:
```bash
tail -f /tmp/ollama-native.log
```

---

## ⚠️ Важные замечания

1. **Не запускайте оба режима одновременно** - будет конфликт портов
2. **Используйте `stop` перед переключением** режимов
3. **Нативный режим требует установки Ollama** на хост-систему
4. **Контейнерный режим более стабилен** для длительной работы
5. **GPU режим показывает максимум M4** для демо и бенчмарков

---

## 🚨 Устранение неполадок

### Конфликт портов:
```bash
./scripts/switch-mode.sh stop
sudo lsof -i :11434  # Найти процесс на порту
```

### Ollama не найдена:
```bash
which ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### Права доступа к моделям:
```bash
sudo chown -R $(whoami) data/ollama_models/
```

### Контейнеры не запускаются:
```bash
docker-compose down
docker system prune
docker-compose up
```

---

## 📊 Мониторинг производительности

### GPU активность:
```bash
sudo powermetrics -n 1 --samplers gpu_power
```

### Память:
```bash
memory_pressure
```

### API тест:
```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "qwen2.5:7b-turbo", "prompt": "тест скорости"}'
```

---

## 🎉 Готовые команды

```bash
# Быстрый старт (контейнеры)
docker-compose up

# Максимальная скорость (GPU)  
./scripts/switch-mode.sh native

# Проверить статус
./scripts/switch-mode.sh status

# Остановить всё
./scripts/switch-mode.sh stop
```

# 📦 Система управления версиями reLink (SemVer 2.0)

Этот каталог содержит скрипты для автоматического управления версиями проекта reLink с поддержкой **Semantic Versioning 2.0**.

## 🚀 Быстрый старт

### Просмотр текущей версии
```bash
python scripts/version_manager.py current
# или
make version-current
```

### Увеличение версии
```bash
# Patch версия (1.0.0 -> 1.0.1)
python scripts/version_manager.py bump --type patch
make version-bump TYPE=patch

# Minor версия (1.0.0 -> 1.1.0)
python scripts/version_manager.py bump --type minor
make version-bump TYPE=minor

# Major версия (1.0.0 -> 2.0.0)
python scripts/version_manager.py bump --type major
make version-bump TYPE=major
```

### Создание релиза
```bash
# Создает стабильный релиз
python scripts/version_manager.py release --type patch
make version-release TYPE=patch
```

### Создание prerelease
```bash
# Создает prerelease версию (1.0.1-rc.1)
python scripts/version_manager.py prerelease --prerelease 1 --type rc
make version-prerelease NAME=1 TYPE=rc
```

### Установка конкретной версии
```bash
python scripts/version_manager.py set --version 2.0.0
make version-set VERSION=2.0.0
```

### Валидация версии
```bash
python scripts/version_manager.py validate --version 2.0.0
make version-validate VERSION=2.0.0
```

### Обновление changelog
```bash
python scripts/version_manager.py changelog --changes "Исправлен баг" "Добавлена новая функция"
make version-changelog CHANGES="Исправлен баг" "Добавлена новая функция"
```

## 📋 Описание скриптов

### `version_manager.py` - Основной менеджер версий

Полноценная система управления версиями с поддержкой SemVer 2.0.

**Возможности:**
- ✅ Парсинг и валидация версий по SemVer 2.0
- ✅ Автоматическое увеличение major/minor/patch версий
- ✅ Поддержка prerelease версий (alpha, beta, rc)
- ✅ Поддержка build меток
- ✅ Сравнение версий
- ✅ Автоматическое обновление всех файлов проекта
- ✅ Генерация changelog
- ✅ Интеграция с Git

**Команды:**
```bash
# Основные команды
current          # Показать текущую версию
bump --type      # Увеличить версию (major|minor|patch)
release --type   # Создать релиз
prerelease       # Создать prerelease
set --version    # Установить конкретную версию
validate --version # Валидировать версию
changelog --changes # Обновить changelog
```

### `extract_version.py` - Извлечение версии

Извлекает версию из VERSION файла или README.md.

**Использование:**
```bash
python scripts/extract_version.py [путь_к_readme]
```

**Возвращает:**
- Версию в формате SemVer при успехе
- Код ошибки 1 при неудаче

### `update_version.py` - Обновление версий

Автоматически обновляет версию во всех файлах проекта.

**Использование:**
```bash
# Обновить версию во всех файлах
python scripts/update_version.py

# Синхронизировать версию из README
python scripts/update_version.py sync
```

## 🏗️ Архитектура системы

### Файлы версий
- `VERSION` - Основной файл с версией
- `README.md` - Документация с версией
- `frontend/package.json` - Версия фронтенда
- `pyproject.toml` - Версия Python проекта

### Классы и структуры

#### `Version` - Класс версии
```python
@dataclass
class Version:
    major: int          # Основная версия
    minor: int          # Минорная версия  
    patch: int          # Патч версия
    prerelease: Optional[str] = None  # Prerelease (alpha, beta, rc)
    build: Optional[str] = None       # Build метка
```

#### `VersionManager` - Менеджер версий
```python
class VersionManager:
    def get_current_version() -> Version
    def set_version(version: Version) -> None
    def bump_version(bump_type: str) -> Version
    def create_release(release_type: str) -> Version
    def create_prerelease(prerelease_type: str, name: str) -> Version
    def generate_changelog(version: Version, changes: List[str]) -> None
```

## 📊 SemVer 2.0 Форматы

### Стабильные версии
```
MAJOR.MINOR.PATCH
1.0.0
2.1.3
```

### Prerelease версии
```
MAJOR.MINOR.PATCH-PRERELEASE
1.0.0-alpha.1
1.0.0-beta.2
1.0.0-rc.1
```

### Версии с build метками
```
MAJOR.MINOR.PATCH-PRERELEASE+BUILD
1.0.0-alpha.1+build.123
1.0.0+20231201
```

## 🔄 Workflow использования

### 1. Разработка новой функции
```bash
# Создаем prerelease для тестирования
make version-prerelease NAME=feature1 TYPE=alpha
# Результат: 1.0.1-alpha.feature1
```

### 2. Подготовка к релизу
```bash
# Создаем release candidate
make version-prerelease NAME=1 TYPE=rc
# Результат: 1.0.1-rc.1
```

### 3. Создание релиза
```bash
# Создаем стабильный релиз
make version-release TYPE=patch
# Результат: 1.0.1
```

### 4. Обновление changelog
```bash
make version-changelog CHANGES="Исправлен баг с авторизацией" "Добавлена поддержка новых форматов"
```

## 🎯 Примеры использования

### Типичный workflow релиза
```bash
# 1. Проверяем текущую версию
make version-current

# 2. Создаем prerelease для тестирования
make version-prerelease NAME=1 TYPE=rc

# 3. Тестируем приложение

# 4. Создаем стабильный релиз
make version-release TYPE=patch

# 5. Обновляем changelog
make version-changelog CHANGES="Исправлены критические баги" "Улучшена производительность"

# 6. Коммитим изменения
git add .
git commit -m "Release v1.0.1"

# 7. Создаем Git тег
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

### Автоматизация в CI/CD
```bash
# В GitHub Actions или GitLab CI
- name: Bump version
  run: |
    make version-bump TYPE=patch
    make version-changelog CHANGES="${{ github.event.head_commit.message }}"
  
- name: Create release
  run: |
    git add .
    git commit -m "Bump version to $(python scripts/version_manager.py current)"
    git tag -a v$(python scripts/version_manager.py current) -m "Release v$(python scripts/version_manager.py current)"
    git push origin main --tags
```

## 🔧 Конфигурация

### Переменные окружения
```bash
# В .env файле
API_VERSION=1.0.0  # Автоматически обновляется
```

### Настройка в config.py
```python
# Автоматическое получение версии из VERSION файла
version = get_version_from_readme() or "1.0.0"
```

## 🚨 Важные замечания

1. **Всегда используйте SemVer 2.0** - это стандарт индустрии
2. **Prerelease версии меньше стабильных** - 1.0.0-alpha.1 < 1.0.0
3. **Build метки не влияют на сравнение** - 1.0.0+build1 == 1.0.0+build2
4. **Коммитьте изменения после обновления версии**
5. **Создавайте Git теги для релизов**

## 🆘 Устранение неполадок

### Ошибка "Неверный формат версии"
```bash
# Проверьте формат версии
make version-validate VERSION=1.0.0
```

### Ошибка "Файл не найден"
```bash
# Убедитесь, что вы в корне проекта
pwd
ls VERSION README.md
```

### Ошибка Git
```bash
# Проверьте статус Git
git status
git log --oneline -5
```

---

**Система управления версиями reLink** обеспечивает надежное и стандартизированное управление версиями проекта в соответствии с лучшими практиками индустрии.

# 🧠 Умная система управления Docker кешем

## Обзор

Умная система управления Docker кешем - это аналог Git для Docker слоев, который автоматически определяет изменения в коде и пересобирает только затронутые слои, сохраняя кеш для неизмененных частей.

## 🎯 Проблема

При разработке с Docker часто приходится:
- Ждать полную пересборку при каждом небольшом изменении
- Использовать `--no-cache` и терять все преимущества кеширования
- Сталкиваться с устаревшими слоями кеша
- Тратить время на ручное управление кешем

## 💡 Решение

Умная система решает эти проблемы:

1. **Анализ изменений** - вычисляет хеши файлов для определения изменений
2. **Селективная пересборка** - пересобирает только затронутые слои
3. **Автоматическая инвалидация** - инвалидирует зависимые слои
4. **Git-подобный подход** - как Git определяет изменения в дереве коммитов

## 🚀 Быстрый старт

### Установка зависимостей
```bash
make install-deps
```

### Умная сборка
```bash
# Обычная умная сборка
make smart-build

# Принудительная пересборка
make smart-build-force

# Сборка конкретного сервиса
make smart-build-service SERVICE=backend
```

### Управление кешем
```bash
# Статистика кеша
make smart-cache-stats

# Очистка невалидного кеша
make smart-cache-clean

# Полная очистка кеша
make smart-cache-reset
```

## 📊 Как это работает

### 1. Анализ Dockerfile
Система анализирует Dockerfile и определяет:
- Какие файлы копируются (COPY/ADD команды)
- Базовые образы (FROM команды)
- Зависимости между слоями

### 2. Вычисление хешей
Для каждого слоя вычисляется хеш:
- Содержимого всех файлов в контексте
- Зависимостей (базовых образов)
- Метаданных сборки

### 3. Сравнение изменений
При каждой сборке:
- Сравнивает текущие хеши с сохраненными
- Определяет, какие слои изменились
- Инвалидирует зависимые слои

### 4. Селективная сборка
- Пересобирает только измененные слои
- Использует кеш для неизмененных частей
- Обновляет метаданные кеша

## 🛠️ Использование

### Команды Makefile

```bash
# Основные команды
make smart-build              # Умная сборка с кешем
make smart-build-force        # Принудительная пересборка
make smart-build-service      # Сборка конкретного сервиса

# Управление кешем
make smart-cache-stats        # Статистика кеша
make smart-cache-clean        # Очистка невалидного кеша
make smart-cache-reset        # Полная очистка кеша

# Комплексные команды
make quick-build              # Быстрая сборка и запуск
make full-build               # Полная пересборка и запуск
make dev-setup                # Настройка окружения разработки
```

### Прямое использование Python скрипта

```bash
# Умная сборка
python3 scripts/smart_docker_cache.py --compose-file config/docker-compose.yml

# Сборка конкретного сервиса
python3 scripts/smart_docker_cache.py --service backend

# Принудительная пересборка
python3 scripts/smart_docker_cache.py --force

# Статистика кеша
python3 scripts/smart_docker_cache.py --stats

# Очистка кеша
python3 scripts/smart_docker_cache.py --clean
```

## 📈 Преимущества

### Скорость
- **90%+ экономия времени** при небольших изменениях
- Пересборка только измененных слоев
- Сохранение кеша для неизмененных частей

### Надежность
- Автоматическая инвалидация зависимостей
- Предотвращение устаревших слоев
- Валидация целостности кеша

### Удобство
- Git-подобный подход к изменениям
- Автоматическое определение изменений
- Простое управление через Makefile

## 🔧 Конфигурация

### Структура кеша
```
.docker_cache/
├── cache_metadata.json    # Метаданные кеша
├── layer_hashes/         # Хеши слоев
└── build_logs/          # Логи сборки
```

### Переменные окружения
```bash
DOCKER_BUILDKIT=1                    # Включение BuildKit
COMPOSE_DOCKER_CLI_BUILD=1           # Использование Docker CLI для сборки
SMART_CACHE_DIR=.docker_cache        # Директория кеша
```

## 🧪 Тестирование

### Проверка работы кеша
```bash
# Первая сборка (полная)
make smart-build

# Изменение файла
echo "# Test change" >> backend/app/main.py

# Вторая сборка (только измененные слои)
make smart-build

# Проверка статистики
make smart-cache-stats
```

### Тестирование инвалидации
```bash
# Изменение базового образа в Dockerfile
# Система автоматически инвалидирует зависимые слои
make smart-build
```

## 🐛 Устранение неполадок

### Проблема: Кеш не работает
```bash
# Проверка зависимостей
make check-deps

# Переустановка зависимостей
make install-deps

# Очистка и пересоздание кеша
make smart-cache-reset
```

### Проблема: Устаревшие слои
```bash
# Очистка невалидного кеша
make smart-cache-clean

# Принудительная пересборка
make smart-build-force
```

### Проблема: Медленная сборка
```bash
# Проверка статистики кеша
make smart-cache-stats

# Оптимизация Dockerfile
# - Размещение редко изменяемых слоев в начале
# - Использование .dockerignore
# - Многоэтапная сборка
```

## 📚 Интеграция с LLM Router

Умная система кеша интегрирована с LLM Router для оптимизации сборки AI-компонентов:

### SEO функциональность
- **Индексация сайтов** - использует LLM для анализа контента
- **Генерация рекомендаций** - AI-оптимизированные SEO советы
- **Анализ качества** - автоматическая оценка результатов

### Оптимизация производительности
- **Кеширование LLM запросов** - избежание повторных вычислений
- **Параллельная обработка** - конкурентное выполнение запросов
- **Приоритизация** - важные запросы обрабатываются первыми

### Интеграция с микросервисами
```python
# Пример использования в backend
from app.llm_router import llm_router

# SEO анализ с умным кешем
result = await llm_router.analyze_seo_content(
    content=website_content,
    domain="example.com"
)
```

## 🔄 Обновление базовых образов

### Автоматическое обновление
```bash
# Проверка обновлений базовых образов
docker pull python:3.11-slim
docker pull nginx:alpine

# Инвалидация зависимых слоев
make smart-cache-clean

# Пересборка с новыми образами
make smart-build
```

### Ручное обновление
```bash
# Принудительная пересборка всех образов
make smart-build-force

# Сборка конкретного сервиса
make smart-build-service SERVICE=backend
```

## 📊 Мониторинг

### Статистика использования
```bash
# Общая статистика
make smart-cache-stats

# Детальная информация
python3 scripts/smart_docker_cache.py --stats --verbose
```

### Метрики производительности
- Время сборки до/после внедрения
- Экономия времени на разработку
- Использование кеша (hit/miss ratio)

## 🤝 Вклад в проект

### Добавление новых сервисов
1. Создайте Dockerfile с оптимизированной структурой
2. Добавьте сервис в docker-compose.yml
3. Система автоматически начнет отслеживать изменения

### Расширение функциональности
1. Модифицируйте `SmartDockerCache` класс
2. Добавьте новые команды в Makefile
3. Обновите документацию

## 📄 Лицензия

Проект использует ту же лицензию, что и основной репозиторий reLink.

---

**Умная система управления Docker кешем** - это революционный подход к оптимизации процесса разработки, который экономит время и повышает производительность команды. 