#!/bin/bash

# 🚀 SEO Link Recommender - Оркестратор разработки
# Удобный инструмент для управления Docker-окружением

set -e

# Цвета для красивого вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Эмодзи для красоты
ROCKET="🚀"
GEAR="⚙️"
EYES="👀"
FIRE="🔥"
CLEAN="🧹"
HEART="❤️"
LIGHTNING="⚡"
CONSTRUCTION="🚧"
CHECK="✅"
CROSS="❌"
QUESTION="❓"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

# Проверяем, что мы в правильной директории
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}${CROSS} Ошибка: docker-compose.yml не найден в $PROJECT_DIR${NC}"
    exit 1
fi

# Переходим в директорию проекта
cd "$PROJECT_DIR"

# Функция для красивого заголовка
print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${WHITE}$ROCKET SEO Link Recommender $ROCKET${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo
}

# Функция для показа статуса сервисов
show_status() {
    echo -e "${CYAN}${EYES} Статус сервисов:${NC}"
    docker-compose ps
    echo
    
    echo -e "${CYAN}${LIGHTNING} Использование ресурсов:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    echo
}

# Быстрая проверка здоровья
health_check() {
    echo -e "${GREEN}${HEART} Проверка здоровья сервисов...${NC}"
    
    # Проверяем backend
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} Backend: OK${NC}"
    else
        echo -e "${RED}${CROSS} Backend: Недоступен${NC}"
    fi
    
    # Проверяем frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} Frontend: OK${NC}"
    else
        echo -e "${RED}${CROSS} Frontend: Недоступен${NC}"
    fi
    
    # Проверяем Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} Ollama: OK${NC}"
    else
        echo -e "${RED}${CROSS} Ollama: Недоступен${NC}"
    fi
    
    # Проверяем БД
    if docker-compose exec -T db pg_isready -U seo_user > /dev/null 2>&1; then
        echo -e "${GREEN}${CHECK} PostgreSQL: OK${NC}"
    else
        echo -e "${RED}${CROSS} PostgreSQL: Недоступен${NC}"
    fi
    echo
}

# Логи с фильтрацией и цветами
show_logs() {
    local service="$1"
    local lines="${2:-50}"
    
    case "$service" in
        "backend"|"be")
            echo -e "${BLUE}${EYES} Логи Backend (последние $lines строк):${NC}"
            docker-compose logs --tail="$lines" -f backend
            ;;
        "frontend"|"fe")
            echo -e "${BLUE}${EYES} Логи Frontend (последние $lines строк):${NC}"
            docker-compose logs --tail="$lines" -f frontend
            ;;
        "ollama"|"ol")
            echo -e "${BLUE}${EYES} Логи Ollama (последние $lines строк):${NC}"
            docker-compose logs --tail="$lines" -f ollama
            ;;
        "db"|"database")
            echo -e "${BLUE}${EYES} Логи PostgreSQL (последние $lines строк):${NC}"
            docker-compose logs --tail="$lines" -f db
            ;;
        "all"|"")
            echo -e "${BLUE}${EYES} Все логи (последние $lines строк):${NC}"
            docker-compose logs --tail="$lines" -f
            ;;
        *)
            echo -e "${RED}${CROSS} Неизвестный сервис: $service${NC}"
            echo -e "${YELLOW}Доступные: backend|be, frontend|fe, ollama|ol, db|database, all${NC}"
            ;;
    esac
}

