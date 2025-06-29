#!/bin/bash

# 🔧 Скрипт проверки исправлений ChromaDB
# Проверяет корректность конфигурации и работоспособность сервиса

set -e

echo "🔍 Проверка исправлений ChromaDB..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
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

# Проверка 1: Статус контейнера ChromaDB
check_container_status() {
    log_info "Проверка статуса контейнера ChromaDB..."
    
    if docker-compose ps chromadb | grep -q "Up"; then
        log_success "Контейнер ChromaDB запущен"
    else
        log_error "Контейнер ChromaDB не запущен"
        return 1
    fi
}

# Проверка 2: Health Check
check_health_check() {
    log_info "Проверка Health Check..."
    
    # Проверка через curl
    if curl -f http://localhost:8006/api/v1/heartbeat > /dev/null 2>&1; then
        log_success "Health Check эндпоинт отвечает"
    else
        log_error "Health Check эндпоинт не отвечает"
        return 1
    fi
    
    # Проверка логов health check
    if docker-compose logs chromadb 2>&1 | grep -q "health check"; then
        log_success "Health Check логи найдены"
    else
        log_warning "Health Check логи не найдены (возможно, еще не было проверок)"
    fi
}

# Проверка 3: Переменные окружения
check_environment_variables() {
    log_info "Проверка переменных окружения..."
    
    # Проверка основных переменных
    local env_vars=(
        "CHROMA_SERVER_HOST=0.0.0.0"
        "CHROMA_SERVER_HTTP_PORT=8000"
        "ANONYMIZED_TELEMETRY=False"
        "CHROMA_SERVER_OTEL_ENABLED=True"
    )
    
    for var in "${env_vars[@]}"; do
        local key="${var%=*}"
        local expected_value="${var#*=}"
        local actual_value=$(docker-compose exec -T chromadb env | grep "^$key=" | cut -d'=' -f2-)
        
        if [ "$actual_value" = "$expected_value" ]; then
            log_success "Переменная $key установлена правильно: $actual_value"
        else
            log_error "Переменная $key неверная: ожидалось '$expected_value', получено '$actual_value'"
        fi
    done
}

# Проверка 4: OpenTelemetry
check_opentelemetry() {
    log_info "Проверка настроек OpenTelemetry..."
    
    local otel_enabled=$(docker-compose exec -T chromadb env | grep "CHROMA_SERVER_OTEL_ENABLED" | cut -d'=' -f2)
    local otel_endpoint=$(docker-compose exec -T chromadb env | grep "CHROMA_SERVER_OTEL_ENDPOINT" | cut -d'=' -f2)
    local otel_service=$(docker-compose exec -T chromadb env | grep "CHROMA_SERVER_OTEL_SERVICE_NAME" | cut -d'=' -f2)
    
    if [ "$otel_enabled" = "True" ]; then
        log_success "OpenTelemetry включен"
    else
        log_error "OpenTelemetry не включен"
    fi
    
    if [ -n "$otel_endpoint" ]; then
        log_success "OpenTelemetry endpoint: $otel_endpoint"
    else
        log_error "OpenTelemetry endpoint не установлен"
    fi
    
    if [ -n "$otel_service" ]; then
        log_success "OpenTelemetry service name: $otel_service"
    else
        log_error "OpenTelemetry service name не установлен"
    fi
}

# Проверка 5: Подключение через Python
check_python_connection() {
    log_info "Проверка подключения через Python..."
    
    python3 -c "
import chromadb
try:
    client = chromadb.HttpClient(host='localhost', port=8006)
    heartbeat = client.heartbeat()
    print('✅ ChromaDB подключен успешно')
    print(f'   Heartbeat: {heartbeat}')
except Exception as e:
    print(f'❌ Ошибка подключения к ChromaDB: {e}')
    exit(1)
" 2>/dev/null || {
    log_error "Не удалось подключиться к ChromaDB через Python"
    return 1
}
}

# Проверка 6: Конфигурация docker-compose
check_docker_compose_config() {
    log_info "Проверка конфигурации docker-compose.yml..."
    
    # Проверка health check команды
    if grep -q 'curl.*api/v1/heartbeat' docker-compose.yml; then
        log_success "Health check использует правильный curl эндпоинт"
    else
        log_error "Health check не использует правильный curl эндпоинт"
        return 1
    fi
    
    # Проверка отсутствия nc команды
    if ! grep -q 'nc -z localhost' docker-compose.yml; then
        log_success "Команда nc не используется в health check"
    else
        log_warning "Команда nc все еще используется где-то в конфигурации"
    fi
    
    # Проверка настроек OpenTelemetry
    if grep -q 'CHROMA_SERVER_OTEL_ENABLED=True' docker-compose.yml; then
        log_success "OpenTelemetry включен в конфигурации"
    else
        log_error "OpenTelemetry не включен в конфигурации"
        return 1
    fi
}

# Проверка 7: Логи ошибок
check_error_logs() {
    log_info "Проверка логов на наличие ошибок..."
    
    local error_count=$(docker-compose logs chromadb 2>&1 | grep -i "error\|failed\|exception" | wc -l)
    
    if [ "$error_count" -eq 0 ]; then
        log_success "Ошибок в логах не найдено"
    else
        log_warning "Найдено $error_count ошибок в логах"
        docker-compose logs chromadb 2>&1 | grep -i "error\|failed\|exception" | tail -5
    fi
}

# Основная функция
main() {
    echo "🚀 Запуск проверки исправлений ChromaDB..."
    echo "=================================="
    
    local failed_checks=0
    
    # Выполнение всех проверок
    check_container_status || ((failed_checks++))
    check_health_check || ((failed_checks++))
    check_environment_variables || ((failed_checks++))
    check_opentelemetry || ((failed_checks++))
    check_python_connection || ((failed_checks++))
    check_docker_compose_config || ((failed_checks++))
    check_error_logs || ((failed_checks++))
    
    echo "=================================="
    
    if [ $failed_checks -eq 0 ]; then
        log_success "Все проверки пройдены успешно! ChromaDB работает корректно."
        echo ""
        echo "📊 Краткая сводка:"
        echo "   ✅ Контейнер запущен"
        echo "   ✅ Health check работает"
        echo "   ✅ OpenTelemetry настроен"
        echo "   ✅ Python подключение активно"
        echo "   ✅ Конфигурация корректна"
    else
        log_error "Провалено проверок: $failed_checks"
        echo ""
        echo "🔧 Рекомендации:"
        echo "   1. Проверьте логи: docker-compose logs chromadb"
        echo "   2. Перезапустите сервис: docker-compose restart chromadb"
        echo "   3. Проверьте конфигурацию: cat docker-compose.yml | grep -A 20 chromadb"
        exit 1
    fi
}

# Обработка аргументов командной строки
case "${1:-}" in
    --help|-h)
        echo "Использование: $0 [опции]"
        echo ""
        echo "Опции:"
        echo "  --help, -h     Показать эту справку"
        echo "  --verbose, -v  Подробный вывод"
        echo ""
        echo "Примеры:"
        echo "  $0              Запустить все проверки"
        echo "  $0 --verbose    Подробная проверка с выводом логов"
        exit 0
        ;;
    --verbose|-v)
        set -x
        ;;
esac

# Запуск основной функции
main "$@" 