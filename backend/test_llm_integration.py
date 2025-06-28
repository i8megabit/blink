#!/usr/bin/env python3
"""
🧪 Тестирование индексации WordPress и интеграции с LLM Router

Этот скрипт тестирует:
1. Индексацию WordPress сайта
2. Генерацию SEO рекомендаций через LLM Router
3. Интеграцию всех компонентов системы
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReLinkTester:
    """Тестер для reLink системы"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self.auth_token = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def setup_test_user(self) -> bool:
        """Создание тестового пользователя"""
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/test/setup")
            if response.status_code == 200:
                logger.info("✅ Тестовый пользователь создан")
                return True
            else:
                logger.error(f"❌ Ошибка создания тестового пользователя: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка создания тестового пользователя: {e}")
            return False
    
    async def login(self) -> bool:
        """Вход в систему"""
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/test/login")
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                logger.info("✅ Успешный вход в систему")
                return True
            else:
                logger.error(f"❌ Ошибка входа: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка входа: {e}")
            return False
    
    async def get_headers(self) -> Dict[str, str]:
        """Получение заголовков с авторизацией"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def test_wordpress_indexing(self, domain: str) -> Dict[str, Any]:
        """Тестирование индексации WordPress сайта"""
        try:
            logger.info(f"🔍 Начинаю индексацию WordPress сайта: {domain}")
            
            headers = await self.get_headers()
            payload = {
                "domain": domain,
                "comprehensive": True
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/wordpress/index",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Индексация завершена успешно")
                logger.info(f"   - Найдено статей: {data.get('posts_count', 0)}")
                logger.info(f"   - Домен ID: {data.get('domain_id', 0)}")
                return data
            else:
                logger.error(f"❌ Ошибка индексации: {response.status_code}")
                logger.error(f"   Ответ: {response.text}")
                return {"error": f"HTTP {response.status_code}", "details": response.text}
                
        except Exception as e:
            logger.error(f"❌ Ошибка индексации: {e}")
            return {"error": str(e)}
    
    async def test_seo_recommendations(self, domain: str) -> Dict[str, Any]:
        """Тестирование генерации SEO рекомендаций"""
        try:
            logger.info(f"🧠 Генерирую SEO рекомендации для: {domain}")
            
            headers = await self.get_headers()
            payload = {
                "domain": domain,
                "comprehensive": True
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/seo/recommendations",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                logger.info(f"✅ SEO рекомендации сгенерированы успешно")
                logger.info(f"   - Количество рекомендаций: {len(recommendations)}")
                logger.info(f"   - Проанализировано статей: {data.get('posts_analyzed', 0)}")
                
                # Анализируем типы рекомендаций
                llm_recommendations = [r for r in recommendations if r.get('source') == 'llm_router']
                classic_recommendations = [r for r in recommendations if r.get('source') != 'llm_router']
                
                logger.info(f"   - AI рекомендаций: {len(llm_recommendations)}")
                logger.info(f"   - Классических рекомендаций: {len(classic_recommendations)}")
                
                # Показываем примеры рекомендаций
                for i, rec in enumerate(recommendations[:3]):
                    logger.info(f"   Рекомендация {i+1}: {rec.get('title', 'Без заголовка')} ({rec.get('priority', 'unknown')})")
                
                return data
            else:
                logger.error(f"❌ Ошибка генерации рекомендаций: {response.status_code}")
                logger.error(f"   Ответ: {response.text}")
                return {"error": f"HTTP {response.status_code}", "details": response.text}
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации рекомендаций: {e}")
            return {"error": str(e)}
    
    async def test_llm_router_status(self) -> Dict[str, Any]:
        """Проверка статуса LLM Router"""
        try:
            logger.info("🔧 Проверяю статус LLM Router")
            
            headers = await self.get_headers()
            response = await self.client.get(
                f"{self.base_url}/api/v1/ollama_status",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ LLM Router работает")
                logger.info(f"   - Модель: {data.get('model', 'неизвестно')}")
                logger.info(f"   - Статус: {data.get('status', 'неизвестно')}")
                return data
            else:
                logger.error(f"❌ Ошибка проверки LLM Router: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки LLM Router: {e}")
            return {"error": str(e)}
    
    async def test_full_workflow(self, domain: str) -> Dict[str, Any]:
        """Полный тест рабочего процесса"""
        logger.info("🚀 Начинаю полный тест рабочего процесса")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "domain": domain,
            "steps": {}
        }
        
        # Шаг 1: Проверка LLM Router
        logger.info("\n📋 Шаг 1: Проверка LLM Router")
        llm_status = await self.test_llm_router_status()
        results["steps"]["llm_router_status"] = llm_status
        
        if llm_status.get("error"):
            logger.error("❌ LLM Router недоступен, прерываю тест")
            return results
        
        # Шаг 2: Индексация WordPress
        logger.info("\n📋 Шаг 2: Индексация WordPress")
        indexing_result = await self.test_wordpress_indexing(domain)
        results["steps"]["wordpress_indexing"] = indexing_result
        
        if indexing_result.get("error"):
            logger.error("❌ Ошибка индексации, прерываю тест")
            return results
        
        # Шаг 3: Генерация SEO рекомендаций
        logger.info("\n📋 Шаг 3: Генерация SEO рекомендаций")
        seo_result = await self.test_seo_recommendations(domain)
        results["steps"]["seo_recommendations"] = seo_result
        
        # Анализ результатов
        logger.info("\n📊 Анализ результатов:")
        
        if not seo_result.get("error"):
            recommendations = seo_result.get("recommendations", [])
            llm_recs = [r for r in recommendations if r.get("source") == "llm_router"]
            
            if llm_recs:
                logger.info("✅ LLM Router успешно интегрирован и работает")
                logger.info(f"   - AI рекомендаций: {len(llm_recs)}")
                
                # Показываем пример AI рекомендации
                if llm_recs:
                    ai_rec = llm_recs[0]
                    logger.info(f"   - Пример AI рекомендации: {ai_rec.get('title')}")
                    logger.info(f"     Модель: {ai_rec.get('model_used', 'неизвестно')}")
                    logger.info(f"     Время обработки: {ai_rec.get('processing_time', 0):.2f}с")
            else:
                logger.warning("⚠️ LLM Router не вернул рекомендаций")
        else:
            logger.error("❌ Ошибка в генерации SEO рекомендаций")
        
        return results

async def main():
    """Основная функция тестирования"""
    logger.info("🧪 Запуск тестирования reLink системы")
    
    # Тестовые домены WordPress
    test_domains = [
        "https://wordpress.org",
        "https://www.smashingmagazine.com",
        "https://www.wpbeginner.com"
    ]
    
    async with ReLinkTester() as tester:
        # Настройка тестового пользователя
        if not await tester.setup_test_user():
            logger.error("❌ Не удалось создать тестового пользователя")
            return
        
        # Вход в систему
        if not await tester.login():
            logger.error("❌ Не удалось войти в систему")
            return
        
        # Тестируем каждый домен
        for domain in test_domains:
            logger.info(f"\n{'='*60}")
            logger.info(f"🎯 Тестирование домена: {domain}")
            logger.info(f"{'='*60}")
            
            results = await tester.test_full_workflow(domain)
            
            # Сохраняем результаты
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Результаты сохранены в {filename}")
            
            # Небольшая пауза между тестами
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main()) 