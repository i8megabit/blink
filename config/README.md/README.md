# ⚙️ Config - Конфигурация системы reLink

Централизованная конфигурация для всей платформы reLink, включая Docker Compose файлы, переменные окружения и настройки развертывания.

## 🚀 Быстрый старт

```bash
# Копирование конфигурации
cp config/docker-compose.yml .
cp config/docker.env .env

# Запуск системы
docker-compose up -d
```

## 🏗️ Архитектура

### Структура проекта
```
config/
├── docker-compose.yml           # Основной Docker Compose
├── docker-compose.buildkit.yml  # Сборка с BuildKit
├── docker-compose.native-gpu.yml # Нативная GPU поддержка
├── docker-compose.resources.yml # Ограничения ресурсов
├── docker-compose.simple.yml    # Упрощенная конфигурация
├── docker-compose.vite.yml      # Конфигурация для Vite
├── docker.env                   # Переменные окружения
├── docker-buildkit.env          # BuildKit переменные
├── kubernetes-deployments.yml   # Kubernetes развертывание
├── prometheus.yml               # Конфигурация Prometheus
├── resource_alerts.yml          # Алерты ресурсов
├── scripts/                     # Скрипты конфигурации
├── testing/                     # Тестовая конфигурация
├── VERSION/                     # Версии компонентов
└── README.md/                   # Документация
```

## 🎯 Основные функции

### Docker Compose конфигурации
- **Основная** - полная система с всеми сервисами
- **BuildKit** - оптимизированная сборка
- **Native GPU** - поддержка GPU для LLM
- **Resources** - ограничения ресурсов
- **Simple** - упрощенная для разработки
- **Vite** - конфигурация для frontend

### Переменные окружения
- Централизованное управление настройками
- Различные профили (dev, staging, prod)
- Безопасное хранение секретов
- Валидация конфигурации

### Kubernetes развертывание
- YAML манифесты для всех сервисов
- Service и Ingress конфигурации
- ConfigMaps и Secrets
- Horizontal Pod Autoscaling

## 🔧 Разработка

### Выбор конфигурации
```bash
# Основная конфигурация
docker-compose -f config/docker-compose.yml up -d

# С BuildKit
docker-compose -f config/docker-compose.buildkit.yml up -d

# С GPU поддержкой
docker-compose -f config/docker-compose.native-gpu.yml up -d

# С ограничениями ресурсов
docker-compose -f config/docker-compose.resources.yml up -d
```

### Переменные окружения
```bash
# Копирование переменных
cp config/docker.env .env

# Редактирование
nano .env

# Проверка конфигурации
docker-compose config
```

### Настройка ресурсов
```yaml
# docker-compose.resources.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## 🐳 Docker конфигурации

### Основная конфигурация
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

### BuildKit конфигурация
```yaml
# docker-compose.buildkit.yml
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      cache_from:
        - eberil/relink-base:latest
```

### GPU конфигурация
```yaml
# docker-compose.native-gpu.yml
services:
  llm-tuning:
    build: ./llm_tuning
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## ☸️ Kubernetes

### Развертывание сервисов
```yaml
# kubernetes-deployments.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: relink-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: relink-backend
  template:
    metadata:
      labels:
        app: relink-backend
    spec:
      containers:
      - name: backend
        image: eberil/relink-backend:latest
        ports:
        - containerPort: 8000
```

### Service и Ingress
```yaml
apiVersion: v1
kind: Service
metadata:
  name: relink-backend-service
spec:
  selector:
    app: relink-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

## 📊 Мониторинг

### Prometheus конфигурация
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'relink-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Алерты ресурсов
```yaml
# resource_alerts.yml
groups:
  - name: resource_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
```

## 🔒 Безопасность

### Переменные окружения
```bash
# .env
# База данных
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379

# API ключи
API_SECRET_KEY=your-secret-key

# LLM настройки
OLLAMA_URL=http://localhost:11434
```

### Secrets в Kubernetes
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: relink-secrets
type: Opaque
data:
  database-url: <base64-encoded>
  api-secret-key: <base64-encoded>
```

## 🚀 Деплой

### Локальная разработка
```bash
# Упрощенная конфигурация
docker-compose -f config/docker-compose.simple.yml up -d

# С hot reload
docker-compose -f config/docker-compose.vite.yml up -d
```

### Продакшен
```bash
# Основная конфигурация
docker-compose -f config/docker-compose.yml -f config/docker-compose.prod.yml up -d

# С мониторингом
docker-compose -f config/docker-compose.yml -f config/prometheus.yml up -d
```

### Kubernetes
```bash
# Применение конфигурации
kubectl apply -f config/kubernetes-deployments.yml

# Проверка статуса
kubectl get pods
kubectl get services
```

## 📚 Дополнительная документация

- [Docker Compose](docker-compose.yml)
- [Kubernetes](kubernetes-deployments.yml)
- [Prometheus](prometheus.yml)
- [Переменные окружения](docker.env) 