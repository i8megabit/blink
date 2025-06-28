# Makefile для микросервиса мониторинга reLink

.PHONY: help install test lint format clean build run docker-build docker-run

# Переменные
PYTHON = python3
PIP = pip3
APP_NAME = monitoring
PORT = 8002

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	$(PIP) install -r requirements.txt

install-dev: ## Установить зависимости для разработки
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

test: ## Запустить тесты
	pytest

test-cov: ## Запустить тесты с покрытием
	pytest --cov=app --cov-report=html --cov-report=term-missing

test-fast: ## Запустить быстрые тесты
	pytest -m "not slow"

test-unit: ## Запустить unit тесты
	pytest -m unit

test-integration: ## Запустить integration тесты
	pytest -m integration

lint: ## Проверить код линтером
	flake8 app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

format: ## Отформатировать код
	black app/ tests/
	isort app/ tests/

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

build: clean ## Собрать пакет
	$(PYTHON) setup.py sdist bdist_wheel

run: ## Запустить сервис локально
	uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --reload

run-prod: ## Запустить сервис в production режиме
	uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --workers 4

docker-build: ## Собрать Docker образ
	docker build -t $(APP_NAME) .

docker-run: ## Запустить Docker контейнер
	docker run -d \
		--name $(APP_NAME) \
		-p $(PORT):$(PORT) \
		-e DATABASE_URL=postgresql+asyncpg://seo_user:seo_pass@db:5432/seo_db \
		-e REDIS_HOST=redis \
		-e OLLAMA_URL=http://ollama:11434 \
		$(APP_NAME)

docker-stop: ## Остановить Docker контейнер
	docker stop $(APP_NAME) || true
	docker rm $(APP_NAME) || true

docker-logs: ## Показать логи Docker контейнера
	docker logs -f $(APP_NAME)

docker-shell: ## Войти в Docker контейнер
	docker exec -it $(APP_NAME) /bin/bash

health: ## Проверить здоровье сервиса
	curl -f http://localhost:$(PORT)/health || echo "Service is down"

metrics: ## Получить метрики
	curl http://localhost:$(PORT)/metrics | jq .

alerts: ## Получить алерты
	curl http://localhost:$(PORT)/alerts | jq .

services: ## Получить статус сервисов
	curl http://localhost:$(PORT)/services | jq .

dashboard: ## Получить данные дашборда
	curl http://localhost:$(PORT)/dashboard | jq .

docs: ## Открыть документацию API
	open http://localhost:$(PORT)/docs

redoc: ## Открыть ReDoc документацию
	open http://localhost:$(PORT)/redoc

dev-setup: install format lint test ## Настройка окружения для разработки

ci: lint test-cov ## Команды для CI/CD

all: clean install format lint test-cov build ## Выполнить все команды 