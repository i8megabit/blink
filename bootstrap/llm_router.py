"""
🧠 Интеграция с LLM роутером для всех микросервисов
"""

from typing import Optional, Dict, Any
import httpx
import structlog

from .config import get_settings

logger = structlog.get_logger()

# Глобальный экземпляр LLM роутера
_llm_router: Optional['LLMRouter'] = None

class LLMRouter:
    """Нативная интеграция с LLM роутером"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.LLM_ROUTER_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("LLM Router initialized", base_url=self.base_url)
    
    async def route_request(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Маршрутизация запроса к оптимальной модели"""
        
        try:
            payload = {
                "prompt": prompt,
                "model": model or "auto",
                "context": context or {},
                "service": self.settings.SERVICE_NAME
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/route",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "Request routed successfully",
                model=result.get("model"),
                service=self.settings.SERVICE_NAME
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "LLM routing error",
                error=str(e),
                prompt=prompt[:100] + "..." if len(prompt) > 100 else prompt
            )
            raise
    
    async def analyze_effectiveness(
        self, 
        request_id: str, 
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Анализ эффективности результата"""
        
        try:
            payload = {
                "request_id": request_id,
                "result": result,
                "service": self.settings.SERVICE_NAME
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/analyze",
                json=payload
            )
            
            response.raise_for_status()
            analysis = response.json()
            
            logger.info(
                "Effectiveness analyzed",
                request_id=request_id,
                score=analysis.get("effectiveness_score")
            )
            
            return analysis
            
        except Exception as e:
            logger.error(
                "Effectiveness analysis error",
                error=str(e),
                request_id=request_id
            )
            raise
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Получение списка доступных моделей"""
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/models")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error("Failed to get available models", error=str(e))
            raise
    
    async def close(self):
        """Закрытие соединения"""
        await self.client.aclose()
        logger.info("LLM Router connection closed")

def get_llm_router() -> LLMRouter:
    """Получение глобального экземпляра LLM роутера"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router

async def close_llm_router():
    """Закрытие LLM роутера"""
    global _llm_router
    if _llm_router:
        await _llm_router.close()
        _llm_router = None 