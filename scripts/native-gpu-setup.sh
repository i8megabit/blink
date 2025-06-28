#!/bin/bash

# 🚀 NATIVE GPU SETUP for Apple M4
# Скрипт для запуска Ollama с полным GPU на M4

set -e

echo "🔥 Настройка нативного GPU режима для Apple M4..."

# Проверяем установку Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama не установлена. Устанавливаем..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Останавливаем контейнерную версию если запущена
echo "🛑 Останавливаем контейнерную версию..."
docker-compose down 2>/dev/null || true

# Используем общую папку моделей с контейнерной версией
MODELS_DIR="$(pwd)/data/ollama_models"
mkdir -p "$MODELS_DIR"

echo "📦 Используем общие модели из: $MODELS_DIR"
echo "💡 Модели будут доступны и в контейнерной, и в нативной версии"

# Экспортируем переменные окружения для максимальной производительности
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_MODELS="$MODELS_DIR"

# 🔥 МАКСИМАЛЬНАЯ ОПТИМИЗАЦИЯ ДЛЯ APPLE M4 GPU
export OLLAMA_METAL=1                    # Включаем Metal Performance Shaders
export OLLAMA_FLASH_ATTENTION=1          # Flash Attention для GPU
export OLLAMA_KV_CACHE_TYPE=q8_0         # Квантованный кэш
export OLLAMA_GPU_LAYERS=-1              # Все слои на GPU
export OLLAMA_NUM_PARALLEL=4             # Параллельные запросы
export OLLAMA_MAX_LOADED_MODELS=3        # Больше моделей в памяти
export OLLAMA_KEEP_ALIVE=3h              # Дольше держим модели
export OLLAMA_MAX_TOKENS=8192            # Больше токенов для GPU
export OLLAMA_CONTEXT_LENGTH=8192        # Больший контекст
export OLLAMA_BATCH_SIZE=1024            # Больший батч для GPU

# Запускаем сервер в фоне
echo "🚀 Запускаем Ollama сервер с GPU..."
ollama serve &
OLLAMA_PID=$!

# Ждем запуска
sleep 10

echo "📥 Проверяем и загружаем модели..."

# Проверяем существующие модели
if ollama list | grep -q "qwen2.5:7b"; then
    echo "✅ qwen2.5:7b уже существует"
else
    echo "📥 Загружаем qwen2.5:7b..."
    ollama pull qwen2.5:7b
fi

if ollama list | grep -q "qwen2.5:7b-instruct"; then
    echo "✅ qwen2.5:7b-instruct уже существует"  
else
    echo "📥 Загружаем qwen2.5:7b-instruct..."
    ollama pull qwen2.5:7b-instruct
fi

echo "⚡ Создаем GPU-оптимизированные модели..."

# GPU TURBO модель
ollama create qwen2.5:7b-turbo -f - <<EOF
FROM qwen2.5:7b
# 🔥 GPU TURBO параметры для Apple M4
PARAMETER num_ctx 8192
PARAMETER num_batch 1024
PARAMETER num_thread 12
PARAMETER num_gpu -1
PARAMETER f16_kv true
PARAMETER use_mmap true
PARAMETER use_mlock true
PARAMETER num_predict 4096
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER seed 42
EOF

# GPU INSTRUCT TURBO модель
ollama create qwen2.5:7b-instruct-turbo -f - <<EOF
FROM qwen2.5:7b-instruct
# 🎯 GPU INSTRUCT TURBO для SEO задач
PARAMETER num_ctx 8192
PARAMETER num_batch 1024
PARAMETER num_thread 12
PARAMETER num_gpu -1
PARAMETER f16_kv true
PARAMETER use_mmap true
PARAMETER use_mlock true
PARAMETER num_predict 4096
PARAMETER temperature 0.6
PARAMETER top_p 0.85
PARAMETER repeat_penalty 1.05
PARAMETER seed 42
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
EOF

echo "🏆 GPU модели готовы!"

# Тестируем производительность
echo "🧪 Тестируем GPU производительность..."
time ollama run qwen2.5:7b-turbo "Напиши короткий текст о SEO оптимизации сайтов"

echo ""
echo "✅ НАТИВНЫЙ GPU РЕЖИМ готов!"
echo "🌐 Ollama доступна на: http://localhost:11434"
echo "🔧 Для запуска приложения: docker-compose -f docker-compose.native-gpu.yml up"
echo ""
echo "📊 Для остановки:"
echo "   kill $OLLAMA_PID"
echo "   docker-compose -f docker-compose.native-gpu.yml down" 