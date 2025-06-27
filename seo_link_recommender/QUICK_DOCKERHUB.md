# 🚀 Быстрая настройка Docker Hub

## ⚡ Быстрый старт

### 1. Авторизация в Docker Hub
```bash
docker login
# Введите ваше имя пользователя и пароль/токен
```

### 2. Публикация образов
```bash
# Установите ваше имя пользователя
export DOCKER_USERNAME="your-username"

# Публикация latest версии
./scripts/publish-dockerhub.sh latest
```

## 📋 Что нужно сделать

### ✅ Создать аккаунт Docker Hub
1. Перейдите на [hub.docker.com](https://hub.docker.com)
2. Создайте аккаунт
3. Запомните имя пользователя

### ✅ Создать Access Token
1. В Docker Hub: **Account Settings** → **Security**
2. **New Access Token** → **Read & Write**
3. Скопируйте токен

### ✅ Авторизоваться локально
```bash
docker login
# Username: your-username
# Password: your-access-token
```

### ✅ Настроить GitHub Secrets (для автоматической публикации)
1. GitHub репозиторий → **Settings** → **Secrets and variables** → **Actions**
2. Добавить:
   - `DOCKER_USERNAME` = ваше имя пользователя
   - `DOCKER_PASSWORD` = ваш access token

## 🎯 Результат

После настройки образы будут доступны по адресам:
- `your-username/seo-link-recommender-backend:latest`
- `your-username/seo-link-recommender-frontend-classic:latest`
- `your-username/seo-link-recommender-frontend-vite:latest`

## 🔄 Автоматическая публикация

После настройки GitHub Secrets образы будут автоматически публиковаться при:
- Push в `main` или `develop`
- Создание тега `v*`

## 📚 Подробная документация

См. [DOCKERHUB_SETUP.md](DOCKERHUB_SETUP.md) для полной инструкции. 