# ========================================
# SEO Link Recommender - Makefile
# ========================================

.PHONY: help version get-version set-version tag-version release-version build test clean docs version-update version-sync

# Переменные
PYTHON := python3
VERSION_MANAGER := scripts/version_manager.py
SMART_CACHE := scripts/smart_docker_cache.py
PROFESSIONAL_BUILD := scripts/professional-build.sh

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)🚀 SEO Link Recommender - Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ========================================
# 🚀 ПРОФЕССИОНАЛЬНАЯ СБОРКА С BUILDKIT
# ========================================

buildkit: ## Профессиональная сборка с BuildKit
	@echo "$(BLUE)🚀 Профессиональная сборка с BuildKit...$(NC)"
	@$(PROFESSIONAL_BUILD)

buildkit-full: ## Полная сборка с BuildKit + запуск + проверка здоровья
	@echo "$(BLUE)🚀 Полная сборка с BuildKit...$(NC)"
	@$(PROFESSIONAL_BUILD) -u -h

buildkit-backend: ## Сборка только backend с BuildKit
	@echo "$(BLUE)🚀 Сборка backend с BuildKit...$(NC)"
	@$(PROFESSIONAL_BUILD) -s backend

buildkit-no-cache: ## Сборка с BuildKit без кеша
	@echo "$(BLUE)🚀 Сборка с BuildKit без кеша...$(NC)"
	@$(PROFESSIONAL_BUILD) -n

buildkit-clean: ## Сборка с BuildKit + очистка
	@echo "$(BLUE)🚀 Сборка с BuildKit + очистка...$(NC)"
	@$(PROFESSIONAL_BUILD) -c

buildkit-force: ## Принудительная сборка с BuildKit + полная очистка
	@echo "$(BLUE)🚀 Принудительная сборка с BuildKit...$(NC)"
	@$(PROFESSIONAL_BUILD) -n -f

buildkit-analyze: ## Сборка с BuildKit + анализ образов
	@echo "$(BLUE)🚀 Сборка с BuildKit + анализ...$(NC)"
	@$(PROFESSIONAL_BUILD) -a

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

build: ## Сборка Docker образов (классическая)
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

# ========================================
# Запуск и остановка
# ========================================

up: ## Запуск системы (классический)
	@echo "$(GREEN)🚀 Запуск системы...$(NC)"
	docker-compose up -d

up-buildkit: ## Запуск системы с BuildKit
	@echo "$(BLUE)🚀 Запуск системы с BuildKit...$(NC)"
	docker-compose -f config/docker-compose.buildkit.yml up -d

up-parallel: ## Запуск параллельного режима
	@echo "$(GREEN)🚀 Запуск параллельного режима...$(NC)"
	./run_parallel.sh

down: ## Остановка системы
	@echo "$(GREEN)🛑 Остановка системы...$(NC)"
	docker-compose down

down-buildkit: ## Остановка системы BuildKit
	@echo "$(BLUE)🛑 Остановка системы BuildKit...$(NC)"
	docker-compose -f config/docker-compose.buildkit.yml down

restart: ## Перезапуск системы
	@echo "$(GREEN)🔄 Перезапуск системы...$(NC)"
	docker-compose restart

restart-buildkit: ## Перезапуск системы BuildKit
	@echo "$(BLUE)🔄 Перезапуск системы BuildKit...$(NC)"
	docker-compose -f config/docker-compose.buildkit.yml restart

# ========================================
# Мониторинг и логи
# ========================================

logs: ## Показать логи всех сервисов
	@echo "$(GREEN)📋 Логи системы...$(NC)"
	docker-compose logs -f

logs-buildkit: ## Показать логи системы BuildKit
	@echo "$(BLUE)📋 Логи системы BuildKit...$(NC)"
	docker-compose -f config/docker-compose.buildkit.yml logs -f

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

# ========================================
# Тестирование
# ========================================

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
	docker builder prune -f

clean-docker-force: ## Принудительная очистка Docker
	@echo "$(RED)🧹 Принудительная очистка Docker...$(NC)"
	docker system prune -af
	docker builder prune -af
	docker volume prune -f

# ========================================
# Документация
# ========================================

docs: ## Генерация документации
	@echo "$(GREEN)📚 Генерация документации...$(NC)"
	@cd docs && make docs

docs-serve: ## Запуск сервера документации
	@echo "$(GREEN)📚 Запуск сервера документации...$(NC)"
	@cd docs && make serve

# ========================================
# Развертывание
# ========================================

deploy: ## Развертывание в продакшн
	@echo "$(GREEN)🚀 Развертывание в продакшн...$(NC)"
	@$(PROFESSIONAL_BUILD) -u -h -a

deploy-staging: ## Развертывание в staging
	@echo "$(YELLOW)🚀 Развертывание в staging...$(NC)"
	@$(PROFESSIONAL_BUILD) -s backend -u

# ========================================
# Диагностика
# ========================================

status: ## Статус всех сервисов
	@echo "$(GREEN)📊 Статус сервисов...$(NC)"
	docker-compose ps

status-buildkit: ## Статус сервисов BuildKit
	@echo "$(BLUE)📊 Статус сервисов BuildKit...$(NC)"
	docker-compose -f config/docker-compose.buildkit.yml ps

health: ## Проверка здоровья сервисов
	@echo "$(GREEN)🏥 Проверка здоровья сервисов...$(NC)"
	@$(PROFESSIONAL_BUILD) --help | grep health-check || echo "Используйте: make buildkit-full"

# ========================================
# Утилиты
# ========================================

shell-backend: ## Shell в backend контейнер
	@echo "$(GREEN)🐚 Shell в backend...$(NC)"
	docker-compose exec backend /bin/bash

shell-frontend: ## Shell в frontend контейнер
	@echo "$(GREEN)🐚 Shell в frontend...$(NC)"
	docker-compose exec frontend /bin/sh

shell-db: ## Shell в базу данных
	@echo "$(GREEN)🐚 Shell в базу данных...$(NC)"
	docker-compose exec db psql -U seo_user -d seo_db

# ========================================
# Резервное копирование
# ========================================

backup: ## Резервное копирование данных
	@echo "$(GREEN)💾 Резервное копирование...$(NC)"
	docker-compose exec db pg_dump -U seo_user seo_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Восстановление данных
	@echo "$(GREEN)💾 Восстановление данных...$(NC)"
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)❌ Укажите FILE=путь_к_файлу.sql$(NC)"; \
		exit 1; \
	fi
	docker-compose exec -T db psql -U seo_user -d seo_db < $(FILE) 