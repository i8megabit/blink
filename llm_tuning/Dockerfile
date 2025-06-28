# Multi-stage build для оптимизации размера
FROM python:3.11-slim as builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Создание пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование виртуального окружения
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создание рабочей директории
WORKDIR /app

# Копирование кода приложения
COPY app/ ./app/
COPY alembic.ini .
COPY migrations/ ./migrations/

# Установка прав доступа
RUN chown -R appuser:appuser /app
USER appuser

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose порт
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 