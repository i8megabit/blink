# 🐳 router - Микросервис reLink
FROM eberil/relink-base:latest

# Копирование кода сервиса
COPY . .

# Установка зависимостей сервиса
RUN pip install --no-cache-dir -r requirements.txt

# Открытие порта
EXPOSE 8004

# Запуск сервиса
CMD ["python", "-m", "app.main"]
