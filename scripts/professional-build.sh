#!/bin/bash

# 🚀 ПРОФЕССИОНАЛЬНЫЙ DOCKER BUILD СКРИПТ
# Автоматизированная сборка с BuildKit, pull базовых образов и оптимизацией

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования (должны быть определены в начале)
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Конфигурация
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/config/docker-compose.yml"
ENV_FILE="${PROJECT_ROOT}/config/docker.env"

# Автоматическая загрузка настроек из docker.env
if [ -f "$ENV_FILE" ]; then
    log_info "Загрузка настроек из $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Базовые образы для pull
BASE_IMAGES=(
    "python:3.11.9-slim-bullseye"
    "node:20.11.1-alpine"
    "nginx:1.25-alpine"
    "postgres:16"
    "redis:7-alpine"
    "ollama/ollama:latest"
    "prom/prometheus:latest"
)

# Функция для проверки зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
    
    # Проверка версии Docker
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d'.' -f1)
    if [ "$DOCKER_VERSION" -lt 20 ]; then
        log_warning "Рекомендуется Docker 20+ для лучшей поддержки BuildKit"
    fi
    
    log_success "Зависимости проверены"
}

# Функция для загрузки BuildKit конфигурации
load_buildkit_config() {
    log_info "Загрузка BuildKit конфигурации..."
    
    # Приоритет: docker.env > docker-buildkit.env > дефолтные настройки
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
        log_success "Настройки загружены из $ENV_FILE"
    elif [ -f "${SCRIPT_DIR}/docker-buildkit.env" ]; then
        source "${SCRIPT_DIR}/docker-buildkit.env"
        log_success "BuildKit конфигурация загружена из docker-buildkit.env"
    else
        log_warning "Файлы конфигурации не найдены, используем дефолтные настройки"
        export DOCKER_BUILDKIT=1
        export COMPOSE_DOCKER_CLI_BUILD=1
    fi
    
    # Проверка и вывод текущих настроек
    log_info "Текущие настройки BuildKit:"
    log_info "  DOCKER_BUILDKIT: ${DOCKER_BUILDKIT:-не установлен}"
    log_info "  COMPOSE_DOCKER_CLI_BUILD: ${COMPOSE_DOCKER_CLI_BUILD:-не установлен}"
    log_info "  COMPOSE_FILE: ${COMPOSE_FILE:-не установлен}"
}

# Функция для pull базовых образов
pull_base_images() {
    log_info "Pull базовых образов..."
    
    for image in "${BASE_IMAGES[@]}"; do
        log_info "Pull $image..."
        if docker pull "$image" > /dev/null 2>&1; then
            log_success "✅ $image"
        else
            log_warning "⚠️  Не удалось pull $image (возможно, уже есть локально)"
        fi
    done
    
    log_success "Pull базовых образов завершен"
}

# Функция для очистки Docker
cleanup_docker() {
    local force=${1:-false}
    
    if [ "$force" = true ]; then
        log_info "Принудительная очистка Docker..."
        docker system prune -af
        docker builder prune -af
    else
        log_info "Очистка неиспользуемых Docker ресурсов..."
        docker system prune -f
        docker builder prune -f
    fi
    
    log_success "Очистка завершена"
}

# Функция для сборки с BuildKit
build_with_buildkit() {
    local service=${1:-""}
    local no_cache=${2:-false}
    local pull=${3:-true}
    
    log_info "Сборка с BuildKit..."
    
    # Подготовка команды
    local cmd="docker-compose -f $COMPOSE_FILE build"
    
    if [ -n "$service" ]; then
        cmd="$cmd $service"
        log_info "Сборка сервиса: $service"
    fi
    
    if [ "$no_cache" = true ]; then
        cmd="$cmd --no-cache"
        log_info "Сборка без кеша"
    fi
    
    if [ "$pull" = true ]; then
        cmd="$cmd --pull"
        log_info "Сборка с pull базовых образов"
    fi
    
    # Выполнение сборки
    log_info "Выполнение: $cmd"
    if eval "$cmd"; then
        log_success "Сборка завершена успешно"
    else
        log_error "Ошибка сборки"
        exit 1
    fi
}

# Функция для анализа образов
analyze_images() {
    log_info "Анализ Docker образов..."
    
    echo -e "\n${BLUE}📊 Размеры образов:${NC}"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "(relink|eberil)"
    
    echo -e "\n${BLUE}📊 Использование диска:${NC}"
    docker system df
    
    log_success "Анализ завершен"
}

