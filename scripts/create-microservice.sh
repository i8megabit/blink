#!/bin/bash
# 🚀 create-microservice.sh - Автоматическое создание микросервиса

set -e

# Конфигурация
SERVICE_NAME=$1
SERVICE_PORT=$2
SERVICE_DESCRIPTION=$3

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Ошибка: Укажите имя микросервиса"
    echo "Использование: ./create-microservice.sh <service_name> <port> <description>"
    exit 1
fi

if [ -z "$SERVICE_PORT" ]; then
    echo "❌ Ошибка: Укажите порт микросервиса"
    echo "Использование: ./create-microservice.sh <service_name> <port> <description>"
    exit 1
fi

if [ -z "$SERVICE_DESCRIPTION" ]; then
    SERVICE_DESCRIPTION="Микросервис $SERVICE_NAME для reLink"
fi

echo "🚀 Создание микросервиса: $SERVICE_NAME"

# 1. Создание структуры папок
mkdir -p $SERVICE_NAME/{app,tests,scripts,config}
mkdir -p $SERVICE_NAME/app/{api,models,services,utils}

# 2. Создание Dockerfile
cat > $SERVICE_NAME/Dockerfile << EOF
# 🐳 $SERVICE_NAME - Микросервис reLink
FROM eberil/relink-base:latest

# Копирование кода сервиса
COPY . .

# Установка зависимостей сервиса
RUN pip install --no-cache-dir -r requirements.txt

# Открытие порта
EXPOSE $SERVICE_PORT

# Запуск сервиса
CMD ["python", "-m", "app.main"]
EOF

# 3. Создание docker-compose конфигурации
cat > $SERVICE_NAME/docker-compose.yml << EOF
version: '3.8'

services:
  $SERVICE_NAME:
    build:
      context: .
      dockerfile: Dockerfile
    image: eberil/relink-$SERVICE_NAME:latest
    ports:
      - "$SERVICE_PORT:$SERVICE_PORT"
    environment:
      - SERVICE_NAME=$SERVICE_NAME
      - SERVICE_PORT=$SERVICE_PORT
      - DATABASE_URL=postgresql+asyncpg://seo_user:seo_pass@db:5432/seo_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - redis
      - db
      - ollama
    networks:
      - relink-network

networks:
  relink-network:
    external: true
EOF

# 4. Создание основного приложения
cat > $SERVICE_NAME/app/main.py << EOF
"""
$SERVICE_NAME - Микросервис reLink
$SERVICE_DESCRIPTION
"""

from fastapi import FastAPI
from bootstrap.main import create_app, add_service_routes
from bootstrap.config import get_settings

# Создание приложения с бутстрапом
app = create_app(
    title="$SERVICE_NAME",
    description="$SERVICE_DESCRIPTION",
    version="1.0.0"
)

# Добавление роутов сервиса
from app.api import router
add_service_routes(app, router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=$SERVICE_PORT,
        reload=settings.DEBUG
    )
EOF

# 5. Создание API роутера
cat > $SERVICE_NAME/app/api/__init__.py << EOF
from fastapi import APIRouter
from .routes import router

__all__ = ["router"]
EOF

cat > $SERVICE_NAME/app/api/routes.py << EOF
from fastapi import APIRouter, Depends
from bootstrap.llm_router import get_llm_router
from bootstrap.rag_service import get_rag_service
from bootstrap.ollama_client import get_ollama_client
from bootstrap.monitoring import get_service_monitor
import uuid

router = APIRouter(tags=["$SERVICE_NAME"])

@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "$SERVICE_NAME",
        "description": "$SERVICE_DESCRIPTION"
    }

@router.get("/api/v1/endpoints")
async def get_endpoints():
    """Получение списка эндпоинтов"""
    return {
        "service": "$SERVICE_NAME",
        "endpoints": [
            "/health",
            "/api/v1/endpoints"
        ]
    }

