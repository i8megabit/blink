"""
🤖 Интеграция с Ollama для всех микросервисов
Оптимизировано для MacBook M4 с Metal GPU acceleration
"""

from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx
import structlog
import platform
import psutil
import asyncio
from dataclasses import dataclass

from .config import get_settings

logger = structlog.get_logger()

@dataclass
class ModelSpec:
    """Спецификация модели для оптимизации"""
    name: str
    size_gb: float
    recommended_ram_gb: float
    metal_compatible: bool
    quantization: str
    max_tokens: int

# Глобальный экземпляр Ollama клиента
_ollama_client: Optional['OllamaClient'] = None

class OllamaClient:
    """Нативная интеграция с Ollama с оптимизацией для M4"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.OLLAMA_URL
        self.client = httpx.AsyncClient(timeout=self.settings.OLLAMA_TIMEOUT)
        self.is_m4_mac = self._detect_m4_mac()
        self.system_memory = self._get_system_memory()
        
        # Оптимизация для M4
        if self.is_m4_mac:
            self._optimize_for_m4()
        
        logger.info("Ollama Client initialized", 
                   is_m4_mac=self.is_m4_mac,
                   system_memory_gb=self.system_memory)
    
    def _detect_m4_mac(self) -> bool:
        """Определение MacBook M4"""
        try:
            if platform.system() == "Darwin" and platform.machine() == "arm64":
                # Проверяем наличие M4 специфичных возможностей
                import subprocess
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True)
                return "M4" in result.stdout
            return False
        except:
            return False
    
    def _get_system_memory(self) -> float:
        """Получение объема системной памяти в GB"""
        try:
            return psutil.virtual_memory().total / (1024**3)
        except:
            return 16.0  # Предполагаем 16GB для M4
    
    def _optimize_for_m4(self):
        """Оптимизация для MacBook M4"""
        # Настройки для Metal GPU acceleration
        self.metal_settings = {
            "num_gpu": 1,
            "num_thread": 8,  # M4 имеет 8-10 ядер
            "num_ctx": 4096,  # Оптимальный контекст для M4
            "gpu_layers": 35,  # Используем GPU для большей части модели
            "main_gpu": 0,
            "tensor_split": [0.8, 0.2],  # 80% на GPU, 20% на CPU
            "rope_freq_base": 10000,
            "rope_freq_scale": 0.5
        }
        
        # Управление памятью для M4
        if self.system_memory <= 16:
            self.memory_settings = {
                "max_memory": int(self.system_memory * 0.7 * 1024),  # 70% от RAM
                "batch_size": 512,
                "context_size": 2048
            }
        else:
            self.memory_settings = {
                "max_memory": int(self.system_memory * 0.8 * 1024),  # 80% от RAM
                "batch_size": 1024,
                "context_size": 4096
            }
    
    async def generate(
        self, 
        prompt: str, 
        model: str = "qwen2.5:7b-instruct-turbo",
        **kwargs
    ) -> Dict[str, Any]:
        """Генерация ответа с оптимизацией для M4"""
        
        # Оптимизация параметров для M4
        if self.is_m4_mac:
            kwargs.update(self.metal_settings)
            kwargs.update(self.memory_settings)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            result = response.json()
            
            # Логирование производительности для M4
            if self.is_m4_mac and "eval_duration" in result:
                logger.info("M4 generation completed",
                           model=model,
                           eval_duration=result["eval_duration"],
                           tokens_generated=result.get("eval_count", 0))
            
            return result
            
        except Exception as e:
            logger.error("Ollama generation failed", error=str(e), model=model)
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            models = response.json()["models"]
            
            # Анализ моделей для M4
            if self.is_m4_mac:
                for model in models:
                    model["m4_optimized"] = self._is_model_optimized_for_m4(model)
                    model["recommended_quantization"] = self._get_recommended_quantization(model)
            
            return models
            
        except Exception as e:
            logger.error("Failed to list models", error=str(e))
            return []
    
    def _is_model_optimized_for_m4(self, model: Dict[str, Any]) -> bool:
        """Проверка оптимизации модели для M4"""
        model_name = model.get("name", "").lower()
        
        # Модели, оптимизированные для M4
        m4_optimized_models = [
            "qwen2.5:7b-instruct-turbo",
            "llama3.1:8b-instruct",
            "mistral:7b-instruct",
            "codellama:7b-instruct"
        ]
        
        return any(opt_model in model_name for opt_model in m4_optimized_models)
    
    def _get_recommended_quantization(self, model: Dict[str, Any]) -> str:
        """Рекомендуемая квантизация для M4"""
        size_gb = model.get("size", 0) / (1024**3)
        
        if size_gb <= 4:
            return "Q4_K_M"  # Быстро и качественно
        elif size_gb <= 8:
            return "Q6_K"    # Баланс скорости и качества
        else:
            return "Q8_0"    # Максимальное качество
    
    async def pull_model(self, model: str) -> Dict[str, Any]:
        """Загрузка модели с оптимизацией для M4"""
        
        payload = {"name": model}
        
        # Добавляем параметры для M4
        if self.is_m4_mac:
            payload.update({
                "insecure": True,  # Для локальной разработки
                "quiet": False
            })
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json=payload
            )
            
            result = response.json()
            
            if self.is_m4_mac:
                logger.info("Model pulled for M4", 
                           model=model,
                           size_gb=result.get("size", 0) / (1024**3))
            
            return result
            
        except Exception as e:
            logger.error("Failed to pull model", error=str(e), model=model)
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья с информацией о M4"""
        
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            
            health_info = {
                "status": "healthy",
                "ollama_connected": True,
                "models_count": len(response.json().get("models", [])),
                "service": self.settings.SERVICE_NAME
            }
            
            # Добавляем информацию о M4
            if self.is_m4_mac:
                health_info.update({
                    "m4_optimized": True,
                    "system_memory_gb": self.system_memory,
                    "metal_acceleration": True,
                    "recommended_models": [
                        "qwen2.5:7b-instruct-turbo",
                        "llama3.1:8b-instruct",
                        "mistral:7b-instruct"
                    ]
                })
            
            return health_info
            
        except Exception as e:
            logger.error("Ollama health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": self.settings.SERVICE_NAME
            }

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