#!/bin/bash

# 🚀 УМНЫЙ АВТОКОММИТ С ИНКРЕМЕНТОМ ВЕРСИИ
# Автоматически коммитит изменения в файлах приложения и инкрементирует версию

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[AUTO-COMMIT]${NC} $1"
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

# Получение текущей ветки
CURRENT_BRANCH=$(git branch --show-current)
log "Текущая ветка: $CURRENT_BRANCH"

# Проверка, что мы не в detached HEAD
if [ "$CURRENT_BRANCH" = "" ]; then
    error "Detached HEAD - автокоммит отключен"
    exit 1
fi

# Проверка, что мы не в main/master ветке
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    warning "Автокоммит отключен для main/master ветки"
    exit 0
fi

# Функция для получения текущей версии
get_current_version() {
    if [ -f "VERSION" ]; then
        cat VERSION
    else
        echo "0.0.0"
    fi
}

# Функция для инкремента patch версии
increment_patch_version() {
    local version=$1
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    local patch=$(echo $version | cut -d. -f3)
    
    # Инкремент patch версии
    patch=$((patch + 1))
    
    echo "$major.$minor.$patch"
}

# Функция для проверки изменений в файлах приложения
check_app_changes() {
    # Паттерны файлов приложения (исключая временные, логи, кэш и т.д.)
    local app_patterns=(
        "*.py"
        "*.ts"
        "*.tsx"
        "*.js"
        "*.jsx"
        "*.json"
        "*.yml"
        "*.yaml"
        "*.md"
        "*.txt"
        "*.sh"
        "*.sql"
        "*.html"
        "*.css"
        "*.scss"
        "Dockerfile*"
        "docker-compose*.yml"
        "requirements*.txt"
        "package.json"
        "pyproject.toml"
        "Makefile"
        "VERSION"
    )
    
    # Исключения (файлы, которые не считаются изменениями приложения)
    local exclude_patterns=(
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
        "data/"
        "logs/"
        "screenshots/"
        "test-results/"
        ".docker_cache/"
        ".cursor/"
    )
    
    # Проверяем staged изменения
    local staged_changes=$(git diff --cached --name-only 2>/dev/null || true)
    
    # Проверяем unstaged изменения
    local unstaged_changes=$(git diff --name-only 2>/dev/null || true)
    
    # Объединяем изменения
    local all_changes=$(echo -e "$staged_changes\n$unstaged_changes" | sort -u | grep -v '^$')
    
    if [ -z "$all_changes" ]; then
        return 1
    fi
    
    # Проверяем, есть ли изменения в файлах приложения
    local app_changes=()
    
    while IFS= read -r file; do
        # Пропускаем пустые строки
        if [ -z "$file" ]; then
            continue
        fi
        
        # Проверяем исключения
        local should_exclude=false
        for pattern in "${exclude_patterns[@]}"; do
            if [[ "$file" == $pattern || "$file" =~ $pattern ]]; then
                should_exclude=true
                break
            fi
        done
        
        if [ "$should_exclude" = true ]; then
            continue
        fi
        
        # Проверяем, соответствует ли файл паттернам приложения
        for pattern in "${app_patterns[@]}"; do
            if [[ "$file" == $pattern || "$file" =~ $pattern ]]; then
                app_changes+=("$file")
                break
            fi
        done
    done <<< "$all_changes"
    
    if [ ${#app_changes[@]} -gt 0 ]; then
        log "Обнаружены изменения в файлах приложения:"
        printf '%s\n' "${app_changes[@]}" | sed 's/^/  - /'
        return 0
    else
        return 1
    fi
}

# Функция для создания коммита
create_commit() {
    local new_version=$1
    
    # Обновляем версию
    echo "$new_version" > VERSION
    
    # Добавляем все изменения
    git add .
    
    # Создаем коммит
    git commit -m "v$new_version" --no-verify
    
    success "Коммит создан: v$new_version"
}

# Функция для force push
force_push() {
    local branch=$1
    
    log "Выполняем force push в ветку $branch"
    
    # Проверяем, есть ли удаленный репозиторий
    if ! git remote get-url origin > /dev/null 2>&1; then
        warning "Нет удаленного репозитория origin"
        return 0
    fi
    
    # Force push
    git push origin "$branch" --force-with-lease
    
    success "Force push выполнен успешно"
}

# Основная логика
main() {
    log "Проверка изменений в файлах приложения..."
    
    # Проверяем, есть ли изменения в файлах приложения
    if ! check_app_changes; then
        log "Изменений в файлах приложения не обнаружено"
        exit 0
    fi
    
    # Получаем текущую версию
    local current_version=$(get_current_version)
    log "Текущая версия: $current_version"
    
    # Инкрементируем patch версию
    local new_version=$(increment_patch_version "$current_version")
    log "Новая версия: $new_version"
    
    # Создаем коммит
    create_commit "$new_version"
    
    # Выполняем force push
    force_push "$CURRENT_BRANCH"
    
    success "Автокоммит завершен успешно!"
}

# Запуск основной логики
main "$@" 