@router.get("/api/v1/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    monitor = get_service_monitor()
    return monitor.get_metrics_summary()
EOF

# 6. Создание requirements.txt
cat > $SERVICE_NAME/requirements.txt << EOF
# Зависимости для $SERVICE_NAME
# Базовые зависимости уже включены в eberil/relink-base:latest

# Специфичные зависимости сервиса
# fastapi
# uvicorn
# pydantic
EOF

# 7. Создание тестов
cat > $SERVICE_NAME/tests/__init__.py << EOF
# Тесты для $SERVICE_NAME
EOF

cat > $SERVICE_NAME/tests/test_main.py << EOF
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Тест проверки здоровья"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "$SERVICE_NAME"

def test_endpoints():
    """Тест получения эндпоинтов"""
    response = client.get("/api/v1/endpoints")
    assert response.status_code == 200
    assert response.json()["service"] == "$SERVICE_NAME"

def test_metrics():
    """Тест получения метрик"""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert response.json()["service"] == "$SERVICE_NAME"
EOF

# 8. Создание Makefile
cat > $SERVICE_NAME/Makefile << EOF
.PHONY: build run test clean

SERVICE_NAME = $SERVICE_NAME
PORT = $SERVICE_PORT

build:
	docker build -t eberil/relink-\$(SERVICE_NAME):latest .

run:
	docker-compose up -d

test:
	pytest tests/ -v

clean:
	docker-compose down
	docker rmi eberil/relink-\$(SERVICE_NAME):latest || true
EOF

# 9. Создание README
cat > $SERVICE_NAME/README.md << EOF
# $SERVICE_NAME

$SERVICE_DESCRIPTION

## Запуск

\`\`\`bash
make build
make run
\`\`\`

## Тестирование

\`\`\`bash
make test
\`\`\`

## API

- Health check: http://localhost:$SERVICE_PORT/health
- Swagger UI: http://localhost:$SERVICE_PORT/docs
- Metrics: http://localhost:$SERVICE_PORT/metrics
EOF

# 10. Добавление в основной docker-compose.yml
echo "
  $SERVICE_NAME:
    build:
      context: ../$SERVICE_NAME
      dockerfile: Dockerfile
    image: eberil/relink-$SERVICE_NAME:latest
    ports:
      - \"$SERVICE_PORT:$SERVICE_PORT\"
    environment:
      - SERVICE_NAME=$SERVICE_NAME
      - SERVICE_PORT=$SERVICE_PORT
      - DATABASE_URL=postgresql+asyncpg://seo_user:seo_pass@db:5432/seo_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - redis
      - db
      - ollama
    networks:
      - relink-network" >> config/docker-compose.yml

# 11. Создание фронтенд интеграции
mkdir -p frontend/src/components/services
cat > frontend/src/components/services/$SERVICE_NAME.tsx << EOF
import React from 'react';
import { Card, Button, Badge } from '../ui';

interface $SERVICE_NAME^Props {
  serviceName: string;
  description: string;
}

export const $SERVICE_NAME^Component: React.FC<$SERVICE_NAME^Props> = ({
  serviceName,
  description
}) => {
  const [isConnected, setIsConnected] = React.useState(false);

  const testConnection = async () => {
    try {
      const response = await fetch(\`http://localhost:$SERVICE_PORT/health\`);
      setIsConnected(response.ok);
    } catch (error) {
      setIsConnected(false);
    }
  };

  return (
    <Card>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">{serviceName}</h3>
          <p className="text-gray-600">{description}</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant={isConnected ? "success" : "error"}>
            {isConnected ? "Connected" : "Disconnected"}
          </Badge>
          <Button onClick={testConnection} size="sm">
            Test
          </Button>
          <Button 
            onClick={() => window.open(\`http://localhost:$SERVICE_PORT/docs\`, '_blank')}
            size="sm"
            variant="outline"
          >
            Swagger
          </Button>
        </div>
      </div>
    </Card>
  );
};
EOF

# 12. Git операции
git add .
git commit -m "🚀 Add $SERVICE_NAME microservice

- Created service structure
- Added Docker configuration
- Integrated with bootstrap
- Added frontend integration
- Added tests

Service: $SERVICE_NAME
Port: $SERVICE_PORT
Description: $SERVICE_DESCRIPTION"

echo "✅ Микросервис $SERVICE_NAME успешно создан!"
echo "📁 Структура создана в папке: $SERVICE_NAME"
echo "🐳 Docker образ: eberil/relink-$SERVICE_NAME:latest"
echo "🌐 Порт: $SERVICE_PORT"
echo "📚 Swagger UI: http://localhost:$SERVICE_PORT/docs"
echo "🔗 Интеграция с фронтендом добавлена"
echo "📝 Git коммит создан"

echo ""
echo "🚀 Следующие шаги:"
echo "1. cd $SERVICE_NAME"
echo "2. make build"
echo "3. make run"
echo "4. Проверить http://localhost:$SERVICE_PORT/health" 