# 🚀 Бенчмарки производительности LLM Tuning Microservice

Этот каталог содержит инструменты для тестирования производительности всех API эндпоинтов LLM Tuning Microservice.

## 📋 Содержание

- `performance_test.py` - Основной скрипт бенчмарков
- `README.md` - Данная инструкция

## 🎯 Доступные бенчмарки

### 1. A/B Тестирование (`ab_testing`)
- Создание A/B тестов
- Выбор моделей для тестирования
- Запись результатов
- **Количество запросов по умолчанию**: 100

### 2. Автоматическая оптимизация (`optimization`)
- Запуск оптимизации моделей
- Получение статуса оптимизации
- **Количество запросов по умолчанию**: 50

### 3. Оценка качества (`quality_assessment`)
- Оценка качества ответов моделей
- Анализ по различным критериям
- **Количество запросов по умолчанию**: 100

### 4. Мониторинг здоровья системы (`system_health`)
- Получение текущего состояния здоровья
- История метрик здоровья
- **Количество запросов по умолчанию**: 200

### 5. Расширенная статистика (`extended_stats`)
- Статистика по моделям
- Общая статистика системы
- **Количество запросов по умолчанию**: 100

## 🚀 Запуск бенчмарков

### Предварительные требования

1. **Установка зависимостей**:
```bash
pip install aiohttp psutil matplotlib numpy
```

2. **Запуск LLM Tuning Microservice**:
```bash
# В корневой директории проекта
make run
# или
docker-compose up -d
```

### Полный бенчмарк

Запуск всех бенчмарков последовательно:

```bash
cd benchmarks
python performance_test.py
```

### Конкретный бенчмарк

Запуск конкретного бенчмарка с указанием количества запросов:

```bash
# A/B тестирование с 50 запросами
python performance_test.py ab_testing 50

# Оптимизация с 30 запросами
python performance_test.py optimization 30

# Оценка качества с 200 запросами
python performance_test.py quality_assessment 200

# Мониторинг здоровья с 100 запросами
python performance_test.py system_health 100

# Расширенная статистика с 150 запросами
python performance_test.py extended_stats 150
```

### Через Makefile

```bash
# Полный бенчмарк
make benchmark

# Конкретный бенчмарк
make benchmark-ab-testing
make benchmark-optimization
make benchmark-quality-assessment
make benchmark-system-health
make benchmark-extended-stats
```

## 📊 Результаты

После выполнения бенчмарков создаются следующие файлы:

### 1. `benchmark_report.txt`
Текстовый отчет с детальной статистикой:
- Системные метрики (память, CPU)
- Результаты по каждому тесту
- Общие выводы и рекомендации

### 2. `benchmark_results.png`
Графики производительности:
- Среднее время ответа по тестам
- Процент успешных запросов
- Запросов в секунду
- Использование памяти во время тестов

## 📈 Метрики производительности

### Время ответа
- **Отлично**: < 1.0 секунды
- **Хорошо**: 1.0 - 3.0 секунды
- **Требует оптимизации**: > 3.0 секунды

### Процент успеха
- **Отлично**: > 95%
- **Хорошо**: 90% - 95%
- **Требует внимания**: < 90%

### Запросов в секунду (RPS)
- **Высокая нагрузка**: > 100 RPS
- **Средняя нагрузка**: 50 - 100 RPS
- **Низкая нагрузка**: < 50 RPS

## 🔧 Настройка

### Изменение базового URL

По умолчанию бенчмарки используют `http://localhost:8000`. Для изменения:

```python
async with PerformanceBenchmark("http://your-server:8000") as benchmark:
    # ваши тесты
```

### Настройка количества запросов

```python
# В функции run_full_benchmark()
await benchmark.benchmark_ab_testing(100)      # вместо 50
await benchmark.benchmark_optimization(50)     # вместо 20
await benchmark.benchmark_quality_assessment(200)  # вместо 100
await benchmark.benchmark_system_health(300)   # вместо 150
await benchmark.benchmark_extended_stats(150)  # вместо 80
```

### Добавление новых бенчмарков

1. Создайте новую функцию в классе `PerformanceBenchmark`:
```python
async def benchmark_new_feature(self, num_requests: int = 100) -> Dict:
    """Бенчмарк новой функции"""
    print(f"🆕 Бенчмарк новой функции ({num_requests} запросов)...")
    
    results = []
    for i in range(num_requests):
        # Ваши запросы
        result = await self._make_request("POST", "/api/v1/new-feature", data)
        results.append((f"new_feature_{i}", result))
    
    return self._analyze_results("new_feature", results)
```

2. Добавьте вызов в `run_full_benchmark()`:
```python
await benchmark.benchmark_new_feature(100)
```

3. Добавьте обработку в `run_specific_benchmark()`:
```python
elif benchmark_name == "new_feature":
    result = await benchmark.benchmark_new_feature(num_requests)
```

## 🐛 Отладка

### Проблемы с подключением

Если бенчмарки не могут подключиться к сервису:

1. Проверьте, что сервис запущен:
```bash
curl http://localhost:8000/health
```

2. Проверьте логи сервиса:
```bash
docker-compose logs llm-tuning
```

### Проблемы с памятью

Если бенчмарки потребляют слишком много памяти:

1. Уменьшите количество запросов
2. Добавьте задержки между запросами
3. Используйте сборщик мусора

### Проблемы с производительностью

Если результаты показывают плохую производительность:

1. Проверьте нагрузку на систему
2. Убедитесь, что нет других процессов
3. Проверьте конфигурацию сервиса

## 📝 Примеры использования

### Быстрая проверка производительности

```bash
# Быстрый тест с минимальным количеством запросов
python performance_test.py ab_testing 10
python performance_test.py quality_assessment 20
```

### Стресс-тестирование

```bash
# Высокая нагрузка для проверки стабильности
python performance_test.py system_health 1000
python performance_test.py extended_stats 500
```

### Сравнение версий

```bash
# Тест старой версии
git checkout v1.0.0
python performance_test.py > results_v1.0.0.txt

# Тест новой версии
git checkout main
python performance_test.py > results_main.txt

# Сравнение результатов
diff results_v1.0.0.txt results_main.txt
```

## 🔄 Интеграция с CI/CD

### GitHub Actions

```yaml
name: Performance Tests
on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install aiohttp psutil matplotlib numpy
      - name: Start service
        run: docker-compose up -d
      - name: Wait for service
        run: sleep 30
      - name: Run benchmarks
        run: |
          cd benchmarks
          python performance_test.py
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: |
            benchmarks/benchmark_report.txt
            benchmarks/benchmark_results.png
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install aiohttp psutil matplotlib numpy'
            }
        }
        
        stage('Start Service') {
            steps {
                sh 'docker-compose up -d'
                sh 'sleep 30'
            }
        }
        
        stage('Run Benchmarks') {
            steps {
                dir('benchmarks') {
                    sh 'python performance_test.py'
                }
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'benchmarks/*.txt,benchmarks/*.png'
            }
        }
    }
}
```

## 📚 Дополнительные ресурсы

- [Документация API](../docs/API_EXTENDED.md)
- [Инструкция по интеграции](../INTEGRATION.md)
- [Основной README](../README.md)
- [Примеры использования](../examples/api_examples.py)

## 🤝 Вклад в разработку

Для улучшения бенчмарков:

1. Добавьте новые метрики
2. Улучшите визуализацию
3. Добавьте новые типы тестов
4. Оптимизируйте производительность самих бенчмарков

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи сервиса
2. Убедитесь в корректности конфигурации
3. Создайте issue в репозитории
4. Обратитесь к команде разработки 