# 🐳 Monitoring Service - Микросервис reLink
FROM python:3.11-slim AS builder

# Системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Продакшн образ
FROM python:3.11-slim AS production

# Системные зависимости для продакшна
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Рабочая директория
WORKDIR /app

# Копирование Python из builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin/python* /usr/local/bin/
COPY --from=builder /usr/local/bin/pip* /usr/local/bin/

# Копирование кода
COPY --from=builder /app /app

# Права доступа
RUN chown -R appuser:appuser /app
USER appuser

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "-m", "app.main"] 