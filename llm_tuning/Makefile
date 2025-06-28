# Makefile для LLM Tuning Microservice

.PHONY: help install dev test lint format clean docker-build docker-run docker-stop docker-logs migrate migrate-create health-check

# Переменные
SERVICE_NAME = llm-tuning
DOCKER_IMAGE = llm-tuning:latest
DOCKER_CONTAINER = llm-tuning-container
PYTHON = python3
PIP = pip3

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)LLM Tuning Microservice - Команды управления$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Зависимости установлены!$(NC)"

install-dev: ## Установить зависимости для разработки
	@echo "$(GREEN)Установка зависимостей для разработки...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)Зависимости для разработки установлены!$(NC)"

dev: ## Запуск в режиме разработки
	@echo "$(GREEN)Запуск в режиме разработки...$(NC)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

prod: ## Запуск в продакшн режиме
	@echo "$(GREEN)Запуск в продакшн режиме...$(NC)"
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

test: ## Запуск тестов
	@echo "$(GREEN)Запуск тестов...$(NC)"
	pytest -v

test-cov: ## Запуск тестов с покрытием
	@echo "$(GREEN)Запуск тестов с покрытием...$(NC)"
	pytest --cov=app --cov-report=html --cov-report=term

test-watch: ## Запуск тестов в режиме наблюдения
	@echo "$(GREEN)Запуск тестов в режиме наблюдения...$(NC)"
	pytest-watch -- -v

lint: ## Проверка стиля кода
	@echo "$(GREEN)Проверка стиля кода...$(NC)"
	flake8 app/ tests/
	mypy app/

format: ## Форматирование кода
	@echo "$(GREEN)Форматирование кода...$(NC)"
	black app/ tests/
	isort app/ tests/

clean: ## Очистка временных файлов
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

docker-build: ## Сборка Docker образа
	@echo "$(GREEN)Сборка Docker образа...$(NC)"
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Запуск Docker контейнера
	@echo "$(GREEN)Запуск Docker контейнера...$(NC)"
	docker run -d \
		--name $(DOCKER_CONTAINER) \
		-p 8000:8000 \
		--env-file .env \
		$(DOCKER_IMAGE)

docker-stop: ## Остановка Docker контейнера
	@echo "$(GREEN)Остановка Docker контейнера...$(NC)"
	docker stop $(DOCKER_CONTAINER) || true
	docker rm $(DOCKER_CONTAINER) || true

docker-logs: ## Просмотр логов Docker контейнера
	@echo "$(GREEN)Логи Docker контейнера:$(NC)"
	docker logs -f $(DOCKER_CONTAINER)

docker-compose-up: ## Запуск с Docker Compose
	@echo "$(GREEN)Запуск с Docker Compose...$(NC)"
	docker-compose up -d

docker-compose-down: ## Остановка Docker Compose
	@echo "$(GREEN)Остановка Docker Compose...$(NC)"
	docker-compose down

docker-compose-logs: ## Просмотр логов Docker Compose
	@echo "$(GREEN)Логи Docker Compose:$(NC)"
	docker-compose logs -f

migrate: ## Применение миграций
	@echo "$(GREEN)Применение миграций...$(NC)"
	alembic upgrade head

migrate-create: ## Создание новой миграции
	@echo "$(GREEN)Создание новой миграции...$(NC)"
	@read -p "Введите описание миграции: " description; \
	alembic revision --autogenerate -m "$$description"

migrate-rollback: ## Откат последней миграции
	@echo "$(GREEN)Откат последней миграции...$(NC)"
	alembic downgrade -1

init-db: ## Инициализация базы данных
	@echo "$(GREEN)Инициализация базы данных...$(NC)"
	$(PYTHON) -m app.create_tables

health-check: ## Проверка здоровья сервиса
	@echo "$(GREEN)Проверка здоровья сервиса...$(NC)"
	curl -f http://localhost:8000/health || echo "$(RED)Сервис недоступен$(NC)"

api-docs: ## Открыть API документацию
	@echo "$(GREEN)Открытие API документации...$(NC)"
	open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Откройте http://localhost:8000/docs в браузере"

setup-dev: ## Настройка окружения для разработки
	@echo "$(GREEN)Настройка окружения для разработки...$(NC)"
	cp env.example .env
	@echo "$(YELLOW)Отредактируйте .env файл с вашими настройками$(NC)"
	$(MAKE) install-dev
	$(MAKE) init-db
	@echo "$(GREEN)Окружение для разработки настроено!$(NC)"

setup-prod: ## Настройка продакшн окружения
	@echo "$(GREEN)Настройка продакшн окружения...$(NC)"
	cp env.example .env
	@echo "$(YELLOW)Отредактируйте .env файл для продакшн настроек$(NC)"
	$(MAKE) install
	$(MAKE) init-db
	$(MAKE) migrate
	@echo "$(GREEN)Продакшн окружение настроено!$(NC)"

backup-db: ## Резервное копирование базы данных
	@echo "$(GREEN)Резервное копирование базы данных...$(NC)"
	@read -p "Введите имя файла бэкапа: " filename; \
	pg_dump $$DATABASE_URL > backups/$$filename.sql

