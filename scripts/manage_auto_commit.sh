#!/bin/bash

# 🚀 УПРАВЛЕНИЕ АВТОКОММИТОМ
# Скрипт для включения/отключения и управления автокоммитом

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[AUTO-COMMIT-MANAGER]${NC} $1"
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

# Проверка, что мы в git репозитории
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    error "Не git репозиторий"
    exit 1
fi

# Получение корневой директории git
get_git_root() {
    git rev-parse --show-toplevel
}

# Проверка статуса автокоммита
check_auto_commit_status() {
    local git_root=$(get_git_root)
    local hooks_dir="$git_root/.git/hooks"
    
    echo "📊 Статус автокоммита:"
    echo ""
    
    # Проверяем pre-commit hook
    if [ -f "$hooks_dir/pre-commit" ] && [ -x "$hooks_dir/pre-commit" ]; then
        echo "✅ pre-commit hook: активен"
    else
        echo "❌ pre-commit hook: неактивен"
    fi
    
    # Проверяем post-commit hook
    if [ -f "$hooks_dir/post-commit" ] && [ -x "$hooks_dir/post-commit" ]; then
        echo "✅ post-commit hook: активен"
    else
        echo "❌ post-commit hook: неактивен"
    fi
    
    # Проверяем скрипт автокоммита
    if [ -f "$git_root/scripts/auto_commit.sh" ] && [ -x "$git_root/scripts/auto_commit.sh" ]; then
        echo "✅ auto_commit.sh: доступен"
    else
        echo "❌ auto_commit.sh: недоступен"
    fi
    
    # Проверяем файловый монитор
    if [ -f "$git_root/scripts/file_watcher.sh" ] && [ -x "$git_root/scripts/file_watcher.sh" ]; then
        echo "✅ file_watcher.sh: доступен"
    else
        echo "❌ file_watcher.sh: недоступен"
    fi
    
    # Проверяем CI/CD конфигурацию
    if [ -f "$git_root/.gitlab-ci.yml" ]; then
        echo "✅ .gitlab-ci.yml: существует"
        if grep -q "when: never" "$git_root/.gitlab-ci.yml"; then
            echo "✅ CI/CD: отключен"
        else
            echo "⚠️  CI/CD: активен"
        fi
    else
        echo "❌ .gitlab-ci.yml: отсутствует"
    fi
    
    echo ""
}

# Включение автокоммита
enable_auto_commit() {
    local git_root=$(get_git_root)
    local hooks_dir="$git_root/.git/hooks"
    
    log "Включение автокоммита..."
    
    # Делаем скрипты исполняемыми
    chmod +x "$git_root/scripts/auto_commit.sh"
    chmod +x "$git_root/scripts/file_watcher.sh"
    chmod +x "$git_root/scripts/disable_ci.sh"
    
    # Делаем hooks исполняемыми
    chmod +x "$hooks_dir/pre-commit"
    chmod +x "$hooks_dir/post-commit"
    
    success "Автокоммит включен"
    echo ""
    echo "📝 Доступные команды:"
    echo "  - Ручной запуск автокоммита: ./scripts/auto_commit.sh"
    echo "  - Мониторинг файлов: ./scripts/file_watcher.sh"
    echo "  - Отключение CI/CD: ./scripts/disable_ci.sh"
    echo ""
}

# Отключение автокоммита
disable_auto_commit() {
    local git_root=$(get_git_root)
    local hooks_dir="$git_root/.git/hooks"
    
    log "Отключение автокоммита..."
    
    # Переименовываем hooks (делаем неактивными)
    if [ -f "$hooks_dir/pre-commit" ]; then
        mv "$hooks_dir/pre-commit" "$hooks_dir/pre-commit.disabled"
        success "pre-commit hook отключен"
    fi
    
    if [ -f "$hooks_dir/post-commit" ]; then
        mv "$hooks_dir/post-commit" "$hooks_dir/post-commit.disabled"
        success "post-commit hook отключен"
    fi
    
    success "Автокоммит отключен"
}

