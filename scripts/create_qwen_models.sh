#!/bin/bash

# Скрипт для создания оптимизированных моделей Qwen2.5 для Mac M4
# Автор: AI Assistant
# Дата: $(date)

set -e

echo "🚀 Создание оптимизированных моделей Qwen2.5 для Mac M4"
echo "=================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
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

# Проверка наличия Ollama
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        log_error "Ollama не установлен. Установите Ollama: https://ollama.ai"
        exit 1
    fi
    log_success "Ollama найден: $(ollama --version)"
}

# Проверка системы
check_system() {
    if [[ $(uname -m) == "arm64" ]]; then
        log_success "Обнаружен Apple Silicon"
        if [[ $(sysctl -n machdep.cpu.brand_string) == *"M4"* ]]; then
            log_success "Обнаружен Mac M4 - максимальная оптимизация"
        else
            log_warning "Apple Silicon обнаружен, но не M4. Оптимизация может быть не максимальной"
        fi
    else
        log_warning "Не Apple Silicon. Оптимизация может быть не оптимальной"
    fi
}

# Создание модели
create_model() {
    local model_name=$1
    local modelfile_path=$2
    local description=$3
    
    log_info "Создание модели: $model_name"
    log_info "Описание: $description"
    
    if [ -f "$modelfile_path" ]; then
        log_info "Использование Modelfile: $modelfile_path"
        ollama create "$model_name" -f "$modelfile_path"
    else
        log_error "Modelfile не найден: $modelfile_path"
        return 1
    fi
    
    if [ $? -eq 0 ]; then
        log_success "Модель $model_name создана успешно"
    else
        log_error "Ошибка при создании модели $model_name"
        return 1
    fi
}

# Тестирование модели
test_model() {
    local model_name=$1
    local test_prompt="Привет! Как дела? Ответь кратко."
    
    log_info "Тестирование модели: $model_name"
    
    # Проверка доступности модели
    if ollama list | grep -q "$model_name"; then
        log_success "Модель $model_name доступна"
        
        # Быстрый тест
        log_info "Выполнение быстрого теста..."
        response=$(ollama run "$model_name" "$test_prompt" --timeout 30s 2>/dev/null || echo "Тест не выполнен")
        
        if [[ $response != "Тест не выполнен" ]]; then
            log_success "Модель $model_name работает корректно"
        else
            log_warning "Модель $model_name создана, но тест не выполнен"
        fi
    else
        log_error "Модель $model_name не найдена"
        return 1
    fi
}

# Основная функция
main() {
    log_info "Начало процесса создания моделей"
    
    # Проверки
    check_ollama
    check_system
    
    # Создание моделей
    models=(
        "qwen2.5-7b-instruct-turbo:latest|ollama_models/qwen2.5-7b-instruct-turbo.Modelfile|Базовая оптимизированная модель для M4"
        "qwen2.5-7b-instruct-turbo-q4km:latest|ollama_models/qwen2.5-7b-instruct-turbo-q4km.Modelfile|Q4_K_M квантизация - лучший баланс качество/производительность"
        "qwen2.5-7b-instruct-turbo-q5km:latest|ollama_models/qwen2.5-7b-instruct-turbo-q5km.Modelfile|Q5_K_M квантизация - высокая точность"
        "qwen2.5-7b-instruct-turbo-neural:latest|ollama_models/qwen2.5-7b-instruct-turbo-neural.Modelfile|Специализация под Neural Engine"
        "qwen2.5-7b-instruct-turbo-ultra:latest|ollama_models/qwen2.5-7b-instruct-turbo-ultra.Modelfile|Ультра-оптимизация для максимальной производительности"
        "qwen2.5-7b-instruct-turbo-code:latest|ollama_models/qwen2.5-7b-instruct-turbo-code.Modelfile|Специализация для программирования и разработки"
    )
    
    successful_models=()
    failed_models=()
    
    for model_info in "${models[@]}"; do
        IFS='|' read -r model_name modelfile_path description <<< "$model_info"
        
        if create_model "$model_name" "$modelfile_path" "$description"; then
            successful_models+=("$model_name")
            test_model "$model_name"
        else
            failed_models+=("$model_name")
        fi
        
        echo ""
    done
    
    # Итоговый отчет
    echo "=================================================="
    log_info "ИТОГОВЫЙ ОТЧЕТ"
    echo "=================================================="
    
    if [ ${#successful_models[@]} -gt 0 ]; then
        log_success "Успешно созданные модели (${#successful_models[@]}):"
        for model in "${successful_models[@]}"; do
            echo "  ✅ $model"
        done
    fi
    
    if [ ${#failed_models[@]} -gt 0 ]; then
        log_error "Неудачные модели (${#failed_models[@]}):"
        for model in "${failed_models[@]}"; do
            echo "  ❌ $model"
        done
    fi
    
    # Рекомендации по использованию
    echo ""
    log_info "РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ:"
    echo "=================================================="
    echo "1. qwen2.5-7b-instruct-turbo-q4km - для повседневных задач (РЕКОМЕНДУЕМАЯ)"
    echo "2. qwen2.5-7b-instruct-turbo-q5km - для задач требующих высокой точности"
    echo "3. qwen2.5-7b-instruct-turbo-neural - для AI-интенсивных задач"
    echo "4. qwen2.5-7b-instruct-turbo-ultra - для максимальной производительности"
    echo "5. qwen2.5-7b-instruct-turbo-code - для программирования и разработки"
    echo "6. qwen2.5-7b-instruct-turbo - базовая модель для тестирования"
    echo ""
    echo "Команды для запуска:"
    echo "  ollama run qwen2.5-7b-instruct-turbo-q4km"
    echo "  ollama run qwen2.5-7b-instruct-turbo-q5km"
    echo "  ollama run qwen2.5-7b-instruct-turbo-neural"
    echo "  ollama run qwen2.5-7b-instruct-turbo-ultra"
    echo "  ollama run qwen2.5-7b-instruct-turbo-code"
    
    log_success "Процесс завершен!"
}

# Запуск основной функции
main "$@" 