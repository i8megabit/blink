# Makefile для reLink - AI-Powered SEO Platform
# Оптимизирован для Apple Silicon M4

.PHONY: help metrics resources build test deploy clean

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m # No Color

help: ## Показать справку по командам
	@echo "$(BLUE)🔗 reLink - AI-Powered SEO Platform$(NC)"
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

metrics: ## Обновить метрики проекта в README.md
	@echo "$(BLUE)📊 Обновление метрик проекта...$(NC)"
	@python3 update_metrics.py

resources: ## Рассчитать лимиты ресурсов для всех микросервисов
	@echo "$(BLUE)🚀 Расчет лимитов ресурсов для Apple Silicon M4...$(NC)"
	@python3 resource_limits.py

build: ## Собрать все Docker образы
	@echo "$(BLUE)🔨 Сборка Docker образов...$(NC)"
	@docker-compose build --parallel

build-native: ## Собрать образы с оптимизацией для Apple Silicon
	@echo "$(BLUE)🍎 Сборка с оптимизацией для Apple Silicon...$(NC)"
	@DOCKER_DEFAULT_PLATFORM=linux/arm64 docker-compose build --parallel

up: ## Запустить все сервисы
	@echo "$(BLUE)🚀 Запуск всех сервисов...$(NC)"
	@docker-compose up -d

up-native: ## Запустить с оптимизацией для Apple Silicon
	@echo "$(BLUE)🍎 Запуск с оптимизацией для Apple Silicon...$(NC)"
	@docker-compose -f docker-compose.native-gpu.yml up -d

down: ## Остановить все сервисы
	@echo "$(RED)🛑 Остановка всех сервисов...$(NC)"
	@docker-compose down

logs: ## Показать логи всех сервисов
	@echo "$(BLUE)📋 Логи сервисов:$(NC)"
	@docker-compose logs -f

status: ## Показать статус сервисов
	@echo "$(BLUE)📊 Статус сервисов:$(NC)"
	@docker-compose ps

test: ## Запустить все тесты
	@echo "$(BLUE)🧪 Запуск тестов...$(NC)"
	@cd frontend && npm test
	@cd backend && python -m pytest

test-e2e: ## Запустить E2E тесты
	@echo "$(BLUE)🧪 Запуск E2E тестов...$(NC)"
	@cd frontend && npm run test:e2e

lint: ## Проверить код линтером
	@echo "$(BLUE)🔍 Проверка кода...$(NC)"
	@cd frontend && npm run lint
	@cd backend && python -m flake8 .

format: ## Форматировать код
	@echo "$(BLUE)✨ Форматирование кода...$(NC)"
	@cd frontend && npm run format
	@cd backend && python -m black .

clean: ## Очистить все контейнеры и образы
	@echo "$(RED)🧹 Очистка Docker...$(NC)"
	@docker-compose down -v --rmi all
	@docker system prune -f

clean-all: ## Полная очистка (включая node_modules)
	@echo "$(RED)🧹 Полная очистка...$(NC)"
	@docker-compose down -v --rmi all
	@docker system prune -f
	@cd frontend && rm -rf node_modules package-lock.json
	@cd backend && rm -rf __pycache__ .pytest_cache

install: ## Установить зависимости
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	@cd frontend && npm install
	@cd backend && pip install -r requirements.txt

dev: ## Запустить в режиме разработки
	@echo "$(BLUE)🔧 Запуск в режиме разработки...$(NC)"
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

prod: ## Запустить в production режиме
	@echo "$(BLUE)🚀 Запуск в production режиме...$(NC)"
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

monitor: ## Открыть мониторинг
	@echo "$(BLUE)📊 Открытие мониторинга...$(NC)"
	@open http://localhost:3000
	@open http://localhost:8000/docs
	@open http://localhost:9090

backup: ## Создать резервную копию данных
	@echo "$(BLUE)💾 Создание резервной копии...$(NC)"
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U postgres relink > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Восстановить данные из резервной копии
	@echo "$(BLUE)🔄 Восстановление данных...$(NC)"
	@ls -la backups/
	@echo "Введите имя файла для восстановления:"
	@read filename && docker-compose exec -T postgres psql -U postgres relink < backups/$$filename

update: ## Обновить все зависимости
	@echo "$(BLUE)🔄 Обновление зависимостей...$(NC)"
	@cd frontend && npm update
	@cd backend && pip install --upgrade -r requirements.txt

security: ## Проверить безопасность
	@echo "$(BLUE)🛡️ Проверка безопасности...$(NC)"
	@cd frontend && npm audit
	@cd backend && safety check

performance: ## Запустить тесты производительности
	@echo "$(BLUE)⚡ Тесты производительности...$(NC)"
	@cd backend && python -m pytest tests/test_performance.py -v

docs: ## Сгенерировать документацию
	@echo "$(BLUE)📚 Генерация документации...$(NC)"
	@cd backend && python -m pydoc -w app/
	@cd frontend && npm run build:docs

deploy: build test up ## Полный деплой (сборка + тесты + запуск)
	@echo "$(GREEN)✅ Деплой завершен!$(NC)"

# Специальные команды для Apple Silicon
apple-setup: ## Настройка для Apple Silicon
	@echo "$(BLUE)🍎 Настройка для Apple Silicon M4...$(NC)"
	@echo "export OLLAMA_METAL=1" >> ~/.zshrc
	@echo "export OLLAMA_FLASH_ATTENTION=1" >> ~/.zshrc
	@echo "export OLLAMA_KV_CACHE_TYPE=q8_0" >> ~/.zshrc
	@echo "export OLLAMA_CONTEXT_LENGTH=4096" >> ~/.zshrc
	@echo "export OLLAMA_BATCH_SIZE=512" >> ~/.zshrc
	@echo "export OLLAMA_NUM_PARALLEL=2" >> ~/.zshrc
	@echo "$(GREEN)✅ Переменные окружения добавлены в ~/.zshrc$(NC)"
	@echo "$(YELLOW)Перезапустите терминал или выполните: source ~/.zshrc$(NC)"

# Команды для мониторинга
check-health: ## Проверить здоровье сервисов
	@echo "$(BLUE)🏥 Проверка здоровья сервисов...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)❌ Backend недоступен$(NC)"
	@curl -f http://localhost:3000 || echo "$(RED)❌ Frontend недоступен$(NC)"
	@curl -f http://localhost:11434/api/tags || echo "$(RED)❌ Ollama недоступен$(NC)"

# Команды для разработки
watch: ## Запустить в режиме наблюдения
	@echo "$(BLUE)👀 Режим наблюдения...$(NC)"
	@cd frontend && npm run dev &
	@cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Информационные команды
info: ## Показать информацию о проекте
	@echo "$(BLUE)📋 Информация о проекте:$(NC)"
	@echo "  Версия: 4.1.1"
	@echo "  Python: 3.11+"
	@echo "  Node.js: 18+"
	@echo "  Docker: готов"
	@echo "  Apple Silicon: оптимизирован"
	@echo ""
	@echo "$(YELLOW)Порты:$(NC)"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend: http://localhost:8000"
	@echo "  Ollama: http://localhost:11434"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana: http://localhost:3001"

version: ## Показать версию
	@echo "reLink v4.1.1 - AI-Powered SEO Platform"
	@echo "Оптимизирован для Apple Silicon M4" 