restore-db: ## Восстановление базы данных
	@echo "$(GREEN)Восстановление базы данных...$(NC)"
	@read -p "Введите имя файла бэкапа: " filename; \
	psql $$DATABASE_URL < backups/$$filename.sql

monitor: ## Мониторинг сервиса
	@echo "$(GREEN)Мониторинг сервиса...$(NC)"
	@echo "$(YELLOW)Health Check:$(NC)"
	curl -s http://localhost:8000/health | jq .
	@echo "$(YELLOW)Метрики:$(NC)"
	curl -s http://localhost:8000/api/v1/metrics/summary | jq .

logs: ## Просмотр логов
	@echo "$(GREEN)Просмотр логов...$(NC)"
	tail -f logs/llm-tuning.log

create-test-data: ## Создание тестовых данных
	@echo "$(GREEN)Создание тестовых данных...$(NC)"
	$(PYTHON) scripts/create_test_data.py

cleanup-test-data: ## Очистка тестовых данных
	@echo "$(GREEN)Очистка тестовых данных...$(NC)"
	$(PYTHON) scripts/cleanup_test_data.py

benchmark: ## Запуск всех бенчмарков
	@echo "$(GREEN)Запуск всех бенчмарков производительности...$(NC)"
	cd benchmarks && $(PYTHON) performance_test.py

benchmark-ab-testing: ## Бенчмарк A/B тестирования
	@echo "$(GREEN)Запуск бенчмарка A/B тестирования...$(NC)"
	cd benchmarks && $(PYTHON) performance_test.py ab_testing

benchmark-optimization: ## Бенчмарк оптимизации
	@echo "$(GREEN)Запуск бенчмарка оптимизации...$(NC)"
	cd benchmarks && $(PYTHON) performance_test.py optimization

benchmark-quality-assessment: ## Бенчмарк оценки качества
	@echo "$(GREEN)Запуск бенчмарка оценки качества...$(NC)"
	cd benchmarks && $(PYTHON) performance_test.py quality_assessment

benchmark-system-health: ## Бенчмарк мониторинга здоровья
	@echo "$(GREEN)Запуск бенчмарка мониторинга здоровья...$(NC)"
	cd benchmarks && $(PYTHON) performance_test.py system_health

benchmark-extended-stats: ## Бенчмарк расширенной статистики
	@echo "$(GREEN)Запуск бенчмарка расширенной статистики...$(NC)"
	cd benchmarks && $(PYTHON) performance_test.py extended_stats

benchmark-stress: ## Стресс-тестирование
	@echo "$(GREEN)Запуск стресс-тестирования...$(NC)"
	cd benchmarks && $(PYTHON) performance_test.py system_health 1000
	cd benchmarks && $(PYTHON) performance_test.py extended_stats 500

benchmark-quick: ## Быстрый бенчмарк
	@echo "$(GREEN)Запуск быстрого бенчмарка...$(NC)"
	cd benchmarks && $(PYTHON) performance_test.py ab_testing 10
	cd benchmarks && $(PYTHON) performance_test.py quality_assessment 20

benchmark-install-deps: ## Установка зависимостей для бенчмарков
	@echo "$(GREEN)Установка зависимостей для бенчмарков...$(NC)"
	$(PIP) install aiohttp psutil matplotlib numpy

benchmark-clean: ## Очистка результатов бенчмарков
	@echo "$(GREEN)Очистка результатов бенчмарков...$(NC)"
	rm -f benchmarks/benchmark_report.txt
	rm -f benchmarks/benchmark_results.png

security-check: ## Проверка безопасности
	@echo "$(GREEN)Проверка безопасности...$(NC)"
	bandit -r app/
	safety check

update-deps: ## Обновление зависимостей
	@echo "$(GREEN)Обновление зависимостей...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements.txt

check-env: ## Проверка переменных окружения
	@echo "$(GREEN)Проверка переменных окружения...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN).env файл найден$(NC)"; \
		cat .env | grep -v "^#" | grep -v "^$$" | while read line; do \
			echo "$$line"; \
		done; \
	else \
		echo "$(RED).env файл не найден$(NC)"; \
		echo "$(YELLOW)Скопируйте env.example в .env и настройте переменные$(NC)"; \
	fi

# Команды для разработки
dev-setup: setup-dev ## Полная настройка для разработки
dev-start: dev ## Запуск в режиме разработки
dev-test: test ## Запуск тестов
dev-lint: lint ## Проверка стиля кода
dev-format: format ## Форматирование кода

# Команды для продакшн
prod-setup: setup-prod ## Полная настройка для продакшн
prod-start: prod ## Запуск в продакшн режиме
prod-docker: docker-build docker-run ## Запуск в Docker
prod-compose: docker-compose-up ## Запуск с Docker Compose

# Команды для CI/CD
ci-install: install ## Установка для CI
ci-test: test-cov ## Тесты для CI
ci-lint: lint ## Проверка стиля для CI
ci-security: security-check ## Проверка безопасности для CI

# Алиасы
up: dev ## Алиас для dev
down: docker-stop ## Алиас для docker-stop
build: docker-build ## Алиас для docker-build
run: docker-run ## Алиас для docker-run
logs: docker-logs ## Алиас для docker-logs
test: test ## Алиас для test
lint: lint ## Алиас для lint
format: format ## Алиас для format
clean: clean ## Алиас для clean 