# Умная пересборка (только изменившиеся сервисы)
smart_rebuild() {
    local services=("$@")
    
    if [ ${#services[@]} -eq 0 ]; then
        services=("backend" "frontend")
    fi
    
    echo -e "${YELLOW}${CONSTRUCTION} Умная пересборка сервисов: ${services[*]}${NC}"
    
    for service in "${services[@]}"; do
        echo -e "${BLUE}${GEAR} Пересборка $service...${NC}"
        docker-compose build --no-cache "$service"
        docker-compose up -d "$service"
    done
    
    echo -e "${GREEN}${CHECK} Пересборка завершена!${NC}"
}

# Быстрый перезапуск без пересборки
quick_restart() {
    local services=("$@")
    
    if [ ${#services[@]} -eq 0 ]; then
        services=("backend" "frontend")
    fi
    
    echo -e "${LIGHTNING}${YELLOW} Быстрый перезапуск: ${services[*]}${NC}"
    docker-compose restart "${services[@]}"
    echo -e "${GREEN}${CHECK} Перезапуск завершён!${NC}"
}

# Полная очистка с опциями
deep_clean() {
    echo -e "${RED}${FIRE} ВНИМАНИЕ: Полная очистка Docker-окружения!${NC}"
    echo -e "${YELLOW}Это удалит:${NC}"
    echo -e "  • Все контейнеры проекта"
    echo -e "  • Неиспользуемые образы"
    echo -e "  • Неиспользуемые тома"
    echo -e "  • Неиспользуемые сети"
    echo
    
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CLEAN}${YELLOW} Очистка...${NC}"
        
        # Останавливаем всё
        docker-compose down -v --remove-orphans
        
        # Удаляем образы проекта
        docker images --format "table {{.Repository}}:{{.Tag}}" | grep "seo_link_recommender" | xargs -r docker rmi -f
        
        # Очищаем неиспользуемое
        docker system prune -af --volumes
        
        echo -e "${GREEN}${CHECK} Очистка завершена!${NC}"
    else
        echo -e "${BLUE}Очистка отменена.${NC}"
    fi
}

# Подключение к контейнеру
enter_container() {
    local service="$1"
    local shell="${2:-bash}"
    
    case "$service" in
        "backend"|"be")
            echo -e "${BLUE}${GEAR} Подключение к Backend...${NC}"
            docker-compose exec backend "$shell"
            ;;
        "frontend"|"fe")
            echo -e "${BLUE}${GEAR} Подключение к Frontend...${NC}"
            docker-compose exec frontend "$shell"
            ;;
        "db"|"database")
            echo -e "${BLUE}${GEAR} Подключение к PostgreSQL...${NC}"
            docker-compose exec db psql -U seo_user seo_db
            ;;
        "ollama"|"ol")
            echo -e "${BLUE}${GEAR} Подключение к Ollama...${NC}"
            docker-compose exec ollama "$shell"
            ;;
        *)
            echo -e "${RED}${CROSS} Неизвестный сервис: $service${NC}"
            echo -e "${YELLOW}Доступные: backend|be, frontend|fe, db|database, ollama|ol${NC}"
            ;;
    esac
}

# Мониторинг ресурсов в реальном времени
monitor() {
    echo -e "${CYAN}${EYES} Мониторинг ресурсов (Ctrl+C для выхода):${NC}"
    echo
    watch -n 2 'docker stats --no-stream'
}

# Dev-режим с автоперезапуском при изменениях
dev_mode() {
    echo -e "${BLUE}${ROCKET} Режим разработки с автоперезапуском...${NC}"
    echo -e "${YELLOW}Отслеживаем изменения в backend/ и frontend/${NC}"
    echo -e "${YELLOW}Для выхода нажмите Ctrl+C${NC}"
    echo
    
    # Запускаем контейнеры
    docker-compose up -d
    
    # Функция для перезапуска сервиса
    reload_service() {
        local service="$1"
        echo -e "${LIGHTNING}${YELLOW} Обнаружены изменения в $service, перезапускаем...${NC}"
        docker-compose restart "$service"
        echo -e "${GREEN}${CHECK} $service перезапущен${NC}"
    }
    
    # Отслеживаем изменения
    if command -v fswatch &> /dev/null; then
        fswatch -o backend/ frontend/ | while read; do
            # Определяем какой сервис перезапускать
            if [[ $(find backend/ -newer .last_backend_change 2>/dev/null) ]]; then
                touch .last_backend_change
                reload_service "backend"
            fi
            if [[ $(find frontend/ -newer .last_frontend_change 2>/dev/null) ]]; then
                touch .last_frontend_change  
                reload_service "frontend"
            fi
        done
    else
        echo -e "${YELLOW}Установите fswatch для автоперезапуска: brew install fswatch${NC}"
        echo -e "${BLUE}Пока что просто следим за логами...${NC}"
        docker-compose logs -f
    fi
}

