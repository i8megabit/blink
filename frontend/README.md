# 🎨 reLink Frontend

Элегантный, масштабируемый фронтенд для мощной микросервисной архитектуры reLink. Спроектирован как "солист группы" - лицо продукта, которое видят все первым.

## 🚀 Особенности

- **🎯 Микросервисная интеграция** - единый интерфейс для всех сервисов
- **⚡ Высокая производительность** - оптимизированная загрузка и кэширование
- **🎨 Современный дизайн** - элегантный UI с темной темой
- **📱 Адаптивность** - работает на всех устройствах
- **🔍 Глобальный поиск** - поиск по всем данным и сервисам
- **🧪 A/B тестирование** - сравнение производительности моделей
- **🏆 Бенчмарки** - измерение качества и скорости
- **📊 Мониторинг** - отслеживание состояния системы

## 🏗️ Архитектура

```
Frontend (React + TypeScript)
├── Dashboard - Главный дашборд
├── LLM Models - Управление моделями
├── System Monitoring - Мониторинг
├── Global Search - Поиск
├── A/B Testing - Тестирование
└── Benchmarks - Бенчмарки
```

## 🚀 Быстрый старт

### Предварительные требования

- Node.js 18+
- npm или yarn
- Доступ к микросервисам reLink

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/your-org/relink.git
cd relink/frontend

# Установка зависимостей
npm install

# Настройка окружения
cp .env.example .env.local
```

### Настройка окружения

Отредактируйте `.env.local`:

```env
# Основной бэкенд
REACT_APP_BACKEND_URL=http://localhost:8000

# LLM Tuning микросервис
REACT_APP_LLM_TUNING_URL=http://localhost:8001

# Мониторинг
REACT_APP_MONITORING_URL=http://localhost:8002

# Тестирование
REACT_APP_TESTING_URL=http://localhost:8003

# Документация
REACT_APP_DOCS_URL=http://localhost:8004

# Бенчмарки
REACT_APP_BENCHMARK_URL=http://localhost:8005

# Поиск
REACT_APP_SEARCH_URL=http://localhost:8006

# Workflow
REACT_APP_WORKFLOW_URL=http://localhost:8007
```

### Запуск

```bash
# Режим разработки
npm start

# Production сборка
npm run build

# Запуск production версии
npm run serve
```

## 📁 Структура проекта

```
src/
├── components/           # React компоненты
│   ├── ui/              # Базовые UI компоненты
│   │   ├── Card.tsx     # Карточки
│   │   ├── Button.tsx   # Кнопки
│   │   ├── Badge.tsx    # Бейджи
│   │   └── Progress.tsx # Прогресс-бары
│   ├── LLMModels.tsx    # Управление LLM моделями
│   ├── SystemMonitoring.tsx # Мониторинг системы
│   ├── GlobalSearch.tsx # Глобальный поиск
│   ├── ABTesting.tsx    # A/B тестирование
│   └── Benchmarks.tsx   # Бенчмарки
├── hooks/               # React хуки
│   └── useMicroservices.ts # Хуки для работы с микросервисами
├── lib/                 # Утилиты и конфигурация
│   └── microservices.ts # Конфигурация микросервисов
├── types/               # TypeScript типы
│   └── microservices.ts # Типы для микросервисов
├── pages/               # Страницы приложения
│   └── Dashboard.tsx    # Главный дашборд
└── App.tsx              # Главный компонент
```

## 🎯 Основные компоненты

### Dashboard

Главная страница с интеграцией всех сервисов:

- **Обзор системы** - статистика и быстрые действия
- **Управление моделями** - создание и настройка LLM
- **Мониторинг** - отслеживание состояния сервисов
- **A/B тестирование** - сравнение производительности
- **Бенчмарки** - измерение качества моделей
- **Глобальный поиск** - поиск по всем данным

### LLM Models

Управление языковыми моделями:

- Просмотр доступных моделей
- Создание новых моделей
- Настройка параметров
- Мониторинг производительности
- Управление версиями

### System Monitoring

Мониторинг состояния системы:

- Статус всех сервисов
- Метрики производительности
- Алерты и уведомления
- Логи и ошибки
- Ресурсы системы

### Global Search

Глобальный поиск по всем сервисам:

- Поиск по моделям, тестам, бенчмаркам
- Фильтрация по типам и датам
- История поиска
- Подсказки и автодополнение
- Фасетный поиск

### A/B Testing

A/B тестирование моделей:

- Создание тестовых конфигураций
- Настройка распределения трафика
- Мониторинг результатов
- Статистический анализ
- Автоматическое определение победителя

### Benchmarks

Бенчмарки производительности:

- Создание наборов тестов
- Измерение метрик качества
- Сравнение моделей
- Отчеты и визуализация
- Экспорт результатов

## 🎣 Хуки

### useLLMModels

```tsx
import { useLLMModels } from './hooks/useMicroservices'

const { models, loading, error, createModel, updateModel, deleteModel } = useLLMModels()
```

### useSystemMonitoring

```tsx
import { useSystemMonitoring } from './hooks/useMicroservices'

const { health, loading, error, acknowledgeAlert } = useSystemMonitoring()
```

### useABTests

```tsx
import { useABTests } from './hooks/useMicroservices'

const { tests, loading, error, createTest, startTest, stopTest } = useABTests()
```

### useBenchmarks

```tsx
import { useBenchmarks } from './hooks/useMicroservices'

const { benchmarkSuites, loading, error, createBenchmarkSuite, runBenchmarkSuite } = useBenchmarks()
```

### useGlobalSearch

```tsx
import { useGlobalSearch } from './hooks/useMicroservices'

