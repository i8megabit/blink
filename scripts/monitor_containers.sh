#!/bin/bash

# 🚀 Скрипт мониторинга контейнеров reLink
# Диагностика проблем с рестартующимися контейнерами

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для логирования
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

log_debug() {
    echo -e "${CYAN}🔍 $1${NC}"
}

# Проверяем, что Docker запущен
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker не запущен или недоступен"
        exit 1
    fi
    log_success "Docker доступен"
}

# Получаем статус всех контейнеров reLink
get_container_status() {
    log_info "Получение статуса контейнеров reLink..."
    
    echo ""
    echo "📊 СТАТУС КОНТЕЙНЕРОВ"
    echo "===================="
    
    docker ps -a --filter "name=relink" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Size}}" | head -1
    docker ps -a --filter "name=relink" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Size}}" | tail -n +2 | sort
    
    echo ""
}

# Проверяем контейнеры с проблемами
check_problematic_containers() {
    log_info "Проверка проблемных контейнеров..."
    
    local problematic_containers=$(docker ps -a --filter "name=relink" --filter "status=exited" --format "{{.Names}}")
    
    if [ -n "$problematic_containers" ]; then
        log_warning "Найдены остановленные контейнеры:"
        echo "$problematic_containers" | while read container; do
            echo "  - $container"
        done
        echo ""
    else
        log_success "Все контейнеры работают"
    fi
}

# Анализируем логи контейнера
analyze_container_logs() {
    local container_name=$1
    local lines=${2:-50}
    
    log_info "Анализ логов контейнера: $container_name (последние $lines строк)"
    
    if docker ps -q -f name="$container_name" | grep -q .; then
        echo ""
        echo "📋 ЛОГИ $container_name"
        echo "=================="
        docker logs --tail $lines "$container_name" 2>&1 | head -20
        echo ""
    else
        log_warning "Контейнер $container_name не найден или не запущен"
    fi
}

# Проверяем ресурсы системы
check_system_resources() {
    log_info "Проверка системных ресурсов..."
    
    echo ""
    echo "💻 СИСТЕМНЫЕ РЕСУРСЫ"
    echo "==================="
    
    # CPU
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    echo "CPU: ${cpu_usage}%"
    
    # Память
    local memory_info=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    local total_memory=$(sysctl hw.memsize | awk '{print $2}')
    local free_memory=$((memory_info * 4096))
    local used_memory=$((total_memory - free_memory))
    local memory_percent=$((used_memory * 100 / total_memory))
    echo "Память: ${memory_percent}% (используется $((used_memory / 1024 / 1024))MB из $((total_memory / 1024 / 1024))MB)"
    
    # Диск
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    echo "Диск: ${disk_usage}%"
    
    echo ""
}

# Проверяем сетевые соединения
check_network_connections() {
    log_info "Проверка сетевых соединений..."
    
    echo ""
    echo "🌐 СЕТЕВЫЕ СОЕДИНЕНИЯ"
    echo "==================="
    
    # Проверяем порты reLink
    local ports=("3000" "8001" "8002" "8003" "8004" "8005" "8006" "9090" "11434" "6379")
    
    for port in "${ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            local process=$(lsof -i :$port | head -2 | tail -1 | awk '{print $1}')
            log_success "Порт $port: занят процессом $process"
        else
            log_warning "Порт $port: свободен"
        fi
    done
    
    echo ""
}

