# 🐳 Настройка Docker Hub для SEO Link Recommender

## 📋 Обзор

Этот документ описывает процесс настройки и публикации Docker образов проекта SEO Link Recommender в Docker Hub.

## 🎯 Цели

- ✅ Автоматическая публикация образов при релизах
- ✅ Поддержка multi-architecture (AMD64, ARM64)
- ✅ Версионирование образов
- ✅ Тестирование образов после публикации

## 🔧 Настройка Docker Hub

### 1. Создание аккаунта Docker Hub

1. Перейдите на [hub.docker.com](https://hub.docker.com)
2. Создайте аккаунт или войдите в существующий
3. Запомните ваше имя пользователя

### 2. Создание Access Token

1. В Docker Hub перейдите в **Account Settings** → **Security**
2. Нажмите **New Access Token**
3. Дайте токену имя (например, "seo-link-recommender")
4. Выберите **Read & Write** права
5. Скопируйте токен (он показывается только один раз!)

### 3. Локальная авторизация

```bash
# Авторизация в Docker Hub
docker login

# Введите ваше имя пользователя и токен
Username: your-username
Password: your-access-token
```

## 🚀 Ручная публикация образов

### Использование скрипта

```bash
# Публикация latest версии
./scripts/publish-dockerhub.sh latest

# Публикация конкретной версии
./scripts/publish-dockerhub.sh version v1.0.0

# С переменной окружения
DOCKER_USERNAME=your-username ./scripts/publish-dockerhub.sh latest
```

### Ручная публикация

```bash
# Тегирование образов
docker tag seo_link_recommender-backend:latest your-username/seo-link-recommender-backend:latest
docker tag seo_link_recommender-frontend-classic:latest your-username/seo-link-recommender-frontend-classic:latest
docker tag seo_link_recommender-frontend-vite:latest your-username/seo-link-recommender-frontend-vite:latest

# Публикация
docker push your-username/seo-link-recommender-backend:latest
docker push your-username/seo-link-recommender-frontend-classic:latest
docker push your-username/seo-link-recommender-frontend-vite:latest
```

## 🔄 Автоматическая публикация через GitHub Actions

### 1. Настройка Secrets в GitHub

В вашем GitHub репозитории перейдите в **Settings** → **Secrets and variables** → **Actions** и добавьте:

- `DOCKER_USERNAME` - ваше имя пользователя Docker Hub
- `DOCKER_PASSWORD` - ваш Docker Hub Access Token

### 2. Триггеры публикации

Образы автоматически публикуются при:

- ✅ Push в ветку `main` или `develop`
- ✅ Создание тега `v*` (например, `v1.0.0`)
- ✅ Pull Request (только сборка, без публикации)

### 3. Поддерживаемые теги

- `latest` - последняя версия
- `v1.0.0` - семантическое версионирование
- `v1.0` - мажорная.минорная версия
- `main-abc123` - коммит-хеш для ветки main
- `develop-abc123` - коммит-хеш для ветки develop

## 📦 Структура образов

### Backend Image
- **Имя**: `seo-link-recommender-backend`
- **Основа**: Python 3.11 Alpine
- **Размер**: ~1.7GB
- **Архитектуры**: AMD64, ARM64

### Frontend Classic Image
- **Имя**: `seo-link-recommender-frontend-classic`
- **Основа**: Nginx Alpine
- **Размер**: ~80MB
- **Архитектуры**: AMD64, ARM64

### Frontend Vite Image
- **Имя**: `seo-link-recommender-frontend-vite`
- **Основа**: Nginx Alpine
- **Размер**: ~76MB
- **Архитектуры**: AMD64, ARM64

## 🧪 Тестирование образов

### Локальное тестирование

```bash
# Тест Backend
docker run --rm your-username/seo-link-recommender-backend:latest python -c "print('Backend OK')"

# Тест Frontend Classic
docker run --rm your-username/seo-link-recommender-frontend-classic:latest nginx -t

# Тест Frontend Vite
docker run --rm your-username/seo-link-recommender-frontend-vite:latest nginx -t
```

### Интеграционное тестирование

```bash
# Запуск с образами из Docker Hub
docker-compose -f docker-compose.parallel.yml up -d

# Проверка доступности
curl http://localhost:3000  # Classic Frontend
curl http://localhost:3001  # Vite Frontend
curl http://localhost:8000/api/v1/health  # Backend
```

## 📊 Мониторинг публикации

### GitHub Actions

1. Перейдите в **Actions** вашего репозитория
2. Найдите workflow "🐳 Publish Docker Images"
3. Просмотрите логи выполнения

### Docker Hub

1. Перейдите в ваш профиль Docker Hub
2. Найдите репозитории `seo-link-recommender-*`
3. Проверьте теги и размеры образов

## 🔍 Отладка проблем

### Проблемы с авторизацией

```bash
# Проверка авторизации
docker info | grep Username

# Переавторизация
docker logout
docker login
```

### Проблемы с публикацией

```bash
# Проверка размера образа
docker images | grep seo_link_recommender

# Очистка старых образов
docker system prune -a

# Пересборка образов
docker-compose -f docker-compose.parallel.yml build --no-cache
```

### Проблемы с GitHub Actions

1. Проверьте Secrets в настройках репозитория
2. Убедитесь, что токен имеет права Read & Write
3. Проверьте логи в Actions

## 📝 Best Practices

### Версионирование

- Используйте семантическое версионирование (v1.0.0)
- Всегда публикуйте `latest` тег
- Используйте теги с префиксом ветки для разработки

### Безопасность

- Никогда не коммитьте токены в код
- Используйте Access Tokens вместо паролей
- Регулярно обновляйте токены

### Оптимизация

- Используйте multi-stage builds
- Минимизируйте размер образов
- Используйте .dockerignore для исключения ненужных файлов

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи GitHub Actions
2. Убедитесь в корректности Secrets
3. Проверьте права доступа к Docker Hub
4. Обратитесь к документации Docker Hub

---

**Дата создания**: 27 июня 2025  
**Статус**: ✅ Готово к использованию 

docker.io/your-username/seo-link-recommender-backend:latest
docker.io/your-username/seo-link-recommender-frontend-classic:latest
docker.io/your-username/seo-link-recommender-frontend-vite:latest 