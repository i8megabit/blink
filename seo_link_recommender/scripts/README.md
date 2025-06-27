# 🛠 Скрипты управления Ollama на Apple M4

## 📋 Обзор скриптов

| Скрипт | Назначение | Использование |
|--------|------------|---------------|
| `switch-mode.sh` | 🔄 Переключатель режимов | Основной скрипт для всех операций |
| `native-gpu-setup.sh` | ⚡ Настройка GPU | Первоначальная настройка нативной Ollama |
| `check_ollama.sh` | 🔍 Проверка состояния | Диагностика Ollama |
| `monitor_ollama_startup.sh` | 📊 Мониторинг запуска | Отслеживание запуска контейнера |

---

## 🚀 Основные команды

### Переключатель режимов (главный скрипт):
```bash
./scripts/switch-mode.sh status     # Проверить статус
./scripts/switch-mode.sh container  # Запуск контейнеров (основной)
./scripts/switch-mode.sh native     # Запуск нативного GPU
./scripts/switch-mode.sh stop       # Остановить все
```

### Первоначальная настройка GPU (только один раз):
```bash
./scripts/native-gpu-setup.sh       # Установка и настройка
```

---

## 🔧 Режимы работы

### 📦 Контейнерный режим (по умолчанию)
- **Запуск:** `docker-compose up` или `./scripts/switch-mode.sh container`
- **Порты:** 8000 (backend), 3000 (frontend), 11434 (ollama)
- **Производительность:** ~15-25 tok/s
- **Память:** 8-12GB
- **Преимущества:** Стабильный, изолированный, простой

### ⚡ Нативный GPU режим (резервный)
- **Запуск:** `./scripts/switch-mode.sh native`
- **Порты:** 8001 (backend), 3001 (frontend), 11434 (ollama)
- **Производительность:** ~40-60 tok/s  
- **Память:** 12-16GB
- **Преимущества:** Максимальная скорость, Metal Performance Shaders

---

## 💾 Общие модели

Все режимы используют **общую папку моделей**:
```
ollama_models/
├── models/           # Сами модели
├── blobs/           # Blob данные
└── manifests/       # Метаданные
```

**Преимущества:**
- ✅ Модели скачиваются один раз
- ✅ Быстрое переключение режимов
- ✅ Экономия дискового пространства
- ✅ Синхронизация кастомных моделей

---

## 🎯 Типичные сценарии

### 🏠 Ежедневная работа:
```bash
docker-compose up
# Доступ: http://localhost:8000
```

### 🔥 Демонстрация/бенчмарк:
```bash
./scripts/switch-mode.sh native
# Доступ: http://localhost:8001  
```

### 🔄 Переключение туда-обратно:
```bash
# В GPU режим
./scripts/switch-mode.sh native

# Обратно в контейнеры  
./scripts/switch-mode.sh container
```

### 🛑 Полная остановка:
```bash
./scripts/switch-mode.sh stop
```

---

## 🔍 Диагностика

### Проверить что работает:
```bash
./scripts/switch-mode.sh status
```

### Детальная диагностика:
```bash
./scripts/check_ollama.sh
```

### Мониторинг запуска:
```bash
./scripts/monitor_ollama_startup.sh
```

### Логи нативной Ollama:
```bash
tail -f /tmp/ollama-native.log
```

---

## ⚠️ Важные замечания

1. **Не запускайте оба режима одновременно** - будет конфликт портов
2. **Используйте `stop` перед переключением** режимов
3. **Нативный режим требует установки Ollama** на хост-систему
4. **Контейнерный режим более стабилен** для длительной работы
5. **GPU режим показывает максимум M4** для демо и бенчмарков

---

## 🚨 Устранение неполадок

### Конфликт портов:
```bash
./scripts/switch-mode.sh stop
sudo lsof -i :11434  # Найти процесс на порту
```

### Ollama не найдена:
```bash
which ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### Права доступа к моделям:
```bash
sudo chown -R $(whoami) ollama_models/
```

### Контейнеры не запускаются:
```bash
docker-compose down
docker system prune
docker-compose up
```

---

## 📊 Мониторинг производительности

### GPU активность:
```bash
sudo powermetrics -n 1 --samplers gpu_power
```

### Память:
```bash
memory_pressure
```

### API тест:
```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "qwen2.5:7b-turbo", "prompt": "тест скорости"}'
```

---

## 🎉 Готовые команды

```bash
# Быстрый старт (контейнеры)
docker-compose up

# Максимальная скорость (GPU)  
./scripts/switch-mode.sh native

# Проверить статус
./scripts/switch-mode.sh status

# Остановить всё
./scripts/switch-mode.sh stop
``` 