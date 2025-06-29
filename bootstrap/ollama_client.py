"""
🤖 Интеграция с Ollama для всех микросервисов
"""

from typing import Dict, Any, Optional, List
import httpx
import structlog

from .config import get_settings

logger = structlog.get_logger()

# Глобальный экземпляр Ollama клиента
_ollama_client: Optional['OllamaClient'] = None

class OllamaClient:
    """Нативная интеграция с Ollama"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.OLLAMA_URL
        self.client = httpx.AsyncClient(timeout=60.0)
        
        logger.info("Ollama client initialized", base_url=self.base_url)
    
    async def generate(
        self, 
        prompt: str, 
        model: str = "qwen2.5:7b-instruct-turbo",
        **kwargs
    ) -> Dict[str, Any]:
        """Генерация ответа через Ollama"""
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "Ollama generation completed",
                model=model,
                response_length=len(result.get("response", ""))
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Ollama generation error",
                error=str(e),
                model=model,
                prompt=prompt[:100] + "..." if len(prompt) > 100 else prompt
            )
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            result = response.json()
            
            logger.info("Ollama models retrieved", count=len(result.get("models", [])))
            
            return result.get("models", [])
            
        except Exception as e:
            logger.error("Failed to get Ollama models", error=str(e))
            raise
    
    async def pull_model(self, model: str) -> Dict[str, Any]:
        """Загрузка модели"""
        
        try:
            payload = {"name": model}
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("Ollama model pulled", model=model)
            
            return result
            
        except Exception as e:
            logger.error("Failed to pull Ollama model", error=str(e), model=model)
            raise
    
    async def delete_model(self, model: str) -> Dict[str, Any]:
        """Удаление модели"""
        
        try:
            payload = {"name": model}
            response = await self.client.delete(
                f"{self.base_url}/api/delete",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("Ollama model deleted", model=model)
            
            return result
            
        except Exception as e:
            logger.error("Failed to delete Ollama model", error=str(e), model=model)
            raise
    
    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """Получение информации о модели"""
        
        try:
            payload = {"name": model}
            response = await self.client.post(
                f"{self.base_url}/api/show",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("Ollama model info retrieved", model=model)
            
            return result
            
        except Exception as e:
            logger.error("Failed to get Ollama model info", error=str(e), model=model)
            raise
    
    async def close(self):
        """Закрытие соединения"""
        await self.client.aclose()
        logger.info("Ollama client connection closed")

def get_ollama_client() -> OllamaClient:
    """Получение глобального экземпляра Ollama клиента"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client

async def close_ollama_client():
    """Закрытие Ollama клиента"""
    global _ollama_client
    if _ollama_client:
        await _ollama_client.close()
        _ollama_client = None 