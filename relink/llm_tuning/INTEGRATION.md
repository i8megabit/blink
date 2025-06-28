# 🔗 Интеграция LLM Tuning с reLink

Руководство по интеграции LLM Tuning микросервиса с основным проектом reLink для создания мощной AI-платформы для SEO-инженеров.

## 🎯 Обзор интеграции

LLM Tuning микросервис предоставляет следующие возможности для reLink:

- **🧠 Умная маршрутизация** запросов к оптимальным LLM моделям
- **📚 RAG система** для работы с SEO базой знаний
- **⚡ Динамический тюнинг** моделей под специфические задачи
- **📊 Мониторинг** производительности и качества ответов
- **🍎 Оптимизация** для Apple Silicon (M1/M2/M3)

## 🏗️ Архитектура интеграции

```
┌─────────────────┐    HTTP/JSON    ┌──────────────────┐
│   reLink Main   │ ──────────────► │  LLM Tuning API  │
│   Application   │                 │   (Port 8001)    │
└─────────────────┘                 └──────────────────┘
         │                                   │
         │                                   ▼
         │                          ┌──────────────────┐
         │                          │   Ollama Models  │
         │                          │   (Port 11434)   │
         │                          └──────────────────┘
         │                                   │
         │                                   ▼
         │                          ┌──────────────────┐
         │                          │   ChromaDB RAG   │
         │                          │   (Port 8000)    │
         └──────────────────────────┴──────────────────┘
```

## 🚀 Быстрый старт

### 1. Запуск LLM Tuning микросервиса

```bash
# Переход в директорию LLM Tuning
cd relink/llm_tuning

# Копирование конфигурации для Apple Silicon
cp docker-compose.apple-silicon.yml docker-compose.yml
cp Makefile.apple-silicon Makefile

# Создание .env файла
cp .env.example .env

# Запуск всех сервисов
make setup-prod
```

### 2. Проверка работоспособности

```bash
# Проверка здоровья всех сервисов
make health

# Проверка API
curl http://localhost:8001/health

# Проверка Ollama
curl http://localhost:11434/api/tags
```

### 3. Интеграция с reLink

```bash
# В основном проекте reLink добавьте в .env:
LLM_TUNING_URL=http://localhost:8001
LLM_TUNING_API_KEY=apple-silicon-api-key-2024
LLM_TUNING_ENABLED=true
```

## 🔧 Настройка интеграции

### Конфигурация в основном проекте

#### 1. Добавление зависимостей

```python
# requirements.txt
aiohttp>=3.8.0
asyncio-mqtt>=0.11.0
```

#### 2. Создание клиента интеграции

```python
# app/llm_integration.py
from integration.relink_client import LLMTuningConfig, LLMTuningClient, ReLinkIntegration

# Конфигурация
llm_config = LLMTuningConfig(
    base_url=os.getenv("LLM_TUNING_URL", "http://localhost:8001"),
    api_key=os.getenv("LLM_TUNING_API_KEY", "apple-silicon-api-key-2024")
)

# Создание клиента
async def get_llm_client():
    return LLMTuningClient(llm_config)
```

#### 3. Интеграция в существующие сервисы

```python
# app/services/seo_service.py
from app.llm_integration import get_llm_client

class SEOService:
    def __init__(self):
        self.llm_client = None
    
    async def analyze_website(self, url: str):
        # Получение клиента LLM Tuning
        async with await get_llm_client() as client:
            integration = ReLinkIntegration(client)
            
            # Анализ SEO контента
            analysis = await integration.analyze_seo_content(
                content=website_content,
                domain=url
            )
            
            # Генерация рекомендаций
            recommendations = await integration.generate_seo_recommendations({
                "url": url,
                "type": "website",
                "audience": "general",
                "keywords": extracted_keywords,
                "issues": detected_issues
            })
            
            return {
                "analysis": analysis,
                "recommendations": recommendations
            }
```

### Настройка Docker Compose

#### 1. Обновление основного docker-compose.yml

```yaml
# В основном проекте reLink
services:
  # Существующие сервисы...
  
  # Интеграция с LLM Tuning
  llm-tuning:
    external: true
    name: llm-tuning_llm-tuning

networks:
  default:
    external: true
    name: llm-tuning_llm-tuning-network
```

#### 2. Переменные окружения

```bash
# .env
# LLM Tuning интеграция
LLM_TUNING_URL=http://llm-tuning:8001
LLM_TUNING_API_KEY=apple-silicon-api-key-2024
LLM_TUNING_ENABLED=true
LLM_TUNING_TIMEOUT=30
LLM_TUNING_MAX_RETRIES=3

# Настройки для Apple Silicon
OLLAMA_METAL=1
OLLAMA_FLASH_ATTENTION=1
OLLAMA_KV_CACHE_TYPE=q8_0
```

## 📊 Использование API

### Основные эндпоинты

#### 1. Анализ SEO контента

```python
# POST /api/v1/rag/query
{
    "query": "Проанализируй SEO контент",
    "model": "qwen2.5:7b-turbo",
    "top_k": 5,
    "include_sources": true
}
```

#### 2. Маршрутизация запросов

```python
# POST /api/v1/route
{
    "prompt": "Сгенерируй SEO рекомендации",
    "context": "Данные сайта...",
    "model": "qwen2.5:7b-turbo"
}
```

#### 3. Тюнинг моделей

```python
# POST /api/v1/tuning/sessions
{
    "model_id": 1,
    "training_data": [...],
    "strategy": "adaptive"
}
```

### Примеры использования

#### Анализ веб-страницы

