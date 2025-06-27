# syntax=docker/dockerfile:1

# ========================================
# Multi-stage build для статических файлов
# ========================================

# Многоэтапная сборка для оптимизации размера образа
FROM nginx:alpine as production

# Устанавливаем метаданные образа
LABEL maintainer="SEO Link Recommender Team"
LABEL version="1.0"
LABEL description="Frontend for SEO Link Recommender"

# Создаем непривилегированного пользователя
RUN addgroup -g 1001 -S nginx-app && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-app -g nginx-app nginx-app

# Этап сборки ассетов
FROM alpine:3.19 as assets-builder

# Устанавливаем curl для проверки
RUN apk add --no-cache curl && rm -rf /var/cache/apk/*

WORKDIR /app

# Копируем файлы
COPY frontend/index.html ./index.html
COPY frontend/nginx.conf ./nginx.conf

# Удаляем предупреждение о Babel из HTML
RUN sed -i 's|transformScriptTags.ts:253 You are using the in-browser Babel transformer. Be sure to precompile your scripts for production - https://babeljs.io/docs/setup/||g' index.html

# Продакшн этап
FROM production

# Копируем конфигурацию nginx
COPY --from=assets-builder /app/nginx.conf /etc/nginx/conf.d/default.conf

# Копируем статические файлы
COPY --from=assets-builder /app/index.html /usr/share/nginx/html/index.html

# Устанавливаем правильные права доступа
RUN chown -R nginx-app:nginx-app /var/cache/nginx && \
    chown -R nginx-app:nginx-app /var/log/nginx && \
    chown -R nginx-app:nginx-app /etc/nginx/conf.d && \
    chown -R nginx-app:nginx-app /usr/share/nginx/html && \
    touch /var/run/nginx.pid && \
    chown -R nginx-app:nginx-app /var/run/nginx.pid

# Переключаемся на непривилегированного пользователя
USER nginx-app

# Проверяем здоровье приложения
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Открываем порт
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]
