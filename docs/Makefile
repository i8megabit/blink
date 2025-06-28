# Makefile для микросервиса документации

.PHONY: help install test lint format clean build run docker-build docker-run

# Переменные
PYTHON = python3
PIP = pip3
DOCKER_IMAGE = seo-docs
DOCKER_TAG = latest

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	$(PIP) install -r requirements.txt

install-dev: ## Установить зависимости для разработки
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-cov black isort flake8 mypy

test: ## Запустить тесты
	pytest

test-cov: ## Запустить тесты с покрытием
	pytest --cov=app --cov-report=html --cov-report=term-missing

test-watch: ## Запустить тесты в режиме наблюдения
	pytest-watch

lint: ## Проверить код линтером
	flake8 app/ tests/
	mypy app/

format: ## Отформатировать код
	black app/ tests/
	isort app/ tests/

format-check: ## Проверить форматирование кода
	black --check app/ tests/
	isort --check-only app/ tests/

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

build: ## Собрать Docker образ
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

run: ## Запустить локально
	uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

run-prod: ## Запустить в продакшн режиме
	uvicorn app.main:app --host 0.0.0.0 --port 8001

docker-run: ## Запустить в Docker
	docker run -p 8001:8001 $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-stop: ## Остановить Docker контейнер
	docker stop $$(docker ps -q --filter ancestor=$(DOCKER_IMAGE):$(DOCKER_TAG))

docker-logs: ## Показать логи Docker контейнера
	docker logs -f $$(docker ps -q --filter ancestor=$(DOCKER_IMAGE):$(DOCKER_TAG))

health: ## Проверить здоровье сервиса
	curl -f http://localhost:8001/api/v1/health

version: ## Получить версию
	curl -s http://localhost:8001/api/v1/version | jq .

cache-stats: ## Получить статистику кэша
	curl -s http://localhost:8001/api/v1/cache/stats | jq .

clear-cache: ## Очистить кэш
	curl -X DELETE http://localhost:8001/api/v1/cache/clear

docs: ## Открыть документацию API
	open http://localhost:8001/docs

redoc: ## Открыть ReDoc документацию
	open http://localhost:8001/redoc

dev: install-dev ## Установить зависимости для разработки и запустить
	$(MAKE) run

ci: format-check lint test ## Запустить CI проверки

all: clean install-dev format lint test build ## Выполнить все проверки и сборку 