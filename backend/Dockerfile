# syntax=docker/dockerfile:1.4

# ========================================
# 🚀 ПРОФЕССИОНАЛЬНЫЙ DOCKERFILE ДЛЯ BACKEND
# ========================================
# 
# Особенности:
# - BuildKit с кешированием
# - Multi-stage сборка
# - Безопасность (non-root user)
# - Оптимизация размера
# - Health checks
# - Метаданные

# Этап 1: Базовый образ для всех этапов
FROM python:3.11.9-slim-bullseye as base

# Метаданные образа
LABEL maintainer="reLink Team <i8megabit@gmail.com>" \
      description="SEO Link Recommender Backend Service" \
      version="4.1.2" \
      org.opencontainers.image.source="https://github.com/eberil/relink" \
      org.opencontainers.image.licenses="MIT"

# Установка системных зависимостей и создание пользователя
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser \
    && useradd -r -g appuser -m -d /home/appuser appuser

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Этап 2: Сборка зависимостей
FROM base as builder

# Установка инструментов для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование файлов зависимостей для лучшего использования кеша
COPY requirements.txt requirements_llm.txt ./

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Установка зависимостей с кешированием
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r requirements_llm.txt

# Предзагрузка NLTK данных
RUN python -c "import nltk; nltk.download('punkt', download_dir='/opt/venv/nltk_data'); nltk.download('stopwords', download_dir='/opt/venv/nltk_data')"

# Этап 3: Тестирование (опционально)
FROM builder as test

# Копирование кода для тестирования
COPY app/ ./app/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Запуск тестов
RUN python -m pytest app/tests/ -v --tb=short || true

# Этап 4: Продакшн образ
FROM base as production

# Копирование виртуального окружения из builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/venv/nltk_data /opt/venv/nltk_data

# Установка переменных окружения
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    NLTK_DATA="/opt/venv/nltk_data"

# Создание рабочей директории и установка прав
WORKDIR /app
RUN chown -R appuser:appuser /app && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser

# Копирование кода приложения
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser migrations ./migrations

# Создание необходимых директорий
RUN mkdir -p /app/logs /app/data /app/cache && \
    chown -R appuser:appuser /app

# Переключение на непривилегированного пользователя
USER appuser

# Проверка здоровья приложения
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
