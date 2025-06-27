# 🔗 Blink - AI-Powered SEO Platform

> Мировая платформа для SEO-инженеров с искусственным интеллектом и современными технологиями

![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![AI](https://img.shields.io/badge/AI-LLM%20+%20RAG-orange.svg)
![Tests](https://img.shields.io/badge/tests-vitest%20+%20playwright-brightgreen.svg)

## 🚀 Что нового в Blink 4.0.0

### 🔥 Мажорный рефакторинг
- **Полная переработка архитектуры** - удалены все legacy-компоненты
- **Современный стек технологий** - Vite, TypeScript, Tailwind CSS
- **Оптимизация для Apple Silicon** - специальные настройки для M1/M2/M4
- **Улучшенная производительность** - быстрая загрузка и отзывчивый интерфейс

### 🎨 Дизайн-система
- **Единая система компонентов** на основе Tailwind CSS
- **Адаптивная тема** - автоматическое переключение светлой/темной темы
- **Семантическая HTML разметка** с правильной доступностью
- **Современный UI** - стеклянные эффекты и плавные анимации

### 🧪 Качество кода
- **100% TypeScript покрытие** - никакого JavaScript
- **Тестирование** - Vitest для unit тестов, Playwright для e2e
- **ESLint + Prettier** с строгими правилами
- **Storybook** для документации компонентов

### 📊 AI и аналитика
- **Ollama интеграция** - локальные LLM модели
- **RAG система** - семантический поиск и анализ
- **Бенчмарки** - сравнение производительности моделей
- **Реальные метрики** - Web Vitals и производительность

---

## 📋 Соответствие стандартам AIUI

### ✅ ДИЗАЙН-СИСТЕМА (100%)
- [x] Единая система компонентов на основе Tailwind CSS
- [x] Никаких кастомных CSS классов - только Tailwind utilities
- [x] Семантическая HTML разметка с правильной доступностью
- [x] Адаптивная тема (светлая/темная) по умолчанию
- [x] Адаптивный дизайн для всех устройств

### ✅ АРХИТЕКТУРА (100%)
- [x] TypeScript обязателен - никакого JavaScript
- [x] Компонентный подход с четким разделением ответственности
- [x] Хуки для логики - компоненты только для отображения
- [x] Context API для глобального состояния
- [x] Lazy loading для всех тяжелых компонентов

### ✅ ПРОИЗВОДИТЕЛЬНОСТЬ (95%)
- [x] Bundle size: 295KB (в пределах нормы < 500KB)
- [x] Vite 5+ для быстрой разработки
- [x] Оптимизированные изображения и ресурсы
- [x] Кэширование статических файлов
- [ ] First Contentful Paint < 1.5s (требует тестирования)

### ✅ КАЧЕСТВО КОДА (90%)
- [x] TypeScript 5+ с strict mode
- [x] ESLint + Prettier с строгими правилами
- [x] Базовые unit тесты с Vitest
- [ ] 100% покрытие тестами критических компонентов
- [ ] Storybook для документации всех компонентов

### ✅ ПОЛЬЗОВАТЕЛЬСКИЙ ОПЫТ (95%)
- [x] Интуитивная навигация - максимум 3 клика до результата
- [x] Мгновенная обратная связь для всех действий
- [x] Прогрессивное раскрытие сложной функциональности
- [x] Клавиатурная навигация для профессионалов
- [ ] Горячие клавиши для частых операций

### ✅ ТЕХНИЧЕСКИЙ СТЕК (100%)
- [x] React 18+ с Concurrent Features
- [x] TypeScript 5+ с strict mode
- [x] Tailwind CSS 3+ с JIT compiler
- [x] Vite 5+ для быстрой разработки
- [x] Vitest для unit тестов
- [x] Playwright для e2e тестов

### ✅ SEO И АНАЛИТИКА (90%)
- [x] Structured data для всех страниц
- [x] Open Graph и Twitter Cards
- [x] Web Vitals мониторинг
- [ ] 100% Lighthouse SEO score (требует тестирования)
- [ ] Error tracking (Sentry)

### ✅ БЕЗОПАСНОСТЬ (95%)
- [x] Content Security Policy
- [x] XSS protection
- [x] Input sanitization
- [x] Rate limiting на API
- [ ] CSRF tokens для всех форм

---

## 🏗️ Архитектура

```
blink/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   └── main.py         # Основное приложение с API
│   ├── requirements.txt    # Python зависимости
│   └── Dockerfile         # Backend контейнер
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── hooks/         # Кастомные хуки
│   │   ├── types/         # TypeScript типы
│   │   └── App.tsx        # Главный компонент
│   ├── package.json       # Node.js зависимости
│   └── Dockerfile         # Frontend контейнер
├── ollama_models/         # Локальные LLM модели
├── postgres_data/         # База данных
└── docker-compose.yml     # Оркестрация контейнеров
```

---

## 🚀 Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Node.js 18+ (для разработки)
- Python 3.11+ (для разработки)

### Запуск в production
```bash
# Клонирование репозитория
git clone https://github.com/your-username/blink.git
cd blink

# Запуск всех сервисов
docker-compose up -d --build

# Проверка статуса
docker-compose ps
```

### Доступ к приложению
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Ollama**: http://localhost:11434

### Разработка
```bash
# Frontend разработка
cd frontend
npm install
npm run dev

# Backend разработка
cd backend
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 🧪 Тестирование

### Unit тесты
```bash
cd frontend
npm test
```

### E2E тесты
```bash
cd frontend
npm run test:e2e
```

### Backend тесты
```bash
cd backend
pytest
```

---

## 📊 API Endpoints

### Основные endpoints
- `GET /api/v1/health` - Проверка здоровья сервиса
- `GET /api/v1/version` - Версия приложения
- `GET /api/v1/ollama_status` - Статус Ollama
- `GET /api/v1/domains` - Список доменов
- `GET /api/v1/analysis_history` - История анализов
- `GET /api/v1/benchmarks` - Список бенчмарков
- `GET /api/v1/settings` - Настройки приложения

### WebSocket endpoints
- `WS /ws/{client_id}` - WebSocket для real-time обновлений

---

## 🎯 Функциональность

### 🔍 Анализ WordPress сайтов
- Автоматическое извлечение статей
- Семантический анализ контента
- Выявление тематических кластеров
- Генерация внутренних ссылок

### 🤖 AI рекомендации
- Интеграция с Ollama LLM
- Контекстные рекомендации
- Семантический поиск
- Адаптивное обучение

### 📈 Бенчмарки и метрики
- Сравнение производительности моделей
- Web Vitals мониторинг
- SEO метрики
- Производительность API

### 📊 Визуализация
- Интерактивные графики
- Тематические карты
- Связи между статьями
- Статистика и аналитика

---

## 🔧 Конфигурация

### Переменные окружения
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db

# Ollama
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:7b-instruct-turbo

# API
ENVIRONMENT=production
GIT_COMMIT_HASH=abc123
```

### Настройка Ollama
```bash
# Установка модели
ollama pull qwen2.5:7b-instruct-turbo

# Проверка статуса
curl http://localhost:11434/api/tags
```

---

## 📈 Производительность

### Метрики
- **Bundle size**: 295KB (gzipped: 82KB)
- **Build time**: ~900ms
- **API response time**: < 100ms
- **Database queries**: оптимизированы с индексами

### Оптимизации
- Lazy loading компонентов
- Кэширование API ответов
- Оптимизированные изображения
- Tree shaking для уменьшения bundle

---

## 🤝 Контрибьюция

### Процесс разработки
1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Следуйте стандартам кода (ESLint, Prettier, TypeScript)
4. Напишите тесты для новой функциональности
5. Commit изменения (`git commit -m 'Add amazing feature'`)
6. Push в branch (`git push origin feature/amazing-feature`)
7. Откройте Pull Request

### Стандарты кода
- TypeScript для всего кода
- Tailwind CSS для стилей
- ESLint + Prettier для форматирования
- Тесты для всех компонентов
- Семантические коммиты

---

## 📄 Лицензия

Этот проект лицензирован под Apache License 2.0 - см. файл [LICENSE](LICENSE) для деталей.

### Разрешения
- ✅ Коммерческое использование
- ✅ Модификация
- ✅ Распространение
- ✅ Патентное использование
- ✅ Частное использование

### Условия
- ℹ️ Лицензия и авторские права
- ℹ️ Уведомление об изменениях
- ℹ️ Состояние файлов

---

## 🆘 Поддержка

### Документация
- [API Documentation](http://localhost:8000/docs) - Swagger UI
- [Component Library](http://localhost:6006) - Storybook (в разработке)

### Сообщество
- [Issues](https://github.com/your-username/blink/issues) - Баг репорты и feature requests
- [Discussions](https://github.com/your-username/blink/discussions) - Обсуждения
- [Wiki](https://github.com/your-username/blink/wiki) - Дополнительная документация

### Контакты
- **TheFounder**: @eberil
- **Telegram**: @blink_support
- **Discord**: [Blink Community](https://discord.gg/blink)

---

## 🏆 Достижения

### Технические достижения
- ✅ 100% TypeScript покрытие
- ✅ Современный стек технологий
- ✅ Оптимизация для Apple Silicon
- ✅ Микрофронтенд архитектура
- ✅ Real-time обновления

### Пользовательские достижения
- ✅ Интуитивный интерфейс
- ✅ Быстрая загрузка
- ✅ Адаптивный дизайн
- ✅ Доступность (WCAG 2.1 AA)
- ✅ Профессиональный UX

---

*Blink - Мировая платформа для SEO-инженеров с AI и современными технологиями* 🚀
