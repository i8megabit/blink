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

# Конфигурация
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/config/docker-compose.yml"

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

# Функции логирования
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
    
    if [ -f "${SCRIPT_DIR}/docker-buildkit.env" ]; then
        source "${SCRIPT_DIR}/docker-buildkit.env"
        log_success "BuildKit конфигурация загружена"
    else
        log_warning "Файл docker-buildkit.env не найден, используем дефолтные настройки"
        export DOCKER_BUILDKIT=1
        export COMPOSE_DOCKER_CLI_BUILD=1
    fi
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

# Функция для показа справки
show_help() {
    echo -e "${BLUE}🚀 Профессиональный Docker Build Скрипт${NC}"
    echo ""
    echo "Использование: $0 [ОПЦИИ]"
    echo ""
    echo "Опции:"
    echo "  -s, --service SERVICE    Сборка конкретного сервиса"
    echo "  -n, --no-cache          Сборка без кеша"
    echo "  -p, --no-pull           Не pull базовые образы"
    echo "  -c, --cleanup           Очистка Docker после сборки"
    echo "  -f, --force-cleanup     Принудительная очистка"
    echo "  -a, --analyze           Анализ образов после сборки"
    echo "  -h, --health-check      Проверка здоровья после запуска"
    echo "  -u, --up                Запуск сервисов после сборки"
    echo "  -d, --down              Остановка сервисов перед сборкой"
    echo "  --help                  Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0                      # Полная сборка с BuildKit"
    echo "  $0 -s backend           # Сборка только backend"
    echo "  $0 -n -c                # Сборка без кеша + очистка"
    echo "  $0 -u -h                # Сборка + запуск + проверка здоровья"
}

# Основная функция
main() {
    local service=""
    local no_cache=false
    local no_pull=false
    local cleanup=false
    local force_cleanup=false
    local analyze=false
    local health_check_flag=false
    local up=false
    local down=false
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--service)
                service="$2"
                shift 2
                ;;
            -n|--no-cache)
                no_cache=true
                shift
                ;;
            -p|--no-pull)
                no_pull=true
                shift
                ;;
            -c|--cleanup)
                cleanup=true
                shift
                ;;
            -f|--force-cleanup)
                force_cleanup=true
                shift
                ;;
            -a|--analyze)
                analyze=true
                shift
                ;;
            -h|--health-check)
                health_check_flag=true
                shift
                ;;
            -u|--up)
                up=true
                shift
                ;;
            -d|--down)
                down=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Неизвестная опция: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Начало работы
    echo -e "${BLUE}🚀 Запуск профессиональной сборки Docker${NC}"
    echo "=================================="
    
    # Проверка зависимостей
    check_dependencies
    
    # Загрузка конфигурации BuildKit
    load_buildkit_config
    
    # Остановка сервисов если нужно
    if [ "$down" = true ]; then
        log_info "Остановка сервисов..."
        docker-compose -f "$COMPOSE_FILE" down
    fi
    
    # Pull базовых образов
    if [ "$no_pull" = false ]; then
        pull_base_images
    fi
    
    # Сборка
    build_with_buildkit "$service" "$no_cache" "$no_pull"
    
    # Анализ образов
    if [ "$analyze" = true ]; then
        analyze_images
    fi
    
    # Очистка
    if [ "$cleanup" = true ] || [ "$force_cleanup" = true ]; then
        cleanup_docker "$force_cleanup"
    fi
    
    # Запуск сервисов
    if [ "$up" = true ]; then
        log_info "Запуск сервисов..."
        docker-compose -f "$COMPOSE_FILE" up -d
        
        # Проверка здоровья
        if [ "$health_check_flag" = true ]; then
            health_check
        fi
    fi
    
    log_success "🎉 Профессиональная сборка завершена!"
}

# Запуск основной функции
main "$@" 