```python
async def analyze_webpage(url: str):
    # Получение контента страницы
    content = await fetch_webpage_content(url)
    
    # Анализ через LLM Tuning
    async with LLMTuningClient(config) as client:
        integration = ReLinkIntegration(client)
        
        analysis = await integration.analyze_seo_content(
            content=content,
            domain=url
        )
        
        return analysis
```

#### Генерация SEO рекомендаций

```python
async def generate_recommendations(website_data: dict):
    async with LLMTuningClient(config) as client:
        integration = ReLinkIntegration(client)
        
        recommendations = await integration.generate_seo_recommendations(
            website_data=website_data
        )
        
        return recommendations
```

#### Оптимизация контента

```python
async def optimize_content(content: str, keywords: list):
    async with LLMTuningClient(config) as client:
        integration = ReLinkIntegration(client)
        
        optimized = await integration.optimize_content(
            content=content,
            target_keywords=keywords
        )
        
        return optimized
```

## 🔍 Мониторинг и отладка

### Проверка интеграции

```bash
# Проверка подключения
curl -H "Authorization: Bearer apple-silicon-api-key-2024" \
     http://localhost:8001/health

# Проверка моделей
curl http://localhost:8001/api/v1/models

# Проверка RAG
curl -X POST http://localhost:8001/api/v1/rag/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "model": "qwen2.5:7b-turbo"}'
```

### Логи и метрики

```bash
# Просмотр логов
make docker-logs

# Мониторинг метрик
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus

# Проверка производительности
make performance-test
```

### Устранение неполадок

#### Проблема: LLM Tuning недоступен

```bash
# Проверка статуса сервисов
make health

# Перезапуск сервисов
make restart

# Проверка логов
make docker-logs
```

#### Проблема: Медленные ответы

```bash
# Проверка настроек Apple Silicon
make optimize-models

# Проверка использования ресурсов
docker stats llm-tuning-apple-silicon

# Оптимизация параметров
# Увеличьте OLLAMA_MEM_FRACTION в .env
```

#### Проблема: Ошибки аутентификации

```bash
# Проверка API ключа
echo $LLM_TUNING_API_KEY

# Обновление ключа в .env
LLM_TUNING_API_KEY=apple-silicon-api-key-2024

# Перезапуск сервисов
make restart
```

## 🎛️ Продвинутая настройка

### Кастомные модели

```bash
# Создание специализированной модели для SEO
docker-compose exec ollama ollama create seo-expert -f Modelfile

# Modelfile:
FROM qwen2.5:7b-turbo
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
SYSTEM "Ты эксперт по SEO и веб-аналитике. Твоя задача - помогать оптимизировать веб-сайты для поисковых систем."
```

### Оптимизация производительности

```bash
# Настройка под ваше железо
# Apple M1 (8GB):
OLLAMA_MEM_FRACTION=0.7
OLLAMA_CONTEXT_LENGTH=2048
OLLAMA_BATCH_SIZE=256

# Apple M2 Pro (32GB):
OLLAMA_MEM_FRACTION=0.9
OLLAMA_CONTEXT_LENGTH=8192
OLLAMA_BATCH_SIZE=1024
```

### Масштабирование

```bash
# Горизонтальное масштабирование
docker-compose up -d --scale llm-tuning=3

# Настройка балансировщика нагрузки
# Добавьте nginx или traefik для распределения запросов
```

## 📈 Метрики и аналитика

### Ключевые метрики

- **Response Time**: время ответа API
- **Throughput**: количество запросов в секунду
- **Model Performance**: качество ответов моделей
- **Cache Hit Rate**: эффективность кэширования
- **Error Rate**: частота ошибок

### Дашборды Grafana

```bash
# Импорт дашбордов
# 1. Откройте Grafana: http://localhost:3000
# 2. Добавьте источник данных Prometheus
# 3. Импортируйте дашборды из grafana/dashboards/
```

## 🔒 Безопасность

### Настройки безопасности

```bash
# В .env файле:
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
RATE_LIMIT_PER_MINUTE=100
ENABLE_API_KEYS=true

# Настройка файрвола
sudo ufw allow 8001/tcp  # LLM Tuning API
sudo ufw allow 11434/tcp # Ollama
```

### Аудит и логирование

```bash
# Просмотр логов безопасности
docker-compose logs | grep -i "error\|warning\|security"

# Мониторинг API запросов
curl -H "X-API-Key: your-key" http://localhost:8001/api/v1/models
```

## 🚀 Продакшн деплой

### Подготовка к продакшну

```bash
# Настройка продакшн среды
make setup-prod

# Настройка резервного копирования
make backup

# Настройка мониторинга
make monitor
```

### CI/CD интеграция

```yaml
# .github/workflows/deploy.yml
name: Deploy LLM Tuning
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy LLM Tuning
        run: |
          cd relink/llm_tuning
          make docker-build
          make docker-run
          make health
```

## 📚 Дополнительные ресурсы

### Документация

- [LLM Tuning API Docs](http://localhost:8001/docs)
- [Ollama Documentation](https://ollama.ai/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)

### Сообщество

- [GitHub Issues](https://github.com/your-repo/issues)
- [Discord](https://discord.gg/your-server)
- [Telegram](https://t.me/your-channel)

## 🤝 Поддержка

Если у вас возникли проблемы с интеграцией:

1. Проверьте раздел [Устранение неполадок](#устранение-неполадок)
2. Запустите диагностику: `make apple-silicon-optimize`
3. Создайте issue в GitHub с логами: `make logs-tail`
4. Обратитесь в сообщество

---

**🔗 Интеграция LLM Tuning с reLink - Мощная AI-платформа для SEO-инженеров!** 