# 🐳 Frontend - React приложение reLink
# Этап 1: Сборка React приложения
FROM node:18-alpine AS builder

# Установка зависимостей для сборки
RUN apk add --no-cache git python3 make g++

# Рабочая директория
WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci --only=production

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Этап 2: Продакшн сервер
FROM nginx:alpine AS production

# Копирование собранного приложения
COPY --from=builder /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Открытие порта
EXPOSE 3000

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]
