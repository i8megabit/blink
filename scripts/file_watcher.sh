#!/bin/bash

# 🚀 ФАЙЛОВЫЙ МОНИТОР - ОТСЛЕЖИВАНИЕ ИЗМЕНЕНИЙ В РЕАЛЬНОМ ВРЕМЕНИ
# Мониторит изменения в файлах приложения и запускает автокоммит

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[FILE-WATCHER]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    if ! command -v inotifywait &> /dev/null; then
        error "inotifywait не установлен. Установите inotify-tools:"
        echo "  Ubuntu/Debian: sudo apt-get install inotify-tools"
        echo "  macOS: brew install fswatch"
        echo "  CentOS/RHEL: sudo yum install inotify-tools"
        exit 1
    fi
}

# Получение корневой директории git
get_git_root() {
    git rev-parse --show-toplevel
}

# Создание списка директорий для мониторинга
get_watch_directories() {
    local git_root=$(get_git_root)
    
    # Основные директории приложения
    local dirs=(
        "$git_root/frontend/src"
        "$git_root/backend/app"
        "$git_root/llm_tuning/app"
        "$git_root/testing/app"
        "$git_root/monitoring/app"
        "$git_root/scripts"
        "$git_root/config"
        "$git_root/docs"
    )
    
    # Проверяем существование директорий
    local existing_dirs=()
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            existing_dirs+=("$dir")
        fi
    done
    
    echo "${existing_dirs[@]}"
}

# Создание списка файлов для исключения
get_exclude_patterns() {
    # Паттерны файлов для исключения
    local patterns=(
        "*.log"
        "*.tmp"
        "*.temp"
        "*.cache"
        "*.pyc"
        "*.pyo"
        "__pycache__"
        "node_modules"
        ".git"
        ".venv"
        ".env"
        "*.pid"
        "*.lock"
        ".DS_Store"
        "Thumbs.db"
        "*.swp"
        "*.swo"
        "*~"
        ".pytest_cache"
        ".coverage"
        "htmlcov"
        "dist"
        "build"
        "*.egg-info"
        "*.so"
        "*.dll"
        "*.exe"
        "*.bin"
        "*.gguf"
        "data"
        "logs"
        "screenshots"
        "test-results"
        ".docker_cache"
        ".cursor"
    )
    
    # Формируем строку для inotifywait
    local exclude_string=""
    for pattern in "${patterns[@]}"; do
        exclude_string="$exclude_string --exclude '$pattern'"
    done
    
    echo "$exclude_string"
}

# Функция для запуска автокоммита
run_auto_commit() {
    local auto_commit_script="$(get_git_root)/scripts/auto_commit.sh"
    
    if [ -f "$auto_commit_script" ] && [ -x "$auto_commit_script" ]; then
        log "Запуск автокоммита..."
        "$auto_commit_script" &
        success "Автокоммит запущен"
    else
        error "Скрипт автокоммита не найден или не исполняемый: $auto_commit_script"
    fi
}

# Основная функция мониторинга
monitor_files() {
    local git_root=$(get_git_root)
    local watch_dirs=($(get_watch_directories))
    local exclude_patterns=$(get_exclude_patterns)
    
    log "Запуск мониторинга файлов..."
    log "Мониторимые директории:"
    for dir in "${watch_dirs[@]}"; do
        echo "  - $dir"
    done
    
    # Проверяем, есть ли директории для мониторинга
    if [ ${#watch_dirs[@]} -eq 0 ]; then
        error "Нет директорий для мониторинга"
        exit 1
    fi
    
    # Запускаем мониторинг
    log "Мониторинг запущен. Нажмите Ctrl+C для остановки."
    
    # Используем inotifywait для мониторинга
    inotifywait -m -r -e modify,create,delete,move \
        --format '%w%f %e' \
        $exclude_patterns \
        "${watch_dirs[@]}" | while read file event; do
        
        # Проверяем, что файл существует и не является временным
        if [ -f "$file" ] && [[ ! "$file" =~ \.(log|tmp|temp|cache|pyc|pyo|swp|swo)$ ]]; then
            log "Обнаружено изменение: $file ($event)"
            
            # Небольшая задержка для предотвращения множественных срабатываний
            sleep 2
            
            # Запускаем автокоммит
            run_auto_commit
        fi
    done
}

# Функция для macOS (использует fswatch)
monitor_files_macos() {
    local git_root=$(get_git_root)
    local watch_dirs=($(get_watch_directories))
    
    log "Запуск мониторинга файлов (macOS)..."
    log "Мониторимые директории:"
    for dir in "${watch_dirs[@]}"; do
        echo "  - $dir"
    done
    
    # Проверяем, есть ли директории для мониторинга
    if [ ${#watch_dirs[@]} -eq 0 ]; then
        error "Нет директорий для мониторинга"
        exit 1
    fi
    
    # Запускаем мониторинг с помощью fswatch
    log "Мониторинг запущен. Нажмите Ctrl+C для остановки."
    
    fswatch -o "${watch_dirs[@]}" | while read f; do
        log "Обнаружены изменения в файлах"
        
        # Небольшая задержка для предотвращения множественных срабатываний
        sleep 2
        
        # Запускаем автокоммит
        run_auto_commit
    done
}

# Определение операционной системы
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)     echo "linux" ;;
        CYGWIN*)    echo "windows" ;;
        MINGW*)     echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

# Основная логика
main() {
    log "Запуск файлового монитора..."
    
    # Проверяем зависимости
    check_dependencies
    
    # Определяем ОС и запускаем соответствующий мониторинг
    local os=$(detect_os)
    
    case "$os" in
        "linux")
            monitor_files
            ;;
        "macos")
            if command -v fswatch &> /dev/null; then
                monitor_files_macos
            else
                error "fswatch не установлен. Установите: brew install fswatch"
                exit 1
            fi
            ;;
        *)
            error "Неподдерживаемая операционная система: $os"
            exit 1
            ;;
    esac
}

# Обработка сигналов
trap 'echo -e "\n${YELLOW}[INFO]${NC} Мониторинг остановлен"; exit 0' INT TERM

# Запуск основной логики
main "$@" 