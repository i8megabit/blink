# syntax=docker/dockerfile:1

# ========================================
# Multi-stage build для оптимизации размера
# ========================================

# Многоэтапная сборка для оптимизации размера образа
FROM python:3.11-slim as base

# Метаданные для лучшей организации
LABEL maintainer="seo-team" \
      description="SEO Link Recommender Backend" \
      version="1.0"

# Устанавливаем системные зависимости и создаем пользователя
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser \
    && useradd -r -g appuser -m -d /home/appuser appuser

# Этап сборки зависимостей
FROM base as builder

# Устанавливаем инструменты для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только requirements для лучшего использования кеша
COPY requirements.txt ./requirements.txt

# Создаем виртуальное окружение и устанавливаем зависимости
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем зависимости с оптимизацией
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Предзагружаем NLTK данные
RUN python -c "import nltk; nltk.download('punkt', download_dir='/opt/venv/nltk_data'); nltk.download('stopwords', download_dir='/opt/venv/nltk_data')"

# Продакшн этап
FROM base as production

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/venv/nltk_data /opt/venv/nltk_data

# Устанавливаем переменные окружения
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV NLTK_DATA="/opt/venv/nltk_data"

# Создаем рабочую директорию и устанавливаем права
WORKDIR /app
RUN chown -R appuser:appuser /app && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser

# Копируем код приложения
COPY --chown=appuser:appuser app ./app
RUN ls -l /app/app

# Переключаемся на непривилегированного пользователя
USER appuser

# Проверяем здоровье приложения
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
