# 🎨 Frontend Integration Guide

## Обзор

Фронтенд reLink представляет собой элегантный, масштабируемый интерфейс, который интегрируется с множественными микросервисами. Он спроектирован как "солист группы" - лицо продукта, которое видят все первым.

## 🏗️ Архитектура

### Микросервисная интеграция

```
Frontend (React + TypeScript)
├── Backend API (Main Service)
├── LLM Tuning Microservice
├── Monitoring Service
├── Testing Service
├── Documentation Service
├── Benchmark Service
├── Search Service
└── Workflow Service
```

### Ключевые принципы

- **Единый интерфейс** - все сервисы доступны через единый API Gateway
- **Адаптивность** - интерфейс адаптируется к состоянию сервисов
- **Масштабируемость** - легко добавлять новые сервисы
- **Производительность** - оптимизированная загрузка и кэширование

## 🚀 Быстрый старт

### Установка зависимостей

```bash
cd frontend
npm install
```

### Настройка окружения

Создайте файл `.env.local`:

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

### Запуск в режиме разработки

```bash
npm start
```

## 📁 Структура проекта

```
src/
├── components/           # React компоненты
│   ├── ui/              # Базовые UI компоненты
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
└── pages/               # Страницы приложения
    └── Dashboard.tsx    # Главный дашборд
```

## 🔧 Основные компоненты

### Dashboard

Главная страница приложения с интеграцией всех сервисов:

```tsx
import { Dashboard } from './pages/Dashboard'

function App() {
  return <Dashboard />
}
```

### LLM Models

Управление LLM моделями:

```tsx
import { LLMModels } from './components/LLMModels'

// В дашборде
<LLMModels />
```

### System Monitoring

Мониторинг состояния системы:

```tsx
import { SystemMonitoring } from './components/SystemMonitoring'

// В дашборде
<SystemMonitoring />
```

### Global Search

Глобальный поиск по всем сервисам:

```tsx
import { GlobalSearch } from './components/GlobalSearch'

// В дашборде
<GlobalSearch />
```

### A/B Testing

A/B тестирование моделей:

```tsx
import { ABTesting } from './components/ABTesting'

// В дашборде
<ABTesting />
```

### Benchmarks

Бенчмарки производительности:

```tsx
import { Benchmarks } from './components/Benchmarks'

// В дашборде
<Benchmarks />
```

## 🎣 Хуки для микросервисов

### useLLMModels

Управление LLM моделями:

```tsx
import { useLLMModels } from './hooks/useMicroservices'

const { models, loading, error, createModel, updateModel, deleteModel } = useLLMModels()
```

### useSystemMonitoring

Мониторинг системы:

```tsx
import { useSystemMonitoring } from './hooks/useMicroservices'

const { health, loading, error, acknowledgeAlert } = useSystemMonitoring()
```

### useABTests

A/B тестирование:

```tsx
import { useABTests } from './hooks/useMicroservices'

const { tests, loading, error, createTest, startTest, stopTest } = useABTests()
```

### useBenchmarks

Бенчмарки:

```tsx
import { useBenchmarks } from './hooks/useMicroservices'

const { benchmarkSuites, loading, error, createBenchmarkSuite, runBenchmarkSuite } = useBenchmarks()
```

### useGlobalSearch

Глобальный поиск:

```tsx
import { useGlobalSearch } from './hooks/useMicroservices'

const { searchResults, loading, error, search, getSuggestions } = useGlobalSearch()
```

## 🔌 Конфигурация сервисов

### microservices.ts

Центральная конфигурация всех микросервисов:

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

## 🔄 Состояние приложения

### Глобальное состояние

Фронтенд использует React Context для глобального состояния:

```tsx
// Состояние сервисов
const [services, setServices] = useState<Microservice[]>([])

// Состояние пользователя
const [user, setUser] = useState<User | null>(null)

// Состояние уведомлений
const [notifications, setNotifications] = useState<Notification[]>([])
```

### Кэширование

Используется React Query для кэширования данных:

