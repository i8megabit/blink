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
# - Обновленный SQLite для ChromaDB

# Этап 1: Базовый образ для всех этапов
FROM python:3.11.9-slim-bullseye as base

# Метаданные образа
LABEL maintainer="reLink Team <i8megabit@gmail.com>" \
      description="SEO Link Recommender Backend Service" \
      version="4.1.2" \
      org.opencontainers.image.source="https://github.com/eberil/relink" \
      org.opencontainers.image.licenses="MIT"

# Установка системных зависимостей и обновление SQLite
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Установка новой версии SQLite для ChromaDB
RUN wget https://www.sqlite.org/2024/sqlite-autoconf-3450100.tar.gz \
    && tar -xzf sqlite-autoconf-3450100.tar.gz \
    && cd sqlite-autoconf-3450100 \
    && ./configure --prefix=/usr/local \
    && make \
    && make install \
    && cd .. \
    && rm -rf sqlite-autoconf-3450100*

# Создание пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Этап 2: Установка зависимостей
FROM base as dependencies

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Обновление pip и установка зависимостей
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Этап 3: Сборка приложения
FROM base as builder

# Копирование виртуального окружения
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование исходного кода
COPY . .

# Компиляция Python файлов
RUN python -m compileall .

# Этап 4: Продакшн образ
FROM python:3.11.9-slim-bullseye as production

# Метаданные
LABEL maintainer="reLink Team <i8megabit@gmail.com>" \
      description="SEO Link Recommender Backend Service" \
      version="4.1.2"

# Установка только необходимых системных зависимостей
RUN apt-get update && apt-get install -y \
    libpq5 \
    libffi7 \
    libssl1.1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Копирование собранного sqlite3 из base
COPY --from=base /usr/local/bin/sqlite3 /usr/local/bin/sqlite3
COPY --from=base /usr/local/lib/libsqlite3.so* /usr/local/lib/

# Создание пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Установка рабочей директории
WORKDIR /app

# Копирование виртуального окружения
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование скомпилированного кода
COPY --from=builder /app /app

# Смена владельца файлов
RUN chown -R appuser:appuser /app

# Переключение на пользователя приложения
USER appuser

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Экспорт порта
EXPOSE 8000

# Команда запуска
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
