# Makefile для управления reLink проектом
# Оптимизирован для MacBook Pro M4 16GB

.PHONY: help build up down restart logs clean test analyze-dagorod build-smart build-base-smart chromadb-optimization auto-cleanup cache-stats cache-clean

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

build-smart: ## Умная сборка с кешированием
	@echo "$(GREEN)Умная сборка с кешированием...$(NC)"
	python scripts/smart_docker_cache.py --build-all

build-base-smart: ## Умная сборка базового образа
	@echo "$(GREEN)Умная сборка базового образа...$(NC)"
	python scripts/smart_docker_cache.py --build-base

build-service-smart: ## Умная сборка конкретного сервиса
	@echo "$(GREEN)Умная сборка сервиса...$(NC)"
	@read -p "Введите имя сервиса: " service; \
	python scripts/smart_docker_cache.py --build-service $$service

build-force: ## Принудительная сборка всех сервисов
	@echo "$(RED)Принудительная сборка всех сервисов...$(NC)"
	python scripts/smart_docker_cache.py --build-all --force

cache-stats: ## Показать статистику кеша
	@echo "$(GREEN)Статистика Docker кеша:$(NC)"
	python scripts/smart_docker_cache.py --stats

cache-clean: ## Очистить кеш
	@echo "$(RED)Очистка Docker кеша...$(NC)"
	python scripts/smart_docker_cache.py --clean

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
	$(MAKE) build-smart
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
	@echo "  make build-smart    # Умная сборка с кешированием"
	@echo "  make up            # Запустить все сервисы"
	@echo "  make analyze-dagorod  # Полный анализ dagorod.ru"
	@echo "  make logs          # Показать логи"
	@echo "  make down          # Остановить сервисы"

# 🏗️ АРХИТЕКТУРНЫЕ КОМАНДЫ
detect-arch:
	@echo "🔍 Определение архитектуры..."
	@source scripts/detect-architecture.sh

run-arch: detect-arch
	@echo "🚀 Запуск с автоматическим определением архитектуры..."
	@docker-compose -f 1-docker-compose.yml up -d

build-arch: detect-arch
	@echo "🔨 Сборка с автоматическим определением архитектуры..."
	@docker-compose -f 1-docker-compose.yml build

chromadb-optimization: ## Оптимизация ChromaDB
	@echo "$(GREEN)Оптимизация ChromaDB...$(NC)"
	python scripts/smart_docker_cache.py --chromadb-optimization

auto-cleanup: ## Автоматическая очистка коллекций ChromaDB
	@echo "$(GREEN)Автоматическая очистка коллекций ChromaDB...$(NC)"
	python scripts/smart_docker_cache.py --auto-cleanup

# Команды для управления ChromaDB
chromadb-status: ## Статус ChromaDB
	@echo "$(GREEN)Статус ChromaDB:$(NC)"
	@curl -s http://localhost:8001/api/v1/rag/collections | jq . || echo "$(RED)ChromaDB недоступен$(NC)"

chromadb-cleanup: ## Очистка старых коллекций ChromaDB
	@echo "$(GREEN)Очистка старых коллекций ChromaDB...$(NC)"
	@curl -X POST http://localhost:8001/api/v1/rag/cleanup | jq . || echo "$(RED)Ошибка очистки$(NC)"

chromadb-stats: ## Статистика ChromaDB
	@echo "$(GREEN)Статистика ChromaDB:$(NC)"
	@curl -s http://localhost:8001/api/v1/stats | jq . || echo "$(RED)ChromaDB недоступен$(NC)"

# Команды для тестирования RAG
test-rag-add: ## Тест добавления документов в RAG
	@echo "$(GREEN)Тест добавления документов в RAG...$(NC)"
	@curl -X POST "http://localhost:8001/api/v1/rag/add?collection=test" \
		-H "Content-Type: application/json" \
		-d '[{"text": "SEO оптимизация важна для ранжирования сайтов", "metadata": {"source": "test", "type": "seo"}}]' | jq .

test-rag-search: ## Тест поиска в RAG
	@echo "$(GREEN)Тест поиска в RAG...$(NC)"
	@curl -X POST "http://localhost:8001/api/v1/rag/search" \
		-H "Content-Type: application/json" \
		-d '{"query": "SEO оптимизация", "collection": "test", "top_k": 5}' | jq .

test-rag-collections: ## Тест получения коллекций
	@echo "$(GREEN)Тест получения коллекций...$(NC)"
	@curl -s http://localhost:8001/api/v1/rag/collections | jq .

# Команды для разработки
dev-setup: ## Настройка для разработки
	@echo "$(GREEN)Настройка для разработки...$(NC)"
	@chmod +x scripts/*.py
	@chmod +x scripts/*.sh
	@echo "$(GREEN)Настройка завершена$(NC)"

quick-test: ## Быстрый тест системы
	@echo "$(GREEN)Быстрый тест системы...$(NC)"
	@make health
	@make test-rag-collections
	@make test-rag-add
	@make test-rag-search

# Команды для анализа
analyze-dagorod: ## Анализ DAGOROD
	@echo "$(GREEN)Анализ DAGOROD...$(NC)"
	@python backend/advanced_seo_benchmark.py

# Команды для развертывания
deploy: ## Развертывание
	@echo "$(GREEN)Развертывание...$(NC)"
	@make build-smart
	@make up
	@make health

deploy-force: ## Принудительное развертывание
	@echo "$(GREEN)Принудительное развертывание...$(NC)"
	@python scripts/smart_docker_cache.py --build-all --force
	@make up
	@make health