# Makefile для микросервиса тестирования reLink

.PHONY: help install test lint format clean build run docker-build docker-run

# Переменные
PYTHON = python3
PIP = pip3
APP_NAME = testing
PORT = 8003

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

test-performance: ## Запустить performance тесты
	pytest -m performance

test-load: ## Запустить load тесты
	locust -f tests/load/locustfile.py --host=http://localhost:$(PORT)

lint: ## Проверить код линтером
	flake8 app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/
	mypy app/

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
	rm -rf reports/

build: clean ## Собрать пакет
	$(PYTHON) setup.py sdist bdist_wheel

run: ## Запустить сервис локально
	uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --reload

run-prod: ## Запустить сервис в production режиме
	uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --workers 4

docker-build: ## Собрать Docker образ
	docker build -t relink-testing:latest .

docker-run: ## Запустить Docker контейнер
	docker run -d --name relink-testing \
		-p $(PORT):$(PORT) \
		-e DATABASE_URL=postgresql://user:pass@host:5432/testing \
		-e REDIS_URL=redis://localhost:6379 \
		relink-testing:latest

docker-stop: ## Остановить Docker контейнер
	docker stop relink-testing || true
	docker rm relink-testing || true

docker-logs: ## Показать логи Docker контейнера
	docker logs -f relink-testing

migrate: ## Применить миграции базы данных
	alembic upgrade head

migrate-create: ## Создать новую миграцию
	alembic revision --autogenerate -m "$(message)"

seed: ## Заполнить базу тестовыми данными
	$(PYTHON) -m app.scripts.seed_database

generate-report: ## Сгенерировать отчет о тестировании
	pytest --html=reports/report.html --self-contained-html

benchmark: ## Запустить бенчмарки
	pytest --benchmark-only

security-scan: ## Сканирование безопасности
	bandit -r app/
	safety check

all: install lint test ## Установить, проверить и протестировать 