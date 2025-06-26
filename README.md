# Быстрый старт на macOS

Версия: 0.1.0

## Запуск без контейнеров

Убедитесь, что на системе установлен Python 3.11.
Склонируйте репозиторий и перейдите в папку проекта:

```bash
git clone https://github.com/yourname/seo-link-recommender.git
cd seo-link-recommender
```

```bash
# создание виртуального окружения и установка зависимостей
python3 -m venv .venv
source .venv/bin/activate
pip install -r seo-link-recommender/backend/requirements.txt
uvicorn app.main:app --app-dir seo-link-recommender/backend/app --reload
```

## Запуск через Docker

Требуется установленный Docker Desktop.

```bash
docker compose -f seo-link-recommender/docker-compose.yml up --build
```

После сборки приложение доступно по адресу http://localhost:8000.

## Публикация образов

GitHub Actions автоматически публикует образ с тегом `latest` из любой ветки. При работе с веткой `main` дополнительно публикуется тег `dev`, а текущий коммит помечается тегом версии, указанной в начале этого файла.

## Тестирование

```bash
pytest
```
