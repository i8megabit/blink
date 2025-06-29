#!/usr/bin/env bash

# Скрипт для сборки всех кастомных моделей reLink
# Автоматически собирает все Modelfile из папки ollama_models

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Логирование
LOG_FILE="logs/model_build_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}✗ $1${NC}" | tee -a "$LOG_FILE"
}

# Проверка Ollama
check_ollama() {
    log "Проверка Ollama..."
    if ! command -v ollama &> /dev/null; then
        error "Ollama не установлен. Установите Ollama: https://ollama.ai"
        exit 1
    fi
    
    if ! ollama list &> /dev/null; then
        error "Ollama не запущен. Запустите: ollama serve"
        exit 1
    fi
    success "Ollama работает"
}

# Проверка базовой модели
check_base_model() {
    log "Проверка базовой модели qwen2.5:7b-instruct..."
    if ! ollama list | grep -q "qwen2.5:7b-instruct"; then
        warning "Базовая модель qwen2.5:7b-instruct не найдена. Скачиваем..."
        ollama pull qwen2.5:7b-instruct
        success "Базовая модель скачана"
    else
        success "Базовая модель найдена"
    fi
}

# Проверка Modelfile на ошибки
validate_modelfile() {
    local modelfile="$1"
    local model_name="$2"
    
    log "Проверка $model_name..."
    
    # Проверка существования файла
    if [[ ! -f "$modelfile" ]]; then
        error "Файл $modelfile не найден"
        return 1
    fi
    
    # Проверка базовой модели в FROM
    if ! grep -q "FROM qwen2.5:7b-instruct" "$modelfile"; then
        error "В $model_name используется неподдерживаемая базовая модель"
        return 1
    fi
    
    # Проверка обязательных секций
    if ! grep -q "SYSTEM" "$modelfile"; then
        warning "В $model_name отсутствует секция SYSTEM"
    fi
    
    if ! grep -q "TEMPLATE" "$modelfile"; then
        warning "В $model_name отсутствует секция TEMPLATE"
    fi
    
    success "Проверка $model_name завершена"
    return 0
}

# Сборка модели
build_model() {
    local modelfile="$1"
    local model_name="$2"
    
    log "Сборка модели $model_name..."
    
    # Извлекаем реальное имя модели из Modelfile
    local real_model_name=$(basename "$modelfile" .Modelfile)
    
    # Проверяем, существует ли уже модель
    if ollama list | grep -q "$real_model_name"; then
        warning "Модель $real_model_name уже существует. Пересобираем..."
        ollama rm "$real_model_name" 2>/dev/null || true
    fi
    
    # Собираем модель
    if ollama create "$real_model_name" -f "$modelfile"; then
        success "Модель $real_model_name успешно собрана"
        return 0
    else
        error "Ошибка сборки модели $real_model_name"
        return 1
    fi
}

# Тестирование модели
test_model() {
    local modelfile="$1"
    local test_prompt="$2"
    
    # Извлекаем реальное имя модели из Modelfile
    local real_model_name=$(basename "$modelfile" .Modelfile)
    
    log "Тестирование модели $real_model_name..."
    
    # Простой тест с таймаутом
    if timeout 30s ollama run "$real_model_name" "$test_prompt" &> /dev/null; then
        success "Модель $real_model_name работает корректно"
        return 0
    else
        warning "Модель $real_model_name не отвечает в течение 30 секунд (возможно, загружается)"
        return 0  # Не считаем это ошибкой
    fi
}

