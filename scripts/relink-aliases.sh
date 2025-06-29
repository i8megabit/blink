
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
