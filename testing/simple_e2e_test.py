#!/usr/bin/env python3
"""
Простой тест интеграции ChromaDB без телеметрии
"""

import requests
import time
import json

def test_chromadb():
    """Тест ChromaDB"""
    try:
        # Проверка heartbeat
        response = requests.get("http://localhost:8006/api/v2/heartbeat", timeout=5)
        if response.status_code == 200:
            print("✅ ChromaDB heartbeat: OK")
            
            # Получение tenant и database
            response = requests.get("http://localhost:8006/api/v2/auth/identity", timeout=5)
            if response.status_code == 200:
                identity = response.json()
                tenant = identity.get('tenant', 'default_tenant')
                database = identity.get('databases', ['default_database'])[0]
                
                # Проверка коллекций с правильным путем
                collections_url = f"http://localhost:8006/api/v2/tenants/{tenant}/databases/{database}/collections"
                response = requests.get(collections_url, timeout=5)
                if response.status_code == 200:
                    collections = response.json()
                    print(f"✅ ChromaDB collections: найдено {len(collections)} коллекций")
                    return True
                else:
                    print(f"❌ ChromaDB collections: ошибка {response.status_code}")
                    return False
            else:
                print(f"❌ ChromaDB identity: ошибка {response.status_code}")
                return False
        else:
            print(f"❌ ChromaDB heartbeat: ошибка {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ChromaDB: ошибка подключения - {e}")
        return False

def test_ollama():
    """Тест Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models_count = len(data.get('models', []))
            print(f"✅ Ollama API: доступен")
            
            if models_count > 0:
                model_names = [model.get('name', '') for model in data.get('models', [])]
                print(f"✅ Ollama модели: найдено {models_count} моделей")
                print(f"   Доступные модели: {', '.join(model_names[:3])}{'...' if len(model_names) > 3 else ''}")
                return True
            else:
                print(f"⚠️  Ollama модели: НЕТ МОДЕЛЕЙ! Система не может генерировать рекомендации")
                return False
        else:
            print(f"❌ Ollama: ошибка {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama: ошибка подключения - {e}")
        return False

def test_relink():
    """Тест relink service"""
    try:
        response = requests.get("http://localhost:8003/health", timeout=5)
        if response.status_code == 200:
            print("✅ relink service: OK")
            return True
        else:
            print(f"❌ relink service: ошибка {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ relink service: ошибка подключения - {e}")
        return False

def test_router():
    """Тест router"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ router: OK")
            return True
        else:
            print(f"❌ router: ошибка {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ router: ошибка подключения - {e}")
        return False

def test_llm_tuning():
    """Тест LLM tuning service"""
    try:
        response = requests.get("http://localhost:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ LLM tuning service: OK")
            return True
        else:
            print(f"❌ LLM tuning service: ошибка {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LLM tuning service: ошибка подключения - {e}")
        return False

def main():
    """Основная функция"""
    print("🧪 Простой тест интеграции ChromaDB без телеметрии")
    print("=" * 60)
    
    tests = [
        ("ChromaDB", test_chromadb),
        ("Ollama", test_ollama),
        ("relink service", test_relink),
        ("router", test_router),
        ("LLM tuning service", test_llm_tuning),
    ]
    
    results = {}
    successful = 0
    
    for name, test_func in tests:
        print(f"\n🔍 Тестирование {name}...")
        result = test_func()
        results[name] = result
        if result:
            successful += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты: {successful}/{len(tests)} тестов прошли успешно")
    print(f"📈 Процент успеха: {(successful/len(tests)*100):.1f}%")
    
    if successful == len(tests):
        print("🎉 Все сервисы работают корректно!")
    else:
        print("⚠️  Некоторые сервисы имеют проблемы")
    
    # Сохранение результатов
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": len(tests),
        "successful_tests": successful,
        "success_rate": (successful/len(tests)*100),
        "results": results
    }
    
    filename = f"simple_test_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Отчет сохранен в: {filename}")

if __name__ == "__main__":
    main() 