# 🚀 CI/CD Setup Guide

## 📋 Обзор

Наш CI/CD pipeline автоматизирует весь процесс разработки, тестирования и развертывания проекта Blink.

## 🔧 Настройка Secrets

### GitHub Secrets

Добавьте следующие secrets в настройках репозитория (Settings → Secrets and variables → Actions):

```bash
DOCKERHUB_USERNAME=eberil
DOCKERHUB_TOKEN=your_dockerhub_token
```

### Получение Docker Hub Token

1. Войдите в [Docker Hub](https://hub.docker.com)
2. Перейдите в Account Settings → Security
3. Создайте новый Access Token
4. Скопируйте токен в GitHub Secrets

## 🔄 Workflow Описание

### 1. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

**Триггеры:**
- Push в `main` или `dev` ветки
- Pull Request в `main` ветку

**Jobs:**

#### 🧪 Test
- Запускает все unit тесты
- Проверяет покрытие кода (цель: 100%)
- Загружает отчеты в Codecov

#### 🐳 Build and Push
- Собирает Docker образы
- Публикует в Docker Hub с тегами:
  - `4.0.0` - конкретная версия
  - `prod` - продакшн готовый (только main)
  - `latest` - последняя стабильная
  - `dev` - разработка (только dev)
  - `dev-000` - dev с патчем (только dev)

#### 🏷️ Create Release
- Создает GitHub Release (только main)
- Генерирует changelog
- Автоматически тегирует версию

#### 🔄 Auto-merge to Dev
- Инкрементирует минорную версию
- Создает PR в dev ветку
- Автоматически мержит с squash

### 2. Code Quality (`.github/workflows/code-quality.yml`)

**Проверки:**
- ESLint, TypeScript, Prettier
- Black, isort, Flake8, MyPy
- Безопасность (npm audit, safety, bandit)
- Производительность (размер бандла)

## 📊 Отчеты и Метрики

### Code Coverage
- Frontend: 54.62% (цель: 100%)
- Backend: покрытие тестами
- Отчеты в Codecov

### Bundle Size
- Цель: < 500KB для основного бандла
- Мониторинг в CI/CD

### Security
- npm audit для frontend
- safety для Python зависимостей
- bandit для Python кода

## 🚀 Автоматизация

### Версионирование
Версия извлекается из `README.md`:
```markdown
**Версия:** 4.0.0
```

### Тегирование
Автоматическое создание тегов:
- `v4.0.0` - релиз тег
- `4.0.0` - Docker тег
- `prod` - продакшн тег
- `latest` - последний стабильный

### Релизы
Автоматическое создание GitHub Releases с:
- Changelog из коммитов
- Docker образами
- Описанием изменений

## 🔧 Локальная разработка

### Pre-commit hooks
```bash
# Frontend
cd frontend
npm run lint
npm run type-check
npm run format:check

# Backend
cd backend
black --check .
isort --check-only .
flake8 app/ tests/
mypy app/
```

### Тестирование
```bash
# Frontend
npm test -- --coverage

# Backend
python -m pytest tests/ -v --cov=app
```

## 📈 Мониторинг

### GitHub Actions
- Статус в README
- Уведомления в Slack/Discord
- Автоматические комментарии в PR

### Docker Hub
- Автоматические сборки
- Тегирование версий
- Сканирование безопасности

## 🛠️ Troubleshooting

### Частые проблемы

1. **Docker Hub авторизация**
   ```bash
   # Проверьте токен
   docker login
   ```

2. **Тесты падают**
   ```bash
   # Запустите локально
   npm test
   python -m pytest
   ```

3. **Coverage не проходит**
   ```bash
   # Проверьте покрытие
   npm run test:coverage
   ```

### Логи
- GitHub Actions logs
- Docker build logs
- Test coverage reports

## 🔮 Будущие улучшения

- [ ] E2E тесты с Playwright
- [ ] Performance тесты
- [ ] Автоматическое развертывание
- [ ] Slack/Discord интеграция
- [ ] Dependency updates automation
- [ ] Security scanning
- [ ] Multi-platform builds

## 📞 Поддержка

При проблемах с CI/CD:
1. Проверьте GitHub Actions logs
2. Убедитесь в правильности secrets
3. Проверьте локальные тесты
4. Создайте issue с деталями 