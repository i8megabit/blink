#!/bin/bash
# 🔍 Скрипт определения архитектуры для Docker сборки

set -e

echo "🔍 Определение архитектуры системы..."

# Определение архитектуры
ARCH=$(uname -m)
OS=$(uname -s)

echo "📋 Система: $OS"
echo "🏗️  Архитектура: $ARCH"

# Настройка переменных окружения для Docker
case $ARCH in
    "arm64"|"aarch64")
        echo "🍎 Обнаружена ARM64 архитектура (Apple Silicon)"
        export DOCKERFILE="Dockerfile.apple-silicon"
        export DOCKER_PLATFORM="linux/arm64"
        echo "✅ Используется Dockerfile.apple-silicon"
        ;;
    "x86_64"|"amd64")
        echo "💻 Обнаружена x86_64 архитектура"
        export DOCKERFILE="Dockerfile.base"
        export DOCKER_PLATFORM="linux/amd64"
        echo "✅ Используется Dockerfile.base"
        ;;
    *)
        echo "⚠️  Неизвестная архитектура: $ARCH"
        echo "🔄 Используется универсальный Dockerfile.base"
        export DOCKERFILE="Dockerfile.base"
        export DOCKER_PLATFORM="linux/amd64"
        ;;
esac

# Создание .env файла для docker-compose
cat > .env.architecture << EOF
# Автоматически сгенерировано скриптом detect-architecture.sh
# Архитектура: $ARCH
# Операционная система: $OS

# Dockerfile для llm_tuning
DOCKERFILE=$DOCKERFILE

# Платформа Docker
DOCKER_PLATFORM=$DOCKER_PLATFORM

# Дополнительные настройки для ARM64
$(if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    echo "# ARM64 оптимизации"
    echo "DOCKER_BUILDKIT=1"
    echo "COMPOSE_DOCKER_CLI_BUILD=1"
fi)
EOF

echo "📝 Создан файл .env.architecture"
echo "🚀 Для запуска с автоматическим определением архитектуры:"
echo "   source scripts/detect-architecture.sh && docker-compose -f 1-docker-compose.yml up -d"

# Экспорт переменных для текущей сессии
export $(cat .env.architecture | xargs)

echo "✅ Переменные окружения настроены для текущей сессии" 