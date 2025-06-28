# ========================================
# SEO Link Recommender - Makefile
# ========================================

.PHONY: help version get-version set-version tag-version release-version build test clean docs version-update version-sync

# Переменные
PYTHON := python3
VERSION_MANAGER := scripts/version_manager.py
SMART_CACHE := scripts/smart_docker_cache.py

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)🚀 SEO Link Recommender - Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ========================================
# Умная система управления Docker кешем
# ========================================

smart-build: ## Умная сборка с кешем
	@echo "$(GREEN)🧠 Умная сборка с кешем...$(NC)"
	@$(PYTHON) $(SMART_CACHE) --compose-file config/docker-compose.yml

smart-build-force: ## Принудительная умная сборка
	@echo "$(GREEN)🧠 Принудительная умная сборка...$(NC)"
	@$(PYTHON) $(SMART_CACHE) --compose-file config/docker-compose.yml --force

smart-build-service: ## Умная сборка конкретного сервиса
	@echo "$(GREEN)🧠 Умная сборка сервиса $(SERVICE)...$(NC)"
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)❌ Укажите SERVICE=имя_сервиса$(NC)"; \
		exit 1; \
	fi
	@$(PYTHON) $(SMART_CACHE) --compose-file config/docker-compose.yml --service $(SERVICE)

smart-cache-stats: ## Статистика умного кеша
	@echo "$(GREEN)📊 Статистика умного кеша...$(NC)"
	@$(PYTHON) $(SMART_CACHE) --stats

smart-cache-clean: ## Очистка невалидного кеша
	@echo "$(GREEN)🧹 Очистка невалидного кеша...$(NC)"
	@$(PYTHON) $(SMART_CACHE) --clean

smart-cache-reset: ## Полная очистка кеша
	@echo "$(GREEN)🗑️ Полная очистка кеша...$(NC)"
	@rm -rf .docker_cache
	@echo "$(GREEN)✅ Кеш полностью очищен$(NC)"

# ========================================
# Управление версиями (SemVer 2.0)
# ========================================

.PHONY: version version-current version-bump version-release version-prerelease version-set version-validate version-changelog

version: version-current
	@echo "📦 Информация о версии"

version-current:
	@echo "🔍 Текущая версия:"
	@$(PYTHON) $(VERSION_MANAGER) current

version-bump:
	@echo "🚀 Увеличение версии..."
	@if [ -z "$(TYPE)" ]; then \
		echo "❌ Укажите TYPE=major|minor|patch"; \
		exit 1; \
	fi
	@$(PYTHON) $(VERSION_MANAGER) bump --type $(TYPE)

version-release:
	@echo "🎉 Создание релиза..."
	@$(PYTHON) $(VERSION_MANAGER) release --type $(or $(TYPE),patch)

version-prerelease:
	@echo "🔧 Создание prerelease..."
	@if [ -z "$(NAME)" ]; then \
		echo "❌ Укажите NAME=имя_prerelease"; \
		exit 1; \
	fi
	@$(PYTHON) $(VERSION_MANAGER) prerelease --prerelease $(NAME) --type $(or $(TYPE),rc)

version-set:
	@echo "⚙️ Установка версии..."
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ Укажите VERSION=X.Y.Z"; \
		exit 1; \
	fi
	@$(PYTHON) $(VERSION_MANAGER) set --version $(VERSION)

version-validate:
	@echo "✅ Валидация версии..."
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ Укажите VERSION=X.Y.Z"; \
		exit 1; \
	fi
	@$(PYTHON) $(VERSION_MANAGER) validate --version $(VERSION)

version-changelog:
	@echo "📝 Обновление changelog..."
	@if [ -z "$(CHANGES)" ]; then \
		echo "❌ Укажите CHANGES=\"изменение1 изменение2\""; \
		exit 1; \
	fi
	@$(PYTHON) $(VERSION_MANAGER) changelog --changes $(CHANGES)

# ========================================
# Сборка и тестирование
# ========================================

build: ## Сборка Docker образов
	@echo "$(GREEN)🔨 Сборка Docker образов...$(NC)"
	docker-compose build

build-parallel: ## Сборка для параллельного режима
	@echo "$(GREEN)🔨 Сборка для параллельного режима...$(NC)"
	docker-compose -f docker-compose.parallel.yml build

build-no-cache: ## Сборка без кеша
	@echo "$(GREEN)🔨 Сборка без кеша...$(NC)"
	docker-compose build --no-cache