# Быстрый просмотр важной информации
quick_info() {
    print_header
    
    echo -e "${CYAN}${LIGHTNING} Быстрая сводка:${NC}"
    echo
    
    # Статус контейнеров одной строкой
    echo -e "${WHITE}Контейнеры:${NC}"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Контейнеры не запущены"
    echo
    
    # Использование ресурсов
    echo -e "${WHITE}Ресурсы:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | head -n 5
    echo
    
    # Быстрая проверка эндпоинтов
    echo -e "${WHITE}Доступность:${NC}"
    check_endpoint() {
        local name="$1"
        local url="$2"
        if curl -s -m 3 "$url" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $name ($url)"
        else
            echo -e "  ${RED}✗${NC} $name ($url)"
        fi
    }
    
    check_endpoint "Frontend" "http://localhost:3000"
    check_endpoint "Backend API" "http://localhost:8000/api/v1/health"
    check_endpoint "Ollama" "http://localhost:11434/api/tags"
    echo
}

# Открыть в браузере
open_browser() {
    local target="${1:-frontend}"
    
    case "$target" in
        "frontend"|"fe"|"app")
            echo -e "${BLUE}${ROCKET} Открываем фронтенд...${NC}"
            open "http://localhost:3000" 2>/dev/null || xdg-open "http://localhost:3000" 2>/dev/null || echo "Откройте http://localhost:3000"
            ;;
        "backend"|"be"|"api")
            echo -e "${BLUE}${ROCKET} Открываем API документацию...${NC}"
            open "http://localhost:8000/docs" 2>/dev/null || xdg-open "http://localhost:8000/docs" 2>/dev/null || echo "Откройте http://localhost:8000/docs"
            ;;
        "ollama"|"ol")
            echo -e "${BLUE}${ROCKET} Показываем статус Ollama...${NC}"
            curl -s http://localhost:11434/api/tags | jq '.' 2>/dev/null || curl -s http://localhost:11434/api/tags
            ;;
        *)
            echo -e "${RED}${CROSS} Неизвестная цель: $target${NC}"
            echo -e "${YELLOW}Доступные: frontend|fe|app, backend|be|api, ollama|ol${NC}"
            ;;
    esac
}

# Очистка логов Docker
clear_logs() {
    echo -e "${CLEAN}${YELLOW} Очистка логов Docker...${NC}"
    
    # Получаем список контейнеров проекта
    containers=$(docker-compose ps -q 2>/dev/null)
    
    if [ -n "$containers" ]; then
        echo "$containers" | while read container; do
            if [ -n "$container" ]; then
                echo -e "${BLUE}Очищаем логи контейнера $(docker inspect --format='{{.Name}}' "$container" | sed 's/^\///')...${NC}"
                echo "" > "$(docker inspect --format='{{.LogPath}}' "$container")" 2>/dev/null || true
            fi
        done
        echo -e "${GREEN}${CHECK} Логи очищены${NC}"
    else
        echo -e "${YELLOW}Контейнеры не найдены${NC}"
    fi
}

# Проверка и установка зависимостей системы
check_system_deps() {
    echo -e "${BLUE}${GEAR} Проверка системных зависимостей...${NC}"
    
    # Проверяем Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}${CROSS} Docker не установлен${NC}"
        echo -e "${YELLOW}Установите Docker: https://docker.com/get-started${NC}"
    else
        echo -e "${GREEN}${CHECK} Docker: $(docker --version)${NC}"
    fi
    
    # Проверяем Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}${CROSS} Docker Compose не установлен${NC}"
        echo -e "${YELLOW}Установите Docker Compose${NC}"
    else
        echo -e "${GREEN}${CHECK} Docker Compose: $(docker-compose --version)${NC}"
    fi
    
    # Проверяем curl
    if ! command -v curl &> /dev/null; then
        echo -e "${YELLOW}${QUESTION} curl не найден (рекомендуется для проверок)${NC}"
    else
        echo -e "${GREEN}${CHECK} curl доступен${NC}"
    fi
    
    # Проверяем jq
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}${QUESTION} jq не найден (рекомендуется для JSON: brew install jq)${NC}"
    else
        echo -e "${GREEN}${CHECK} jq доступен${NC}"
    fi
    
    # Проверяем fswatch для dev режима
    if ! command -v fswatch &> /dev/null; then
        echo -e "${YELLOW}${QUESTION} fswatch не найден (для dev режима: brew install fswatch)${NC}"
    else
        echo -e "${GREEN}${CHECK} fswatch доступен${NC}"
    fi
}