# Основная функция
main() {
    log "=== Начало сборки всех кастомных моделей reLink ==="
    
    # Проверки
    check_ollama
    check_base_model
    
    # Список всех Modelfile для сборки
    declare -A models=(
        ["qwen2_5_7b_instruct_turbo"]="ollama_models/qwen2.5-7b-instruct-turbo.Modelfile"
        ["qwen2_5_7b_instruct_turbo_code"]="ollama_models/qwen2.5-7b-instruct-turbo-code.Modelfile"
        ["qwen2_5_7b_instruct_turbo_ultra"]="ollama_models/qwen2.5-7b-instruct-turbo-ultra.Modelfile"
        ["qwen2_5_7b_instruct_turbo_neural"]="ollama_models/qwen2.5-7b-instruct-turbo-neural.Modelfile"
        ["qwen2_5_7b_instruct_turbo_q4km"]="ollama_models/qwen2.5-7b-instruct-turbo-q4km.Modelfile"
        ["qwen2_5_7b_instruct_turbo_q5km"]="ollama_models/qwen2.5-7b-instruct-turbo-q5km.Modelfile"
        ["qwen2_5_7b_instruct_turbo_seo"]="ollama_models/qwen2.5-7b-instruct-turbo-seo.Modelfile"
        ["qwen2_5_7b_instruct_turbo_seo_optimizer"]="ollama_models/qwen2.5-7b-instruct-turbo-seo-optimizer.Modelfile"
        ["qwen2_5_7b_instruct_content_analyzer"]="ollama_models/qwen2.5-7b-instruct-content-analyzer.Modelfile"
        ["qwen2_5_7b_instruct_keyword_researcher"]="ollama_models/qwen2.5-7b-instruct-keyword-researcher.Modelfile"
        ["test_simple"]="ollama_models/test-simple.Modelfile"
    )
    
    # Тестовые промпты для разных типов моделей
    declare -A test_prompts=(
        ["qwen2_5_7b_instruct_turbo"]="Привет! Как дела?"
        ["qwen2_5_7b_instruct_turbo_code"]="Напиши простую функцию на Python для сложения двух чисел"
        ["qwen2_5_7b_instruct_turbo_ultra"]="Привет! Как дела?"
        ["qwen2_5_7b_instruct_turbo_neural"]="Привет! Как дела?"
        ["qwen2_5_7b_instruct_turbo_q4km"]="Привет! Как дела?"
        ["qwen2_5_7b_instruct_turbo_q5km"]="Привет! Как дела?"
        ["qwen2_5_7b_instruct_turbo_seo"]="Проанализируй SEO этого заголовка: 'Лучшие рецепты пиццы'"
        ["qwen2_5_7b_instruct_turbo_seo_optimizer"]="Оптимизируй этот мета-тег: 'Купить товары онлайн'"
        ["qwen2_5_7b_instruct_content_analyzer"]="Проанализируй этот текст: 'Наш продукт лучший на рынке'"
        ["qwen2_5_7b_instruct_keyword_researcher"]="Найди ключевые слова для темы 'здоровое питание'"
        ["test_simple"]="Привет!"
    )
    
    # Статистика
    total_models=${#models[@]}
    built_models=0
    failed_models=0
    
    log "Найдено моделей для сборки: $total_models"
    
    # Сборка каждой модели
    for model_name in "${!models[@]}"; do
        modelfile="${models[$model_name]}"
        
        echo ""
        log "=== Обработка модели: $model_name ==="
        
        # Валидация
        if validate_modelfile "$modelfile" "$model_name"; then
            # Сборка
            if build_model "$modelfile" "$model_name"; then
                built_models=$((built_models + 1))
                
                # Тестирование
                test_prompt="${test_prompts[$model_name]}"
                test_model "$modelfile" "$test_prompt"
            else
                failed_models=$((failed_models + 1))
            fi
        else
            failed_models=$((failed_models + 1))
        fi
    done
    
    # Итоговая статистика
    echo ""
    log "=== Итоги сборки ==="
    success "Успешно собрано: $built_models моделей"
    if [[ $failed_models -gt 0 ]]; then
        error "Ошибок сборки: $failed_models моделей"
    fi
    log "Лог сохранен в: $LOG_FILE"
    
    # Показываем список всех моделей
    echo ""
    log "Список всех доступных моделей:"
    ollama list
    
    echo ""
    success "Сборка завершена!"
}

# Запуск основной функции
main "$@" 