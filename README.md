# 🔗 SEO Link Recommender

> Интеллектуальная система генерации внутренних ссылок с использованием LLM и RAG

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![AI](https://img.shields.io/badge/AI-LLM%20+%20RAG-orange.svg)

## 🏗️ Архитектура решения

```mermaid
graph TB
    subgraph "🌐 Client Layer"
        U[👤 User] 
        B[🌍 Browser]
    end
    
    subgraph "🐳 Docker Environment"
        subgraph "Frontend Container :3000"
            F[⚛️ React Frontend<br/>HTML + JSX + CSS]
            N[🔧 Nginx<br/>Static Files Server]
        end
        
        subgraph "Backend Container :8000"
            API[🚀 FastAPI Backend<br/>Python 3.11]
            WS[🔌 WebSocket Manager<br/>Real-time Updates]
            RAG[📚 RAG Manager<br/>Semantic Search]
            AI[🧠 AI Thought Generator<br/>Intelligence Layer]
            CUM[🧬 Cumulative Manager<br/>Learning & Evolution]
        end
        
        subgraph "Database Container :5432"
            PG[(🗄️ PostgreSQL<br/>Domain Data)]
        end
        
        subgraph "LLM Container :11434"
            OL[🤖 Ollama<br/>qwen2.5:7b-turbo]
            M1[📝 Model 1<br/>7b-instruct-turbo]
            M2[📝 Model 2<br/>7b-base]
        end
        
        subgraph "Vector Database"
            CHR[(🔍 ChromaDB<br/>Embeddings & RAG)]
        end
    end
    
    %% User interactions
    U --> B
    B -.->|HTTP :3000| F
    F -.->|API :8000| API
    F -.->|WebSocket| WS
    
    %% Internal connections
    API -.-> PG
    API -.-> CHR
    API -.-> OL
    RAG -.-> CHR
    AI -.-> OL
    CUM -.-> PG
    
    %% Data flow
    API -.->|WordPress API| EXT[🌐 External WordPress Sites]
    
    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef backend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px  
    classDef database fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef llm fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef external fill:#fafafa,stroke:#424242,stroke-width:2px
    
    class F,N frontend
    class API,WS,RAG,AI,CUM backend
    class PG,CHR database
    class OL,M1,M2 llm
    class EXT external
```

## 📊 Архитектура данных

```mermaid
erDiagram
    DOMAINS ||--o{ WORDPRESS_POSTS : "содержит"
    DOMAINS ||--o{ THEMATIC_GROUPS : "группирует"
    DOMAINS ||--o{ ANALYSIS_HISTORY : "отслеживает"
    DOMAINS ||--o{ LINK_RECOMMENDATIONS : "генерирует"
    DOMAINS ||--o{ CUMULATIVE_INSIGHTS : "накапливает"

    WORDPRESS_POSTS ||--o{ ARTICLE_EMBEDDINGS : "векторизует"
    WORDPRESS_POSTS ||--o{ SEMANTIC_CONNECTIONS : "связывает"
    WORDPRESS_POSTS }o--|| THEMATIC_GROUPS : "принадлежит"

    SEMANTIC_CONNECTIONS ||--o{ LINK_RECOMMENDATIONS : "основа для"
    
    THEMATIC_GROUPS ||--o{ THEMATIC_CLUSTER_ANALYSIS : "анализирует"
    
    MODEL_CONFIGURATIONS ||--o{ BENCHMARK_RUNS : "тестирует"
    BENCHMARK_RUNS ||--o{ BENCHMARK_COMPARISONS : "сравнивает"

    DOMAINS {
        int id PK
        string name "example.com"
        string display_name
        string description  
        string language "ru/en"
        string category
        datetime created_at
        datetime updated_at
        bool is_active
        int total_posts
        int total_analyses
        datetime last_analysis_at
    }

    WORDPRESS_POSTS {
        int id PK
        int domain_id FK
        int thematic_group_id FK
        int wp_post_id "WordPress ID"
        string title
        text content
        text excerpt
        string link
        text semantic_summary "Для LLM"
        json key_concepts "Массив концепций"
        json entity_mentions "NER данные"
        string content_type "guide/review/news"
        string difficulty_level "easy/medium/hard"
        string target_audience
        float content_quality_score
        float semantic_richness "Плотность семантики"
        float linkability_score "Потенциал ссылок"
        datetime published_at
        datetime created_at
        datetime updated_at
        datetime last_analyzed_at
    }

    SEMANTIC_CONNECTIONS {
        int id PK
        int source_post_id FK
        int target_post_id FK
        string connection_type "semantic/topical/hierarchical"
        float strength "0.0-1.0"
        float confidence
        int usage_count "Накопительно"
        float success_rate
        float evolution_score "Эволюция связи"
        text connection_context "Объяснение"
        string suggested_anchor
        json alternative_anchors
        bool bidirectional
        json semantic_tags
        string theme_intersection
        datetime created_at
        datetime updated_at
        datetime validated_at
        datetime last_recommended_at
    }

    LINK_RECOMMENDATIONS {
        int id PK
        int domain_id FK  
        int source_post_id FK
        int target_post_id FK
        string anchor_text
        text reasoning
        float quality_score
        int generation_count "Сколько раз генерировалась"
        int improvement_iterations
        string status "active/deprecated/improved"
        int semantic_connection_id FK
        int previous_version_id FK "Эволюция"
        text improvement_reason
        datetime created_at
        datetime updated_at
    }

    CUMULATIVE_INSIGHTS {
        int id PK
        int domain_id FK
        string insight_type "pattern/gap/opportunity/trend"
        string insight_category "semantic/structural/thematic"
        string title
        text description
        json evidence "Подтверждающие данные"
        float impact_score
        float confidence_level
        float actionability
        json related_posts
        json related_clusters
        json related_connections
        string status "discovered/validated/applied"
        int applied_count
        datetime created_at
        datetime validated_at
    }
```

## ⚡ Поток обработки данных

```mermaid
flowchart TD
    subgraph "📊 Входные данные"
        WP[🌐 WordPress Sites<br/>REST API /wp-json/wp/v2/posts]
        USER[👤 User Input<br/>Domain URLs]
    end

    subgraph "🔄 Процесс обработки"
        FETCH[📥 Smart Fetching<br/>Delta Indexing]
        PARSE[🔍 Content Parsing<br/>BeautifulSoup + NLP]
        NLP[🧠 NLP Processing<br/>NLTK + TF-IDF]
        EMBED[📐 Vectorization<br/>ChromaDB Embeddings]
        CLUSTER[🎯 Thematic Clustering<br/>K-Means + Semantic Analysis]
    end

    subgraph "🤖 AI/LLM Слой"
        OLLAMA[🦙 Ollama LLM<br/>qwen2.5:7b-turbo]
        THOUGHT[💭 AI Thought Generator<br/>Intelligent Reasoning]
        CONTEXT[🧮 Context Builder<br/>RAG + Historical Data]
        GENERATE[⚡ Link Generation<br/>Semantic + Strategic]
    end

    subgraph "💾 Хранилища данных"
        PG[🗄️ PostgreSQL<br/>Structured Data]
        CHROMA[🔍 ChromaDB<br/>Vector Embeddings]
        CACHE[⚡ Memory Cache<br/>Hot Data]
    end

    subgraph "🧬 Кумулятивный интеллект"
        EVOLVE[🌱 Evolution Engine<br/>Learning from History]
        INSIGHTS[💡 Insight Generator<br/>Pattern Recognition]
        DEDUPE[🔄 Deduplication<br/>Smart Filtering]
        RANK[🎯 Intelligent Ranking<br/>Quality Scoring]
    end

    subgraph "📤 Выходные данные"
        API[🚀 REST API<br/>JSON Responses]
        WS[🔌 WebSocket<br/>Real-time Updates]
        RECS[📋 Link Recommendations<br/>with Reasoning]
    end

    USER --> FETCH
    WP --> FETCH
    FETCH --> PARSE
    PARSE --> NLP
    NLP --> EMBED
    EMBED --> CLUSTER
    
    PARSE --> PG
    EMBED --> CHROMA
    CLUSTER --> PG

    CLUSTER --> CONTEXT
    PG --> CONTEXT
    CHROMA --> CONTEXT
    CONTEXT --> OLLAMA
    OLLAMA --> THOUGHT
    THOUGHT --> GENERATE
    
    GENERATE --> EVOLVE
    PG --> EVOLVE
    EVOLVE --> INSIGHTS
    INSIGHTS --> DEDUPE
    DEDUPE --> RANK
    
    RANK --> CACHE
    INSIGHTS --> CACHE
    
    RANK --> API
    RANK --> WS
    API --> RECS
    WS --> RECS

    RECS -.->|👍 Feedback| EVOLVE
    CACHE -.->|📊 Analytics| INSIGHTS
```

## 🚀 Быстрый старт

### Требования
- **Docker Desktop** (рекомендуется)
- **Python 3.11+** (для разработки)
- **16GB RAM** (минимум для Ollama)

### 🐳 Запуск через Docker (рекомендуется)

```bash
git clone https://github.com/yourname/seo_link_recommender.git
cd seo_link_recommender
docker compose -f seo_link_recommender/docker-compose.yml up --build
```

**Доступные сервисы:**
- 🌍 **Frontend**: http://localhost:3000
- 🚀 **Backend API**: http://localhost:8000
- 🤖 **Ollama LLM**: http://localhost:11434
- 🗄️ **PostgreSQL**: localhost:5432

### 💻 Локальная разработка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r seo_link_recommender/backend/requirements.txt
export DATABASE_URL=postgresql+asyncpg://seo_user:seo_pass@localhost/seo_db
uvicorn app.main:app --app-dir seo_link_recommender/backend/app --reload
```

## 🤖 Конфигурация LLM

### Основная модель: qwen2.5:7b-turbo
- 🎯 **Оптимизирована для SEO задач**
- 🇷🇺 **Отличное понимание русского языка**
- ⚡ **Высокая скорость генерации**
- 💾 **Размер: ~4.3GB**

```bash
ollama pull qwen2.5:7b
```

### Альтернативные модели

| Модель | Размер | Сценарий использования |
|--------|--------|----------------------|
| `gemma3:1b` | ~1.8GB | 💡 Слабые устройства |
| `qwen2.5:7b-instruct` | ~4.3GB | 📝 Инструкции и гайды |
| `llama3.1:8b` | ~4.7GB | 🏆 Максимальное качество |
| `mistral:7b` | ~4.1GB | 📄 Текстовые задачи |

```bash
export OLLAMA_MODEL=имя_модели
```

## 🔗 API Endpoints

### Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/wp_index` | 🏠 **Основной эндпоинт** - индексация домена |
| `GET` | `/api/v1/models/available` | 🤖 Список доступных LLM моделей |
| `GET` | `/api/v1/domains` | 🌐 Список индексированных доменов |
| `GET` | `/api/v1/analysis_history` | 📊 История анализов |
| `GET` | `/api/v1/health` | ❤️ Проверка здоровья системы |
| `WS` | `/ws/{client_id}` | 🔌 WebSocket для прогресса |

### Пример запроса

```bash
curl -X POST "http://localhost:8000/api/v1/wp_index" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "client_id": "user123",
    "comprehensive": true
  }'
```

## 🧠 Возможности системы

### ✨ Интеллектуальные функции
- 🎯 **Семантический анализ** контента
- 🧮 **RAG-поиск** по векторным представлениям
- 🤖 **LLM-генерация** осмысленных связей
- 🧬 **Кумулятивное обучение** на исторических данных
- 💡 **Автоматические инсайты** и рекомендации

### 📊 Аналитика и метрики
- 📈 **Качество связей** (0.0-1.0)
- 🎲 **Семантическая плотность** контента
- 🔗 **Потенциал линковки** статей
- 📋 **История эволюции** рекомендаций
- 🎯 **Тематическая кластеризация**

### 🚀 Производительность
- ⚡ **~15-25 tokens/sec** в контейнерном режиме
- 🎭 **Двухрежимная система**: CPU + GPU
- 🔄 **Умная дельта-индексация**
- 💾 **Кэширование** горячих данных
- 🧠 **Отложенный прогрев** моделей

## 🧪 Тестирование

```bash
# Все тесты
python -m pytest -q

# Конкретные компоненты
python -m pytest seo_link_recommender/backend/tests/test_health.py -v
python -m pytest seo_link_recommender/backend/tests/test_wp.py -v
```

## 🔧 Настройка окружения

### Переменные окружения

```bash
# LLM конфигурация
export OLLAMA_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=qwen2.5:7b-turbo

# База данных
export DATABASE_URL=postgresql+asyncpg://seo_user:seo_pass@localhost/seo_db

# Производительность
export OLLAMA_CONTEXT_LENGTH=4096
export OLLAMA_BATCH_SIZE=512
export OLLAMA_NUM_PARALLEL=2
```

### Docker переменные

См. файл `docker-compose.yml` для полного списка оптимизационных переменных Apple M4.

## 📈 Мониторинг

- 🏥 **Health Check**: `GET /api/v1/health`
- 🤖 **Ollama Status**: `GET /api/v1/ollama_status`
- 📊 **Real-time WebSocket**: `/ws/{client_id}`
- 📝 **Логи Docker**: `docker compose logs -f`

## 🛠️ Разработка

### Структура проекта

```
seo_link_recommender/
├── 🌐 frontend/          # React UI
├── 🚀 backend/           # FastAPI + AI
├── 🗄️ postgres_data/    # База данных  
├── 📦 ollama_models/     # Модели LLM
├── 🔧 scripts/          # Утилиты
└── 📋 docker-compose.yml # Оркестрация
```

### Ключевые компоненты

- **IntelligentThoughtGenerator**: Генерация AI мыслей
- **AdvancedRAGManager**: Семантический поиск
- **CumulativeIntelligenceManager**: Обучение на данных
- **WebSocketManager**: Real-time обновления

## 📄 Лицензия

MIT License - подробности в файле `LICENSE`

---

<div align="center">

**🔗 SEO Link Recommender** - Интеллектуальная генерация внутренних ссылок

Made with ❤️ and 🤖 AI

</div>
