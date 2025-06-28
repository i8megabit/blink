#!/bin/bash

# 🚀 Скрипт для запуска бенчмарков производительности LLM Tuning Microservice

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
BASE_URL=${BASE_URL:-"http://localhost:8000"}
PYTHON_CMD=${PYTHON_CMD:-"python3"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Функции
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_service() {
    print_info "Проверка доступности сервиса..."
    if curl -f -s "$BASE_URL/health" > /dev/null; then
        print_success "Сервис доступен"
        return 0
    else
        print_error "Сервис недоступен по адресу $BASE_URL"
        print_warning "Убедитесь, что сервис запущен: make run"
        return 1
    fi
}

install_dependencies() {
    print_info "Проверка зависимостей..."
    local missing_deps=()
    
    if ! python3 -c "import aiohttp" 2>/dev/null; then
        missing_deps+=("aiohttp")
    fi
    
    if ! python3 -c "import psutil" 2>/dev/null; then
        missing_deps+=("psutil")
    fi
    
    if ! python3 -c "import matplotlib" 2>/dev/null; then
        missing_deps+=("matplotlib")
    fi
    
    if ! python3 -c "import numpy" 2>/dev/null; then
        missing_deps+=("numpy")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_warning "Отсутствуют зависимости: ${missing_deps[*]}"
        read -p "Установить зависимости? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Установка зависимостей..."
            pip3 install "${missing_deps[@]}"
            print_success "Зависимости установлены"
        else
            print_error "Зависимости не установлены. Запуск невозможен."
            exit 1
        fi
    else
        print_success "Все зависимости установлены"
    fi
}

run_benchmark() {
    local benchmark_name=$1
    local num_requests=${2:-100}
    
    print_header "Запуск бенчмарка: $benchmark_name"
    print_info "Количество запросов: $num_requests"
    
    cd "$SCRIPT_DIR"
    if $PYTHON_CMD performance_test.py "$benchmark_name" "$num_requests"; then
        print_success "Бенчмарк $benchmark_name завершен успешно"
    else
        print_error "Бенчмарк $benchmark_name завершился с ошибкой"
        return 1
    fi
}

run_full_benchmark() {
    print_header "Запуск полного бенчмарка"
    
    cd "$SCRIPT_DIR"
    if $PYTHON_CMD performance_test.py; then
        print_success "Полный бенчмарк завершен успешно"
    else
        print_error "Полный бенчмарк завершился с ошибкой"
        return 1
    fi
}

show_results() {
    print_header "Результаты бенчмарков"
    
    if [ -f "$SCRIPT_DIR/benchmark_report.txt" ]; then
        echo -e "${GREEN}📄 Отчет:${NC}"
        cat "$SCRIPT_DIR/benchmark_report.txt"
        echo
    fi
    
    if [ -f "$SCRIPT_DIR/benchmark_results.png" ]; then
        print_success "📊 Графики сохранены в: $SCRIPT_DIR/benchmark_results.png"
    fi
}

clean_results() {
    print_info "Очистка результатов бенчмарков..."
    rm -f "$SCRIPT_DIR/benchmark_report.txt"
    rm -f "$SCRIPT_DIR/benchmark_results.png"
    print_success "Результаты очищены"
}

show_help() {
    cat << EOF
🚀 Скрипт для запуска бенчмарков производительности

Использование: $0 [КОМАНДА] [ПАРАМЕТРЫ]

Команды:
    full                    Запуск всех бенчмарков
    ab-testing [N]         Бенчмарк A/B тестирования (N запросов, по умолчанию 100)
    optimization [N]       Бенчмарк оптимизации (N запросов, по умолчанию 50)
    quality [N]            Бенчмарк оценки качества (N запросов, по умолчанию 100)
    health [N]             Бенчмарк мониторинга здоровья (N запросов, по умолчанию 200)
    stats [N]              Бенчмарк расширенной статистики (N запросов, по умолчанию 100)
    stress                 Стресс-тестирование (1000+ запросов)
    quick                  Быстрый бенчмарк (минимальное количество запросов)
    check                  Проверка сервиса и зависимостей
    install-deps           Установка зависимостей
    clean                  Очистка результатов
    results                Показать результаты
    help                   Показать эту справку

Переменные окружения:
    BASE_URL               URL сервиса (по умолчанию: http://localhost:8000)
    PYTHON_CMD             Команда Python (по умолчанию: python3)

Примеры:
    $0 full                    # Полный бенчмарк
    $0 ab-testing 50          # A/B тестирование с 50 запросами
    $0 stress                 # Стресс-тестирование
    $0 check                  # Проверка готовности
    BASE_URL=http://prod:8000 $0 full  # Бенчмарк продакшн сервера

EOF
}

# Основная логика
main() {
    local command=${1:-help}
    
    case $command in
        full)
            check_service
            install_dependencies
            run_full_benchmark
            show_results
            ;;
        ab-testing)
            check_service
            install_dependencies
            run_benchmark "ab_testing" "$2"
            ;;
        optimization)
            check_service
            install_dependencies
            run_benchmark "optimization" "$2"
            ;;
        quality)
            check_service
            install_dependencies
            run_benchmark "quality_assessment" "$2"
            ;;
        health)
            check_service
            install_dependencies
            run_benchmark "system_health" "$2"
            ;;
        stats)
            check_service
            install_dependencies
            run_benchmark "extended_stats" "$2"
            ;;
        stress)
            check_service
            install_dependencies
            print_header "Стресс-тестирование"
            run_benchmark "system_health" 1000
            run_benchmark "extended_stats" 500
            show_results
            ;;
        quick)
            check_service
            install_dependencies
            print_header "Быстрый бенчмарк"
            run_benchmark "ab_testing" 10
            run_benchmark "quality_assessment" 20
            show_results
            ;;
        check)
            check_service
            install_dependencies
            print_success "Система готова к запуску бенчмарков"
            ;;
        install-deps)
            install_dependencies
            ;;
        clean)
            clean_results
            ;;
        results)
            show_results
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Неизвестная команда: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Обработка сигналов
trap 'print_error "Бенчмарк прерван пользователем"; exit 1' INT TERM

# Запуск
main "$@" 