#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции ChromaDB v2 (без OpenTelemetry)
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
        # Проверка доступности ChromaDB на правильном порту с API v2
        response = requests.get("http://localhost:8006/api/v2/heartbeat", timeout=5)
        if response.status_code == 200:
            return {"status": "success", "message": "ChromaDB доступен"}
        else:
            return {"status": "error", "message": f"ChromaDB недоступен: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка подключения к ChromaDB: {e}"}

def get_auth_identity() -> Dict[str, Any]:
    """Получение tenant и database из ChromaDB"""
    try:
        response = requests.get("http://localhost:8006/api/v2/auth/identity", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success", 
                "data": data,
                "tenant": data.get("tenant_id", "default_tenant"),
                "database": data.get("database_id", "default_database")
            }
        else:
            return {"status": "error", "message": f"Ошибка получения identity: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка получения identity: {e}"}

def test_chromadb_api() -> Dict[str, Any]:
    """Тестирование основных API ChromaDB v2"""
    try:
        # Получаем tenant и database
        identity = get_auth_identity()
        if identity["status"] != "success":
            return identity
        
        tenant = identity["tenant"]
        database = identity["database"]
        
        print(f"Используем tenant: {tenant}, database: {database}")
        
        # Создание коллекции с API v2
        collection_name = f"test_collection_{int(time.time())}"
        collection_data = {
            "name": collection_name,
            "metadata": {"description": "Test collection for integration testing"}
        }
        
        create_url = f"http://localhost:8006/api/v2/tenants/{tenant}/databases/{database}/collections"
        response = requests.post(create_url, json=collection_data, timeout=10)
        
        if response.status_code == 200:
            collection_info = response.json()
            collection_id = collection_info.get("id")
            
            # Добавление документов в коллекцию
            add_url = f"http://localhost:8006/api/v2/tenants/{tenant}/databases/{database}/collections/{collection_id}/add"
            documents_data = {
                "documents": ["This is a test document"],
                "metadatas": [{"source": "test"}],
                "ids": ["test_id_1"]
            }
            
            add_response = requests.post(add_url, json=documents_data, timeout=10)
            
            if add_response.status_code in (200, 201):
                return {
                    "status": "success", 
                    "message": f"Коллекция {collection_name} создана и документы добавлены",
                    "collection_id": collection_id
                }
            else:
                return {
                    "status": "error", 
                    "message": f"Ошибка добавления документов: {add_response.status_code}"
                }
        else:
            return {
                "status": "error", 
                "message": f"Ошибка создания коллекции: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        return {"status": "error", "message": f"Ошибка API тестирования: {e}"}

def test_chromadb_health() -> Dict[str, Any]:
    """Тестирование health check ChromaDB"""
    try:
        response = requests.get("http://localhost:8006/api/v2/heartbeat", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success", 
                "message": "Health check пройден",
                "data": data
            }
        else:
            return {"status": "error", "message": f"Health check не пройден: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка health check: {e}"}

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование интеграции ChromaDB v2")
    print("=" * 50)
    
    # Тест подключения
    print("\n1. Тестирование подключения к ChromaDB...")
    connection_result = test_chromadb_connection()
    print(f"   Результат: {connection_result['status']} - {connection_result['message']}")
    
    if connection_result["status"] != "success":
        print("❌ ChromaDB недоступен, прекращаем тестирование")
        return
    
    # Тест health check
    print("\n2. Тестирование health check...")
    health_result = test_chromadb_health()
    print(f"   Результат: {health_result['status']} - {health_result['message']}")
    
    # Получение identity
    print("\n3. Получение tenant и database...")
    identity_result = get_auth_identity()
    print(f"   Результат: {identity_result['status']}")
    if identity_result["status"] == "success":
        print(f"   Tenant: {identity_result['tenant']}")
        print(f"   Database: {identity_result['database']}")
    
    # Тест API
    print("\n4. Тестирование API операций...")
    api_result = test_chromadb_api()
    print(f"   Результат: {api_result['status']} - {api_result['message']}")
    
    # Итоговый результат
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    
    all_tests = [
        ("Подключение", connection_result),
        ("Health Check", health_result),
        ("Identity", identity_result),
        ("API Операции", api_result)
    ]
    
    passed = 0
    total = len(all_tests)
    
    for test_name, result in all_tests:
        status = "✅" if result["status"] == "success" else "❌"
        print(f"   {status} {test_name}: {result['status']}")
        if result["status"] == "success":
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ChromaDB v2 работает корректно.")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте конфигурацию.")

if __name__ == "__main__":
    main() 