# Функция для проверки здоровья сервисов
health_check() {
    log_info "Проверка здоровья сервисов..."
    
    # Ждем запуска сервисов
    sleep 10
    
    # Проверяем основные сервисы
    local services=("backend" "frontend" "docs" "testing")
    
    for service in "${services[@]}"; do
        log_info "Проверка $service..."
        
        # Получаем порт сервиса
        local port=""
        case $service in
            "backend") port="8000" ;;
            "frontend") port="3000" ;;
            "docs") port="8001" ;;
            "testing") port="8003" ;;
        esac
        
        if [ -n "$port" ]; then
            if curl -f "http://localhost:$port/health" > /dev/null 2>&1 || \
               curl -f "http://localhost:$port/api/v1/health" > /dev/null 2>&1 || \
               curl -f "http://localhost:$port/" > /dev/null 2>&1; then
                log_success "✅ $service (порт $port)"
            else
                log_warning "⚠️  $service (порт $port) - не отвечает"
            fi
        fi
    done
}

# Функция для запуска сервисов
start_services() {
    log_info "Запуск сервисов..."
    
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        log_success "Сервисы запущены"
    else
        log_error "Ошибка запуска сервисов"
        exit 1
    fi
}

# Функция для остановки сервисов
stop_services() {
    log_info "Остановка сервисов..."
    
    if docker-compose -f "$COMPOSE_FILE" down; then
        log_success "Сервисы остановлены"
    else
        log_error "Ошибка остановки сервисов"
        exit 1
    fi
}

# Функция для перезапуска сервисов
restart_services() {
    log_info "Перезапуск сервисов..."
    stop_services
    start_services
    log_success "Сервисы перезапущены"
}

# Функция для просмотра логов
show_logs() {
    local service=${1:-""}
    
    if [ -n "$service" ]; then
        log_info "Логи сервиса $service..."
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        log_info "Логи всех сервисов..."
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Главная функция
main() {
    local command=${1:-"help"}
    
    case $command in
        "help"|"-h"|"--help")
            echo -e "${BLUE}🚀 reLink Professional Build Script${NC}"
            echo ""
            echo -e "${GREEN}Команды:${NC}"
            echo "  build [service]     - Сборка всех сервисов или конкретного сервиса"
            echo "  build-no-cache      - Сборка без кеша"
            echo "  pull                - Pull базовых образов"
            echo "  up                  - Запуск сервисов"
            echo "  down                - Остановка сервисов"
            echo "  restart             - Перезапуск сервисов"
            echo "  logs [service]      - Просмотр логов"
            echo "  health              - Проверка здоровья сервисов"
            echo "  analyze             - Анализ Docker образов"
            echo "  cleanup             - Очистка Docker ресурсов"
            echo "  cleanup-force       - Принудительная очистка"
            echo "  quick-start         - Быстрый старт (сборка + запуск + проверка)"
            echo "  dev                 - Режим разработки (пересборка + логи)"
            echo "  prod                - Продакшн режим (с проверками)"
            echo ""
            echo -e "${GREEN}Примеры:${NC}"
            echo "  $0 build backend    - Сборка только backend"
            echo "  $0 build-no-cache   - Сборка без кеша"
            echo "  $0 logs backend     - Логи только backend"
            echo "  $0 quick-start      - Полный цикл запуска"
            ;;
        "build")
            check_dependencies
            load_buildkit_config
            pull_base_images
            build_with_buildkit "${2:-}" false true
            analyze_images
            ;;
        "build-no-cache")
            check_dependencies
            load_buildkit_config
            pull_base_images
            build_with_buildkit "${2:-}" true true
            analyze_images
            ;;
        "pull")
            check_dependencies
            pull_base_images
            ;;
        "up")
            check_dependencies
            load_buildkit_config
            start_services
            ;;
        "down")
            check_dependencies
            stop_services
            ;;
        "restart")
            check_dependencies
            load_buildkit_config
            restart_services
            ;;
        "logs")
            check_dependencies
            show_logs "${2:-}"
            ;;
        "health")
            check_dependencies
            health_check
            ;;
        "analyze")
            check_dependencies
            analyze_images
            ;;
        "cleanup")
            check_dependencies
            cleanup_docker false
            ;;
        "cleanup-force")
            check_dependencies
            cleanup_docker true
            ;;
        "quick-start")
            check_dependencies
            load_buildkit_config
            pull_base_images
            build_with_buildkit "" false true
            start_services
            health_check
            analyze_images
            log_success "🚀 Система готова к работе!"
            ;;
        "dev")
            check_dependencies
            load_buildkit_config
            build_with_buildkit "" true true
            start_services
            show_logs
            ;;
        "prod")
            check_dependencies
            load_buildkit_config
            pull_base_images
            build_with_buildkit "" false true
            start_services
            health_check
            analyze_images
            log_success "🚀 Продакшн система развернута!"
            ;;
        *)
            log_error "Неизвестная команда: $command"
            echo "Используйте '$0 help' для справки"
            exit 1
            ;;
    esac
}

# Запуск главной функции
main "$@" 