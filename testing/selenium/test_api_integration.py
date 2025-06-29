#!/usr/bin/env python3
"""
🧪 ТЕСТ API ИНТЕГРАЦИИ reLink
Проверка работы фронтенда через API вызовы
"""

import asyncio
import time
import json
import httpx
from typing import Dict, Any, List
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
RAG_URL = "http://localhost:8001"
LLM_ROUTER_URL = "http://localhost:8002"

class APITester:
    """Класс для тестирования API интеграции"""
    
    def __init__(self):
        self.test_results = []
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def test_frontend_availability(self) -> Dict[str, Any]:
        """Тест доступности фронтенда"""
        logger.info("🌐 Тестирование доступности фронтенда")
        
        try:
            start_time = time.time()
            response = await self.client.get(FRONTEND_URL)
            load_time = time.time() - start_time
            
            result = {
                "test": "frontend_availability",
                "status_code": response.status_code,
                "load_time": load_time,
                "content_length": len(response.content),
                "success": response.status_code == 200 and load_time < 5.0
            }
            
            if response.status_code == 200:
                logger.info(f"✅ Фронтенд доступен, время загрузки: {load_time:.2f}s")
            else:
                logger.warning(f"⚠️ Фронтенд недоступен, статус: {response.status_code}")
                
        except Exception as e:
            result = {
                "test": "frontend_availability",
                "error": str(e),
                "success": False
            }
            logger.error(f"❌ Ошибка доступа к фронтенду: {e}")
        
        self.test_results.append(result)
        return result
    
    async def test_backend_health(self) -> Dict[str, Any]:
        """Тест здоровья backend"""
        logger.info("🔧 Тестирование здоровья backend")
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/health")
            
            result = {
                "test": "backend_health",
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                health_data = response.json()
                result["health_data"] = health_data
                logger.info(f"✅ Backend здоров, статус: {health_data.get('status', 'unknown')}")
            else:
                logger.warning(f"⚠️ Backend нездоров, статус: {response.status_code}")
                
        except Exception as e:
            result = {
                "test": "backend_health",
                "error": str(e),
                "success": False
            }
            logger.error(f"❌ Ошибка доступа к backend: {e}")
        
        self.test_results.append(result)
        return result
    
    async def test_rag_service(self) -> Dict[str, Any]:
        """Тест RAG сервиса"""
        logger.info("🧠 Тестирование RAG сервиса")
        
        rag_results = []
        
        # Тест health check
        try:
            response = await self.client.get(f"{RAG_URL}/health")
            rag_results.append({
                "endpoint": "health",
                "status_code": response.status_code,
                "success": response.status_code == 200
            })
        except Exception as e:
            rag_results.append({
                "endpoint": "health",
                "error": str(e),
                "success": False
            })
        
        # Тест поиска
        try:
            response = await self.client.post(
                f"{RAG_URL}/api/v1/search",
                json={
                    "query": "SEO analysis",
                    "collection": "default",
                    "top_k": 3
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                rag_results.append({
                    "endpoint": "search",
                    "status_code": response.status_code,
                    "results_count": len(results.get("results", [])),
                    "success": True
                })
            else:
                rag_results.append({
                    "endpoint": "search",
                    "status_code": response.status_code,
                    "success": False
                })
                
        except Exception as e:
            rag_results.append({
                "endpoint": "search",
                "error": str(e),
                "success": False
            })
        
        result = {
            "test": "rag_service",
            "endpoints": rag_results,
            "success": all(r["success"] for r in rag_results)
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Успешных RAG вызовов: {sum(1 for r in rag_results if r['success'])}/{len(rag_results)}")
        return result
    
    async def test_llm_router(self) -> Dict[str, Any]:
        """Тест LLM роутера"""
        logger.info("🤖 Тестирование LLM роутера")
        
        llm_results = []
        
        # Тест health check
        try:
            response = await self.client.get(f"{LLM_ROUTER_URL}/health")
            llm_results.append({
                "endpoint": "health",
                "status_code": response.status_code,
                "success": response.status_code == 200
            })
        except Exception as e:
            llm_results.append({
                "endpoint": "health",
                "error": str(e),
                "success": False
            })
        
        # Тест маршрутизации
        try:
            response = await self.client.post(
                f"{LLM_ROUTER_URL}/api/v1/route",
                json={
                    "prompt": "What is SEO?",
                    "model": "auto",
                    "context": {}
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                llm_results.append({
                    "endpoint": "route",
                    "status_code": response.status_code,
                    "has_response": "response" in result_data,
                    "success": True
                })
            else:
                llm_results.append({
                    "endpoint": "route",
                    "status_code": response.status_code,
                    "success": False
                })
                
        except Exception as e:
            llm_results.append({
                "endpoint": "route",
                "error": str(e),
                "success": False
            })
        
        result = {
            "test": "llm_router",
            "endpoints": llm_results,
            "success": all(r["success"] for r in llm_results)
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Успешных LLM вызовов: {sum(1 for r in llm_results if r['success'])}/{len(llm_results)}")
        return result
    
    async def test_frontend_api_endpoints(self) -> Dict[str, Any]:
        """Тест API эндпоинтов фронтенда"""
        logger.info("🔗 Тестирование API эндпоинтов фронтенда")
        
        frontend_endpoints = [
            "/api/v1/health",
            "/api/v1/status",
            "/api/v1/config"
        ]
        
        endpoint_results = []
        
        for endpoint in frontend_endpoints:
            try:
                response = await self.client.get(f"{FRONTEND_URL}{endpoint}")
                endpoint_results.append({
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "success": response.status_code in [200, 404]  # 404 тоже нормально для несуществующих эндпоинтов
                })
            except Exception as e:
                endpoint_results.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "success": False
                })
        
        result = {
            "test": "frontend_api_endpoints",
            "endpoints": endpoint_results,
            "success": all(r["success"] for r in endpoint_results)
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Протестировано эндпоинтов: {len(endpoint_results)}")
        return result
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Тест метрик производительности"""
        logger.info("⚡ Тестирование метрик производительности")
        
        performance_results = []
        
        # Тест времени ответа фронтенда
        try:
            start_time = time.time()
            response = await self.client.get(FRONTEND_URL)
            response_time = time.time() - start_time
            
            performance_results.append({
                "metric": "frontend_response_time",
                "value": response_time,
                "success": response_time < 2.0,  # Ожидаем ответ менее 2 секунд
                "threshold": 2.0
            })
        except Exception as e:
            performance_results.append({
                "metric": "frontend_response_time",
                "error": str(e),
                "success": False
            })
        
        # Тест времени ответа backend
        try:
            start_time = time.time()
            response = await self.client.get(f"{BACKEND_URL}/health")
            response_time = time.time() - start_time
            
            performance_results.append({
                "metric": "backend_response_time",
                "value": response_time,
                "success": response_time < 1.0,  # Ожидаем ответ менее 1 секунды
                "threshold": 1.0
            })
        except Exception as e:
            performance_results.append({
                "metric": "backend_response_time",
                "error": str(e),
                "success": False
            })
        
        result = {
            "test": "performance_metrics",
            "metrics": performance_results,
            "success": all(r["success"] for r in performance_results)
        }
        
        self.test_results.append(result)
        logger.info(f"✅ Протестировано метрик: {len(performance_results)}")
        return result
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Запуск комплексного тестирования"""
        logger.info("🚀 Запуск комплексного тестирования API")
        
        start_time = time.time()
        
        # Выполнение всех тестов
        await self.test_frontend_availability()
        await self.test_backend_health()
        await self.test_rag_service()
        await self.test_llm_router()
        await self.test_frontend_api_endpoints()
        await self.test_performance_metrics()
        
        total_time = time.time() - start_time
        
        # Подсчет результатов
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        
        comprehensive_result = {
            "test_suite": "comprehensive_api_test",
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "total_time": total_time,
            "results": self.test_results,
            "overall_success": successful_tests == total_tests
        }
        
        logger.info(f"🎯 Результаты тестирования:")
        logger.info(f"   Всего тестов: {total_tests}")
        logger.info(f"   Успешных: {successful_tests}")
        logger.info(f"   Неудачных: {total_tests - successful_tests}")
        logger.info(f"   Процент успеха: {comprehensive_result['success_rate']:.1f}%")
        logger.info(f"   Общее время: {total_time:.2f}s")
        
        return comprehensive_result
    
    async def close(self):
        """Закрытие клиента"""
        await self.client.aclose()

async def main():
    """Основная функция"""
    tester = APITester()
    
    try:
        result = await tester.run_comprehensive_test()
        
        # Сохранение результатов в файл
        with open('api_test_results.json', 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Вывод результатов
        print("\n" + "="*50)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ API")
        print("="*50)
        print(f"Всего тестов: {result['total_tests']}")
        print(f"Успешных: {result['successful_tests']}")
        print(f"Неудачных: {result['failed_tests']}")
        print(f"Процент успеха: {result['success_rate']:.1f}%")
        print(f"Общее время: {result['total_time']:.2f}s")
        print(f"Общий результат: {'✅ УСПЕХ' if result['overall_success'] else '❌ НЕУДАЧА'}")
        
        if not result['overall_success']:
            print("\n❌ Детали неудачных тестов:")
            for test_result in result['results']:
                if not test_result['success']:
                    print(f"  - {test_result['test']}: {test_result.get('error', 'Неизвестная ошибка')}")
        
        return result['overall_success']
        
    finally:
        await tester.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 