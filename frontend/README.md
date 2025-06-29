# 🎨 Frontend - React приложение reLink

Frontend приложение reLink построено на современном стеке React + TypeScript + Tailwind CSS с нативной интеграцией микросервисов.

## 🚀 Быстрый старт

```bash
# Установка зависимостей
npm install

# Запуск в режиме разработки
npm run dev

# Сборка для продакшена
npm run build

# Предпросмотр продакшен сборки
npm run preview
```

## 🏗️ Архитектура

### Технологический стек
- **React 18+** с Concurrent Features
- **TypeScript 5+** с strict mode
- **Tailwind CSS 3+** с JIT compiler
- **Vite 5+** для быстрой разработки
- **Vitest** для unit тестов
- **Playwright** для e2e тестов

### Структура проекта
```
src/
├── components/          # Переиспользуемые компоненты
│   ├── ui/             # Базовые UI компоненты
│   ├── forms/          # Формы и валидация
│   ├── layout/         # Компоненты макета
│   └── features/       # Функциональные компоненты
├── hooks/              # Кастомные хуки
├── lib/                # Утилиты и конфигурация
├── types/              # TypeScript типы
├── stores/             # Глобальное состояние
└── pages/              # Страницы приложения
```

## 🎯 Основные функции

### SEO Анализ
- Анализ WordPress сайтов
- Генерация SEO рекомендаций
- Визуализация связей между страницами
- Экспорт результатов анализа

### Микросервисы интеграция
- Нативная интеграция с backend API
- Автоматическое обнаружение сервисов
- Мониторинг состояния микросервисов
- Управление конфигурацией

### AI/ML функции
- Интеграция с LLM моделями
- RAG система для контекстного поиска
- Автоматическая генерация контента
- Анализ эффективности

## 🔧 Разработка

### Команды разработки
```bash
# Запуск в режиме разработки
npm run dev

# Запуск тестов
npm run test

# Запуск e2e тестов
npm run test:e2e

# Проверка типов
npm run type-check

# Линтинг
npm run lint

# Форматирование кода
npm run format
```

### Создание компонентов
```bash
# Создание нового компонента
npm run create:component MyComponent

# Создание новой страницы
npm run create:page MyPage

# Создание нового хука
npm run create:hook useMyHook
```

## 🧪 Тестирование

### Unit тесты
```bash
# Запуск всех unit тестов
npm run test

# Запуск тестов в watch режиме
npm run test:watch

# Покрытие кода
npm run test:coverage
```

### E2E тесты
```bash
# Запуск e2e тестов
npm run test:e2e

# Запуск e2e тестов в UI режиме
npm run test:e2e:ui
```

## 🐳 Docker

### Сборка образа
```bash
# Сборка образа
docker build -t relink-frontend .

# Запуск контейнера
docker run -p 3000:3000 relink-frontend
```

### Docker Compose
```bash
# Запуск с остальными сервисами
docker-compose up frontend
```

## 📊 Производительность

### Метрики качества
- **Bundle size**: < 500KB для основного бандла
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

### Оптимизации
- Code splitting по маршрутам
- Lazy loading тяжелых компонентов
- Оптимизация изображений
- Tree shaking неиспользуемого кода

## 🎨 Дизайн-система

### Принципы
- **Минимализм** - только необходимые элементы
- **Функциональность** - каждый элемент имеет цель
- **Профессионализм** - корпоративный стиль
- **Инновационность** - современные паттерны

### Компоненты
- Единая система на основе Tailwind CSS
- Семантическая HTML разметка
- Темная тема по умолчанию
- Адаптивный дизайн

## 🔒 Безопасность

- Content Security Policy
- XSS protection
- CSRF tokens для форм
- Input sanitization
- Rate limiting на API

## 📱 Доступность

- WCAG 2.1 AA compliance
- Клавиатурная навигация
- Screen reader поддержка
- Высокий контраст
- Фокус-индикаторы

## 🚀 Деплой

### Продакшен сборка
```bash
# Сборка для продакшена
npm run build

# Предпросмотр
npm run preview
```

### CI/CD
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging

## 📚 Дополнительная документация

- [API документация](https://api.relink.dev)
- [Дизайн-система](https://design.relink.dev)
- [Компоненты](https://components.relink.dev)

## 🤝 Вклад в проект

1. Следуйте [правилам кодирования](../docs/CODING_STANDARDS.md)
2. Пишите тесты для новых функций
3. Обновляйте документацию
4. Проверяйте доступность

---

**Frontend reLink** - современный интерфейс для SEO-инженеров 🎨
