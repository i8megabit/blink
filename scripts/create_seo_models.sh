#!/bin/bash

# Скрипт для создания SEO-специализированных моделей для проекта reLink
# Основа: qwen2.5:7b-instruct

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Проверка Ollama
check_ollama() {
    log "Проверка Ollama..."
    if ! command -v ollama &> /dev/null; then
        error "Ollama не установлен. Установите Ollama: https://ollama.ai"
        exit 1
    fi
    
    if ! ollama list &> /dev/null; then
        error "Ollama не запущен. Запустите: brew services start ollama"
        exit 1
    fi
    
    log "Ollama работает корректно"
}

# Проверка базовой модели
check_base_model() {
    log "Проверка базовой модели qwen2.5:7b-instruct..."
    
    if ollama list | grep -q "qwen2.5:7b-instruct"; then
        log "Базовая модель qwen2.5:7b-instruct найдена"
        return 0
    else
        warn "Базовая модель qwen2.5:7b-instruct не найдена"
        return 1
    fi
}

# Скачивание базовой модели
download_base_model() {
    log "Скачивание базовой модели qwen2.5:7b-instruct..."
    ollama pull qwen2.5:7b-instruct
    log "Базовая модель успешно скачана"
}

# Создание SEO модели
create_seo_model() {
    local model_name=$1
    local modelfile_path=$2
    local description=$3
    
    log "Создание модели: $model_name"
    log "Описание: $description"
    
    if [ ! -f "$modelfile_path" ]; then
        error "Modelfile не найден: $modelfile_path"
        return 1
    fi
    
    # Проверяем, существует ли модель
    if ollama list | grep -q "$model_name"; then
        warn "Модель $model_name уже существует. Удаляем старую версию..."
        ollama rm "$model_name"
    fi
    
    # Создаем новую модель
    log "Создание модели из $modelfile_path..."
    ollama create "$model_name" -f "$modelfile_path"
    
    if [ $? -eq 0 ]; then
        log "✅ Модель $model_name успешно создана"
    else
        error "❌ Ошибка при создании модели $model_name"
        return 1
    fi
}

# Тестирование модели
test_model() {
    local model_name=$1
    local test_prompt=$2
    
    log "Тестирование модели: $model_name"
    
    # Простой тест
    echo "Тестовый запрос: $test_prompt"
    echo "Ответ модели:"
    echo "---"
    
    # Запускаем тест с таймаутом
    timeout 30s ollama run "$model_name" "$test_prompt" || {
        warn "Тест модели $model_name прерван по таймауту (это нормально для первого запуска)"
    }
    
    echo "---"
    log "Тест модели $model_name завершен"
}

# Основная функция
main() {
    log "🚀 Запуск создания SEO моделей для проекта reLink"
    
    # Проверки
    check_ollama
    
    if ! check_base_model; then
        download_base_model
    fi
    
    # Создание моделей
    log "📝 Создание SEO-специализированных моделей..."
    
    # 1. Основная SEO модель
    create_seo_model \
        "qwen2.5-7b-instruct-seo" \
        "ollama_models/qwen2.5-7b-instruct-turbo-seo.Modelfile" \
        "Основная SEO модель для анализа и оптимизации"
    
    # 2. SEO оптимизатор
    create_seo_model \
        "qwen2.5-7b-instruct-seo-optimizer" \
        "ollama_models/qwen2.5-7b-instruct-turbo-seo-optimizer.Modelfile" \
        "Автоматический SEO оптимизатор контента"
    
    # 3. Анализатор контента
    create_seo_model \
        "qwen2.5-7b-instruct-content-analyzer" \
        "ollama_models/qwen2.5-7b-instruct-content-analyzer.Modelfile" \
        "Анализатор качества и SEO контента"
    
    # 4. Исследователь ключевых слов
    create_seo_model \
        "qwen2.5-7b-instruct-keyword-researcher" \
        "ollama_models/qwen2.5-7b-instruct-keyword-researcher.Modelfile" \
        "Исследователь и аналитик ключевых слов"
    
    # Тестирование моделей
    log "🧪 Тестирование созданных моделей..."
    
    test_model "qwen2.5-7b-instruct-seo" \
        "Проанализируй SEO оптимизацию для сайта интернет-магазина электроники"
    
    test_model "qwen2.5-7b-instruct-seo-optimizer" \
        "Оптимизируй этот заголовок для SEO: 'Наш продукт лучший'"
    
    test_model "qwen2.5-7b-instruct-content-analyzer" \
        "Оцени качество этого контента: 'Мы продаем товары. Наши товары хорошие.'"
    
    test_model "qwen2.5-7b-instruct-keyword-researcher" \
        "Найди связанные ключевые слова для 'купить ноутбук'"
    
    # Финальный отчет
    log "📊 Отчет о созданных моделях:"
    echo ""
    ollama list | grep "qwen2.5-7b-instruct"
    echo ""
    
    log "✅ Все SEO модели успешно созданы!"
    log "🎯 Модели готовы для использования в проекте reLink"
    
    # Инструкции по использованию
    echo ""
    info "📖 ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ:"
    echo ""
    echo "1. Основная SEO модель:"
    echo "   ollama run qwen2.5-7b-instruct-seo 'ваш запрос'"
    echo ""
    echo "2. SEO оптимизатор:"
    echo "   ollama run qwen2.5-7b-instruct-seo-optimizer 'ваш контент'"
    echo ""
    echo "3. Анализатор контента:"
    echo "   ollama run qwen2.5-7b-instruct-content-analyzer 'анализируемый контент'"
    echo ""
    echo "4. Исследователь ключевых слов:"
    echo "   ollama run qwen2.5-7b-instruct-keyword-researcher 'основное ключевое слово'"
    echo ""
}

# Обработка ошибок
trap 'error "Скрипт прерван пользователем"; exit 1' INT TERM

# Запуск основной функции
main "$@" 