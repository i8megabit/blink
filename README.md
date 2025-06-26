# Быстрый старт на macOS

Версия: 0.1.0

## Запуск без контейнеров

Убедитесь, что на системе установлен Python 3.11.
Склонируйте репозиторий и перейдите в папку проекта:

```bash
git clone https://github.com/yourname/seo_link_recommender.git
cd seo_link_recommender
```

```bash
# создание виртуального окружения и установка зависимостей
python3 -m venv .venv
source .venv/bin/activate
pip install -r seo_link_recommender/backend/requirements.txt
export DATABASE_URL=postgresql+asyncpg://seo_user:seo_pass@localhost/seo_db
uvicorn app.main:app --app-dir seo_link_recommender/backend/app --reload
```

## Запуск через Docker

Требуется установленный Docker Desktop.

```bash
docker compose -f seo_link_recommender/docker-compose.yml up --build
```

После сборки бекенд доступен на http://localhost:8000, а фронтенд
открывается по адресу http://localhost:3000. PostgreSQL запускается как
отдельный сервис в Docker и доступен по адресу
`postgresql://seo_user:seo_pass@localhost:5432/seo_db`.
Фронтенд обращается к API бекенда через nginx и позволяет отправить текст,
получить список ссылок и просмотреть историю сохранённых рекомендаций.
Для генерации ссылок нужен запущенный локальный сервер Ollama. Его адрес можно
задать переменной окружения `OLLAMA_URL` (по умолчанию используется
`http://localhost:11434/api/generate`).

## Модель Ollama

По умолчанию используется модель **qwen2.5:7b** - оптимизированная для SEO задач:
- Отличный баланс качества/стабильности/ресурсов
- Хорошее понимание русского языка  
- Эффективная генерация анкор-текстов
- Размер: ~4.3GB

Для установки модели:
```bash
ollama pull qwen2.5:7b
```

### Альтернативные модели

Можно использовать другие модели через переменную `OLLAMA_MODEL`:

**Для слабых устройств:**
```bash
export OLLAMA_MODEL=gemma3:1b  # Размер: ~1.8GB
```

**Для максимального качества:**
```bash
export OLLAMA_MODEL=llama3.1:8b  # Размер: ~4.7GB
```

**Для текстовых задач:**
```bash
export OLLAMA_MODEL=mistral:7b  # Размер: ~4.1GB
```

## Тестирование

```bash
python -m pytest -q
```
