# ⚡ Быстрый запуск - Параллельный режим

## 🚀 Один клик - оба варианта

```bash
# 1. Перейдите в директорию проекта
cd seo_link_recommender

# 2. Запустите оба варианта
./run_parallel.sh
```

## 🌐 Доступ через 2 минуты

| Вариант | URL | Описание |
|---------|-----|----------|
| 🎯 **Classic** | http://localhost:3000 | Обычный frontend |
| ⚡ **Vite** | http://localhost:3001 | Современный frontend |
| 🔧 **API** | http://localhost:8000 | Backend |
| 🧠 **Ollama** | http://localhost:11434 | AI модели |

## 🛑 Остановка

```bash
# Ctrl+C в терминале или
docker-compose -f docker-compose.parallel.yml down
```

## 🔍 Проверка статуса

```bash
# Статус контейнеров
docker-compose -f docker-compose.parallel.yml ps

# Логи
docker-compose -f docker-compose.parallel.yml logs -f
```

## 🚨 Если что-то не работает

```bash
# Очистка и перезапуск
docker-compose -f docker-compose.parallel.yml down
docker system prune -f
./run_parallel.sh
```

---

**🎉 Готово!** Теперь у вас запущены оба варианта для сравнения. 