build-service: ## Сборка конкретного сервиса
	@echo "$(GREEN)🔨 Сборка сервиса $(SERVICE)...$(NC)"
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)❌ Укажите SERVICE=имя_сервиса$(NC)"; \
		exit 1; \
	fi
	docker-compose build $(SERVICE)

test: ## Запуск тестов
	@echo "$(GREEN)🧪 Запуск тестов...$(NC)"
	@cd backend && python3 -m pytest -v

test-frontend: ## Тесты frontend
	@echo "$(GREEN)🧪 Тесты frontend...$(NC)"
	@cd frontend && npm test

test-docs: ## Тесты микросервиса документации
	@echo "$(GREEN)🧪 Тесты микросервиса документации...$(NC)"
	@cd docs && make test

test-testing: ## Тесты микросервиса тестирования
	@echo "$(GREEN)🧪 Тесты микросервиса тестирования...$(NC)"
	@cd testing && make test

test-e2e: ## E2E тесты
	@echo "$(GREEN)🧪 E2E тесты...$(NC)"
	@cd frontend && npm run test:e2e

# ========================================
# Запуск и остановка
# ========================================

up: ## Запуск системы
	@echo "$(GREEN)🚀 Запуск системы...$(NC)"
	docker-compose up -d

up-parallel: ## Запуск параллельного режима
	@echo "$(GREEN)🚀 Запуск параллельного режима...$(NC)"
	./run_parallel.sh

down: ## Остановка системы
	@echo "$(GREEN)🛑 Остановка системы...$(NC)"
	docker-compose down

restart: ## Перезапуск системы
	@echo "$(GREEN)🔄 Перезапуск системы...$(NC)"
	docker-compose restart

# ========================================
# Мониторинг и логи
# ========================================

logs: ## Показать логи всех сервисов
	@echo "$(GREEN)📋 Логи системы...$(NC)"
	docker-compose logs -f

logs-backend: ## Логи backend
	@echo "$(GREEN)📋 Логи backend...$(NC)"
	docker-compose logs -f backend

logs-frontend: ## Логи frontend
	@echo "$(GREEN)📋 Логи frontend...$(NC)"
	docker-compose logs -f frontend

logs-docs: ## Логи микросервиса документации
	@echo "$(GREEN)📋 Логи микросервиса документации...$(NC)"
	docker-compose logs -f docs

logs-testing: ## Логи микросервиса тестирования
	@echo "$(GREEN)📋 Логи микросервиса тестирования...$(NC)"
	docker-compose logs -f testing

logs-redis: ## Логи Redis
	@echo "$(GREEN)📋 Логи Redis...$(NC)"
	docker-compose logs -f redis

logs-ollama: ## Логи Ollama
	@echo "$(GREEN)📋 Логи Ollama...$(NC)"
	docker-compose logs -f ollama

status: ## Статус контейнеров
	@echo "$(GREEN)📊 Статус контейнеров...$(NC)"
	docker-compose ps

stats: ## Статистика использования ресурсов
	@echo "$(GREEN)📊 Статистика ресурсов...$(NC)"
	docker stats

# ========================================
# Микросервис документации
# ========================================

docs-health: ## Проверка здоровья микросервиса документации
	@echo "$(GREEN)🏥 Проверка здоровья микросервиса документации...$(NC)"
	@curl -f http://localhost:8001/api/v1/health || echo "$(RED)❌ Микросервис документации недоступен$(NC)"

docs-version: ## Получение версии из микросервиса документации
	@echo "$(GREEN)🏷️ Версия из микросервиса документации...$(NC)"
	@curl -s http://localhost:8001/api/v1/version | jq . || echo "$(RED)❌ Ошибка получения версии$(NC)"

docs-cache-stats: ## Статистика кэша микросервиса документации
	@echo "$(GREEN)📊 Статистика кэша...$(NC)"
	@curl -s http://localhost:8001/api/v1/cache/stats | jq . || echo "$(RED)❌ Ошибка получения статистики кэша$(NC)"

docs-clear-cache: ## Очистка кэша микросервиса документации
	@echo "$(GREEN)🧹 Очистка кэша...$(NC)"
	@curl -X DELETE http://localhost:8001/api/v1/cache/clear || echo "$(RED)❌ Ошибка очистки кэша$(NC)"

docs-open: ## Открыть документацию API микросервиса
	@echo "$(GREEN)📖 Открытие документации API...$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8001/docs; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8001/docs; \
	else \
		echo "$(YELLOW)📖 Документация API: http://localhost:8001/docs$(NC)"; \
	fi

