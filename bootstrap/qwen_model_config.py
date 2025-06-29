"""
🎯 Конфигурация модели qwen-2.5-instruct-alibaba
Детальные спецификации и оптимизация для reLink
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class QwenModelType(Enum):
    """Типы моделей Qwen"""
    QWEN_2_5_7B_INSTRUCT = "qwen2.5:7b-instruct"
    QWEN_2_5_7B_INSTRUCT_TURBO = "qwen2.5:7b-instruct-turbo"
    QWEN_2_5_14B_INSTRUCT = "qwen2.5:14b-instruct"
    QWEN_2_5_32B_INSTRUCT = "qwen2.5:32b-instruct"

@dataclass
class QwenModelSpec:
    """Спецификация модели Qwen"""
    name: str
    model_type: QwenModelType
    parameters: int  # в миллиардах
    context_length: int
    training_tokens: int  # в триллионах
    quantization_support: List[str]
    recommended_use_cases: List[str]
    performance_characteristics: Dict[str, Any]

class QwenModelConfig:
    """Конфигурация для моделей Qwen 2.5"""
    
    def __init__(self):
        self.models = {
            "qwen2.5:7b-instruct": QwenModelSpec(
                name="qwen2.5:7b-instruct",
                model_type=QwenModelType.QWEN_2_5_7B_INSTRUCT,
                parameters=7_000_000_000,
                context_length=32_768,
                training_tokens=18_000_000_000_000,  # 18T tokens
                quantization_support=["Q4_K_M", "Q6_K", "Q8_0", "F16"],
                recommended_use_cases=[
                    "general_assistant",
                    "code_generation",
                    "text_analysis",
                    "content_generation"
                ],
                performance_characteristics={
                    "inference_speed": "fast",
                    "memory_efficiency": "high",
                    "quality_score": 8.5,
                    "multilingual_support": True,
                    "code_capabilities": "excellent"
                }
            ),
            "qwen2.5:7b-instruct-turbo": QwenModelSpec(
                name="qwen2.5:7b-instruct-turbo",
                model_type=QwenModelType.QWEN_2_5_7B_INSTRUCT_TURBO,
                parameters=7_000_000_000,
                context_length=32_768,
                training_tokens=18_000_000_000_000,  # 18T tokens
                quantization_support=["Q4_K_M", "Q6_K", "Q8_0", "F16"],
                recommended_use_cases=[
                    "real_time_assistant",
                    "interactive_chat",
                    "quick_analysis",
                    "streaming_generation"
                ],
                performance_characteristics={
                    "inference_speed": "very_fast",
                    "memory_efficiency": "very_high",
                    "quality_score": 8.0,
                    "multilingual_support": True,
                    "code_capabilities": "excellent",
                    "streaming_optimized": True
                }
            ),
            "qwen2.5:14b-instruct": QwenModelSpec(
                name="qwen2.5:14b-instruct",
                model_type=QwenModelType.QWEN_2_5_14B_INSTRUCT,
                parameters=14_000_000_000,
                context_length=32_768,
                training_tokens=18_000_000_000_000,  # 18T tokens
                quantization_support=["Q4_K_M", "Q6_K", "Q8_0", "F16"],
                recommended_use_cases=[
                    "complex_analysis",
                    "detailed_generation",
                    "research_assistant",
                    "high_quality_content"
                ],
                performance_characteristics={
                    "inference_speed": "medium",
                    "memory_efficiency": "medium",
                    "quality_score": 9.0,
                    "multilingual_support": True,
                    "code_capabilities": "outstanding",
                    "reasoning_capabilities": "excellent"
                }
            )
        }
    
    def get_model_spec(self, model_name: str) -> Optional[QwenModelSpec]:
        """Получение спецификации модели"""
        return self.models.get(model_name)
    
    def get_optimal_quantization(self, model_name: str, memory_gb: float) -> str:
        """Выбор оптимальной квантизации для доступной памяти"""
        spec = self.get_model_spec(model_name)
        if not spec:
            return "Q4_K_M"
        
        # Расчет размера модели в GB
        model_size_gb = spec.parameters * 2 / (1024**3)  # F16 размер
        
        if memory_gb >= model_size_gb * 2:  # Достаточно памяти для F16
            return "F16"
        elif memory_gb >= model_size_gb * 1.5:  # Достаточно для Q8
            return "Q8_0"
        elif memory_gb >= model_size_gb * 1.2:  # Достаточно для Q6
            return "Q6_K"
        else:  # Минимальная квантизация
            return "Q4_K_M"
    
    def get_optimized_prompt_template(self, model_name: str, task_type: str) -> str:
        """Получение оптимизированного промпт-шаблона"""
        
        base_template = """<|im_start|>system
