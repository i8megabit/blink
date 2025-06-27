#!/bin/bash

echo "🔍 Мониторинг запуска Ollama..."
echo "⏰ $(date)"
echo ""

# Функция для проверки статуса
check_status() {
    local container_name="relink-ollama-1"
    
    echo "📊 Статус контейнера:"
    docker ps --filter "name=$container_name" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    echo "🔄 Последние 10 строк логов:"
    docker logs $container_name --tail 10 2>/dev/null || echo "❌ Контейнер не найден"
    echo ""
    
    # Проверка API
    echo "🌐 Проверка API:"
    curl -s -m 5 http://localhost:11434/api/tags >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ API доступно"
        # Получаем список моделей
        models=$(curl -s -m 5 http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | sed 's/"name":"\([^"]*\)"/\1/' | tr '\n' ', ')
        echo "📋 Модели: $models"
    else
        echo "❌ API недоступно"
    fi
    echo ""
}

# Мониторинг в цикле
counter=0
max_checks=30  # 5 минут (30 * 10 секунд)

while [ $counter -lt $max_checks ]; do
    counter=$((counter + 1))
    echo "🔄 Проверка $counter/$max_checks"
    
    check_status
    
    # Проверяем готовность модели
    if curl -s -m 5 http://localhost:11434/api/tags | grep -q "qwen2.5:7b-optimized"; then
        echo "🎉 Модель qwen2.5:7b-optimized готова!"
        
        # Быстрый тест генерации
        echo "🧪 Тест генерации..."
        response=$(curl -s -m 30 -X POST http://localhost:11434/api/generate \
            -H "Content-Type: application/json" \
            -d '{"model":"qwen2.5:7b-optimized","prompt":"Скажи привет","stream":false,"options":{"num_predict":5}}')
        
        if [ $? -eq 0 ] && [ ! -z "$response" ]; then
            echo "✅ Генерация работает!"
            echo "📝 Ответ: $(echo $response | grep -o '"response":"[^"]*"' | sed 's/"response":"\([^"]*\)"/\1/')"
        else
            echo "❌ Генерация не работает"
        fi
        
        echo ""
        echo "🚀 Ollama готов к работе!"
        exit 0
    fi
    
    echo "⏳ Ожидание 10 секунд..."
    sleep 10
    echo "────────────────────────────────────────"
done

echo "⏰ Время ожидания истекло"
echo "❌ Возможны проблемы с запуском Ollama"
exit 1 