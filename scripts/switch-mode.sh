#!/bin/bash

# 🔄 ПЕРЕКЛЮЧАТЕЛЬ РЕЖИМОВ для Apple M4
# Быстрое переключение между контейнерным и нативным GPU режимами

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

show_help() {
    echo "🔄 Переключатель режимов Ollama"
    echo ""
    echo "Использование:"
    echo "  $0 container  - Запуск в контейнерном режиме"
    echo "  $0 native     - Запуск в нативном GPU режиме"
    echo "  $0 status     - Показать текущий статус"
    echo "  $0 stop       - Остановить все службы"
    echo ""
    echo "Режимы:"
    echo "  📦 container - Docker контейнеры, CPU оптимизация (~15-25 tok/s)"
    echo "  ⚡ native    - Нативная Ollama с GPU (~40-60 tok/s)"
}

check_status() {
    echo "🔍 Проверка статуса служб..."
    
    # Проверяем контейнеры
    if docker-compose ps | grep -q "ollama.*Up"; then
        echo "📦 Контейнерная Ollama: ЗАПУЩЕНА"
        CONTAINER_STATUS="running"
    else
        echo "📦 Контейнерная Ollama: остановлена"
        CONTAINER_STATUS="stopped"
    fi
    
    # Проверяем нативную Ollama
    if pgrep -f "ollama serve" > /dev/null; then
        echo "⚡ Нативная Ollama: ЗАПУЩЕНА"
        NATIVE_STATUS="running"
    else  
        echo "⚡ Нативная Ollama: остановлена"
        NATIVE_STATUS="stopped"
    fi
    
    # Проверяем доступность API
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "🌐 API доступен на: http://localhost:11434"
        echo "📋 Доступные модели:"
        curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "   Не удалось получить список моделей"
    else
        echo "❌ API недоступен на порту 11434"
    fi
}

stop_all() {
    echo "🛑 Останавливаем все службы..."
    
    # Остановка контейнеров
    if docker-compose ps | grep -q "Up"; then
        echo "📦 Останавливаем контейнеры..."
        docker-compose down
    fi
    
    # Остановка нативной Ollama
    if pgrep -f "ollama serve" > /dev/null; then
        echo "⚡ Останавливаем нативную Ollama..."
        pkill -f "ollama serve" || true
        sleep 2
    fi
    
    echo "✅ Все службы остановлены"
}

start_container_mode() {
    echo "📦 Переключение в контейнерный режим..."
    
    # Останавливаем нативную версию если запущена
    if pgrep -f "ollama serve" > /dev/null; then
        echo "🛑 Останавливаем нативную Ollama..."  
        pkill -f "ollama serve" || true
        sleep 2
    fi
    
    # Запускаем контейнеры
    echo "🚀 Запускаем контейнеры..."
    cd "$PROJECT_DIR"
    docker-compose up -d
    
    echo "⏳ Ждем запуска служб..."
    sleep 10
    
    # Проверяем готовность
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Контейнерный режим готов!"
            echo "🌐 Доступ: http://localhost:8000 (backend), http://localhost:3000 (frontend)"
            return 0
        fi
        echo "⏳ Ожидание... ($i/30)"
        sleep 2
    done
    
    echo "❌ Не удалось запустить контейнерный режим за 60 секунд"
    return 1
}

start_native_mode() {
    echo "⚡ Переключение в нативный GPU режим..."
    
    # Проверяем установку Ollama
    if ! command -v ollama &> /dev/null; then
        echo "❌ Ollama не установлена локально"
        echo "💡 Запустите: ./scripts/native-gpu-setup.sh"
        return 1
    fi
    
    # Останавливаем контейнеры
    if docker-compose ps | grep -q "Up"; then
        echo "🛑 Останавливаем контейнеры..."
        docker-compose down
    fi
    
    # Настраиваем переменные среды
    export OLLAMA_HOST=0.0.0.0:11434
    export OLLAMA_MODELS="$PROJECT_DIR/data/ollama_models"
    export OLLAMA_METAL=1
    export OLLAMA_FLASH_ATTENTION=1
    export OLLAMA_KV_CACHE_TYPE=q8_0
    export OLLAMA_GPU_LAYERS=-1
    export OLLAMA_NUM_PARALLEL=4
    export OLLAMA_KEEP_ALIVE=3h
    
    # Запускаем нативную Ollama в фоне
    echo "🚀 Запускаем нативную Ollama с GPU..."
    nohup ollama serve > /tmp/ollama-native.log 2>&1 &
    OLLAMA_PID=$!
    
    echo "⏳ Ждем запуска нативной Ollama..."
    sleep 5
    
    # Проверяем готовность
    for i in {1..20}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✅ Нативная Ollama запущена (PID: $OLLAMA_PID)"
            
            # Запускаем только backend и frontend в контейнерах
            echo "🚀 Запускаем backend и frontend..."
            docker-compose -f docker-compose.native-gpu.yml up -d
            
            echo "✅ Нативный GPU режим готов!"
            echo "🌐 Доступ: http://localhost:8001 (backend), http://localhost:3001 (frontend)"  
            echo "📊 Логи Ollama: tail -f /tmp/ollama-native.log"
            echo "🛑 Остановка: kill $OLLAMA_PID"
            return 0
        fi
        echo "⏳ Ожидание... ($i/20)"
        sleep 1
    done
    
    echo "❌ Не удалось запустить нативную Ollama"
    kill $OLLAMA_PID 2>/dev/null || true
    return 1
}

# Главная логика
cd "$PROJECT_DIR"

case "${1:-help}" in
    "container"|"docker")
        start_container_mode
        ;;
    "native"|"gpu") 
        start_native_mode
        ;;
    "status"|"check")
        check_status
        ;;
    "stop"|"down")
        stop_all
        ;;
    "help"|"-h"|"--help"|*)
        show_help
        ;;
esac 