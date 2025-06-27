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
ollama_models/
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
sudo chown -R $(whoami) ollama_models/
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