const { searchResults, loading, error, search, getSuggestions } = useGlobalSearch()
```

## 🎨 UI Компоненты

### Card

```tsx
import { Card } from './components/ui'

<Card className="p-6">
  <h3>Заголовок</h3>
  <p>Содержимое</p>
</Card>
```

### Button

```tsx
import { Button } from './components/ui'

<Button 
  onClick={handleClick}
  className="bg-blue-600 hover:bg-blue-700 text-white"
>
  Нажми меня
</Button>
```

### Badge

```tsx
import { Badge } from './components/ui'

<Badge color="green" size="sm">
  Успех
</Badge>
```

### Progress

```tsx
import { Progress } from './components/ui'

<Progress 
  value={75} 
  max={100}
  color="blue"
  size="md"
/>
```

## 🔧 Конфигурация

### Микросервисы

Центральная конфигурация в `src/lib/microservices.ts`:

```tsx
export const MICROSERVICES_CONFIG = {
  backend: {
    service_name: 'backend',
    base_url: process.env.REACT_APP_BACKEND_URL,
    api_version: 'v1',
    authentication: { type: 'none' },
    rate_limits: { requests_per_minute: 1000 },
    retry_config: { max_retries: 3 }
  },
  llm_tuning: {
    service_name: 'llm_tuning',
    base_url: process.env.REACT_APP_LLM_TUNING_URL,
    api_version: 'v1',
    authentication: { type: 'none' },
    rate_limits: { requests_per_minute: 500 },
    retry_config: { max_retries: 3 }
  }
  // ... другие сервисы
}
```

### Типы

TypeScript типы для всех микросервисов в `src/types/microservices.ts`:

```tsx
export interface LLMModel {
  id: string
  name: string
  display_name: string
  version: string
  model_type: 'base' | 'tuned' | 'custom'
  status: 'available' | 'loading' | 'error' | 'unavailable'
  // ... другие поля
}

export interface ABTestConfig {
  id: string
  name: string
  description: string
  models: string[]
  test_cases: ABTestCase[]
  // ... другие поля
}
```

## 🧪 Тестирование

### Unit тесты

```bash
npm test
```

### Integration тесты

```bash
npm run test:integration
```

### E2E тесты

```bash
npm run test:e2e
```

## 🚀 Деплой

### Production сборка

```bash
npm run build
```

### Docker

```bash
# Сборка образа
docker build -t relink-frontend .

# Запуск контейнера
docker run -p 3000:3000 relink-frontend
```

### Docker Compose

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://backend:8000
      - REACT_APP_LLM_TUNING_URL=http://llm-tuning:8001
    depends_on:
      - backend
      - llm-tuning
```

## 📊 Производительность

### Оптимизации

- **Code Splitting** - ленивая загрузка компонентов
- **Memoization** - кэширование вычислений
- **Virtual Scrolling** - для больших списков
- **Image Optimization** - сжатие и lazy loading
- **Bundle Analysis** - анализ размера бандла

### Метрики

- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## 🔒 Безопасность

### Аутентификация

- JWT токены
- Автоматическое обновление
- Защищенные роуты

### Валидация

- TypeScript типы
- Runtime валидация
- Санитизация данных

### HTTPS

- Принудительное HTTPS в production
- Secure cookies
- CSP заголовки

## 📈 Мониторинг

### Web Vitals

```tsx
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

// Отправка метрик
function sendToAnalytics(metric: any) {
  analytics.track('web_vital', metric)
}
```

### Error Tracking

```tsx
// Отслеживание ошибок
window.addEventListener('error', (event) => {
  errorTracker.captureException(event.error)
})
```

## 🤝 Разработка

### Code Style

- ESLint + Prettier
- TypeScript strict mode
- Conventional Commits
- Pre-commit hooks

### Git Workflow

1. Создание feature ветки
2. Разработка с тестами
3. Code review
4. Merge в main
5. Автоматический деплой

### Команды

```bash
# Разработка
npm start

# Тестирование
npm test
npm run test:watch
npm run test:coverage

# Линтинг
npm run lint
npm run lint:fix

# Типы
npm run type-check

# Сборка
npm run build
npm run build:analyze
```

## 📚 Документация

- [Frontend Integration Guide](./FRONTEND_INTEGRATION.md)
- [API Documentation](../docs/API_EXTENDED.md)
- [Integration Guide](../INTEGRATION.md)

## 🐛 Отладка

### DevTools

- React Developer Tools
- Redux DevTools (если используется)
- Network tab для API запросов

### Логи

```tsx
// Включение debug логов
localStorage.setItem('debug', 'relink:*')
```

### Профилирование

```tsx
// Профилирование производительности
import { Profiler } from 'react'

<Profiler id="Dashboard" onRender={onRenderCallback}>
  <Dashboard />
</Profiler>
```

## 🤝 Поддержка

### Сообщество

- [GitHub Issues](https://github.com/your-org/relink/issues)
- [Discord](https://discord.gg/relink)
- [Documentation](https://docs.relink.com)

### Команда

- **Frontend Lead**: [@your-name](https://github.com/your-name)
- **UI/UX**: [@designer](https://github.com/designer)
- **DevOps**: [@devops](https://github.com/devops)

## 📄 Лицензия

MIT License - см. [LICENSE](../LICENSE) файл.

---

**Frontend reLink** - элегантный интерфейс для мощной микросервисной архитектуры! 🚀

Создано с ❤️ командой reLink 