# 🚀 reLink Makefile - Автоматизация с BuildKit
# Автоматически использует профессиональный скрипт сборки и BuildKit

.PHONY: help build build-no-cache build-service up down restart logs clean analyze health

# Переменные
COMPOSE_FILE = config/docker-compose.yml
BUILD_SCRIPT = scripts/professional-build.sh

# Цвета для вывода
GREEN = \033[0;32m
BLUE = \033[0;34m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Помощь
help:
	@echo -e "$(BLUE)🚀 reLink - Команды Makefile$(NC)"
	@echo ""
	@echo -e "$(GREEN)Сборка:$(NC)"
	@echo "  build          - Сборка всех сервисов с BuildKit"
	@echo "  build-no-cache - Сборка без кеша"
	@echo "  build-service  - Сборка конкретного сервиса (make build-service SERVICE=backend)"
	@echo ""
	@echo -e "$(GREEN)Управление:$(NC)"
	@echo "  up             - Запуск всех сервисов"
	@echo "  down           - Остановка всех сервисов"
	@echo "  restart        - Перезапуск всех сервисов"
	@echo ""
	@echo -e "$(GREEN)Мониторинг:$(NC)"
	@echo "  logs           - Просмотр логов"
	@echo "  health         - Проверка здоровья сервисов"
	@echo "  analyze        - Анализ Docker образов"
	@echo ""
	@echo -e "$(GREEN)Очистка:$(NC)"
	@echo "  clean          - Очистка Docker ресурсов"
	@echo ""

# Проверка существования скрипта сборки
check-build-script:
	@if [ ! -f "$(BUILD_SCRIPT)" ]; then \
		echo -e "$(RED)❌ Скрипт сборки не найден: $(BUILD_SCRIPT)$(NC)"; \
		exit 1; \
	fi

# Сборка всех сервисов с BuildKit
build: check-build-script
	@echo -e "$(BLUE)🚀 Запуск профессиональной сборки с BuildKit...$(NC)"
	@$(BUILD_SCRIPT) build

# Сборка без кеша
build-no-cache: check-build-script
	@echo -e "$(BLUE)🚀 Запуск сборки без кеша...$(NC)"
	@$(BUILD_SCRIPT) build --no-cache

# Сборка конкретного сервиса
build-service: check-build-script
	@if [ -z "$(SERVICE)" ]; then \
		echo -e "$(RED)❌ Укажите сервис: make build-service SERVICE=backend$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)🚀 Сборка сервиса $(SERVICE) с BuildKit...$(NC)"
	@$(BUILD_SCRIPT) build $(SERVICE)

# Запуск сервисов
up:
	@echo -e "$(BLUE)🚀 Запуск всех сервисов...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) up -d

# Остановка сервисов
down:
	@echo -e "$(YELLOW)🛑 Остановка всех сервисов...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) down

# Перезапуск сервисов
restart: down up
	@echo -e "$(GREEN)✅ Сервисы перезапущены$(NC)"

# Просмотр логов
logs:
	@echo -e "$(BLUE)📋 Просмотр логов...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) logs -f

# Проверка здоровья сервисов
health: check-build-script
	@echo -e "$(BLUE)🏥 Проверка здоровья сервисов...$(NC)"
	@$(BUILD_SCRIPT) health

# Анализ Docker образов
analyze: check-build-script
	@echo -e "$(BLUE)📊 Анализ Docker образов...$(NC)"
	@$(BUILD_SCRIPT) analyze

# Очистка Docker ресурсов
clean: check-build-script
	@echo -e "$(YELLOW)🧹 Очистка Docker ресурсов...$(NC)"
	@$(BUILD_SCRIPT) cleanup

# Полная очистка (принудительная)
clean-force: check-build-script
	@echo -e "$(RED)🧹 Принудительная очистка Docker ресурсов...$(NC)"
	@$(BUILD_SCRIPT) cleanup --force

# Быстрый старт (сборка + запуск)
quick-start: build up health
	@echo -e "$(GREEN)✅ Система готова к работе!$(NC)"

# Разработка (с пересборкой)
dev: build-no-cache up logs

# Продакшн (с проверками)
prod: build up health analyze
	@echo -e "$(GREEN)✅ Продакшн система развернута!$(NC)" 