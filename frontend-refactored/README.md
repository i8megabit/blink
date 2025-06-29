# reLink Frontend - Микросервисный React интерфейс

Современный React интерфейс для микросервисной архитектуры SEO-платформы reLink, построенный с использованием TypeScript, Vite, Tailwind CSS и React Query.

## 🚀 Особенности

### Архитектура
- **Микросервисная архитектура** - взаимодействие с множественными backend сервисами
- **TypeScript** - полная типизация для надежности кода
- **React Query** - эффективное управление состоянием и кэшированием
- **Vite** - быстрая сборка и разработка
- **Tailwind CSS** - современный CSS фреймворк
- **React Router** - клиентская маршрутизация
- **Zustand** - легковесное управление состоянием

### Функциональность
- **Управление доменами** - добавление, редактирование, удаление доменов
- **Анализ SEO** - запуск и мониторинг анализа доменов
- **LLM интеграция** - работа с различными языковыми моделями
- **Тестирование** - запуск и просмотр результатов тестов
- **Мониторинг** - отслеживание состояния системы и метрик
- **Документация** - встроенная система документации
- **Уведомления** - система уведомлений и алертов
- **Настройки** - персонализация интерфейса

## 📁 Структура проекта

```
src/
├── components/          # React компоненты
│   ├── Layout/         # Компоненты макета
│   ├── UI/             # Базовые UI компоненты
│   └── Features/       # Компоненты функциональности
├── pages/              # Страницы приложения
├── hooks/              # React хуки
│   ├── useMicroservices.ts  # Хуки для работы с микросервисами
│   └── useApi.ts       # Базовые API хуки
├── services/           # API сервисы
│   └── api.ts          # Централизованный API клиент
├── context/            # React контексты
│   ├── AppContext.tsx  # Глобальное состояние приложения
│   └── ThemeContext.tsx # Управление темой
├── types/              # TypeScript типы
│   └── index.ts        # Основные типы
├── utils/              # Утилиты
├── styles/             # Стили
└── App.tsx             # Главный компонент
```

## 🛠️ Технологический стек

### Основные технологии
- **React 18** - UI библиотека
- **TypeScript 5** - типизированный JavaScript
- **Vite 4** - сборщик и dev сервер
- **Tailwind CSS 3** - CSS фреймворк
- **React Query 5** - управление состоянием
- **React Router 6** - маршрутизация
- **Zustand 4** - управление состоянием

### Дополнительные библиотеки
- **Axios** - HTTP клиент
- **React Hook Form** - управление формами
- **Zod** - валидация схем
- **Recharts** - графики и диаграммы
- **Framer Motion** - анимации
- **React Hot Toast** - уведомления
- **Lucide React** - иконки
- **Date-fns** - работа с датами

### Инструменты разработки
- **ESLint** - линтинг кода
- **Prettier** - форматирование
- **Vitest** - тестирование
- **Storybook** - документация компонентов
- **Husky** - git hooks

## 🚀 Быстрый старт

### Предварительные требования
- Node.js 18+
- Yarn 4+
- Docker (опционально)

### Установка зависимостей
```bash
yarn install
```

### Разработка
```bash
# Запуск dev сервера
yarn dev

# Сборка для production
yarn build

# Предварительный просмотр сборки
yarn preview
```

### Тестирование
```bash
# Запуск тестов
yarn test

# Тесты с UI
yarn test:ui

# Покрытие кода
yarn test:coverage
```

### Линтинг и форматирование
```bash
# Проверка линтера
yarn lint

# Исправление ошибок линтера
yarn lint:fix

# Проверка типов
yarn type-check

# Форматирование кода
yarn format
```

## 🐳 Docker

### Сборка образа
```bash
docker build -t eberil/relink-frontend:4.1.2 .
```

### Запуск контейнера
```bash
docker run -p 3000:80 eberil/relink-frontend:4.1.2
```

### Docker Compose
```yaml
frontend:
  build:
    context: ./frontend-refactored
    dockerfile: Dockerfile
  image: eberil/relink-frontend:4.1.2
  ports:
    - "3000:80"
  environment:
    - REACT_APP_BACKEND_URL=http://backend:8000
    - REACT_APP_ROUTER_URL=http://router:8004
    - REACT_APP_TESTING_URL=http://testing:8003
    - REACT_APP_MONITORING_URL=http://monitoring:8002
    - REACT_APP_DOCS_URL=http://docs:8001
  depends_on:
    - backend
    - router
    - testing
    - monitoring
    - docs
```

## 🔧 Конфигурация

### Переменные окружения
```bash
# URLs микросервисов
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_ROUTER_URL=http://localhost:8004
REACT_APP_TESTING_URL=http://localhost:8003
REACT_APP_MONITORING_URL=http://localhost:8002
REACT_APP_DOCS_URL=http://localhost:8001

# Настройки приложения
REACT_APP_API_TIMEOUT=30000
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENVIRONMENT=development
```

### Vite конфигурация
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

## 📊 API интеграция

