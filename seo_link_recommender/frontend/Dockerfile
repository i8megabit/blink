# syntax=docker/dockerfile:1

# ========================================
# Простой Dockerfile для статических файлов
# ========================================

FROM nginx:alpine AS production

# Устанавливаем метаданные образа
LABEL maintainer="SEO Link Recommender Team"
LABEL version="3.0.17"
LABEL description="Frontend for SEO Link Recommender"

# Создаем непривилегированного пользователя
RUN addgroup -g 1001 -S nginx-app && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-app -g nginx-app nginx-app

# Копируем конфигурацию nginx
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Копируем готовые статические файлы
COPY frontend/dist/ /usr/share/nginx/html/

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
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Открываем порт
EXPOSE 80

# Запускаем nginx
CMD ["nginx", "-g", "daemon off;"]
