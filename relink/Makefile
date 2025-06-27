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

dev-backend: ## Запуск backend в режиме разработки
	@echo "$(GREEN)🔧 Запуск backend в режиме разработки...$(NC)"
	@cd backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Запуск frontend в режиме разработки
	@echo "$(GREEN)🔧 Запуск frontend в режиме разработки...$(NC)"
	@cd frontend && npm run dev

# ========================================
# Проверки
# ========================================

check: ## Проверка системы
	@echo "$(GREEN)🔍 Проверка системы...$(NC)"
	@echo "$(YELLOW)Проверка Docker...$(NC)"
	@docker --version
	@echo "$(YELLOW)Проверка Docker Compose...$(NC)"
	@docker-compose --version
	@echo "$(YELLOW)Проверка портов...$(NC)"
	@lsof -i :3000 -i :8000 -i :11434 || echo "$(GREEN)✅ Порты свободны$(NC)"

health: ## Проверка здоровья системы
	@echo "$(GREEN)🏥 Проверка здоровья системы...$(NC)"
	@curl -s http://localhost:8000/api/v1/health || echo "$(RED)❌ Backend недоступен$(NC)"
	@curl -s http://localhost:11434/api/tags || echo "$(RED)❌ Ollama недоступен$(NC)"

# ========================================
# Утилиты
# ========================================

shell-backend: ## Shell в backend контейнере
	@echo "$(GREEN)🐚 Shell в backend...$(NC)"
	docker-compose exec backend /bin/bash

shell-frontend: ## Shell в frontend контейнере
	@echo "$(GREEN)🐚 Shell в frontend...$(NC)"
	docker-compose exec frontend /bin/sh

shell-ollama: ## Shell в Ollama контейнере
	@echo "$(GREEN)🐚 Shell в Ollama...$(NC)"
	docker-compose exec ollama /bin/sh

# ========================================
# Специальные команды
# ========================================

quick-start: ## Быстрый старт (сборка + запуск)
	@echo "$(GREEN)⚡ Быстрый старт...$(NC)"
	@make build
	@make up
	@echo "$(GREEN)✅ Система запущена!$(NC)"
	@echo "$(YELLOW)🌐 Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)🔧 Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)🧠 Ollama: http://localhost:11434$(NC)"

quick-start-parallel: ## Быстрый старт параллельного режима
	@echo "$(GREEN)⚡ Быстрый старт параллельного режима...$(NC)"
	@make build-parallel
	@make up-parallel
	@echo "$(GREEN)✅ Система запущена!$(NC)"
	@echo "$(YELLOW)🌐 Classic Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)⚡ Vite Frontend: http://localhost:3001$(NC)"
	@echo "$(YELLOW)🔧 Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)🧠 Ollama: http://localhost:11434$(NC)"

# ========================================
# Информация
# ========================================

info: ## Информация о проекте
	@echo "$(GREEN)📋 Информация о проекте$(NC)"
	@echo "$(YELLOW)Название:$(NC) SEO Link Recommender"
	@make get-version
	@echo "$(YELLOW)Автор:$(NC) Команда разработки"
	@echo "$(YELLOW)Лицензия:$(NC) MIT"
	@echo "$(YELLOW)GitHub:$(NC) https://github.com/your-repo"
	@echo "$(YELLOW)Документация:$(NC) DOCUMENTATION.md" 