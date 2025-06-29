#!/bin/bash

# 🧪 СКРИПТ ЗАПУСКА КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ ФРОНТЕНДА
# Интеграция Selenium + RAG + LLM

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Конфигурация
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8000"
RAG_URL="http://localhost:8001"
LLM_ROUTER_URL="http://localhost:8002"

# Проверка зависимостей
check_dependencies() {
    log_info "🔍 Проверка зависимостей..."
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 не найден"
        exit 1
    fi
    
    # Проверка pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 не найден"
        exit 1
    fi
    
    # Проверка Brave Browser
    if [ ! -f "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" ]; then
        log_warning "Brave Browser не найден, будет использован Chrome"
    fi
    
    log_success "Зависимости проверены"
}

# Установка зависимостей
install_dependencies() {
    log_info "📦 Установка зависимостей..."
    
    cd "$(dirname "$0")"
    
    # Установка Python зависимостей
    pip3 install -r requirements.txt
    
    # Установка дополнительных зависимостей для тестирования
    pip3 install pytest-asyncio httpx webdriver-manager
    
    log_success "Зависимости установлены"
}

# Проверка доступности сервисов
check_services() {
    log_info "🔗 Проверка доступности сервисов..."
    
    local services=(
        "Frontend:3000"
        "Backend:8000"
        "RAG:8001"
        "LLM Router:8002"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        local url="http://localhost:$port"
        
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            log_success "$name доступен ($url)"
        else
            log_warning "$name недоступен ($url)"
        fi
    done
}

# Запуск фронтенда (если не запущен)
start_frontend() {
    log_info "🚀 Запуск фронтенда..."
    
    if ! curl -s --max-time 5 "$FRONTEND_URL" > /dev/null 2>&1; then
        log_info "Фронтенд не запущен, запускаем..."
        
        # Переход в папку фронтенда
        cd ../../frontend
        
        # Установка зависимостей
        if [ ! -d "node_modules" ]; then
            log_info "Установка npm зависимостей..."
            npm install
        fi
        
        # Запуск в фоне
        npm run dev &
        FRONTEND_PID=$!
        
        # Ожидание запуска
        log_info "Ожидание запуска фронтенда..."
        for i in {1..30}; do
            if curl -s --max-time 5 "$FRONTEND_URL" > /dev/null 2>&1; then
                log_success "Фронтенд запущен (PID: $FRONTEND_PID)"
                break
            fi
            sleep 1
        done
        
        if [ $i -eq 30 ]; then
            log_error "Фронтенд не запустился за 30 секунд"
            exit 1
        fi
        
        cd - > /dev/null
    else
        log_success "Фронтенд уже запущен"
    fi
}

# Запуск тестов
run_tests() {
    log_info "🧪 Запуск комплексного тестирования..."
    
    cd "$(dirname "$0")"
    
    # Создание папки для результатов
    mkdir -p results
    
    # Запуск тестов
    python3 test_comprehensive_frontend.py -v
    
    # Проверка результатов
    if [ -f "frontend_test_results.json" ]; then
        log_success "Тесты завершены, результаты сохранены"
        
        # Показ кратких результатов
        echo ""
        log_info "📊 Краткие результаты:"
        python3 -c "
import json
with open('frontend_test_results.json', 'r') as f:
    data = json.load(f)
print(f'Всего тестов: {data[\"total_tests\"]}')
print(f'Успешных: {data[\"successful_tests\"]}')
print(f'Неудачных: {data[\"failed_tests\"]}')
print(f'Процент успеха: {data[\"success_rate\"]:.1f}%')
print(f'Общее время: {data[\"total_time\"]:.2f}s')
"
        
        # Перемещение результатов
        mv frontend_test_results.json results/
        mv frontend_test.log results/ 2>/dev/null || true
        
    else
        log_error "Тесты не создали файл результатов"
        exit 1
    fi
}

# Генерация отчета
generate_report() {
    log_info "📋 Генерация отчета..."
    
    cd "$(dirname "$0")"
    
    if [ -f "results/frontend_test_results.json" ]; then
        python3 -c "
import json
import datetime

with open('results/frontend_test_results.json', 'r') as f:
    data = json.load(f)

report = f'''# Отчет о тестировании фронтенда reLink

**Дата:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Тест-сьют:** {data['test_suite']}

## Общие результаты

- **Всего тестов:** {data['total_tests']}
- **Успешных:** {data['successful_tests']}
- **Неудачных:** {data['failed_tests']}
- **Процент успеха:** {data['success_rate']:.1f}%
- **Общее время:** {data['total_time']:.2f}s
- **Общий результат:** {'✅ УСПЕХ' if data['overall_success'] else '❌ НЕУДАЧА'}

## Детальные результаты

'''

for result in data['results']:
    status = '✅' if result['success'] else '❌'
    report += f'''
### {result['test']} {status}

- **Статус:** {'Успех' if result['success'] else 'Неудача'}
'''

if 'performance_metrics' in result:
    report += f'- **Время загрузки:** {result.get('load_time', 'N/A'):.2f}s\n'

if 'accessibility_issues' in result:
    report += f'- **Проблемы доступности:** {len(result['accessibility_issues'])}\n'

if 'interactions' in result:
    successful = sum(1 for r in result['interactions'] if r['success'])
    report += f'- **Успешных взаимодействий:** {successful}/{len(result['interactions'])}\n'

if 'devices' in result:
    successful = sum(1 for r in result['devices'] if r['success'])
    report += f'- **Успешных устройств:** {successful}/{len(result['devices'])}\n'

if 'endpoints' in result:
    successful = sum(1 for r in result['endpoints'] if r['success'])
    report += f'- **Успешных API:** {successful}/{len(result['endpoints'])}\n'

if 'services' in result:
    successful = sum(1 for r in result['services'] if r['success'])
    report += f'- **Успешных AI сервисов:** {successful}/{len(result['services'])}\n'

report += '''

## Рекомендации

'''

if not data['overall_success']:
    report += '''
### Требует внимания:
- Исправить неудачные тесты
- Проверить доступность сервисов
- Оптимизировать производительность
'''
else:
    report += '''
### Все тесты прошли успешно! 🎉
- Система работает корректно
- Рекомендуется регулярное тестирование
'''

with open('results/frontend_test_report.md', 'w', encoding='utf-8') as f:
    f.write(report)

print('Отчет сгенерирован: results/frontend_test_report.md')
"
        
        log_success "Отчет сгенерирован: results/frontend_test_report.md"
    fi
}

# Очистка
cleanup() {
    log_info "🧹 Очистка..."
    
    # Остановка фронтенда если мы его запускали
    if [ ! -z "$FRONTEND_PID" ]; then
        log_info "Остановка фронтенда (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Очистка временных файлов
    rm -f *.pyc
    rm -rf __pycache__
    
    log_success "Очистка завершена"
}

# Обработка сигналов
trap cleanup EXIT

# Основная функция
main() {
    echo "🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ФРОНТЕНДА reLink"
    echo "================================================"
    
    check_dependencies
    install_dependencies
    check_services
    start_frontend
    run_tests
    generate_report
    
    echo ""
    log_success "Тестирование завершено!"
    echo "📁 Результаты сохранены в папке: results/"
    echo "📋 Отчет: results/frontend_test_report.md"
}

# Запуск
main "$@" 