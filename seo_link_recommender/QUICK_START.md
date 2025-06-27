# 🚀 Быстрый старт с резервным GPU режимом

## 📦 Основной режим (по умолчанию)
```bash
# Стандартный запуск в контейнерах
cd seo_link_recommender
docker-compose up
```
**Доступ:** http://localhost:8000 (backend), http://localhost:3000 (frontend)

---

## ⚡ Резервный GPU режим (в 2-3 раза быстрее!)

### 1️⃣ Первоначальная настройка (только один раз):
```bash
# Установка нативной Ollama с общими моделями
./seo_link_recommender/scripts/native-gpu-setup.sh
```

### 2️⃣ Быстрое переключение между режимами:
```bash
# Переключатель режимов
./seo_link_recommender/scripts/switch-mode.sh

# Варианты:
./seo_link_recommender/scripts/switch-mode.sh container  # В контейнеры  
./seo_link_recommender/scripts/switch-mode.sh native     # В GPU режим
./seo_link_recommender/scripts/switch-mode.sh status     # Статус
./seo_link_recommender/scripts/switch-mode.sh stop       # Остановить всё
```

---

## 🔄 Команды для разных ситуаций

### 🏠 Обычная работа (рекомендуется):
```bash
cd seo_link_recommender
docker-compose up
```

### 🔥 Максимальная производительность:
```bash  
./seo_link_recommender/scripts/switch-mode.sh native
```

### 🔍 Проверить что работает:
```bash
./seo_link_recommender/scripts/switch-mode.sh status
```

### 🛑 Остановить всё:
```bash
./seo_link_recommender/scripts/switch-mode.sh stop
```

---

## 📊 Сравнение режимов

| Режим | Скорость | Доступ | Использование |
|-------|----------|--------|--------------|
| **Контейнеры** | 15-25 tok/s | :8000, :3000 | Ежедневная работа |
| **Нативный GPU** | 40-60 tok/s | :8001, :3001 | Демо, бенчмарки |

---

## 💡 Преимущества общих моделей

✅ **Модели скачиваются только один раз**  
✅ **Быстрое переключение между режимами**  
✅ **Экономия места на диске**  
✅ **Синхронизация кастомных моделей**

---

## 🔧 Устранение проблем

### Ollama не запускается нативно:
```bash
# Проверить установку
which ollama

# Переустановить
curl -fsSL https://ollama.com/install.sh | sh
```

### Конфликт портов:
```bash
# Остановить всё и начать заново
./seo_link_recommender/scripts/switch-mode.sh stop
./seo_link_recommender/scripts/switch-mode.sh container
```

### Модели не видны:
```bash
# Проверить права доступа
ls -la seo_link_recommender/ollama_models/

# Пересоздать модели
./seo_link_recommender/scripts/native-gpu-setup.sh
```

---

## 🎯 Рекомендации

- **Начните с контейнерного режима** - он стабильнее
- **Переключайтесь на GPU для демо** - впечатляет скоростью  
- **Используйте `status`** для диагностики проблем
- **`stop` перед переключением** между режимами

**🔗 Подробное руководство:** `GPU_GUIDE.md` 