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
        self.client = httpx.AsyncClient(timeout=120.0)  # Увеличиваем timeout для больших моделей
        
        # Определение архитектуры
        self.is_apple_silicon = platform.machine() == 'arm64' and platform.system() == 'Darwin'
        self.available_ram = psutil.virtual_memory().total / (1024**3)  # GB
        
        # Оптимизированные модели для M4
        self.m4_optimized_models = {
            "qwen2.5:7b-instruct-turbo": ModelSpec(
                name="qwen2.5:7b-instruct-turbo",
                size_gb=4.2,
                recommended_ram_gb=8.0,
                metal_compatible=True,
                quantization="q4_K_M",
                max_tokens=8192
            ),
            "qwen2.5:14b-instruct": ModelSpec(
                name="qwen2.5:14b-instruct", 
                size_gb=8.4,
                recommended_ram_gb=12.0,
                metal_compatible=True,
                quantization="q4_K_M",
                max_tokens=16384
            ),
            "llama3.1:8b-instruct": ModelSpec(
                name="llama3.1:8b-instruct",
                size_gb=4.8,
                recommended_ram_gb=8.0,
                metal_compatible=True,
                quantization="q4_K_M",
                max_tokens=8192
            )
        }
        
        logger.info(
            "Ollama client initialized for M4",
            base_url=self.base_url,
            is_apple_silicon=self.is_apple_silicon,
            available_ram_gb=round(self.available_ram, 1)
        )
    
    async def get_optimal_model(self, task_type: str = "general") -> str:
        """Выбор оптимальной модели для M4"""
        
        if self.available_ram < 8:
            logger.warning("Low RAM detected, using minimal model")
            return "qwen2.5:7b-instruct-turbo"
        
        if task_type == "coding":
            return "qwen2.5:7b-instruct-turbo"  # Лучше для кода
        elif task_type == "analysis":
            return "qwen2.5:14b-instruct"  # Лучше для анализа
        else:
            return "qwen2.5:7b-instruct-turbo"  # Универсальная
    
    async def generate(
        self, 
        prompt: str, 
        model: str = "auto",
        task_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """Генерация ответа через Ollama с оптимизацией для M4"""
        
        # Автоматический выбор модели
        if model == "auto":
            model = await self.get_optimal_model(task_type)
        
        # Проверка доступности модели
        available_models = await self.list_models()
        model_names = [m["name"] for m in available_models]
        
        if model not in model_names:
            logger.warning(f"Model {model} not found, pulling...")
            await self.pull_model(model)
        
        try:
            # Оптимизированные параметры для M4
            m4_params = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_gpu": 1 if self.is_apple_silicon else 0,
                    "num_thread": 8,  # Оптимально для M4
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "seed": 42
                }
            }
            
            # Добавляем пользовательские параметры
            m4_params.update(kwargs)
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=m4_params
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "Ollama generation completed (M4 optimized)",
                model=model,
                response_length=len(result.get("response", "")),
                generation_time=result.get("total_duration", 0),
                tokens_per_second=result.get("eval_count", 0) / max(result.get("eval_duration", 1), 1)
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
    
    async def generate_stream(
        self,
        prompt: str,
        model: str = "auto",
        task_type: str = "general",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Стриминг генерации с оптимизацией для M4"""
        
        if model == "auto":
            model = await self.get_optimal_model(task_type)
        
        try:
            m4_params = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "num_gpu": 1 if self.is_apple_silicon else 0,
                    "num_thread": 8,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "seed": 42
                }
            }
            m4_params.update(kwargs)
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=m4_params
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = httpx.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except Exception:
                            continue
                            
        except Exception as e:
            logger.error("Ollama streaming error", error=str(e), model=model)
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            result = response.json()
            models = result.get("models", [])
            
            # Добавляем информацию об оптимизации для M4
            for model in models:
                model_name = model.get("name", "")
                if model_name in self.m4_optimized_models:
                    spec = self.m4_optimized_models[model_name]
                    model["m4_optimized"] = True
                    model["recommended_ram_gb"] = spec.recommended_ram_gb
                    model["metal_compatible"] = spec.metal_compatible
                else:
                    model["m4_optimized"] = False
            
            logger.info("Ollama models retrieved", count=len(models))
            
            return models
            
        except Exception as e:
            logger.error("Failed to get Ollama models", error=str(e))
            raise
    
    async def pull_model(self, model: str) -> Dict[str, Any]:
        """Загрузка модели с оптимизацией для M4"""
        
        try:
            # Проверяем, есть ли оптимизированная версия
            if model in self.m4_optimized_models:
                spec = self.m4_optimized_models[model]
                logger.info(f"Pulling M4-optimized model: {model}")
                
                # Проверяем доступную память
                if self.available_ram < spec.recommended_ram_gb:
                    logger.warning(
                        f"Insufficient RAM for {model}. "
                        f"Required: {spec.recommended_ram_gb}GB, "
                        f"Available: {self.available_ram:.1f}GB"
                    )
            
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
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Получение информации о системе для оптимизации"""
        
        try:
            response = await self.client.get(f"{self.base_url}/api/version")
            response.raise_for_status()
            
            version_info = response.json()
            
            system_info = {
                "ollama_version": version_info.get("version"),
                "is_apple_silicon": self.is_apple_silicon,
                "available_ram_gb": round(self.available_ram, 1),
                "cpu_count": psutil.cpu_count(),
                "platform": platform.platform(),
                "architecture": platform.machine()
            }
            
            logger.info("System info retrieved", **system_info)
            
            return system_info
            
        except Exception as e:
            logger.error("Failed to get system info", error=str(e))
            raise
    
    async def optimize_for_m4(self) -> Dict[str, Any]:
        """Оптимизация настроек для MacBook M4"""
        
        optimizations = {
            "metal_acceleration": self.is_apple_silicon,
            "recommended_models": list(self.m4_optimized_models.keys()),
            "memory_management": {
                "available_ram_gb": round(self.available_ram, 1),
                "recommended_max_concurrent": 2 if self.available_ram >= 12 else 1,
                "swap_recommendation": self.available_ram < 8
            },
            "performance_tips": [
                "Use q4_K_M quantization for best speed/size ratio",
                "Enable Metal GPU acceleration for faster inference",
                "Limit concurrent model loading based on available RAM",
                "Use streaming for long responses to reduce memory usage"
            ]
        }
        
        logger.info("M4 optimizations applied", optimizations=optimizations)
        
        return optimizations
    
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