You are a helpful AI assistant specialized in {task_type}. 
Provide accurate, detailed, and professional responses.
<|im_end|>
<|im_start|>user
{user_input}
<|im_end|>
<|im_start|>assistant
"""
        
        # Специфичные шаблоны для разных задач
        task_templates = {
            "seo_analysis": """<|im_start|>system
You are an expert SEO analyst. Analyze websites and provide detailed SEO recommendations.
Focus on technical SEO, content optimization, and internal linking strategies.
<|im_end|>
<|im_start|>user
{user_input}
<|im_end|>
<|im_start|>assistant
""",
            "code_generation": """<|im_start|>system
You are an expert software developer. Write clean, efficient, and well-documented code.
Follow best practices and provide explanations for your solutions.
<|im_end|>
<|im_start|>user
{user_input}
<|im_end|>
<|im_start|>assistant
""",
            "content_generation": """<|im_start|>system
You are a professional content writer. Create engaging, informative, and SEO-optimized content.
Focus on user value, readability, and search engine optimization.
<|im_end|>
<|im_start|>user
{user_input}
<|im_end|>
<|im_start|>assistant
"""
        }
        
        return task_templates.get(task_type, base_template)
    
    def get_optimized_parameters(self, model_name: str, task_type: str) -> Dict[str, Any]:
        """Получение оптимизированных параметров генерации"""
        
        # Базовые параметры для Qwen 2.5
        base_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "seed": 42,
            "num_ctx": 4096,
            "num_thread": 8,
            "num_gpu": 1
        }
        
        # Специфичные параметры для задач
        task_params = {
            "seo_analysis": {
                "temperature": 0.3,  # Более детерминированные ответы
                "top_p": 0.8,
                "num_ctx": 8192,  # Больший контекст для анализа
            },
            "code_generation": {
                "temperature": 0.2,  # Очень детерминированные ответы
                "top_p": 0.7,
                "repeat_penalty": 1.05,
            },
            "content_generation": {
                "temperature": 0.8,  # Более креативные ответы
                "top_p": 0.95,
                "num_ctx": 6144,
            },
            "real_time_chat": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_ctx": 2048,  # Меньший контекст для скорости
            }
        }
        
        # Объединяем параметры
        optimized_params = base_params.copy()
        if task_type in task_params:
            optimized_params.update(task_params[task_type])
        
        return optimized_params
    
    def get_model_recommendations(self, use_case: str, memory_gb: float) -> List[str]:
        """Рекомендации моделей для конкретного случая использования"""
        
        recommendations = []
        
        for model_name, spec in self.models.items():
            # Проверяем подходит ли модель для задачи
            if use_case in spec.recommended_use_cases:
                # Проверяем достаточно ли памяти
                model_size_gb = spec.parameters * 2 / (1024**3)
                if memory_gb >= model_size_gb * 1.5:  # Нужен запас памяти
                    recommendations.append({
                        "model": model_name,
                        "reason": f"Optimal for {use_case}",
                        "memory_required_gb": model_size_gb,
                        "quality_score": spec.performance_characteristics["quality_score"]
                    })
        
        # Сортируем по качеству
        recommendations.sort(key=lambda x: x["quality_score"], reverse=True)
        return recommendations
    
    def get_performance_metrics(self, model_name: str) -> Dict[str, Any]:
        """Получение метрик производительности модели"""
        spec = self.get_model_spec(model_name)
        if not spec:
            return {}
        
        return {
            "model_name": spec.name,
            "parameters": spec.parameters,
            "context_length": spec.context_length,
            "training_tokens": spec.training_tokens,
            "performance": spec.performance_characteristics,
            "recommended_use_cases": spec.recommended_use_cases,
            "quantization_options": spec.quantization_support
        }

# Глобальный экземпляр конфигурации
_qwen_config = QwenModelConfig()

def get_qwen_config() -> QwenModelConfig:
    """Получение глобального экземпляра конфигурации Qwen"""
    return _qwen_config 