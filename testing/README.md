# 🧪 Testing - Автоматизированное тестирование reLink

Микросервис автоматизированного тестирования для платформы reLink с интеграцией Selenium, RAG и LLM технологий.

## 🚀 Быстрый старт

```bash
# Запуск через Docker Compose
docker-compose up -d

# Локальная разработка
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Запуск тестов
pytest tests/
```

## 🏗️ Архитектура

### Технологический стек
- **FastAPI** - веб-фреймворк для API
- **Selenium** - автоматизация браузера
- **Playwright** - современное UI тестирование
- **pytest** - фреймворк тестирования
- **RAG** - контекстное тестирование
- **LLM** - интеллектуальный анализ результатов

### Структура проекта
```
app/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Подключение к БД
├── models.py            # Модели данных
├── services.py          # Бизнес-логика
├── monitoring.py        # Мониторинг
└── api/
    └── routes.py        # API роуты

tests/
├── test_api.py          # API тесты
├── test_services.py     # Тесты сервисов
└── selenium/
    └── test_frontend_smoke.py  # UI тесты

selenium/
└── requirements.txt     # Зависимости для Selenium
```

## 🎯 Основные функции

### UI Тестирование
- Автоматизированное тестирование интерфейса
- Selenium WebDriver интеграция
- Playwright для современных браузеров
- Скриншоты и видео записи

### API Тестирование
- REST API тестирование
- Автоматическая валидация ответов
- Нагрузочное тестирование
- Мониторинг производительности

### RAG Интеграция
- Контекстное понимание тестов
- Динамическая генерация тестовых сценариев
- Анализ результатов через LLM
- Автоматическая оптимизация тестов

### LLM Анализ
- Интеллектуальный анализ ошибок
- Автоматическая генерация отчетов
- Предсказание проблем
- Рекомендации по улучшению

## 🔧 Разработка

### Команды разработки
```bash
# Запуск сервиса
uvicorn app.main:app --reload --port 8001

# Запуск тестов
pytest tests/ -v

# Запуск Selenium тестов
pytest selenium/ -v

# Запуск с покрытием
pytest --cov=app tests/
```

### Создание тестов
```bash
# Создание API теста
pytest tests/test_api.py::test_new_endpoint

# Создание UI теста
pytest selenium/test_new_feature.py

# Создание интеграционного теста
pytest tests/test_integration.py
```

## 🧪 Типы тестов

### Unit тесты
- Тестирование отдельных функций
- Мокирование внешних зависимостей
- Быстрое выполнение
- Высокое покрытие кода

### Integration тесты
- Тестирование взаимодействия компонентов
- Реальные базы данных
- API интеграция
- Проверка бизнес-логики

### E2E тесты
- Полный пользовательский сценарий
- Реальные браузеры
- Автоматизация UI
- Проверка пользовательского опыта

### Performance тесты
- Нагрузочное тестирование
- Стресс-тестирование
- Мониторинг метрик
- Анализ производительности

## 🐳 Docker

### Сборка образа
```bash
# Сборка образа
docker build -t relink-testing .

# Запуск контейнера
docker run -p 8001:8001 relink-testing
```

### Docker Compose
```bash
# Запуск с зависимостями
docker-compose up -d

# Просмотр логов
docker-compose logs -f testing
```

## 📊 API Документация

### Swagger UI
- **Локально**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Основные эндпоинты
- `GET /health` - проверка здоровья
- `POST /tests/execute` - выполнение тестов
- `GET /tests/results` - результаты тестов
- `GET /metrics` - метрики производительности

## 🔍 Selenium Тестирование

### Настройка WebDriver
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Настройка Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=chrome_options)
```

### Пример UI теста
```python
def test_frontend_smoke():
    """Smoke тест фронтенда"""
    driver.get("http://localhost:3000")
    
    # Проверка загрузки страницы
    assert "reLink" in driver.title
    
    # Проверка основных элементов
    assert driver.find_element_by_id("main-content")
    
    # Проверка навигации
    nav = driver.find_element_by_tag_name("nav")
    assert nav.is_displayed()
```

## 📈 Мониторинг и метрики

### Prometheus метрики
- Количество выполненных тестов
- Время выполнения тестов
- Процент успешных тестов
- Количество ошибок по типам

### Grafana дашборды
- Обзор тестирования
- Тренды производительности
- Анализ ошибок
- Прогнозирование проблем

## 🔗 Интеграции

### CI/CD
- Автоматический запуск тестов при push
- Параллельное выполнение тестов
- Уведомления о результатах
- Автоматический rollback при ошибках

### LLM интеграция
- Анализ результатов тестов
- Генерация отчетов
- Предсказание проблем
- Рекомендации по оптимизации

## 🚀 Деплой

### Продакшен
```bash
# Сборка продакшен образа
docker build -t relink-testing:prod .

# Запуск с переменными окружения
docker run -e DATABASE_URL=... relink-testing:prod
```

### CI/CD
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging

## 📚 Дополнительная документация

- [API документация](https://api.relink.dev)
- [Selenium тестирование](selenium/README.md)
- [LLM интеграция](app/llm/README.md)

## 🤝 Вклад в проект

1. Следуйте [правилам кодирования](../docs/CODING_STANDARDS.md)
2. Пишите тесты для новых функций
3. Обновляйте документацию
4. Проверяйте покрытие кода

---

**Testing reLink** - надежное тестирование для SEO-платформы 🧪 