# Бэкап данных
backup_data() {
    local backup_dir="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    echo -e "${BLUE}${GEAR} Создание бэкапа...${NC}"
    
    # Бэкап БД
    echo -e "${YELLOW}Экспорт базы данных...${NC}"
    docker-compose exec -T db pg_dump -U seo_user seo_db > "$backup_dir/database.sql"
    
    # Бэкап Ollama моделей
    echo -e "${YELLOW}Копирование моделей Ollama...${NC}"
    cp -r ollama_models "$backup_dir/"
    
    echo -e "${GREEN}${CHECK} Бэкап создан: $backup_dir${NC}"
}

# Восстановление из бэкапа
restore_data() {
    local backup_dir="$1"
    
    if [ -z "$backup_dir" ] || [ ! -d "$backup_dir" ]; then
        echo -e "${RED}${CROSS} Укажите существующую директорию бэкапа${NC}"
        echo -e "${YELLOW}Пример: $0 restore backups/20241215_143000${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}${CONSTRUCTION} Восстановление из $backup_dir...${NC}"
    
    # Восстановление БД
    if [ -f "$backup_dir/database.sql" ]; then
        echo -e "${BLUE}Восстановление базы данных...${NC}"
        docker-compose exec -T db psql -U seo_user seo_db < "$backup_dir/database.sql"
    fi
    
    # Восстановление моделей
    if [ -d "$backup_dir/ollama_models" ]; then
        echo -e "${BLUE}Восстановление моделей Ollama...${NC}"
        cp -r "$backup_dir/ollama_models" ./
    fi
    
    echo -e "${GREEN}${CHECK} Восстановление завершено!${NC}"
}

# Обновление зависимостей
update_deps() {
    echo -e "${BLUE}${GEAR} Обновление зависимостей...${NC}"
    
    # Python зависимости
    echo -e "${YELLOW}Проверка Python пакетов...${NC}"
    docker-compose exec backend pip list --outdated
    
    echo -e "${GREEN}${CHECK} Проверка завершена. Для обновления пересоберите контейнеры.${NC}"
}

# Тесты
run_tests() {
    echo -e "${BLUE}${GEAR} Запуск тестов...${NC}"
    docker-compose exec backend python -m pytest tests/ -v --color=yes
}

