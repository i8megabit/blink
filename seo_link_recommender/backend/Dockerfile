# syntax=docker/dockerfile:1

# ========================================
# Multi-stage build для оптимизации размера
# ========================================

# Базовый образ с общими зависимостями
FROM python:3.11-slim as base

# Метаданные для лучшей организации
LABEL maintainer="seo-team" \
      description="SEO Link Recommender Backend" \
      version="1.0"

# Создаем пользователя для безопасности (не root) с домашней директорией
RUN groupadd -r appuser && \
    useradd -r -g appuser -m -d /home/appuser appuser

# Устанавливаем системные зависимости в одном слое
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove \
    && apt-get clean

# Стадия для сборки зависимостей
FROM base as builder

# Устанавливаем build-зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем Python зависимости
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt

# Создаем виртуальное окружение для изоляции
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем зависимости с оптимизацией и очисткой кеша
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Скачиваем NLTK данные на стадии сборки для избежания проблем с правами
RUN python -c "import nltk; nltk.download('punkt', download_dir='/opt/venv/share/nltk_data'); nltk.download('stopwords', download_dir='/opt/venv/share/nltk_data')"

# Продакшн стадия - минимальный образ
FROM base as production

# Копируем виртуальное окружение из builder стадии
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV NLTK_DATA="/opt/venv/share/nltk_data"

# Создаем рабочую директорию с правильными правами
WORKDIR /app
RUN chown -R appuser:appuser /app && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser

# Копируем код приложения
COPY --chown=appuser:appuser backend/app ./app
COPY --chown=appuser:appuser frontend ./frontend

# Переключаемся на непривилегированного пользователя
USER appuser

# Healthcheck для мониторинга
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Экспонируем порт
EXPOSE 8000

# Запускаем приложение с оптимальными настройками
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--access-log", "--log-level", "info"]