```tsx
import { useQuery } from '@tanstack/react-query'

const { data: models, isLoading } = useQuery({
  queryKey: ['models'],
  queryFn: fetchModels,
  staleTime: 5 * 60 * 1000, // 5 минут
})
```

## 🚨 Обработка ошибок

### Централизованная обработка

```tsx
const handleError = (error: Error, context: string) => {
  console.error(`Ошибка в ${context}:`, error)
  
  // Показать уведомление пользователю
  addNotification('error', error.message, context)
  
  // Отправить в систему мониторинга
  reportError(error, context)
}
```

### Retry логика

```tsx
const retryConfig = {
  maxRetries: 3,
  backoffFactor: 2,
  maxBackoffMs: 10000,
  retryOnStatusCodes: [500, 502, 503, 504]
}
```

## 📊 Мониторинг и аналитика

### Web Vitals

```tsx
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals'

// Отправка метрик
function sendToAnalytics(metric: any) {
  // Отправка в систему аналитики
  analytics.track('web_vital', metric)
}
```

### Производительность

```tsx
// Измерение времени загрузки компонентов
const startTime = performance.now()

useEffect(() => {
  const endTime = performance.now()
  const loadTime = endTime - startTime
  
  if (loadTime > 1000) {
    console.warn(`Медленная загрузка компонента: ${loadTime}ms`)
  }
}, [])
```

## 🔒 Безопасность

### Аутентификация

```tsx
// Проверка токена
const checkAuth = () => {
  const token = localStorage.getItem('auth_token')
  if (!token) {
    redirectToLogin()
  }
  return token
}
```

### Валидация данных

```tsx
// Валидация входных данных
const validateInput = (data: any) => {
  const schema = z.object({
    name: z.string().min(1),
    email: z.string().email()
  })
  
  return schema.parse(data)
}
```

## 🧪 Тестирование

### Unit тесты

```tsx
import { render, screen } from '@testing-library/react'
import { Dashboard } from './pages/Dashboard'

test('Dashboard renders correctly', () => {
  render(<Dashboard />)
  expect(screen.getByText('Добро пожаловать в reLink')).toBeInTheDocument()
})
```

### Integration тесты

```tsx
import { render, screen, waitFor } from '@testing-library/react'
import { Dashboard } from './pages/Dashboard'

test('Dashboard loads services', async () => {
  render(<Dashboard />)
  
  await waitFor(() => {
    expect(screen.getByText('Backend')).toBeInTheDocument()
  })
})
```

## 🚀 Деплой

### Production сборка

```bash
npm run build
```

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

### Environment variables

```env
# Production
REACT_APP_BACKEND_URL=https://api.relink.com
REACT_APP_LLM_TUNING_URL=https://llm.relink.com
REACT_APP_MONITORING_URL=https://monitoring.relink.com
```

## 📈 Оптимизация

### Code Splitting

```tsx
import { lazy, Suspense } from 'react'

const Dashboard = lazy(() => import('./pages/Dashboard'))

function App() {
  return (
    <Suspense fallback={<div>Загрузка...</div>}>
      <Dashboard />
    </Suspense>
  )
}
```

### Lazy Loading

```tsx
// Ленивая загрузка компонентов
const LLMModels = lazy(() => import('./components/LLMModels'))
const SystemMonitoring = lazy(() => import('./components/SystemMonitoring'))
```

### Memoization

```tsx
import { useMemo } from 'react'

const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data)
}, [data])
```

## 🔧 Настройка разработки

### ESLint

```json
{
  "extends": [
    "react-app",
    "react-app/jest",
    "@typescript-eslint/recommended"
  ],
  "rules": {
    "no-console": "warn",
    "prefer-const": "error"
  }
}
```

### Prettier

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

### TypeScript

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

## 📚 Дополнительные ресурсы

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Query](https://tanstack.com/query/latest)

## 🤝 Поддержка

Для вопросов по интеграции фронтенда:

1. Проверьте документацию API микросервисов
2. Изучите примеры в папке `examples/`
3. Создайте issue в репозитории
4. Обратитесь к команде разработки

---

**Frontend reLink** - элегантный интерфейс для мощной микросервисной архитектуры! 🚀 