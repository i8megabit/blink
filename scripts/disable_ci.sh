#!/bin/bash

# 🚀 ОТКЛЮЧЕНИЕ CI/CD В GITLAB
# Временно отключает CI/CD для предотвращения автоматических сборок

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${BLUE}[CI-DISABLE]${NC} $1"
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

# Получение URL удаленного репозитория
get_remote_url() {
    git remote get-url origin 2>/dev/null || echo ""
}

# Проверка, что это GitLab репозиторий
is_gitlab_repo() {
    local remote_url=$(get_remote_url)
    if [[ "$remote_url" == *"gitlab"* ]]; then
        return 0
    else
        return 1
    fi
}

# Создание .gitlab-ci.yml с отключенными пайплайнами
create_disabled_ci_config() {
    cat > .gitlab-ci.yml << 'EOF'
# 🚫 ВРЕМЕННО ОТКЛЮЧЕННЫЕ CI/CD ПАЙПЛАЙНЫ
# Автоматические сборки отключены для автокоммита

# Отключаем все пайплайны
workflow:
  rules:
    - when: never

# Резервные джобы (закомментированы)
# stages:
#   - build
#   - test
#   - deploy

# build:
#   stage: build
#   script:
#     - echo "Build disabled"
#   rules:
#     - when: never

# test:
#   stage: test
#   script:
#     - echo "Test disabled"
#   rules:
#     - when: never

# deploy:
#   stage: deploy
#   script:
#     - echo "Deploy disabled"
#   rules:
#     - when: never

# Комментарий для разработчиков
# Для включения CI/CD удалите этот файл или измените правила
EOF

    success "Создан .gitlab-ci.yml с отключенными пайплайнами"
}

# Создание .gitlab-ci.yml с условным отключением
create_conditional_ci_config() {
    cat > .gitlab-ci.yml << 'EOF'
# 🚫 УСЛОВНО ОТКЛЮЧЕННЫЕ CI/CD ПАЙПЛАЙНЫ
# Автоматические сборки отключены для автокоммита

# Отключаем пайплайны для автокоммитов
workflow:
  rules:
    # Отключаем для коммитов с версиями (автокоммиты)
    - if: $CI_COMMIT_MESSAGE =~ /^v\d+\.\d+\.\d+$/
      when: never
    # Включаем для остальных коммитов
    - when: always

stages:
  - build
  - test
  - deploy

# Джобы выполняются только для обычных коммитов
build:
  stage: build
  script:
    - echo "Building application..."
    - echo "Build completed"
  rules:
    - if: $CI_COMMIT_MESSAGE =~ /^v\d+\.\d+\.\d+$/
      when: never
    - when: always

test:
  stage: test
  script:
    - echo "Running tests..."
    - echo "Tests completed"
  rules:
    - if: $CI_COMMIT_MESSAGE =~ /^v\d+\.\d+\.\d+$/
      when: never
    - when: always

deploy:
  stage: deploy
  script:
    - echo "Deploying application..."
    - echo "Deploy completed"
  rules:
    - if: $CI_COMMIT_MESSAGE =~ /^v\d+\.\d+\.\d+$/
      when: never
    - when: always
EOF

    success "Создан .gitlab-ci.yml с условным отключением"
}

# Создание .gitlab-ci.yml с полным отключением
create_fully_disabled_ci_config() {
    cat > .gitlab-ci.yml << 'EOF'
# 🚫 ПОЛНОСТЬЮ ОТКЛЮЧЕННЫЕ CI/CD ПАЙПЛАЙНЫ
# Все автоматические сборки отключены

# Отключаем все пайплайны
workflow:
  rules:
    - when: never

# Информация для разработчиков
# Этот файл отключает все CI/CD пайплайны в GitLab
# Для включения CI/CD:
# 1. Удалите этот файл
# 2. Или измените правила workflow
# 3. Или создайте новый .gitlab-ci.yml с нужными джобами
EOF

    success "Создан .gitlab-ci.yml с полным отключением CI/CD"
}

# Основная логика
main() {
    log "Настройка отключения CI/CD..."
    
    # Проверяем, что это GitLab репозиторий
    if ! is_gitlab_repo; then
        warning "Это не GitLab репозиторий. CI/CD отключение не требуется."
        exit 0
    fi
    
    log "Обнаружен GitLab репозиторий"
    
    # Спрашиваем пользователя о типе отключения
    echo "Выберите тип отключения CI/CD:"
    echo "1) Полное отключение (все пайплайны отключены)"
    echo "2) Условное отключение (только для автокоммитов)"
    echo "3) Отмена"
    
    read -p "Введите номер (1-3): " choice
    
    case $choice in
        1)
            create_fully_disabled_ci_config
            ;;
        2)
            create_conditional_ci_config
            ;;
        3)
            log "Отмена операции"
            exit 0
            ;;
        *)
            error "Неверный выбор"
            exit 1
            ;;
    esac
    
    # Коммитим изменения
    if git diff --quiet .gitlab-ci.yml; then
        log "Файл .gitlab-ci.yml не изменился"
    else
        git add .gitlab-ci.yml
        git commit -m "🚫 Отключение CI/CD пайплайнов" --no-verify
        
        # Push изменений
        if git remote get-url origin > /dev/null 2>&1; then
            git push origin $(git branch --show-current)
            success "Изменения отправлены в GitLab"
        else
            warning "Нет удаленного репозитория для push"
        fi
    fi
    
    success "CI/CD отключение настроено успешно!"
}

# Запуск основной логики
main "$@" 