#!/bin/bash

# 🚀 reLink Shell Aliases Setup
# Настройка алиасов для автоматического использования BuildKit

set -euo pipefail

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Определение shell
SHELL_TYPE=""
if [ -n "${ZSH_VERSION:-}" ]; then
    SHELL_TYPE="zsh"
    SHELL_RC="$HOME/.zshrc"
elif [ -n "${BASH_VERSION:-}" ]; then
    SHELL_TYPE="bash"
    SHELL_RC="$HOME/.bashrc"
else
    echo -e "${RED}❌ Неподдерживаемый shell${NC}"
    exit 1
fi

# Пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_SCRIPT="${PROJECT_ROOT}/scripts/professional-build.sh"

# Проверка существования скрипта
if [ ! -f "$BUILD_SCRIPT" ]; then
    echo -e "${RED}❌ Скрипт сборки не найден: $BUILD_SCRIPT${NC}"
    exit 1
fi

# Создание алиасов
create_aliases() {
    echo -e "${BLUE}🔧 Создание алиасов для $SHELL_TYPE...${NC}"
    
    # Создаем временный файл с алиасами
    cat > /tmp/relink_aliases.tmp << 'EOF'

# 🚀 reLink Docker Aliases
# Автоматическое использование BuildKit и профессионального скрипта сборки

# Основные команды сборки
alias relink-build='./scripts/professional-build.sh build'
alias relink-build-nc='./scripts/professional-build.sh build-no-cache'
alias relink-build-service='./scripts/professional-build.sh build'

# Управление сервисами
alias relink-up='./scripts/professional-build.sh up'
alias relink-down='./scripts/professional-build.sh down'
alias relink-restart='./scripts/professional-build.sh restart'

# Мониторинг
alias relink-logs='./scripts/professional-build.sh logs'
alias relink-health='./scripts/professional-build.sh health'
alias relink-analyze='./scripts/professional-build.sh analyze'

# Очистка
alias relink-clean='./scripts/professional-build.sh cleanup'
alias relink-clean-force='./scripts/professional-build.sh cleanup-force'

# Быстрые команды
alias relink-quick='./scripts/professional-build.sh quick-start'
alias relink-dev='./scripts/professional-build.sh dev'
alias relink-prod='./scripts/professional-build.sh prod'

# Makefile алиасы (если доступен)
if [ -f "Makefile" ]; then
    alias relink-make='make -f Makefile'
    alias relink-build-make='make build'
    alias relink-up-make='make up'
    alias relink-down-make='make down'
    alias relink-restart-make='make restart'
    alias relink-logs-make='make logs'
    alias relink-health-make='make health'
    alias relink-analyze-make='make analyze'
    alias relink-clean-make='make clean'
    alias relink-quick-make='make quick-start'
    alias relink-dev-make='make dev'
    alias relink-prod-make='make prod'
fi

# Docker Compose с автоматическим BuildKit
alias dcb='DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -f config/docker-compose.yml build'
alias dcu='DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -f config/docker-compose.yml up -d'
alias dcd='docker-compose -f config/docker-compose.yml down'
alias dcr='docker-compose -f config/docker-compose.yml restart'
alias dcl='docker-compose -f config/docker-compose.yml logs -f'

# Утилиты
alias relink-help='./scripts/professional-build.sh help'
alias relink-status='docker-compose -f config/docker-compose.yml ps'
alias relink-ps='docker ps --filter "name=relink" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

# Переход в директорию проекта
alias relink-cd='cd $(git rev-parse --show-toplevel 2>/dev/null || echo .)'

# Экспорт переменных окружения
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export COMPOSE_FILE=config/docker-compose.yml

echo "🚀 reLink aliases loaded for $SHELL_TYPE"
EOF

    # Добавляем алиасы в shell RC файл
    if ! grep -q "reLink Docker Aliases" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# 🚀 reLink Docker Aliases" >> "$SHELL_RC"
        echo "source $PROJECT_ROOT/scripts/relink-aliases.sh" >> "$SHELL_RC"
        echo -e "${GREEN}✅ Алиасы добавлены в $SHELL_RC${NC}"
    else
        echo -e "${YELLOW}⚠️  Алиасы уже существуют в $SHELL_RC${NC}"
    fi
    
    # Создаем отдельный файл с алиасами
    cp /tmp/relink_aliases.tmp "$PROJECT_ROOT/scripts/relink-aliases.sh"
    chmod +x "$PROJECT_ROOT/scripts/relink-aliases.sh"
    
    echo -e "${GREEN}✅ Алиасы созданы в $PROJECT_ROOT/scripts/relink-aliases.sh${NC}"
}

# Удаление алиасов
remove_aliases() {
    echo -e "${YELLOW}🗑️  Удаление алиасов...${NC}"
    
    # Удаляем строки из shell RC файла
    if [ -f "$SHELL_RC" ]; then
        sed -i.bak '/reLink Docker Aliases/,+1d' "$SHELL_RC"
        echo -e "${GREEN}✅ Алиасы удалены из $SHELL_RC${NC}"
    fi
    
    # Удаляем файл алиасов
    if [ -f "$PROJECT_ROOT/scripts/relink-aliases.sh" ]; then
        rm "$PROJECT_ROOT/scripts/relink-aliases.sh"
        echo -e "${GREEN}✅ Файл алиасов удален${NC}"
    fi
}

# Показать справку
show_help() {
    echo -e "${BLUE}🚀 reLink Shell Aliases Setup${NC}"
    echo ""
    echo "Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  install    - Установить алиасы (по умолчанию)"
    echo "  remove     - Удалить алиасы"
    echo "  help       - Показать эту справку"
    echo ""
    echo "После установки доступны команды:"
    echo "  relink-build      - Сборка с BuildKit"
    echo "  relink-up         - Запуск сервисов"
    echo "  relink-down       - Остановка сервисов"
    echo "  relink-logs       - Просмотр логов"
    echo "  relink-health     - Проверка здоровья"
    echo "  relink-quick      - Быстрый старт"
    echo "  relink-dev        - Режим разработки"
    echo "  relink-prod       - Продакшн режим"
    echo ""
    echo "Также доступны Makefile команды:"
    echo "  relink-build-make - Сборка через Makefile"
    echo "  relink-up-make    - Запуск через Makefile"
    echo ""
    echo "И прямые Docker Compose команды:"
    echo "  dcb               - docker-compose build с BuildKit"
    echo "  dcu               - docker-compose up с BuildKit"
    echo "  dcd               - docker-compose down"
}

# Главная функция
main() {
    local command=${1:-"install"}
    
    case $command in
        "install"|"setup")
            create_aliases
            echo -e "${GREEN}🎉 Алиасы установлены!${NC}"
            echo -e "${BLUE}💡 Перезапустите терминал или выполните: source $SHELL_RC${NC}"
            ;;
        "remove"|"uninstall")
            remove_aliases
            echo -e "${GREEN}✅ Алиасы удалены${NC}"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}❌ Неизвестная команда: $command${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Запуск главной функции
main "$@" 