# Восстановление автокоммита
restore_auto_commit() {
    local git_root=$(get_git_root)
    local hooks_dir="$git_root/.git/hooks"
    
    log "Восстановление автокоммита..."
    
    # Восстанавливаем hooks
    if [ -f "$hooks_dir/pre-commit.disabled" ]; then
        mv "$hooks_dir/pre-commit.disabled" "$hooks_dir/pre-commit"
        chmod +x "$hooks_dir/pre-commit"
        success "pre-commit hook восстановлен"
    fi
    
    if [ -f "$hooks_dir/post-commit.disabled" ]; then
        mv "$hooks_dir/post-commit.disabled" "$hooks_dir/post-commit"
        chmod +x "$hooks_dir/post-commit"
        success "post-commit hook восстановлен"
    fi
    
    success "Автокоммит восстановлен"
}

# Тестирование автокоммита
test_auto_commit() {
    log "Тестирование автокоммита..."
    
    # Создаем тестовый файл
    local test_file="test_auto_commit_$(date +%s).txt"
    echo "Тест автокоммита $(date)" > "$test_file"
    
    # Добавляем файл в git
    git add "$test_file"
    
    # Создаем коммит (это запустит hook)
    git commit -m "🧪 Тест автокоммита" --no-verify
    
    # Удаляем тестовый файл
    rm -f "$test_file"
    git add "$test_file"
    git commit -m "🧹 Удаление тестового файла" --no-verify
    
    success "Тест автокоммита завершен"
}

# Запуск файлового монитора
start_file_watcher() {
    log "Запуск файлового монитора..."
    
    local git_root=$(get_git_root)
    local watcher_script="$git_root/scripts/file_watcher.sh"
    
    if [ -f "$watcher_script" ] && [ -x "$watcher_script" ]; then
        echo "🚀 Файловый монитор запущен в фоновом режиме"
        echo "📝 Логи: /tmp/file_watcher.log"
        echo "🛑 Для остановки: pkill -f file_watcher.sh"
        
        nohup "$watcher_script" > /tmp/file_watcher.log 2>&1 &
        
        success "Файловый монитор запущен"
    else
        error "Скрипт файлового монитора не найден: $watcher_script"
        exit 1
    fi
}

# Остановка файлового монитора
stop_file_watcher() {
    log "Остановка файлового монитора..."
    
    if pkill -f "file_watcher.sh"; then
        success "Файловый монитор остановлен"
    else
        warning "Файловый монитор не был запущен"
    fi
}

# Показать логи
show_logs() {
    echo "📋 Логи автокоммита:"
    echo ""
    
    if [ -f "/tmp/auto_commit.log" ]; then
        echo "📝 Логи автокоммита (/tmp/auto_commit.log):"
        echo "----------------------------------------"
        tail -20 /tmp/auto_commit.log
        echo ""
    else
        echo "❌ Логи автокоммита не найдены"
    fi
    
    if [ -f "/tmp/file_watcher.log" ]; then
        echo "📝 Логи файлового монитора (/tmp/file_watcher.log):"
        echo "----------------------------------------"
        tail -20 /tmp/file_watcher.log
        echo ""
    else
        echo "❌ Логи файлового монитора не найдены"
    fi
}

# Показать справку
show_help() {
    echo "🚀 Управление автокоммитом reLink"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  status     - Показать статус автокоммита"
    echo "  enable     - Включить автокоммит"
    echo "  disable    - Отключить автокоммит"
    echo "  restore    - Восстановить автокоммит"
    echo "  test       - Протестировать автокоммит"
    echo "  watch      - Запустить файловый монитор"
    echo "  stop-watch - Остановить файловый монитор"
    echo "  logs       - Показать логи"
    echo "  help       - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 status"
    echo "  $0 enable"
    echo "  $0 watch"
    echo "  $0 logs"
    echo ""
}

# Основная логика
main() {
    case "${1:-help}" in
        "status")
            check_auto_commit_status
            ;;
        "enable")
            enable_auto_commit
            ;;
        "disable")
            disable_auto_commit
            ;;
        "restore")
            restore_auto_commit
            ;;
        "test")
            test_auto_commit
            ;;
        "watch")
            start_file_watcher
            ;;
        "stop-watch")
            stop_file_watcher
            ;;
        "logs")
            show_logs
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Запуск основной логики
main "$@" 