docs-redoc: ## Открыть ReDoc документацию микросервиса
	@echo "$(GREEN)📋 Открытие ReDoc документации...$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8001/redoc; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8001/redoc; \
	else \
		echo "$(YELLOW)📋 ReDoc документация: http://localhost:8001/redoc$(NC)"; \
	fi

# ========================================
# Очистка и обслуживание
# ========================================

clean: ## Очистка временных файлов
	@echo "$(GREEN)🧹 Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

clean-docker: ## Очистка Docker ресурсов
	@echo "$(GREEN)🧹 Очистка Docker ресурсов...$(NC)"
	docker system prune -f
	docker volume prune -f
	docker network prune -f

clean-all: clean clean-docker smart-cache-reset ## Полная очистка
	@echo "$(GREEN)✅ Полная очистка завершена$(NC)"

# ========================================
# Утилиты
# ========================================

check-deps: ## Проверка зависимостей
	@echo "$(GREEN)🔍 Проверка зависимостей...$(NC)"
	@which docker >/dev/null || (echo "$(RED)❌ Docker не установлен$(NC)" && exit 1)
	@which docker-compose >/dev/null || (echo "$(RED)❌ Docker Compose не установлен$(NC)" && exit 1)
	@which python3 >/dev/null || (echo "$(RED)❌ Python3 не установлен$(NC)" && exit 1)
	@echo "$(GREEN)✅ Все зависимости установлены$(NC)"

install-deps: ## Установка зависимостей для умного кеша
	@echo "$(GREEN)📦 Установка зависимостей для умного кеша...$(NC)"
	pip3 install docker pyyaml

# ========================================
# Комплексные команды
# ========================================

dev-setup: check-deps install-deps smart-cache-stats ## Настройка окружения разработки
	@echo "$(GREEN)✅ Окружение разработки готово$(NC)"

quick-build: smart-build up ## Быстрая сборка и запуск
	@echo "$(GREEN)✅ Быстрая сборка и запуск завершены$(NC)"

full-build: build-no-cache up ## Полная пересборка и запуск
	@echo "$(GREEN)✅ Полная пересборка и запуск завершены$(NC)"

# ========================================
# Документация
# ========================================

docs: ## Открыть документацию API
	@echo "$(GREEN)📖 Открытие документации API...$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8000/docs; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8000/docs; \
	else \
		echo "$(YELLOW)📖 Документация API: http://localhost:8000/docs$(NC)"; \
	fi

redoc: ## Открыть ReDoc документацию
	@echo "$(GREEN)📖 Открытие ReDoc документации...$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8000/redoc; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8000/redoc; \
	else \
		echo "$(YELLOW)📖 ReDoc документация: http://localhost:8000/redoc$(NC)"; \
	fi

# ========================================
# CI/CD
# ========================================

ci: check-deps test ## Запуск CI проверок
	@echo "$(GREEN)✅ CI проверки завершены$(NC)"

ci-full: check-deps test smart-build test-e2e ## Полные CI проверки
	@echo "$(GREEN)✅ Полные CI проверки завершены$(NC)"

# ========================================
# Справка по умному кешу
# ========================================

smart-cache-help: ## Справка по умному кешу
	@echo "$(GREEN)🧠 Умная система управления Docker кешем$(NC)"
	@echo ""
	@echo "$(YELLOW)Основные команды:$(NC)"
	@echo "  smart-build          - Умная сборка с кешем"
	@echo "  smart-build-force    - Принудительная пересборка"
	@echo "  smart-build-service  - Сборка конкретного сервиса (SERVICE=имя)"
	@echo "  smart-cache-stats    - Статистика кеша"
	@echo "  smart-cache-clean    - Очистка невалидного кеша"
	@echo "  smart-cache-reset    - Полная очистка кеша"
	@echo ""
	@echo "$(YELLOW)Примеры использования:$(NC)"
	@echo "  make smart-build"
	@echo "  make smart-build-service SERVICE=backend"
	@echo "  make smart-build-force"
	@echo "  make smart-cache-stats"
	@echo ""
	@echo "$(YELLOW)Как это работает:$(NC)"
	@echo "  1. Анализирует изменения в файлах кода"
	@echo "  2. Вычисляет хеши для определения изменений"
	@echo "  3. Пересобирает только затронутые слои"
	@echo "  4. Сохраняет кеш для неизмененных частей"
	@echo "  5. Автоматически инвалидирует зависимые слои"

# ========================================
# Финальная команда
# ========================================

all: clean install-dev format lint test build ## Выполнить все проверки и сборку

# ========================================
# Остальная часть Makefile остается без изменений
# ======================================== 