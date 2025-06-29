# Многоэтапная сборка для оптимизации размера образа
FROM node:18-alpine AS base

# Установка зависимостей для сборки
RUN apk add --no-cache libc6-compat

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY package*.json ./
COPY yarn.lock ./

# Установка зависимостей
RUN yarn install --frozen-lockfile --production=false

# Этап сборки
FROM base AS builder

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN yarn build

# Этап production
FROM nginx:alpine AS production

# Установка дополнительных пакетов
RUN apk add --no-cache curl

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Копирование собранного приложения
COPY --from=builder /app/dist /usr/share/nginx/html

# Создание пользователя для безопасности
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Изменение владельца файлов
RUN chown -R nextjs:nodejs /usr/share/nginx/html && \
    chown -R nextjs:nodejs /var/cache/nginx && \
    chown -R nextjs:nodejs /var/log/nginx && \
    chown -R nextjs:nodejs /etc/nginx/conf.d

# Переключение на непривилегированного пользователя
USER nextjs

# Открытие порта
EXPOSE 80

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"] 