# 🤖 UX Bot - Автоматизированное тестирование UX reLink

Система автоматизированного тестирования пользовательского опыта для платформы reLink с интеграцией Selenium и AI.

## 🚀 Быстрый старт

```bash
# Запуск через Docker Compose
docker-compose up -d

# Локальная разработка
pip install -r requirements.txt
python app/core.py

# Запуск тестов
pytest tests/
```

## 🏗️ Архитектура

### Технологический стек
- **Selenium** - автоматизация браузера
- **Playwright** - современное UI тестирование
- **Python** - основной язык
- **FastAPI** - API для управления тестами
- **SQLAlchemy** - ORM для работы с БД
- **AI/ML** - интеллектуальный анализ UX

### Структура проекта
```
app/
├── core.py              # Основная логика
├── config.py            # Конфигурация
├── models.py            # Модели данных
├── services/
│   ├── browser_service.py    # Работа с браузером
│   └── scenario_service.py   # Сценарии тестирования
├── api_client.py        # API клиент
└── main.py              # Точка входа

tests/
├── test_ux_bot.py       # Основные тесты
├── test_ux_bot_fast.py  # Быстрые тесты
└── test_comprehensive_ux_bot.py  # Комплексные тесты

reports/                 # Отчеты о тестировании
screenshots/             # Скриншоты
```

## 🎯 Основные функции

### Автоматизированное тестирование
- Автоматическое прохождение пользовательских сценариев
- Тестирование всех основных функций
- Проверка отзывчивости интерфейса
- Анализ производительности

### UX анализ
- Анализ удобства использования
- Выявление проблем интерфейса
- Рекомендации по улучшению
- Метрики пользовательского опыта

### Скриншоты и видео
- Автоматические скриншоты
- Запись видео тестирования
- Документирование проблем
- Сравнение версий

### Интеграция с AI
- Интеллектуальный анализ результатов
- Автоматическая генерация отчетов
- Предсказание проблем UX
- Рекомендации по оптимизации

## 🔧 Разработка

### Команды разработки
```bash
# Запуск основного приложения
python app/core.py

# Запуск тестов
pytest tests/ -v

# Запуск быстрых тестов
pytest tests/test_ux_bot_fast.py

# Запуск комплексных тестов
pytest tests/test_comprehensive_ux_bot.py
```

### Создание сценариев
```python
from app.services.scenario_service import ScenarioService

# Инициализация сервиса
scenario = ScenarioService()

# Создание сценария тестирования
scenario.create_scenario(
    name="user_registration",
    steps=[
        "open_homepage",
        "click_register",
        "fill_form",
        "submit_form",
        "verify_success"
    ]
)

# Запуск сценария
scenario.run_scenario("user_registration")
```

## 🧪 Тестирование

### Unit тесты
```bash
# Запуск всех тестов
pytest

# Запуск конкретного теста
pytest tests/test_ux_bot.py::test_homepage_load

# Запуск с покрытием
pytest --cov=app tests/
```

### Интеграционные тесты
```bash
# Тесты с реальным браузером
pytest tests/test_comprehensive_ux_bot.py

# Тесты API
pytest tests/test_api_client.py
```

## 🐳 Docker

### Сборка образа
```bash
# Сборка образа
docker build -t relink-ux-bot .

# Запуск контейнера
docker run -p 8006:8006 relink-ux-bot
```

### Docker Compose
```bash
# Запуск с зависимостями
docker-compose up -d

# Просмотр логов
docker-compose logs -f ux-bot
```

## 📊 API Документация

### Swagger UI
- **Локально**: http://localhost:8006/docs
- **ReDoc**: http://localhost:8006/redoc

### Основные эндпоинты
- `GET /health` - проверка здоровья
- `POST /scenarios/run` - запуск сценария
- `GET /scenarios/results` - результаты тестирования
- `GET /reports` - отчеты UX

## 🔍 Типы тестирования

### Функциональное тестирование
```python
# Тестирование основных функций
def test_user_registration():
    """Тест регистрации пользователя"""
    browser = BrowserService()
    
    # Открытие страницы
    browser.open_page("http://localhost:3000")
    
    # Нажатие кнопки регистрации
    browser.click_element("#register-btn")
    
    # Заполнение формы
    browser.fill_input("#email", "test@example.com")
    browser.fill_input("#password", "password123")
    
    # Отправка формы
    browser.click_element("#submit-btn")
    
    # Проверка успешной регистрации
    assert browser.element_exists(".success-message")
```

### UX тестирование
```python
# Тестирование пользовательского опыта
def test_navigation_flow():
    """Тест навигации по сайту"""
    browser = BrowserService()
    
    # Проверка доступности элементов
    assert browser.element_visible("#main-nav")
    assert browser.element_clickable("#home-link")
    
    # Проверка отзывчивости
    response_time = browser.measure_response_time("#home-link")
    assert response_time < 1000  # менее 1 секунды
```

## 📈 Метрики UX

### Производительность
- Время загрузки страниц
- Время отклика интерфейса
- Плавность анимаций
- Оптимизация ресурсов

### Удобство использования
- Доступность элементов
- Интуитивность навигации
- Читаемость контента
- Мобильная адаптивность

### Функциональность
- Работоспособность функций
- Обработка ошибок
- Валидация форм
- Интеграция компонентов

## 📋 Отчеты

### Автоматические отчеты
```python
# Генерация отчета
report = ux_bot.generate_report(
    test_name="comprehensive_ux_test",
    format="html"
)

# Экспорт результатов
ux_bot.export_results(
    format="json",
    filename="ux_test_results.json"
)
```

### Скриншоты и видео
```python
# Создание скриншота
browser.take_screenshot("homepage.png")

# Запись видео
browser.start_recording()
# выполнение действий
browser.stop_recording("test_session.mp4")
```

## 🔗 Интеграции

### Selenium
- Автоматизация браузера
- Поддержка различных браузеров
- Эмуляция пользовательских действий
- Создание скриншотов

### Playwright
- Современное UI тестирование
- Поддержка мобильных устройств
- Автоматическая запись видео
- Эмуляция сетевых условий

### AI/ML
- Анализ результатов тестирования
- Предсказание проблем UX
- Автоматическая генерация отчетов
- Рекомендации по улучшению

## 🚀 Деплой

### Продакшен
```bash
# Сборка продакшен образа
docker build -t relink-ux-bot:prod .

# Запуск с переменными окружения
docker run -e DATABASE_URL=... relink-ux-bot:prod
```

### CI/CD
- Автоматическая сборка при push
- Тестирование перед деплоем
- Автоматический деплой в staging

## 📚 Дополнительная документация

- [API документация](https://api.relink.dev)
- [Сценарии тестирования](app/services/scenario_service.py)
- [Браузерный сервис](app/services/browser_service.py) 