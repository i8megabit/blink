# ========================================
# SEO Link Recommender - Makefile
# ========================================

.PHONY: help version get-version set-version tag-version release-version build test clean docs version-update version-sync

# Переменные
PYTHON := python3
VERSION_MANAGER := scripts/version_manager.py

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

clean: ## Очистка Docker ресурсов
	@echo "$(GREEN)🧹 Очистка Docker ресурсов...$(NC)"
	docker system prune -f
	docker volume prune -f

clean-all: ## Полная очистка (включая образы)
	@echo "$(GREEN)🧹 Полная очистка...$(NC)"
	docker system prune -a -f
	docker volume prune -f

clean-data: ## Очистка данных (БД, кэш)
	@echo "$(GREEN)🧹 Очистка данных...$(NC)"
	rm -rf postgres_data chroma_db ollama_models

# ========================================
# Документация
# ========================================

docs: ## Открыть документацию
	@echo "$(GREEN)📚 Открытие документации...$(NC)"
	@if command -v open >/dev/null 2>&1; then \
		open DOCUMENTATION.md; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open DOCUMENTATION.md; \
	else \
		echo "$(YELLOW)📖 Документация: DOCUMENTATION.md$(NC)"; \
	fi

# ========================================
# Разработка
# ========================================

dev-setup: ## Настройка окружения разработки
	@echo "$(GREEN)🔧 Настройка окружения разработки...$(NC)"
	@cd backend && pip install -r requirements.txt
	@cd frontend && npm install
	@cd docs && make install-dev

dev-backend: ## Запуск backend в режиме разработки
	@echo "$(GREEN)🔧 Запуск backend в режиме разработки...$(NC)"
	@cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Запуск frontend в режиме разработки
	@echo "$(GREEN)🔧 Запуск frontend в режиме разработки...$(NC)"
	@cd frontend && npm run dev

dev-docs: ## Запуск микросервиса документации в режиме разработки
	@echo "$(GREEN)🔧 Запуск микросервиса документации в режиме разработки...$(NC)"
	@cd docs && make run

# ========================================
# Утилиты
# ========================================

check-all: ## Проверка всех сервисов
	@echo "$(GREEN)🔍 Проверка всех сервисов...$(NC)"
	@echo "$(YELLOW)Backend:$(NC)"
	@curl -f http://localhost:8000/api/v1/health || echo "$(RED)❌ Backend недоступен$(NC)"
	@echo "$(YELLOW)Frontend:$(NC)"
	@curl -f http://localhost:3000 || echo "$(RED)❌ Frontend недоступен$(NC)"
	@echo "$(YELLOW)Документация:$(NC)"
	@curl -f http://localhost:8001/api/v1/health || echo "$(RED)❌ Микросервис документации недоступен$(NC)"
	@echo "$(YELLOW)Ollama:$(NC)"
	@curl -f http://localhost:11434/api/tags || echo "$(RED)❌ Ollama недоступен$(NC)"
	@echo "$(YELLOW)Redis:$(NC)"
	@docker exec $$(docker ps -q --filter name=redis) redis-cli ping || echo "$(RED)❌ Redis недоступен$(NC)"

# ========================================
# Остальная часть Makefile остается без изменений
# ======================================== 