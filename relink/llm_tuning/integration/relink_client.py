"""
🔗 Клиент для интеграции LLM Tuning с основным проектом reLink
Обеспечивает seamless интеграцию микросервиса с основным приложением
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import json
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class LLMTuningConfig:
    """Конфигурация для подключения к LLM Tuning микросервису"""
    base_url: str = "http://localhost:8001"
    api_key: str = "apple-silicon-api-key-2024"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class LLMTuningClient:
    """Клиент для работы с LLM Tuning микросервисом"""
    
    def __init__(self, config: LLMTuningConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "reLink-LLM-Tuning-Client/1.0"
        }
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            timeout=timeout,
            headers=self._headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Выполнение HTTP запроса с повторными попытками"""
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.request(method, endpoint, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise ValueError(f"Endpoint not found: {endpoint}")
                    elif response.status == 401:
                        raise ValueError("Unauthorized - check API key")
                    elif response.status == 503:
                        raise ValueError("Service unavailable - LLM Tuning service is down")
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья LLM Tuning сервиса"""
        return await self._make_request("GET", "/health")
    
    async def get_models(self, provider: str = None, status: str = None) -> List[Dict]:
        """Получение списка доступных моделей"""
        params = {}
        if provider:
            params["provider"] = provider
        if status:
            params["status"] = status
        
        endpoint = "/api/v1/models"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{query_string}"
        
        return await self._make_request("GET", endpoint)
    
    async def route_request(self, prompt: str, context: str = None, 
                          model: str = None, **kwargs) -> Dict[str, Any]:
        """Маршрутизация запроса к оптимальной модели"""
        data = {
            "prompt": prompt,
            "context": context,
            "model": model,
            **kwargs
        }
        
        return await self._make_request("POST", "/api/v1/route", data)
    
    async def rag_query(self, query: str, model: str = None, 
                       top_k: int = 5, include_sources: bool = True) -> Dict[str, Any]:
        """Выполнение RAG запроса"""
        data = {
            "query": query,
            "model": model,
            "top_k": top_k,
            "include_sources": include_sources
        }
        
        return await self._make_request("POST", "/api/v1/rag/query", data)
    
    async def add_document(self, title: str, content: str, source: str = None,
                          document_type: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """Добавление документа в RAG систему"""
        data = {
            "title": title,
            "content": content,
            "source": source,
            "document_type": document_type,
            "tags": tags or []
        }
        
        return await self._make_request("POST", "/api/v1/rag/documents", data)
    
    async def create_tuning_session(self, model_id: int, training_data: List[Dict],
                                  strategy: str = "adaptive") -> Dict[str, Any]:
        """Создание сессии тюнинга модели"""
        data = {
            "model_id": model_id,
            "training_data": training_data,
            "strategy": strategy
        }
        
        return await self._make_request("POST", "/api/v1/tuning/sessions", data)
    
    async def get_tuning_sessions(self, model_id: int = None, status: str = None) -> List[Dict]:
        """Получение списка сессий тюнинга"""
        params = {}
        if model_id:
            params["model_id"] = model_id
        if status:
            params["status"] = status
        
        endpoint = "/api/v1/tuning/sessions"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{query_string}"
        
        return await self._make_request("GET", endpoint)
    
    async def optimize_model(self, model_id: int) -> Dict[str, Any]:
        """Оптимизация модели"""
        return await self._make_request("POST", f"/api/v1/tuning/optimize?model_id={model_id}")
    
    async def get_metrics(self, model_id: int = None, time_range: str = "24h") -> Dict[str, Any]:
        """Получение метрик производительности"""
        params = {"time_range": time_range}
        if model_id:
            params["model_id"] = model_id
        
        endpoint = "/api/v1/metrics/summary"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint += f"?{query_string}"
        
        return await self._make_request("GET", endpoint)
    
    async def record_metrics(self, model_id: int, response_time: float, 
                           token_count: int, quality_score: float = None) -> Dict[str, Any]:
        """Запись метрик производительности"""
        data = {
            "model_id": model_id,
            "response_time": response_time,
            "token_count": token_count,
            "quality_score": quality_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self._make_request("POST", "/api/v1/metrics", data)


class ReLinkIntegration:
    """Интеграция LLM Tuning с основным проектом reLink"""
    
    def __init__(self, llm_client: LLMTuningClient):
        self.llm_client = llm_client
        self._cache: Dict[str, Any] = {}
    
    async def analyze_seo_content(self, content: str, domain: str = None) -> Dict[str, Any]:
        """Анализ SEO контента с помощью LLM Tuning"""
        try:
            # Формирование промпта для SEO анализа
            prompt = f"""
            Проанализируй следующий контент с точки зрения SEO:
            
            Контент: {content}
            Домен: {domain or 'не указан'}
            
            Предоставь анализ по следующим пунктам:
            1. Ключевые слова и их плотность
            2. Структура заголовков (H1, H2, H3)
            3. Мета-описания и title
            4. Внутренние и внешние ссылки
            5. Оптимизация изображений
            6. Скорость загрузки
            7. Мобильная адаптация
            8. Общие рекомендации по улучшению
            """
            
            # Выполнение RAG запроса
            result = await self.llm_client.rag_query(
                query=prompt,
                model="qwen2.5:7b-turbo",
                top_k=5,
                include_sources=True
            )
            
            return {
                "analysis": result.get("answer", ""),
                "sources": result.get("sources", []),
                "processing_time": result.get("processing_time", 0),
                "domain": domain,
                "content_length": len(content)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing SEO content: {e}")
            return {
                "error": str(e),
                "analysis": "Анализ недоступен",
                "sources": [],
                "processing_time": 0
            }
    
    async def generate_seo_recommendations(self, website_data: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация SEO рекомендаций на основе данных сайта"""
        try:
            # Формирование контекста из данных сайта
            context = f"""
            Данные сайта:
            - URL: {website_data.get('url', 'не указан')}
            - Тип сайта: {website_data.get('type', 'не указан')}
            - Целевая аудитория: {website_data.get('audience', 'не указана')}
            - Основные ключевые слова: {website_data.get('keywords', [])}
            - Текущие проблемы: {website_data.get('issues', [])}
            """
            
            prompt = f"""
            На основе следующих данных сайта, сгенерируй подробные SEO рекомендации:
            
            {context}
            
            Предоставь рекомендации по:
            1. Технической оптимизации
            2. Контентной стратегии
            3. Ключевым словам
            4. Внутренней перелинковке
            5. Внешним ссылкам
            6. Локальному SEO (если применимо)
            7. Приоритетам внедрения
            """
            
            # Маршрутизация запроса к оптимальной модели
            result = await self.llm_client.route_request(
                prompt=prompt,
                context=context,
                model="qwen2.5:7b-turbo"
            )
            
            return {
                "recommendations": result.get("response", ""),
                "model_used": result.get("model", ""),
                "confidence": result.get("confidence", 0),
                "processing_time": result.get("processing_time", 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating SEO recommendations: {e}")
            return {
                "error": str(e),
                "recommendations": "Рекомендации недоступны",
                "model_used": "",
                "confidence": 0,
                "processing_time": 0
            }
    
    async def optimize_content(self, content: str, target_keywords: List[str]) -> Dict[str, Any]:
        """Оптимизация контента под целевые ключевые слова"""
        try:
            prompt = f"""
            Оптимизируй следующий контент под целевые ключевые слова:
            
            Контент: {content}
            Целевые ключевые слова: {', '.join(target_keywords)}
            
            Предоставь:
            1. Оптимизированную версию контента
            2. Рекомендации по структуре
            3. Дополнительные ключевые слова
            4. Мета-описания
            5. Заголовки для социальных сетей
            """
            
            result = await self.llm_client.rag_query(
                query=prompt,
                model="qwen2.5:7b-turbo",
                top_k=3,
                include_sources=True
            )
            
            return {
                "optimized_content": result.get("answer", ""),
                "sources": result.get("sources", []),
                "processing_time": result.get("processing_time", 0),
                "original_length": len(content),
                "target_keywords": target_keywords
            }
            
        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            return {
                "error": str(e),
                "optimized_content": content,
                "sources": [],
                "processing_time": 0
            }
    
    async def add_seo_knowledge_base(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """Добавление SEO базы знаний в RAG систему"""
        try:
            results = []
            for doc in documents:
                result = await self.llm_client.add_document(
                    title=doc.get("title", "SEO Document"),
                    content=doc.get("content", ""),
                    source=doc.get("source", "reLink"),
                    document_type="seo_knowledge",
                    tags=doc.get("tags", ["seo", "optimization"])
                )
                results.append(result)
            
            return {
                "documents_added": len(results),
                "results": results,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error adding SEO knowledge base: {e}")
            return {
                "error": str(e),
                "documents_added": 0,
                "results": [],
                "status": "error"
            }
    
    async def get_performance_metrics(self, time_range: str = "7d") -> Dict[str, Any]:
        """Получение метрик производительности LLM Tuning"""
        try:
            metrics = await self.llm_client.get_metrics(time_range=time_range)
            
            return {
                "metrics": metrics,
                "time_range": time_range,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {
                "error": str(e),
                "metrics": {},
                "time_range": time_range,
                "timestamp": datetime.utcnow().isoformat()
            }


# Декораторы для интеграции
def with_llm_tuning(config: LLMTuningConfig):
    """Декоратор для автоматической интеграции с LLM Tuning"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with LLMTuningClient(config) as client:
                integration = ReLinkIntegration(client)
                kwargs['llm_integration'] = integration
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def cache_llm_results(ttl: int = 3600):
    """Декоратор для кэширования результатов LLM"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Простая реализация кэша - в продакшене использовать Redis
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Проверка кэша
            if hasattr(wrapper, '_cache') and cache_key in wrapper._cache:
                cache_entry = wrapper._cache[cache_key]
                if datetime.utcnow().timestamp() - cache_entry['timestamp'] < ttl:
                    return cache_entry['result']
            
            # Выполнение функции
            result = await func(*args, **kwargs)
            
            # Сохранение в кэш
            if not hasattr(wrapper, '_cache'):
                wrapper._cache = {}
            
            wrapper._cache[cache_key] = {
                'result': result,
                'timestamp': datetime.utcnow().timestamp()
            }
            
            return result
        return wrapper
    return decorator


# Примеры использования
async def example_usage():
    """Пример использования интеграции"""
    config = LLMTuningConfig(
        base_url="http://localhost:8001",
        api_key="your-api-key"
    )
    
    async with LLMTuningClient(config) as client:
        integration = ReLinkIntegration(client)
        
        # Анализ SEO контента
        content = "Ваш SEO контент здесь..."
        analysis = await integration.analyze_seo_content(content, "example.com")
        print("SEO Analysis:", analysis)
        
        # Генерация рекомендаций
        website_data = {
            "url": "https://example.com",
            "type": "e-commerce",
            "audience": "B2C",
            "keywords": ["seo", "optimization"],
            "issues": ["slow loading", "poor mobile"]
        }
        recommendations = await integration.generate_seo_recommendations(website_data)
        print("Recommendations:", recommendations)


if __name__ == "__main__":
    asyncio.run(example_usage()) 