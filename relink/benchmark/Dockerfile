# 🚀 БЕНЧМАРК МИКРОСЕРВИС - ОПТИМИЗИРОВАННЫЙ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash benchmark && \
    chown -R benchmark:benchmark /app
USER benchmark

# Открытие порта
EXPOSE 8002

# Переменные окружения для оптимизации
ENV PYTHONUNBUFFERED=1
ENV PYTHONOPTIMIZE=2
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4"] 