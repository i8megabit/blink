#!/bin/bash

# ========================================
# SEO Link Recommender - Параллельный запуск
# Обычный + Vite варианты одновременно
# ========================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_subheader() {
    echo -e "${CYAN}$1${NC}"
}

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

# Функция для остановки всех контейнеров
cleanup() {
    print_warning "Получен сигнал остановки. Останавливаю контейнеры..."
    docker-compose -f docker-compose.parallel.yml down
    print_status "Контейнеры остановлены."
    exit 0
}

# Устанавливаем обработчик сигналов
trap cleanup SIGINT SIGTERM

print_header "SEO Link Recommender - Параллельный запуск"
print_status "Запускаю оба варианта (обычный + Vite) одновременно..."

# Проверяем, что мы в правильной директории
if [ ! -f "docker-compose.parallel.yml" ]; then
    print_error "Файл docker-compose.parallel.yml не найден. Запустите скрипт из корневой директории проекта."
    exit 1
fi

# Останавливаем существующие контейнеры
print_subheader "Остановка существующих контейнеров..."
docker-compose -f docker-compose.parallel.yml down --remove-orphans 2>/dev/null || true

# Очищаем неиспользуемые образы (опционально)
if [ "$1" = "--clean" ]; then
    print_subheader "Очистка неиспользуемых образов..."
    docker system prune -f
fi

# Запускаем параллельную конфигурацию
print_subheader "Запуск параллельной конфигурации..."
docker-compose -f docker-compose.parallel.yml up --build -d

# Ждем запуска сервисов
print_subheader "Ожидание запуска сервисов..."
sleep 10

# Проверяем статус контейнеров
print_subheader "Проверка статуса контейнеров..."
docker-compose -f docker-compose.parallel.yml ps

# Выводим информацию о доступе
print_header "Доступ к приложениям"
echo ""
echo -e "${GREEN}🎯 Обычный вариант (Classic):${NC}"
echo -e "   URL: ${CYAN}http://localhost:3000${NC}"
echo -e "   Traefik: ${CYAN}http://localhost/classic${NC}"
echo ""
echo -e "${GREEN}⚡ Vite вариант (Modern):${NC}"
echo -e "   URL: ${CYAN}http://localhost:3001${NC}"
echo -e "   Traefik: ${CYAN}http://localhost/vite${NC}"
echo ""
echo -e "${GREEN}🔧 Backend API:${NC}"
echo -e "   URL: ${CYAN}http://localhost:8000${NC}"
echo -e "   Health: ${CYAN}http://localhost:8000/api/v1/health${NC}"
echo ""
echo -e "${GREEN}🧠 Ollama:${NC}"
echo -e "   URL: ${CYAN}http://localhost:11434${NC}"
echo -e "   Models: ${CYAN}http://localhost:11434/api/tags${NC}"
echo ""
echo -e "${GREEN}📊 Traefik Dashboard:${NC}"
echo -e "   URL: ${CYAN}http://localhost:8080${NC}"
echo ""

# Функция для мониторинга логов
monitor_logs() {
    print_subheader "Мониторинг логов (Ctrl+C для остановки)..."
    echo ""
    docker-compose -f docker-compose.parallel.yml logs -f --tail=50
}

# Функция для проверки здоровья сервисов
check_health() {
    print_subheader "Проверка здоровья сервисов..."
    
    # Проверяем backend
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        echo -e "${GREEN}✅ Backend: OK${NC}"
    else
        echo -e "${RED}❌ Backend: ERROR${NC}"
    fi
    
    # Проверяем Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo -e "${GREEN}✅ Ollama: OK${NC}"
    else
        echo -e "${RED}❌ Ollama: ERROR${NC}"
    fi
    
    # Проверяем frontend-classic
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✅ Frontend Classic: OK${NC}"
    else
        echo -e "${RED}❌ Frontend Classic: ERROR${NC}"
    fi
    
    # Проверяем frontend-vite
    if curl -s http://localhost:3001 > /dev/null; then
        echo -e "${GREEN}✅ Frontend Vite: OK${NC}"
    else
        echo -e "${RED}❌ Frontend Vite: ERROR${NC}"
    fi
}

# Проверяем здоровье через 30 секунд
print_status "Ожидание 30 секунд для полного запуска..."
sleep 30
check_health

echo ""
print_warning "Для просмотра логов выполните: docker-compose -f docker-compose.parallel.yml logs -f"
print_warning "Для остановки нажмите Ctrl+C"
echo ""

# Основной цикл мониторинга
while true; do
    sleep 60
    check_health
done 