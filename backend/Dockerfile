# 🐳 Backend Service - Микросервис reLink
FROM python:3.11.9-slim-bullseye AS base

# Системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Python оптимизации
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=2
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Этап зависимостей
FROM base AS dependencies

# Копирование кода
COPY . .

# Этап сборки
FROM base AS builder

# Копирование зависимостей
COPY --from=dependencies /app /app

# Продакшн образ
FROM debian:bullseye-slim AS production

# Системные зависимости для продакшна
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Рабочая директория
WORKDIR /app

# Копирование Python из base
COPY --from=base /usr/local/bin/python* /usr/local/bin/
COPY --from=base /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=base /usr/local/lib/libpython3.11* /usr/local/lib/
COPY --from=base /usr/local/include/python3.11 /usr/local/include/python3.11
COPY --from=base /usr/local/bin/sqlite3 /usr/local/bin/sqlite3
COPY --from=base /usr/local/lib/libsqlite3.so* /usr/local/lib/

# Копирование кода
COPY --from=builder /app /app

# Права доступа
RUN chown -R appuser:appuser /app
USER appuser

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "-m", "app.main"]
