# 🚀 GitHub Actions

## 📋 Workflows

### 1. CI/CD Pipeline (`ci-cd.yml`)

Основной pipeline для автоматизации разработки и развертывания.

**Триггеры:**
- `push` в `main` или `dev`
- `pull_request` в `main`

**Jobs:**
- 🧪 **Test** - Unit тесты и покрытие кода
- 🐳 **Build and Push** - Сборка и публикация Docker образов
- 🏷️ **Create Release** - Создание GitHub Release (только main)
- 🔄 **Auto-merge to Dev** - Автоматический merge в dev с инкрементом версии

### 2. Code Quality (`code-quality.yml`)

Проверка качества кода и безопасности.

**Триггеры:**
- `push` в `main` или `dev`
- `pull_request` в `main` или `dev`

**Jobs:**
- 🎨 **Frontend Quality** - ESLint, TypeScript, Prettier
- 🐍 **Backend Quality** - Black, isort, Flake8, MyPy
- 🔒 **Security** - npm audit, safety, bandit
- ⚡ **Performance** - Размер бандла, оптимизация

## 🔧 Secrets

Необходимые secrets для работы workflows:

```bash
DOCKERHUB_USERNAME=eberil
DOCKERHUB_TOKEN=your_dockerhub_token
```

## 📊 Метрики

### Code Coverage
- **Frontend:** 54.62% (цель: 100%)
- **Backend:** Автоматическое измерение

### Bundle Size
- **Цель:** < 500KB для основного бандла
- **Мониторинг:** Автоматический в CI/CD

### Security
- **npm audit:** Проверка frontend зависимостей
- **safety:** Проверка Python зависимостей
- **bandit:** Статический анализ Python кода

## 🚀 Автоматизация

### Версионирование
Версия автоматически извлекается из `README.md`:
```markdown
**Версия:** 4.1.1
```

### Docker Tags
Автоматическое создание тегов:
- `4.1.1` - Конкретная версия
- `prod` - Продакшн готовый (только main)
- `latest` - Последняя стабильная
- `dev` - Разработка (только dev)
- `dev-000` - Dev с патчем (только dev)

### GitHub Releases
Автоматическое создание релизов с:
- Changelog из коммитов
- Docker образами
- Описанием изменений

## 🔄 Workflow Logic

### Main Branch
1. ✅ Тесты проходят
2. 🐳 Сборка и публикация образов
3. 🏷️ Создание GitHub Release
4. 🔄 Инкремент версии и merge в dev

### Dev Branch
1. ✅ Тесты проходят
2. 🐳 Сборка и публикация dev образов
3. 📊 Проверка качества кода

### Pull Requests
1. ✅ Тесты проходят
2. 📊 Проверка качества кода
3. 🔒 Проверка безопасности

## 📈 Мониторинг

### GitHub Actions
- Статус в README
- Уведомления
- Автоматические комментарии в PR

### Docker Hub
- Автоматические сборки
- Тегирование версий
- Сканирование безопасности

## 🛠️ Локальная разработка

### Pre-commit проверки
```bash
# Frontend
npm run lint
npm run type-check
npm run format:check

# Backend
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

## 🔮 Будущие улучшения

- [ ] E2E тесты с Playwright
- [ ] Performance тесты
- [ ] Автоматическое развертывание
- [ ] Slack/Discord интеграция
- [ ] Dependency updates automation
- [ ] Security scanning
- [ ] Multi-platform builds

## 📞 Поддержка

При проблемах:
1. Проверьте GitHub Actions logs
2. Убедитесь в правильности secrets
3. Проверьте локальные тесты
4. Создайте issue с деталями 