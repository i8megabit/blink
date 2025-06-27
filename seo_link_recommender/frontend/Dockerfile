# syntax=docker/dockerfile:1

# ========================================
# Multi-stage build для статических файлов
# ========================================

# Стадия подготовки статики (можно расширить для сборки JS/CSS)
FROM alpine:3.19 as assets-builder

# Устанавливаем инструменты для обработки статики
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Копируем статические файлы
COPY frontend/index.html ./index.html
COPY frontend/nginx.conf ./nginx.conf

# Здесь можно добавить сборку CSS/JS, минификацию и т.д.
# Например: RUN minify index.html > index.min.html

# Production стадия - минимальный Nginx
FROM nginx:1.25-alpine as production

# Метаданные
LABEL maintainer="seo-team" \
      description="SEO Link Recommender Frontend" \
      version="1.0"

# Создаем непривилегированного пользователя с уникальным GID/UID
RUN addgroup -g 1001 -S nginx-app && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin \
    -G nginx-app -g nginx-app nginx-app

# Копируем оптимизированные статические файлы
COPY --from=assets-builder --chown=nginx-app:nginx-app \
     /app/index.html /usr/share/nginx/html/index.html

COPY --from=assets-builder --chown=nginx-app:nginx-app \
     /app/nginx.conf /etc/nginx/conf.d/default.conf

# Удаляем default конфиг Nginx и создаем нужные директории
RUN rm -f /etc/nginx/conf.d/default.conf.template && \
    mkdir -p /var/cache/nginx/client_temp && \
    chown -R nginx-app:nginx-app /var/cache/nginx && \
    chown -R nginx-app:nginx-app /usr/share/nginx/html && \
    # Создаем файл для PID с правильными правами
    touch /var/run/nginx.pid && \
    chown nginx-app:nginx-app /var/run/nginx.pid

# Healthcheck для мониторинга
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Переключаемся на непривилегированного пользователя
USER nginx-app

# Экспонируем порт
EXPOSE 80

# Запускаем Nginx в foreground режиме
CMD ["nginx", "-g", "daemon off;"]
