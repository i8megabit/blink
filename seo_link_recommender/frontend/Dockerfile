# syntax=docker/dockerfile:1

# ========================================
# Multi-stage build для статических файлов
# ========================================

FROM alpine:3.19 as assets-builder

# Устанавливаем инструменты для обработки статики
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Копируем статические файлы
COPY frontend/index.html ./index.html
COPY frontend/nginx.conf ./nginx.conf

# Убираем предупреждение Babel о продакшн использовании
RUN sed -i 's|transformScriptTags.ts:253 You are using the in-browser Babel transformer||g' index.html

# Production стадия - минимальный Nginx
FROM nginx:alpine as production

# Метаданные
LABEL maintainer="seo-team" \
      description="SEO Link Recommender Frontend" \
      version="1.0"

# Копируем конфигурацию nginx
COPY --from=assets-builder /app/nginx.conf /etc/nginx/conf.d/default.conf

# Копируем статические файлы
COPY --from=assets-builder /app/index.html /usr/share/nginx/html/index.html

# Создаем непривилегированного пользователя
RUN addgroup -g 1001 -S nginx-app && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin \
    -G nginx-app -g nginx-app nginx-app && \
    chown -R nginx-app:nginx-app /usr/share/nginx/html && \
    chown -R nginx-app:nginx-app /var/cache/nginx

# Healthcheck для мониторинга
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Экспонируем порт
EXPOSE 80

# Запускаем Nginx в foreground режиме
CMD ["nginx", "-g", "daemon off;"]