### Микросервисы
Frontend взаимодействует со следующими микросервисами:

1. **Backend (8000)** - управление доменами и анализом
2. **Router (8004)** - LLM маршрутизация
3. **Testing (8003)** - тестирование и бенчмарки
4. **Monitoring (8002)** - мониторинг системы
5. **Docs (8001)** - документация

### API клиент
```typescript
// Пример использования API сервиса
import { domainsService } from './services/api';

// Получение списка доменов
const response = await domainsService.getDomains();
if (response.success) {
  console.log(response.data);
}
```

### React Query хуки
```typescript
// Пример использования хука
import { useDomains } from './hooks/useMicroservices';

function DomainsList() {
  const { data: domains, isLoading, error } = useDomains();
  
  if (isLoading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка: {error.message}</div>;
  
  return (
    <div>
      {domains?.map(domain => (
        <div key={domain.id}>{domain.name}</div>
      ))}
    </div>
  );
}
```

## 🎨 UI/UX

### Дизайн система
- **Темная/светлая тема** - автоматическое переключение
- **Адаптивный дизайн** - поддержка мобильных устройств
- **Доступность** - соответствие WCAG 2.1
- **Анимации** - плавные переходы и эффекты

### Компоненты
- **Layout** - основной макет приложения
- **Navigation** - навигационное меню
- **Cards** - карточки для отображения данных
- **Tables** - таблицы с сортировкой и фильтрацией
- **Charts** - графики и диаграммы
- **Forms** - формы с валидацией
- **Modals** - модальные окна
- **Notifications** - уведомления и алерты

## 🔒 Безопасность

### Защита
- **CSP заголовки** - защита от XSS
- **CORS настройки** - контроль доступа
- **HTTPS** - шифрование трафика
- **Валидация** - проверка входных данных

### Аутентификация
- **JWT токены** - безопасная аутентификация
- **Защищенные маршруты** - контроль доступа
- **Автоматический logout** - истечение сессии

## 📈 Производительность

### Оптимизация
- **Code splitting** - разделение кода
- **Lazy loading** - ленивая загрузка компонентов
- **Кэширование** - React Query кэш
- **Gzip сжатие** - сжатие статических файлов
- **CDN** - доставка статики

### Метрики
- **Lighthouse** - оценка производительности
- **Bundle analyzer** - анализ размера бандла
- **Performance monitoring** - мониторинг производительности

## 🧪 Тестирование

### Стратегия тестирования
- **Unit тесты** - тестирование компонентов
- **Integration тесты** - тестирование интеграций
- **E2E тесты** - тестирование пользовательских сценариев
- **Visual тесты** - тестирование UI

### Инструменты
- **Vitest** - тестовый фреймворк
- **React Testing Library** - тестирование компонентов
- **MSW** - мокирование API
- **Playwright** - E2E тестирование

## 📚 Документация

### Компоненты
- **Storybook** - документация компонентов
- **JSDoc** - документация функций
- **README файлы** - описание модулей

### API документация
- **OpenAPI/Swagger** - документация API
- **TypeScript типы** - типизация API
- **Примеры использования** - практические примеры

## 🤝 Разработка

### Git workflow
1. **Feature branches** - разработка в ветках
2. **Pull requests** - код ревью
3. **CI/CD** - автоматическая сборка и деплой
4. **Semantic versioning** - семантическое версионирование

### Code style
- **ESLint** - правила линтинга
- **Prettier** - форматирование кода
- **TypeScript** - строгая типизация
- **Conventional commits** - стандартные коммиты

## 🚀 Деплой

### Environments
- **Development** - локальная разработка
- **Staging** - тестовое окружение
- **Production** - продакшн окружение

### CI/CD Pipeline
1. **Build** - сборка приложения
2. **Test** - запуск тестов
3. **Lint** - проверка кода
4. **Deploy** - деплой на сервер

## 📊 Мониторинг

### Метрики
- **Performance** - производительность
- **Errors** - ошибки и исключения
- **Usage** - использование функций
- **User feedback** - обратная связь

### Инструменты
- **Sentry** - отслеживание ошибок
- **Google Analytics** - аналитика
- **Custom metrics** - собственные метрики

## 🔮 Планы развития

### Краткосрочные планы
- [ ] Добавление новых компонентов UI
- [ ] Улучшение производительности
- [ ] Расширение тестового покрытия
- [ ] Оптимизация бандла

### Долгосрочные планы
- [ ] PWA функциональность
- [ ] Офлайн режим
- [ ] Интеграция с новыми микросервисами
- [ ] Расширенная аналитика

## 📞 Поддержка

### Контакты
- **Issues** - GitHub Issues
- **Discussions** - GitHub Discussions
- **Documentation** - Wiki проекта

### Сообщество
- **Contributing** - руководство по участию
- **Code of Conduct** - правила поведения
- **Changelog** - история изменений

---

**reLink Frontend** - современный, масштабируемый и производительный интерфейс для SEO-платформы нового поколения! 🚀 