# Проверяем health checks
check_health_endpoints() {
    log_info "Проверка health endpoints..."
    
    echo ""
    echo "🏥 HEALTH CHECKS"
    echo "==============="
    
    local endpoints=(
        "http://localhost:8001/health:Router"
        "http://localhost:8002/health:Benchmark"
        "http://localhost:8003/health:Relink"
        "http://localhost:8004/health:Backend"
        "http://localhost:8005/health:LLM Tuning"
        "http://localhost:9090/-/healthy:Monitoring"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local url=$(echo $endpoint | cut -d: -f1)
        local name=$(echo $endpoint | cut -d: -f2)
        
        if curl -s -f "$url" >/dev/null 2>&1; then
            log_success "$name: OK"
        else
            log_error "$name: FAILED"
        fi
    done
    
    echo ""
}

# Анализируем Docker Compose
analyze_docker_compose() {
    log_info "Анализ Docker Compose конфигурации..."
    
    echo ""
    echo "🐳 DOCKER COMPOSE АНАЛИЗ"
    echo "======================="
    
    if [ -f "docker-compose.yml" ]; then
        # Проверяем количество сервисов
        local service_count=$(grep -c "^  [a-zA-Z]" docker-compose.yml || echo "0")
        log_info "Количество сервисов: $service_count"
        
        # Проверяем health checks
        local health_check_count=$(grep -c "healthcheck:" docker-compose.yml || echo "0")
        log_info "Health checks настроены: $health_check_count"
        
        # Проверяем restart policies
        local restart_policies=$(grep -A1 "restart:" docker-compose.yml | grep -v "restart:" | grep -v "^--$" | wc -l)
        log_info "Restart policies настроены: $restart_policies"
        
        # Проверяем ресурсные лимиты
        local resource_limits=$(grep -c "resources:" docker-compose.yml || echo "0")
        log_info "Ресурсные лимиты настроены: $resource_limits"
        
    else
        log_error "Файл docker-compose.yml не найден"
    fi
    
    echo ""
}

# Рекомендации по исправлению
provide_recommendations() {
    log_info "Генерация рекомендаций..."
    
    echo ""
    echo "💡 РЕКОМЕНДАЦИИ"
    echo "=============="
    
    # Проверяем остановленные контейнеры
    local exited_containers=$(docker ps -a --filter "name=relink" --filter "status=exited" --format "{{.Names}}")
    if [ -n "$exited_containers" ]; then
        echo "1. 🔄 Перезапустите остановленные контейнеры:"
        echo "   docker-compose up -d"
        echo ""
    fi
    
    # Проверяем ресурсы
    local cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    if [ "$cpu_usage" -gt 80 ]; then
        echo "2. ⚡ Высокое использование CPU ($cpu_usage%). Рассмотрите:"
        echo "   - Увеличение ресурсов для контейнеров"
        echo "   - Оптимизацию кода"
        echo "   - Добавление кэширования"
        echo ""
    fi
    
    # Проверяем память
    local memory_info=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    local total_memory=$(sysctl hw.memsize | awk '{print $2}')
    local free_memory=$((memory_info * 4096))
    local used_memory=$((total_memory - free_memory))
    local memory_percent=$((used_memory * 100 / total_memory))
    
    if [ "$memory_percent" -gt 85 ]; then
        echo "3. 🧠 Высокое использование памяти ($memory_percent%). Рекомендации:"
        echo "   - Увеличьте лимиты памяти для контейнеров"
        echo "   - Проверьте утечки памяти"
        echo "   - Добавьте swap файл"
        echo ""
    fi
    
    echo "4. 📊 Для детального мониторинга:"
    echo "   - Откройте http://localhost:9090 (Prometheus)"
    echo "   - Проверьте логи: docker-compose logs -f [service_name]"
    echo "   - Используйте: docker stats"
    echo ""
    
    echo "5. 🔧 Для отладки:"
    echo "   - Включите детальное логирование в .env"
    echo "   - Проверьте health checks: docker-compose ps"
    echo "   - Анализируйте логи: docker-compose logs --tail=100"
    echo ""
}

# Основная функция
main() {
    echo "🚀 МОНИТОРИНГ КОНТЕЙНЕРОВ RELINK"
    echo "================================"
    echo ""
    
    check_docker
    get_container_status
    check_problematic_containers
    check_system_resources
    check_network_connections
    check_health_endpoints
    analyze_docker_compose
    provide_recommendations
    
    log_success "Анализ завершен"
}

# Обработка аргументов командной строки
case "${1:-}" in
    "logs")
        if [ -n "$2" ]; then
            analyze_container_logs "$2" "${3:-50}"
        else
            log_error "Укажите имя контейнера: $0 logs <container_name> [lines]"
        fi
        ;;
    "health")
        check_health_endpoints
        ;;
    "resources")
        check_system_resources
        ;;
    "network")
        check_network_connections
        ;;
    "recommendations")
        provide_recommendations
        ;;
    "help"|"-h"|"--help")
        echo "Использование: $0 [команда]"
        echo ""
        echo "Команды:"
        echo "  logs <container> [lines]  - Анализ логов контейнера"
        echo "  health                    - Проверка health endpoints"
        echo "  resources                 - Проверка системных ресурсов"
        echo "  network                   - Проверка сетевых соединений"
        echo "  recommendations           - Показать рекомендации"
        echo "  help                      - Показать эту справку"
        echo ""
        echo "Примеры:"
        echo "  $0                        - Полный анализ"
        echo "  $0 logs relink-backend    - Логи бэкенда"
        echo "  $0 logs relink-frontend 50 - Логи фронтенда (50 строк)"
        ;;
    *)
        main
        ;;
esac 