#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции ChromaDB с OpenTelemetry
"""

import os
import sys
import time
import requests
import json
from typing import Dict, Any

def test_chromadb_connection() -> Dict[str, Any]:
    """Тестирование подключения к ChromaDB"""
    try:
        # Проверка доступности ChromaDB
        response = requests.get("http://localhost:8006/api/v1/heartbeat", timeout=5)
        if response.status_code == 200:
            return {"status": "success", "message": "ChromaDB доступен"}
        else:
            return {"status": "error", "message": f"ChromaDB недоступен: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка подключения к ChromaDB: {e}"}

def test_otel_collector_connection() -> Dict[str, Any]:
    """Тестирование подключения к OpenTelemetry Collector"""
    try:
        # Проверка доступности OpenTelemetry Collector
        response = requests.get("http://localhost:4317", timeout=5)
        return {"status": "success", "message": "OpenTelemetry Collector доступен"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка подключения к OpenTelemetry Collector: {e}"}

def check_chromadb_environment() -> Dict[str, Any]:
    """Проверка переменных окружения ChromaDB"""
    env_vars = {
        "CHROMA_OTEL_COLLECTION_ENDPOINT": os.getenv("CHROMA_OTEL_COLLECTION_ENDPOINT"),
        "CHROMA_OTEL_SERVICE_NAME": os.getenv("CHROMA_OTEL_SERVICE_NAME"),
        "CHROMA_OTEL_GRANULARITY": os.getenv("CHROMA_OTEL_GRANULARITY"),
        "OTEL_EXPORTER_OTLP_ENDPOINT": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        "OTEL_SERVICE_NAME": os.getenv("OTEL_SERVICE_NAME"),
        "OTEL_TRACES_SAMPLER": os.getenv("OTEL_TRACES_SAMPLER")
    }
    
    missing_vars = [k for k, v in env_vars.items() if not v]
    
    if missing_vars:
        return {
            "status": "warning", 
            "message": f"Отсутствуют переменные окружения: {missing_vars}",
            "env_vars": env_vars
        }
    else:
        return {
            "status": "success", 
            "message": "Все переменные окружения установлены",
            "env_vars": env_vars
        }

def test_chromadb_operations() -> Dict[str, Any]:
    """Тестирование операций ChromaDB"""
    try:
        # Создание тестовой коллекции
        collection_name = f"test_collection_{int(time.time())}"
        
        # Создание коллекции
        create_response = requests.post(
            "http://localhost:8006/api/v1/collections",
            json={"name": collection_name},
            timeout=10
        )
        
        if create_response.status_code != 200:
            return {"status": "error", "message": f"Ошибка создания коллекции: {create_response.status_code}"}
        
        # Получение списка коллекций
        list_response = requests.get("http://localhost:8006/api/v1/collections", timeout=10)
        
        if list_response.status_code == 200:
            collections = list_response.json()
            test_collection = next((c for c in collections if c["name"] == collection_name), None)
            
            if test_collection:
                # Удаление тестовой коллекции
                delete_response = requests.delete(
                    f"http://localhost:8006/api/v1/collections/{collection_name}",
                    timeout=10
                )
                
                return {
                    "status": "success", 
                    "message": "Операции ChromaDB работают корректно",
                    "collection_id": test_collection["id"]
                }
            else:
                return {"status": "error", "message": "Тестовая коллекция не найдена"}
        else:
            return {"status": "error", "message": f"Ошибка получения списка коллекций: {list_response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Ошибка тестирования операций ChromaDB: {e}"}

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование интеграции ChromaDB с OpenTelemetry")
    print("=" * 60)
    
    # Тест 1: Проверка переменных окружения
    print("\n1. Проверка переменных окружения...")
    env_result = check_chromadb_environment()
    print(f"   Статус: {env_result['status']}")
    print(f"   Сообщение: {env_result['message']}")
    
    # Тест 2: Проверка подключения к ChromaDB
    print("\n2. Проверка подключения к ChromaDB...")
    chromadb_result = test_chromadb_connection()
    print(f"   Статус: {chromadb_result['status']}")
    print(f"   Сообщение: {chromadb_result['message']}")
    
    # Тест 3: Проверка подключения к OpenTelemetry Collector
    print("\n3. Проверка подключения к OpenTelemetry Collector...")
    otel_result = test_otel_collector_connection()
    print(f"   Статус: {otel_result['status']}")
    print(f"   Сообщение: {otel_result['message']}")
    
    # Тест 4: Тестирование операций ChromaDB
    print("\n4. Тестирование операций ChromaDB...")
    operations_result = test_chromadb_operations()
    print(f"   Статус: {operations_result['status']}")
    print(f"   Сообщение: {operations_result['message']}")
    
    # Итоговый результат
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    
    all_results = [env_result, chromadb_result, otel_result, operations_result]
    success_count = sum(1 for r in all_results if r['status'] == 'success')
    error_count = sum(1 for r in all_results if r['status'] == 'error')
    warning_count = sum(1 for r in all_results if r['status'] == 'warning')
    
    print(f"   ✅ Успешно: {success_count}")
    print(f"   ⚠️  Предупреждения: {warning_count}")
    print(f"   ❌ Ошибки: {error_count}")
    
    if error_count == 0:
        print("\n🎉 Все тесты прошли успешно!")
        return 0
    else:
        print("\n⚠️  Обнаружены проблемы, требующие внимания.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 