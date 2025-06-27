# SEO Link Recommender Frontend

🚀 **Профессиональный фронтенд для SEO-платформы** с TypeScript, React 18, Vite и Tailwind CSS.

## ✨ Особенности

- **TypeScript** - полная типизация для надежности кода
- **React 18** - современные хуки и компоненты
- **Vite** - быстрая сборка и разработка
- **Tailwind CSS** - утилитарные стили для быстрого прототипирования
- **WebSocket** - реальное время для отслеживания прогресса
- **Профессиональный UI** - вдохновлен лучшими AI-интерфейсами

## 🏗️ Архитектура

```
src/
├── components/          # React компоненты
│   ├── ui/             # Базовые UI компоненты
│   │   ├── Button.tsx  # Кнопка с вариантами
│   │   └── Card.tsx    # Карточка контейнер
│   ├── Notifications.tsx      # Система уведомлений
│   ├── AnalysisProgress.tsx   # Прогресс анализа
│   └── Recommendations.tsx    # Отображение рекомендаций
├── hooks/              # Кастомные React хуки
│   ├── useWebSocket.ts # WebSocket соединение
│   ├── useNotifications.ts # Управление уведомлениями
│   └── useApi.ts       # API запросы
├── types/              # TypeScript типы
│   └── index.ts        # Все типы приложения
├── lib/                # Утилиты
│   └── utils.ts        # Вспомогательные функции
└── App.tsx             # Главный компонент
```

## 🚀 Быстрый старт

### Установка зависимостей

```bash
npm install
```

### Разработка

```bash
npm run dev
```

Приложение будет доступно по адресу: http://localhost:3000

### Сборка

```bash
npm run build
```

### Предпросмотр сборки

```bash
npm run preview
```

## 🧪 Тестирование

```bash
# Запуск тестов
npm test

# Тесты с UI
npm run test:ui

# Покрытие кода
npm run test:coverage

# E2E тесты
npm run test:e2e
```

## 📝 Код и качество

```bash
# Проверка типов
npm run type-check

# Линтинг
npm run lint

# Исправление ошибок линтера
npm run lint:fix

# Форматирование кода
npm run format

# Проверка форматирования
npm run format:check
```

## 🎨 UI Компоненты

### Button

Многофункциональная кнопка с различными вариантами:

```tsx
import { Button } from './components/ui/Button';

// Основная кнопка
<Button>Нажми меня</Button>

// Вторичная кнопка
<Button variant="secondary">Вторичная</Button>

// Призрачная кнопка
<Button variant="ghost">Призрачная</Button>

// Разные размеры
<Button size="sm">Маленькая</Button>
<Button size="lg">Большая</Button>

// Отключенная
<Button disabled>Отключена</Button>
```

### Card

Контейнер для контента:

```tsx
import { Card } from './components/ui/Card';

<Card className="p-6">
  <h2>Заголовок</h2>
  <p>Содержимое карточки</p>
</Card>
```

## 🔌 Хуки

### useWebSocket

Хук для работы с WebSocket соединениями:

```tsx
import { useWebSocket } from './hooks/useWebSocket';

const { status, sendMessage, lastMessage, error, reconnect } = useWebSocket({
  url: 'ws://localhost:8000/ws',
  clientId: 'unique-client-id',
  onMessage: (message) => console.log('Получено:', message),
  onError: (error) => console.error('Ошибка:', error),
  onClose: () => console.log('Соединение закрыто')
});
```

### useNotifications

Хук для управления уведомлениями:

```tsx
import { useNotifications } from './hooks/useNotifications';

const { notifications, addNotification, removeNotification, clearNotifications } = useNotifications();

// Добавить уведомление
addNotification({
  type: 'success',
  title: 'Успех!',
  message: 'Операция выполнена успешно',
  details: 'Дополнительная информация',
  duration: 5000
});
```

### useApi

Хук для API запросов:

```tsx
import { useDomains, useOllamaStatus } from './hooks/useApi';

const { data: domains, loading, execute: loadDomains } = useDomains();
const { data: ollamaStatus, loading: ollamaLoading } = useOllamaStatus();
```

## 📊 Типы данных

### Domain

```tsx
interface Domain {
  id: number;
  name: string;
  display_name: string;
  total_posts: number;
  total_analyses: number;
  last_analysis_at: string | null;
  is_indexed: boolean;
  // ... другие поля
}
```

### Recommendation

```tsx
interface Recommendation {
  from: string;
  to: string;
  anchor: string;
  comment: string;
  quality_score?: number;
}
```

### WebSocketMessage

```tsx
interface WebSocketMessage {
  type: 'progress' | 'error' | 'ollama' | 'ai_thinking' | 'enhanced_ai_thinking' | 'ping';
  step?: string;
  current?: number;
  total?: number;
  percentage?: number;
  details?: string;
  // ... другие поля
}
```

## 🎯 Основные функции

### 1. Мониторинг статуса Ollama
- Проверка готовности модели
- Отображение статуса в реальном времени
- Автоматическое обновление

### 2. Управление доменами
- Список индексированных доменов
- Статистика по каждому домену
- История анализов

### 3. Анализ в реальном времени
- WebSocket соединение для отслеживания прогресса
- Отображение мыслей ИИ
- Детальная информация о каждом этапе

### 4. Рекомендации
- Красивое отображение рекомендаций
- Копирование в буфер обмена
- Фильтрация по качеству
- Статистика

### 5. Уведомления
- Система уведомлений с типами
- Автоматическое исчезновение
- Возможность расширения деталей

## 🔧 Конфигурация

### Vite

```ts
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});
```

### Tailwind CSS

```js
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Кастомные цвета
      }
    }
  },
  plugins: []
};
```

### TypeScript

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## 🚀 Развертывание

### Docker

```dockerfile
# Dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx конфигурация

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](../LICENSE) для деталей.

## 🆘 Поддержка

Если у вас есть вопросы или проблемы:

1. Проверьте [документацию](../README.md)
2. Создайте [Issue](../../issues)
3. Обратитесь к команде разработки

---

**Сделано с ❤️ для SEO-инженеров** 