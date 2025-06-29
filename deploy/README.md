# 🚀 Deploy - Развертывание и DevOps reLink

Система развертывания и DevOps для платформы reLink, включая CI/CD, мониторинг и автоматизацию.

## 🚀 Быстрый старт

```bash
# Клонирование репозитория
git clone https://github.com/your-username/relink.git
cd relink

# Настройка окружения
cp .env.example .env
nano .env

# Запуск системы
make up
```

## 🏗️ Архитектура

### Структура проекта
```
deploy/
├── docker/              # Docker конфигурации
├── kubernetes/          # Kubernetes манифесты
├── terraform/           # Infrastructure as Code
├── ansible/             # Ansible плейбуки
├── scripts/             # Скрипты автоматизации
├── monitoring/          # Мониторинг и алерты
├── ci-cd/               # CI/CD конфигурации
└── docs/                # Документация
```

## 🎯 Основные функции

### CI/CD Pipeline
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging
- Ручной деплой в продакшен

### Infrastructure as Code
- Terraform для облачной инфраструктуры
- Ansible для конфигурации серверов
- Docker для контейнеризации
- Kubernetes для оркестрации

### Мониторинг
- Prometheus для сбора метрик
- Grafana для визуализации
- AlertManager для уведомлений
- ELK Stack для логов

### Безопасность
- Сканирование уязвимостей
- Проверка зависимостей
- Аудит безопасности
- Управление секретами

## 🔧 Разработка

### Локальная разработка
```bash
# Запуск всей системы
make up

# Запуск отдельных сервисов
make up-frontend
make up-backend
make up-llm

# Просмотр логов
make logs
make logs-frontend
make logs-backend
```

### Тестирование
```bash
# Запуск всех тестов
make test

# Запуск конкретных тестов
make test-frontend
make test-backend
make test-selenium

# Покрытие кода
make test-coverage
```

### Сборка
```bash
# Сборка всех образов
make build

# Сборка конкретного образа
make build-frontend
make build-backend

# Публикация в registry
make publish
```

## 🐳 Docker

### Сборка образов
```bash
# Сборка с BuildKit
docker buildx build --platform linux/amd64,linux/arm64 -t eberil/relink:latest .

# Сборка для конкретной архитектуры
docker buildx build --platform linux/amd64 -t eberil/relink:amd64 .

# Сборка с кэшем
docker buildx build --cache-from eberil/relink:latest -t eberil/relink:latest .
```

### Docker Compose
```bash
# Запуск с продакшен конфигурацией
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Масштабирование сервисов
docker-compose up -d --scale backend=3

# Обновление сервисов
docker-compose pull && docker-compose up -d
```

## ☸️ Kubernetes

### Развертывание
```bash
# Применение манифестов
kubectl apply -f kubernetes/

# Проверка статуса
kubectl get pods
kubectl get services
kubectl get ingress

# Масштабирование
kubectl scale deployment relink-backend --replicas=5
```

### Helm Charts
```bash
# Установка через Helm
helm install relink ./helm/relink

# Обновление
helm upgrade relink ./helm/relink

# Удаление
helm uninstall relink
```

## ☁️ Облачная инфраструктура

### Terraform
```bash
# Инициализация
terraform init

# Планирование изменений
terraform plan

# Применение изменений
terraform apply

# Уничтожение инфраструктуры
terraform destroy
```

### Ansible
```bash
# Выполнение плейбука
ansible-playbook -i inventory playbook.yml

# Проверка синтаксиса
ansible-playbook --syntax-check playbook.yml

# Dry run
ansible-playbook --check playbook.yml
```

## 📊 Мониторинг

### Prometheus
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

### Grafana дашборды
```bash
# Импорт дашбордов
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @dashboards/relink-overview.json
```

### Алерты
```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://127.0.0.1:5001/'
```

## 🔒 Безопасность

### Сканирование уязвимостей
```bash
# Сканирование образов
trivy image eberil/relink:latest

# Сканирование зависимостей
trivy fs .

# Сканирование конфигурации
trivy config .
```

### Управление секретами
```bash
# Создание секрета
kubectl create secret generic relink-secrets \
  --from-literal=database-url=postgresql://user:pass@host:5432/db \
  --from-literal=api-key=your-api-key

# Применение секрета
kubectl apply -f secrets/
```

## 🚀 CI/CD

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push
        run: |
          docker buildx build --push -t eberil/relink:${{ github.sha }} .
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/relink-backend backend=eberil/relink:${{ github.sha }}
```

### GitLab CI
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - make test

build:
  stage: build
  script:
    - docker build -t eberil/relink:$CI_COMMIT_SHA .

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/relink-backend backend=eberil/relink:$CI_COMMIT_SHA
```

## 📈 Масштабирование

### Горизонтальное масштабирование
```bash
# Автоматическое масштабирование
kubectl autoscale deployment relink-backend --cpu-percent=80 --min=2 --max=10

# Ручное масштабирование
kubectl scale deployment relink-backend --replicas=5
```

### Вертикальное масштабирование
```yaml
# resources.yml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## 🔄 Backup и восстановление

### Backup базы данных
```bash
# Создание backup
pg_dump -h localhost -U user -d database > backup.sql

# Автоматический backup
crontab -e
0 2 * * * pg_dump -h localhost -U user -d database > /backups/backup_$(date +\%Y\%m\%d).sql
```

### Восстановление
```bash
# Восстановление из backup
psql -h localhost -U user -d database < backup.sql

# Восстановление в Kubernetes
kubectl exec -it postgres-pod -- psql -U user -d database < backup.sql
```

## 📚 Дополнительная документация

- [Docker конфигурации](docker/)
- [Kubernetes манифесты](kubernetes/)
- [Terraform конфигурации](terraform/)
- [Ansible плейбуки](ansible/)
- [CI/CD конфигурации](ci-cd/) 