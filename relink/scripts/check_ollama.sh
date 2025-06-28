#!/bin/bash

echo "🔍 Проверка состояния Ollama..."

# Проверка доступности API
echo "📡 Проверка API..."
curl -s http://localhost:11434/api/tags > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API доступно"
else
    echo "❌ API недоступно"
    exit 1
fi

# Список моделей
echo ""
echo "📋 Доступные модели:"
curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | sed 's/"name":"\([^"]*\)"/- \1/'

# Проверка памяти
echo ""
echo "💾 Использование памяти:"
free -h | grep -E "Mem:|Swap:"

# Тест модели
echo ""
echo "🧪 Тест генерации (короткий)..."
start_time=$(date +%s)
response=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b-instruct-turbo",
    "prompt": "Скажи 'Привет'",
    "stream": false,
    "options": {
      "num_predict": 10,
      "temperature": 0.1
    }
  }' --max-time 30)

end_time=$(date +%s)
duration=$((end_time - start_time))

if [ $? -eq 0 ] && [ ! -z "$response" ]; then
    echo "✅ Модель работает (${duration}с)"
    echo "   Ответ: $(echo $response | grep -o '"response":"[^"]*"' | sed 's/"response":"\([^"]*\)"/\1/')"
else
    echo "❌ Модель не отвечает или зависает"
fi

echo ""
echo "🔧 Рекомендации:"
echo "- Если модель зависает, перезапустите контейнер: docker-compose restart ollama"
echo "- Если не хватает памяти, увеличьте лимиты в docker-compose.yml"
echo "- Для полной переустановки: docker-compose down && docker volume rm relink_ollama_data && docker-compose up" 