# Показать справку
show_help() {
    print_header
    echo -e "${WHITE}Доступные команды:${NC}"
    echo
    echo -e "${GREEN}🚀 Основные команды:${NC}"
    echo -e "  ${CYAN}start${NC}                    - Запуск всех сервисов"
    echo -e "  ${CYAN}stop${NC}                     - Остановка всех сервисов"
    echo -e "  ${CYAN}restart [service...]${NC}     - Быстрый перезапуск (без пересборки)"
    echo -e "  ${CYAN}rebuild [service...]${NC}     - Умная пересборка выбранных сервисов"
    echo -e "  ${CYAN}build${NC}                    - Полная пересборка всех сервисов"
    echo
    echo -e "${GREEN}📊 Мониторинг:${NC}"
    echo -e "  ${CYAN}status${NC}                   - Статус всех сервисов"
    echo -e "  ${CYAN}health${NC}                   - Проверка здоровья сервисов"
    echo -e "  ${CYAN}monitor${NC}                  - Мониторинг ресурсов в реальном времени"
    echo -e "  ${CYAN}logs [service] [lines]${NC}   - Просмотр логов (backend|frontend|ollama|db|all)"
    echo
    echo -e "${GREEN}🔧 Утилиты:${NC}"
    echo -e "  ${CYAN}shell [service]${NC}          - Подключение к контейнеру"
    echo -e "  ${CYAN}test${NC}                     - Запуск тестов"
    echo -e "  ${CYAN}deps${NC}                     - Проверка зависимостей"
    echo -e "  ${CYAN}sys${NC}                      - Проверка системных зависимостей"
    echo -e "  ${CYAN}dev${NC}                      - Режим разработки с автоперезапуском"
    echo
    echo -e "${GREEN}🌐 Быстрый доступ:${NC}"
    echo -e "  ${CYAN}info${NC}                     - Быстрая сводка состояния"
    echo -e "  ${CYAN}open [target]${NC}            - Открыть в браузере (frontend|backend|ollama)"
    echo
    echo -e "${GREEN}💾 Данные:${NC}"
    echo -e "  ${CYAN}backup${NC}                   - Создание бэкапа"
    echo -e "  ${CYAN}restore <dir>${NC}            - Восстановление из бэкапа"
    echo
    echo -e "${GREEN}🧹 Очистка:${NC}"
    echo -e "  ${CYAN}clean${NC}                    - Полная очистка Docker-окружения"
    echo -e "  ${CYAN}prune${NC}                    - Удаление неиспользуемых ресурсов"
    echo -e "  ${CYAN}clear-logs${NC}               - Очистка логов Docker"
    echo
    echo -e "${GREEN}📖 Справка:${NC}"
    echo -e "  ${CYAN}help${NC}                     - Показать эту справку"
    echo
    echo -e "${PURPLE}Примеры использования:${NC}"
    echo -e "  ${YELLOW}$0 start${NC}                          # Запустить всё"
    echo -e "  ${YELLOW}$0 dev${NC}                            # Режим разработки с автоперезапуском"
    echo -e "  ${YELLOW}$0 info${NC}                           # Быстрая сводка состояния"
    echo -e "  ${YELLOW}$0 rebuild backend${NC}                # Пересобрать только backend"
    echo -e "  ${YELLOW}$0 logs ollama 100${NC}                # 100 последних строк логов Ollama"
    echo -e "  ${YELLOW}$0 shell backend${NC}                  # Подключиться к backend"
    echo -e "  ${YELLOW}$0 open frontend${NC}                  # Открыть фронтенд в браузере"
    echo -e "  ${YELLOW}$0 restart backend frontend${NC}       # Перезапустить backend и frontend"
    echo
}

# Основная логика
main() {
    local command="$1"
    shift
    
    case "$command" in
        "start"|"up")
            print_header
            echo -e "${GREEN}${ROCKET} Запуск всех сервисов...${NC}"
            docker-compose up -d
            echo
            health_check
            ;;
        "stop"|"down")
            echo -e "${YELLOW}${CONSTRUCTION} Остановка всех сервисов...${NC}"
            docker-compose down
            ;;
        "restart"|"rs")
            quick_restart "$@"
            ;;
        "rebuild"|"rb")
            smart_rebuild "$@"
            ;;
        "build")
            echo -e "${YELLOW}${CONSTRUCTION} Полная пересборка...${NC}"
            docker-compose build --no-cache
            docker-compose up -d
            ;;
        "status"|"st")
            print_header
            show_status
            ;;
        "health"|"h")
            health_check
            ;;
        "logs"|"l")
            show_logs "$@"
            ;;
        "monitor"|"mon")
            monitor
            ;;
        "shell"|"sh"|"exec")
            enter_container "$@"
            ;;
        "test"|"tests")
            run_tests
            ;;
        "deps"|"dependencies")
            update_deps
            ;;
        "sys"|"system")
            check_system_deps
            ;;
        "dev"|"develop")
            dev_mode
            ;;
        "info"|"i")
            quick_info
            ;;
        "open"|"browse")
            open_browser "$@"
            ;;
        "backup"|"bak")
            backup_data
            ;;
        "restore"|"res")
            restore_data "$@"
            ;;
        "clean")
            deep_clean
            ;;
        "clear-logs"|"clearlogs")
            clear_logs
            ;;
        "prune")
            echo -e "${CLEAN}${YELLOW} Удаление неиспользуемых ресурсов...${NC}"
            docker system prune -f
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            echo -e "${RED}${CROSS} Неизвестная команда: $command${NC}"
            echo -e "${YELLOW}Используйте '$0 help' для справки${NC}"
            exit 1
            ;;
    esac
}

# Запуск
main "$@" 