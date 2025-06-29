# 🚀 reLink - Платформа для SEO-инженеров

**reLink** - это современная платформа для SEO-инженеров, построенная на микросервисной архитектуре с интеграцией AI/ML технологий.

**Версия**: 4.1.3.28  
**Последние исправления**: ✅ Исправлены проблемы с ChromaDB (health check и OpenTelemetry) - см. [CHROMADB_FIXES.md](CHROMADB_FIXES.md)

## 📋 Быстрый старт

```bash
# Клонирование репозитория
git clone https://github.com/your-username/relink.git
cd relink

# Запуск всей системы
make up

# Проверка статуса
make status
```

## 🏗️ Архитектура

reLink построен на микросервисной архитектуре с единой основой:

- **🐳 Единый Docker образ** - все микросервисы используют `eberil/relink-base:latest`
- **🔧 Общий бутстрап** - стандартизированная инициализация всех сервисов
- **📦 Общие зависимости** - централизованное управление пакетами
- **🔗 Нативная интеграция** - идеальная связь между всеми компонентами

## 📚 Документация

### Основные компоненты

| Компонент | Описание | Документация |
|-----------|----------|--------------|
| **Frontend** | React приложение с TypeScript | [📖 Frontend README](frontend/README.md) |
| **Backend** | FastAPI микросервис | [📖 Backend README](backend/README.md) |
| **Testing** | Автоматизированное тестирование | [📖 Testing README](testing/README.md) |
| **Scripts** | Утилиты и автоматизация | [📖 Scripts README](scripts/README.md) |

### Специализированные сервисы

| Сервис | Описание | Документация |
|--------|----------|--------------|
| **LLM Tuning** | Настройка и оптимизация LLM | [📖 LLM Tuning README](llm_tuning/README.md) |
| **Monitoring** | Мониторинг и алерты | [📖 Monitoring README](monitoring/README.md) |
| **Router** | Маршрутизация запросов | [📖 Router README](router/README.md) |
| **Benchmark** | Тестирование производительности | [📖 Benchmark README](benchmark/README.md) |
| **UX Bot** | Автоматизированное тестирование UX | [📖 UX Bot README](ux_bot/README.md) |

### Инфраструктура

| Компонент | Описание | Документация |
|-----------|----------|--------------|
| **Bootstrap** | Общая основа для микросервисов | [📖 Bootstrap README](bootstrap/README.md) |
| **Config** | Конфигурация системы | [📖 Config README](config/README.md) |
| **Deploy** | Развертывание и DevOps | [📖 Deploy README](deploy/README.md) |

## 🚀 Основные команды

```bash
# Запуск всей системы
make up

# Остановка системы
make down

# Пересборка образов
make rebuild

# Просмотр логов
make logs

# Проверка статуса
make status

# Очистка
make clean
```

## 🔧 Разработка

### Создание нового микросервиса

```bash
# Автоматическое создание микросервиса
./scripts/create-microservice.sh my-service 8000 "Описание сервиса"
```

### Тестирование

```bash
# Запуск всех тестов
make test

# Тестирование конкретного компонента
make test-frontend
make test-backend
make test-selenium
```

## 📊 Мониторинг

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Health Checks**: http://localhost:8000/health

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Запустите тесты
5. Создайте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-username/relink/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/relink/discussions)
- **Email**: i8megabit@gmail.com

---

**reLink** - современная платформа для SEO-инженеров 🚀 