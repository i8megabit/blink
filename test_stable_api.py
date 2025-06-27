#!/usr/bin/env python3
"""Тестирование стабильного API генерации рекомендаций."""

import asyncio
import json
import httpx
from datetime import datetime

async def test_stable_recommendations():
    """Тестирует новый стабильный режим генерации."""
    
    # Конфигурация теста
    BACKEND_URL = "http://localhost:8000"
    TEST_DOMAIN = "example.com"  # Замените на реальный домен
    
    print("🧪 Тестирование стабильного режима генерации рекомендаций")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        
        # 1. Проверка статуса Ollama
        print("🔍 1. Проверка статуса Ollama...")
        try:
            response = await client.get(f"{BACKEND_URL}/api/v1/ollama_status")
            if response.status_code == 200:
                status = response.json()
                print(f"   ✅ Ollama статус: {status.get('status', 'unknown')}")
                print(f"   📋 Модель: {status.get('model_name', 'unknown')}")
                print(f"   🚀 Готов к работе: {status.get('ready_for_work', False)}")
            else:
                print(f"   ❌ Ошибка проверки статуса: {response.status_code}")
                return
        except Exception as e:
            print(f"   ❌ Ошибка подключения к бэкенду: {e}")
            return
        
        # 2. Проверка индексации домена (если нужно)
        print(f"\n🔍 2. Проверка индексации домена {TEST_DOMAIN}...")
        try:
            response = await client.get(f"{BACKEND_URL}/api/v1/domains")
            if response.status_code == 200:
                domains = response.json()
                domain_found = False
                for domain in domains:
                    if domain['name'] == TEST_DOMAIN:
                        domain_found = True
                        print(f"   ✅ Домен найден: {domain['total_posts']} статей проиндексировано")
                        break
                
                if not domain_found:
                    print(f"   ⚠️ Домен {TEST_DOMAIN} не проиндексирован")
                    print(f"   💡 Используйте POST /api/v1/wp_index для индексации")
                    return
            else:
                print(f"   ❌ Ошибка получения доменов: {response.status_code}")
                return
        except Exception as e:
            print(f"   ❌ Ошибка проверки доменов: {e}")
            return
        
        # 3. Тестирование стабильного режима
        print(f"\n🚀 3. Запуск стабильной генерации для {TEST_DOMAIN}...")
        
        start_time = datetime.now()
        
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/wp_stable",
                json={
                    "domain": TEST_DOMAIN,
                    "client_id": f"test_{int(start_time.timestamp())}"
                },
                timeout=300.0  # 5 минут
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if response.status_code == 200:
                result = response.json()
                recommendations = result.get('recommendations', [])
                
                print(f"   ✅ Генерация завершена успешно!")
                print(f"   ⏱️ Время выполнения: {duration:.1f} секунд")
                print(f"   📊 Получено рекомендаций: {len(recommendations)}")
                
                # Показываем первые 3 рекомендации
                if recommendations:
                    print(f"\n   📋 Первые рекомендации:")
                    for i, rec in enumerate(recommendations[:3], 1):
                        print(f"   {i}. {rec.get('anchor', 'Без анкора')}")
                        print(f"      🔗 {rec.get('from', 'N/A')} -> {rec.get('to', 'N/A')}")
                        print(f"      💭 {rec.get('comment', 'Без комментария')[:100]}...")
                        print()
                else:
                    print("   ⚠️ Рекомендации не сгенерированы")
                
            else:
                print(f"   ❌ Ошибка генерации: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📋 Детали: {error_detail}")
                except:
                    print(f"   📋 Ответ: {response.text[:200]}...")
                
        except httpx.TimeoutException:
            print(f"   ⏰ Таймаут после 5 минут ожидания")
        except Exception as e:
            print(f"   ❌ Ошибка выполнения: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(test_stable_recommendations()) 