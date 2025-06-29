# Makefile для управления reLink проектом
# Оптимизирован для MacBook Pro M4 16GB

.PHONY: help build up down restart logs clean test analyze-dagorod

# Переменные
COMPOSE_FILE = 1-docker-compose.yml
PROJECT_NAME = relink

# Цвета для вывода
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)reLink - Система анализа и оптимизации внутренних ссылок$(NC)"
	@echo ""
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

build: ## Собрать все контейнеры
	@echo "$(GREEN)Собираем контейнеры...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build --parallel

up: ## Запустить все сервисы
	@echo "$(GREEN)Запускаем сервисы...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)Сервисы запущены!$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Relink API: http://localhost:8001$(NC)"
	@echo "$(YELLOW)Ollama: http://localhost:11434$(NC)"

down: ## Остановить все сервисы
	@echo "$(RED)Останавливаем сервисы...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down

restart: down up ## Перезапустить сервисы

logs: ## Показать логи всех сервисов
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-relink: ## Показать логи сервиса relink
	docker-compose -f $(COMPOSE_FILE) logs -f relink

logs-backend: ## Показать логи backend
	docker-compose -f $(COMPOSE_FILE) logs -f backend

logs-frontend: ## Показать логи frontend
	docker-compose -f $(COMPOSE_FILE) logs -f frontend

clean: ## Очистить все контейнеры и образы
	@echo "$(RED)Очищаем все контейнеры и образы...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down -v --rmi all
	docker system prune -f

# Команды для тестирования
test: ## Запустить все тесты
	@echo "$(GREEN)Запускаем тесты...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec backend python -m pytest tests/ -v
	docker-compose -f $(COMPOSE_FILE) exec frontend npm test

test-relink: ## Тестировать сервис relink
	@echo "$(GREEN)Тестируем сервис relink...$(NC)"
	@echo "$(YELLOW)Проверяем health check...$(NC)"
	curl -f http://localhost:8001/api/v1/health || echo "$(RED)Сервис relink недоступен$(NC)"
	@echo "$(YELLOW)Получаем список эндпоинтов...$(NC)"
	curl -s http://localhost:8001/api/v1/endpoints | jq .

# Команды для анализа dagorod.ru
analyze-dagorod: ## Полный анализ домена dagorod.ru
	@echo "$(GREEN)Запускаем полный анализ dagorod.ru...$(NC)"
	@echo "$(YELLOW)1. Индексируем домен...$(NC)"
	curl -X POST http://localhost:8001/api/v1/index-domain -H "Content-Type: application/json" -d '{"domain": "dagorod.ru"}'
	@echo ""
	@echo "$(YELLOW)2. Анализируем домен...$(NC)"
	curl -X POST http://localhost:8001/api/v1/analyze-domain -H "Content-Type: application/json" -d '{"domain": "dagorod.ru", "include_posts": true, "include_recommendations": true}' | jq .
	@echo ""
	@echo "$(YELLOW)3. Генерируем рекомендации...$(NC)"
	curl -X POST http://localhost:8001/api/v1/generate-recommendations -H "Content-Type: application/json" -d '{"domain": "dagorod.ru", "focus_areas": ["internal_linking", "content_optimization", "technical_seo"], "priority": "high"}' | jq .

index-dagorod: ## Индексировать домен dagorod.ru
	@echo "$(GREEN)Индексируем домен dagorod.ru...$(NC)"
	curl -X POST http://localhost:8001/api/v1/index-domain -H "Content-Type: application/json" -d '{"domain": "dagorod.ru"}' | jq .

status-dagorod: ## Проверить статус индексации dagorod.ru
	@echo "$(GREEN)Проверяем статус индексации dagorod.ru...$(NC)"
	curl -s http://localhost:8001/api/v1/indexing-status/dagorod.ru | jq .

get-posts-dagorod: ## Получить проиндексированные посты dagorod.ru
	@echo "$(GREEN)Получаем посты dagorod.ru...$(NC)"
	curl -s http://localhost:8001/api/v1/posts/dagorod.ru | jq .

get-links-dagorod: ## Получить внутренние ссылки dagorod.ru
	@echo "$(GREEN)Получаем внутренние ссылки dagorod.ru...$(NC)"
	curl -s http://localhost:8001/api/v1/internal-links/dagorod.ru | jq .

dashboard-dagorod: ## Получить данные дашборда для dagorod.ru
	@echo "$(GREEN)Получаем данные дашборда dagorod.ru...$(NC)"
	curl -s http://localhost:8001/api/v1/dashboard/dagorod.ru | jq .

# Команды для мониторинга
monitor: ## Показать статус всех сервисов
	@echo "$(GREEN)Статус сервисов:$(NC)"
	docker-compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "$(YELLOW)Использование ресурсов:$(NC)"
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

