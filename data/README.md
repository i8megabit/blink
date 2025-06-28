# 📊 База данных reLink

## 🗂️ Структура директории

```
data/
├── relink_db/          # PostgreSQL база данных
├── ollama_models/      # Модели Ollama
├── chroma_db/          # ChromaDB векторная база
└── README.md          # Этот файл
```

## ⚠️ Важные замечания

### Git игнорирование
Все файлы базы данных исключены из системы контроля версий git:
- `data/relink_db/**/*` - файлы PostgreSQL
- `data/ollama_models/**/*` - модели Ollama  
- `data/chroma_db/**/*` - файлы ChromaDB

### Инициализация БД
При первом запуске Docker Compose база данных будет автоматически инициализирована.

### Резервное копирование
Для резервного копирования используйте:
```bash
# PostgreSQL
docker exec -t relink-postgres pg_dumpall -c -U postgres > backup.sql

# Восстановление
cat backup.sql | docker exec -i relink-postgres psql -U postgres
```

### Очистка данных
Для полной очистки всех данных:
```bash
docker-compose down -v
rm -rf data/relink_db/*
rm -rf data/chroma_db/*
```

## 🔧 Настройка

### Переменные окружения
Настройте переменные в `.env` файле:
```env
POSTGRES_DB=relink
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

### Права доступа
Убедитесь, что директория `data/` имеет правильные права доступа:
```bash
chmod 755 data/
chmod 755 data/relink_db/
```

## 📈 Мониторинг

### Размер БД
```bash
du -sh data/relink_db/
du -sh data/chroma_db/
du -sh data/ollama_models/
```

### Логи PostgreSQL
```bash
docker logs relink-postgres
```

## 🚨 Безопасность

- Никогда не коммитьте файлы БД в git
- Регулярно делайте резервные копии
- Используйте сильные пароли
- Ограничьте доступ к директории `data/` 