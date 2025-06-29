#!/usr/bin/env python3
"""
Тест подключения ChromaDB к OpenTelemetry
"""

import os
import time
import chromadb

def test_chromadb_otel():
    print("🔍 Тестирование ChromaDB с OpenTelemetry...")
    
    # Настройки подключения
    client = chromadb.HttpClient(
        host="localhost",
        port=8006
    )
    
    try:
        # Проверяем подключение
        print("📡 Подключение к ChromaDB...")
        heartbeat = client.heartbeat()
        print(f"✅ ChromaDB подключен: {heartbeat}")
        
        # Создаем тестовую коллекцию
        print("📚 Создание тестовой коллекции...")
        collection = client.create_collection(
            name="test_otel_collection",
            metadata={"description": "Test collection for OpenTelemetry"}
        )
        print(f"✅ Коллекция создана: {collection.name}")
        
        # Добавляем тестовые данные
        print("📝 Добавление тестовых данных...")
        collection.add(
            documents=["This is a test document for OpenTelemetry"],
            metadatas=[{"source": "test"}],
            ids=["test_id_1"]
        )
        print("✅ Данные добавлены")
        
        # Выполняем поиск
        print("🔍 Выполнение поиска...")
        results = collection.query(
            query_texts=["test document"],
            n_results=1
        )
        print(f"✅ Поиск выполнен: найдено {len(results['documents'][0])} документов")
        
        # Удаляем тестовую коллекцию
        print("🗑️ Удаление тестовой коллекции...")
        client.delete_collection(name="test_otel_collection")
        print("✅ Коллекция удалена")
        
        print("\n🎉 Тест ChromaDB успешно завершен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании ChromaDB: {e}")
        return False

if __name__ == "__main__":
    test_chromadb_otel() 