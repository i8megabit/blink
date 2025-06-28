#!/bin/bash

# ========================================
# Скрипт публикации образов в Docker Hub
# ========================================

set -e

# Конфигурация
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-username"}
PROJECT_NAME="seo-link-recommender"
VERSION=${VERSION:-"latest"}
REGISTRY="docker.io"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка авторизации в Docker Hub
check_docker_auth() {
    log_info "Проверка авторизации в Docker Hub..."
    
    # Проверяем разные способы авторизации
    if docker info 2>/dev/null | grep -q "Username" || \
       docker system info 2>/dev/null | grep -q "Username" || \
       [ -f ~/.docker/config.json ] && grep -q "auths" ~/.docker/config.json; then
        log_success "Авторизация в Docker Hub подтверждена"
        return 0
    fi
    
    log_warning "Не авторизован в Docker Hub"
    log_info "Выполните: docker login"
    return 1
}

# Тегирование образа
tag_image() {
    local image_name=$1
    local tag=$2
    
    log_info "Тегирование образа: $image_name -> $tag"
    
    if docker tag "$image_name" "$tag"; then
        log_success "Образ успешно тегирован: $tag"
    else
        log_error "Ошибка тегирования образа: $image_name"
        return 1
    fi
}

# Публикация образа
push_image() {
    local image_tag=$1
    
    log_info "Публикация образа: $image_tag"
    
    if docker push "$image_tag"; then
        log_success "Образ успешно опубликован: $image_tag"
    else
        log_error "Ошибка публикации образа: $image_tag"
        return 1
    fi
}

# Основная функция публикации
publish_images() {
    log_info "Начинаем публикацию образов в Docker Hub..."
    
    # Проверяем авторизацию
    if ! check_docker_auth; then
        exit 1
    fi
    
    # Список образов для публикации
    images_names=(backend frontend-classic frontend-vite)
    images_tags=(relink-backend:latest relink-frontend-classic:latest relink-frontend-vite:latest)
    
    # Тегируем и публикуем каждый образ
    for i in 0 1 2; do
        name="${images_names[$i]}"
        image_name="${images_tags[$i]}"
        dockerhub_tag="$REGISTRY/$DOCKER_USERNAME/$PROJECT_NAME-$name:$VERSION"
        
        log_info "Обработка образа: $name"
        
        # Проверяем существование образа
        if ! docker image inspect "$image_name" >/dev/null 2>&1; then
            log_warning "Образ не найден: $image_name"
            log_info "Сначала соберите образы: docker-compose -f docker-compose.parallel.yml build"
            continue
        fi
        
        # Тегируем образ
        if tag_image "$image_name" "$dockerhub_tag"; then
            # Публикуем образ
            if push_image "$dockerhub_tag"; then
                log_success "Образ $name успешно опубликован"
            else
                log_error "Ошибка публикации образа $name"
            fi
        else
            log_error "Ошибка тегирования образа $name"
        fi
        
        echo ""
    done
}

# Публикация всех образов с версией
publish_versioned() {
    local version=$1
    
    if [ -z "$version" ]; then
        log_error "Не указана версия"
        echo "Использование: $0 version <version>"
        exit 1
    fi
    
    VERSION="$version"
    log_info "Публикация версии: $VERSION"
    publish_images
}

# Публикация latest версии
publish_latest() {
    log_info "Публикация latest версии"
    VERSION="latest"
    publish_images
}

# Показать справку
show_help() {
    echo "Скрипт публикации образов SEO Link Recommender в Docker Hub"
    echo ""
    echo "Использование:"
    echo "  $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  latest              Публикация latest версии"
    echo "  version <version>   Публикация конкретной версии"
    echo "  help                Показать эту справку"
    echo ""
    echo "Переменные окружения:"
    echo "  DOCKER_USERNAME     Имя пользователя Docker Hub (по умолчанию: your-username)"
    echo "  VERSION            Версия для публикации (по умолчанию: latest)"
    echo ""
    echo "Примеры:"
    echo "  $0 latest"
    echo "  $0 version v1.0.0"
    echo "  DOCKER_USERNAME=myuser $0 latest"
}

# Обработка аргументов командной строки
case "${1:-latest}" in
    "latest")
        publish_latest
        ;;
    "version")
        publish_versioned "$2"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        log_error "Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac

log_success "Публикация завершена!" 