health: ## Проверить здоровье всех сервисов
	@echo "$(GREEN)Проверяем здоровье сервисов...$(NC)"
	@echo "$(YELLOW)Frontend:$(NC)"
	curl -f http://localhost:3000 || echo "$(RED)Frontend недоступен$(NC)"
	@echo "$(YELLOW)Backend:$(NC)"
	curl -f http://localhost:8000/health || echo "$(RED)Backend недоступен$(NC)"
	@echo "$(YELLOW)Relink:$(NC)"
	curl -f http://localhost:8001/api/v1/health || echo "$(RED)Relink недоступен$(NC)"
	@echo "$(YELLOW)Ollama:$(NC)"
	curl -f http://localhost:11434/api/tags || echo "$(RED)Ollama недоступен$(NC)"

# Команды для разработки
dev: ## Запустить в режиме разработки
	@echo "$(GREEN)Запускаем в режиме разработки...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d redis postgres ollama
	@echo "$(YELLOW)Запустите сервисы разработки отдельно:$(NC)"
	@echo "  Backend: cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
	@echo "  Frontend: cd frontend && npm run dev"
	@echo "  Relink: cd relink && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"

# Команды для базы данных
db-init: ## Инициализировать базу данных
	@echo "$(GREEN)Инициализируем базу данных...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec postgres psql -U postgres -d relink -f /docker-entrypoint-initdb.d/init-db.sql

db-reset: ## Сбросить базу данных
	@echo "$(RED)Сбрасываем базу данных...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down -v
	docker-compose -f $(COMPOSE_FILE) up -d postgres
	sleep 5
	$(MAKE) db-init

# Команды для экспорта
export-dagorod: ## Экспортировать анализ dagorod.ru
	@echo "$(GREEN)Экспортируем анализ dagorod.ru...$(NC)"
	@echo "$(YELLOW)JSON формат:$(NC)"
	curl -s http://localhost:8001/api/v1/export-analysis/dagorod.ru?format=json > dagorod_analysis.json
	@echo "$(YELLOW)CSV формат:$(NC)"
	curl -s http://localhost:8001/api/v1/export-analysis/dagorod.ru?format=csv > dagorod_analysis.csv
	@echo "$(GREEN)Экспорт завершен!$(NC)"

# Команды для бенчмаркинга
benchmark: ## Запустить бенчмарк
	@echo "$(GREEN)Запускаем бенчмарк...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec benchmark python benchmark.py

# Команды для обновления
update: ## Обновить все сервисы
	@echo "$(GREEN)Обновляем сервисы...$(NC)"
	git pull
	docker-compose -f $(COMPOSE_FILE) pull
	$(MAKE) build
	$(MAKE) restart

# Команды для отладки
debug: ## Включить режим отладки
	@echo "$(GREEN)Включаем режим отладки...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down
	LOG_LEVEL=DEBUG docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(YELLOW)Логи с отладкой:$(NC)"
	$(MAKE) logs

# Команды для производительности
performance: ## Проверить производительность
	@echo "$(GREEN)Проверяем производительность...$(NC)"
	@echo "$(YELLOW)Тест нагрузки на relink API:$(NC)"
	ab -n 100 -c 10 http://localhost:8001/api/v1/health
	@echo "$(YELLOW)Использование памяти:$(NC)"
	docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"

# Информационные команды
info: ## Показать информацию о проекте
	@echo "$(GREEN)reLink - Система анализа и оптимизации внутренних ссылок$(NC)"
	@echo ""
	@echo "$(YELLOW)Архитектура:$(NC)"
	@echo "  • Frontend: React + TypeScript + Tailwind CSS"
	@echo "  • Backend: FastAPI + SQLAlchemy + PostgreSQL"
	@echo "  • Relink: FastAPI + AI/ML интеграция"
	@echo "  • LLM: Ollama + RAG"
	@echo "  • Кеширование: Redis"
	@echo "  • Мониторинг: Prometheus + Grafana"
	@echo ""
	@echo "$(YELLOW)Основные эндпоинты:$(NC)"
	@echo "  • /api/v1/index-domain - Индексация домена"
	@echo "  • /api/v1/analyze-domain - Анализ домена"
	@echo "  • /api/v1/generate-recommendations - Генерация рекомендаций"
	@echo "  • /api/v1/dashboard/{domain} - Данные дашборда"
	@echo ""
	@echo "$(YELLOW)Быстрый старт:$(NC)"
	@echo "  make up          # Запустить все сервисы"
	@echo "  make analyze-dagorod  # Полный анализ dagorod.ru"
	@echo "  make logs        # Показать логи"
	@echo "  make down        # Остановить сервисы"