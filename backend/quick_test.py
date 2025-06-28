#!/usr/bin/env python3
"""
⚡ Быстрый тест индексации WordPress и LLM интеграции

Простой тест для проверки:
1. Работы API
2. Индексации WordPress
3. LLM Router интеграции
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def quick_test():
    """Быстрый тест системы"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info("🚀 Запуск быстрого теста")
            
            # 1. Проверка здоровья API
            logger.info("📋 Проверка здоровья API...")
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                logger.info("✅ API работает")
            else:
                logger.error(f"❌ API недоступен: {response.status_code}")
                return
            
            # 2. Создание тестового пользователя
            logger.info("📋 Создание тестового пользователя...")
            response = await client.post(f"{base_url}/api/v1/test/setup")
            if response.status_code != 200:
                logger.error(f"❌ Ошибка создания пользователя: {response.status_code}")
                return
            logger.info("✅ Тестовый пользователь создан")
            
            # 3. Вход в систему
            logger.info("📋 Вход в систему...")
            response = await client.post(f"{base_url}/api/v1/test/login")
            if response.status_code != 200:
                logger.error(f"❌ Ошибка входа: {response.status_code}")
                return
            
            data = response.json()
            token = data.get("access_token")
            if not token:
                logger.error("❌ Токен не получен")
                return
            logger.info("✅ Успешный вход")
            
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            # 4. Проверка статуса Ollama
            logger.info("📋 Проверка статуса Ollama...")
            response = await client.get(f"{base_url}/api/v1/ollama_status", headers=headers)
            if response.status_code == 200:
                ollama_data = response.json()
                logger.info(f"✅ Ollama работает: {ollama_data.get('model', 'неизвестно')}")
            else:
                logger.warning(f"⚠️ Ollama недоступен: {response.status_code}")
            
            # 5. Тест индексации WordPress
            test_domain = "https://wordpress.org"
            logger.info(f"📋 Тест индексации: {test_domain}")
            
            payload = {"domain": test_domain, "comprehensive": False}
            response = await client.post(
                f"{base_url}/api/v1/wordpress/index",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                index_data = response.json()
                posts_count = index_data.get("posts_count", 0)
                logger.info(f"✅ Индексация успешна: {posts_count} статей")
                
                # 6. Тест SEO рекомендаций
                if posts_count > 0:
                    logger.info("📋 Генерация SEO рекомендаций...")
                    seo_payload = {"domain": test_domain}
                    response = await client.post(
                        f"{base_url}/api/v1/seo/recommendations",
                        json=seo_payload,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        seo_data = response.json()
                        recommendations = seo_data.get("recommendations", [])
                        llm_recs = [r for r in recommendations if r.get("source") == "llm_router"]
                        
                        logger.info(f"✅ SEO рекомендации сгенерированы: {len(recommendations)} всего, {len(llm_recs)} от AI")
                        
                        if llm_recs:
                            logger.info("🎉 LLM Router успешно интегрирован!")
                            # Показываем пример AI рекомендации
                            ai_rec = llm_recs[0]
                            logger.info(f"   Пример AI рекомендации: {ai_rec.get('title')}")
                        else:
                            logger.warning("⚠️ LLM Router не вернул рекомендаций")
                    else:
                        logger.error(f"❌ Ошибка SEO рекомендаций: {response.status_code}")
                else:
                    logger.warning("⚠️ Нет статей для анализа")
            else:
                logger.error(f"❌ Ошибка индексации: {response.status_code}")
                logger.error(f"   Ответ: {response.text}")
            
            logger.info("🏁 Быстрый тест завершен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка теста: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test()) 