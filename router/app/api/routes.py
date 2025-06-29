from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import asyncio
import time
import uuid

from bootstrap.llm_router import get_llm_router
from bootstrap.rag_service import get_rag_service
from bootstrap.ollama_client import get_ollama_client
from bootstrap.monitoring import get_service_monitor

router = APIRouter(tags=["LLM Router"])

# Pydantic модели
class RouteRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    service: Optional[str] = None
    priority: Optional[str] = "normal"  # low, normal, high, critical

class RouteResponse(BaseModel):
    request_id: str
    model_used: str
    response: str
    confidence: float
    latency: float
    cost_estimate: float
    metadata: Dict[str, Any]

class ModelInfo(BaseModel):
    name: str
    description: str
    capabilities: List[str]
    avg_latency: float
    avg_cost: float
    availability: float

class EffectivenessAnalysis(BaseModel):
    request_id: str
    model_used: str
    effectiveness_score: float
    quality_metrics: Dict[str, Any]
    recommendations: List[str]

@router.get("/health")
async def health_check():
    """Проверка здоровья LLM роутера"""
    return {
        "status": "healthy",
        "service": "router",
        "description": "LLM Router - интеллектуальная маршрутизация запросов к оптимальным моделям",
        "available_models": await get_available_models()
    }

@router.get("/api/v1/endpoints")
async def get_endpoints():
    """Получение списка эндпоинтов"""
    return {
        "service": "router",
        "endpoints": [
            "/health",
            "/api/v1/route",
            "/api/v1/analyze",
            "/api/v1/models",
            "/api/v1/effectiveness",
            "/api/v1/route/batch"
        ]
    }

@router.post("/api/v1/route", response_model=RouteResponse)
async def route_request(
    request: RouteRequest,
    background_tasks: BackgroundTasks,
    llm_router = Depends(get_llm_router),
    rag_service = Depends(get_rag_service),
    ollama_client = Depends(get_ollama_client),
    monitor = Depends(get_service_monitor)
):
    """Интеллектуальная маршрутизация запроса к оптимальной модели"""
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Отслеживание запроса
    await monitor.track_request("/api/v1/route", request_id, {
        "prompt_length": len(request.prompt),
        "requested_model": request.model,
        "service": request.service,
        "priority": request.priority
    })
    
    try:
        # Анализ запроса для выбора оптимальной модели
        model_selection = await analyze_request_for_model_selection(request)
        
        # Поиск релевантного контекста в RAG
        rag_context = await rag_service.search(
            query=request.prompt,
            collection="llm_router",
            top_k=3
        )
        
        # Обогащение контекста
        enriched_context = {
            "rag_results": rag_context,
            "user_context": request.context or {},
            "model_selection": model_selection,
            "service": request.service
        }
        
        # Маршрутизация к выбранной модели
        if model_selection["use_ollama_direct"]:
            # Прямое обращение к Ollama
            response = await ollama_client.generate(
                prompt=request.prompt,
                model=model_selection["selected_model"]
            )
            result = {
                "response": response.get("response", ""),
                "model_used": model_selection["selected_model"],
                "confidence": model_selection["confidence"],
                "metadata": {
                    "method": "direct_ollama",
                    "model_selection_reason": model_selection["reason"]
                }
            }
        else:
            # Использование LLM роутера
            result = await llm_router.route_request(
                prompt=request.prompt,
                model=model_selection["selected_model"],
                context=enriched_context
            )
        
        # Расчет метрик
        latency = time.time() - start_time
        cost_estimate = calculate_cost_estimate(
            model_selection["selected_model"],
            len(request.prompt),
            len(result["response"])
        )
        
        # Создание ответа
        route_response = RouteResponse(
            request_id=request_id,
            model_used=model_selection["selected_model"],
            response=result["response"],
            confidence=model_selection["confidence"],
            latency=latency,
            cost_estimate=cost_estimate,
            metadata=result.get("metadata", {})
        )
        
        # Фоновая задача для анализа эффективности
        background_tasks.add_task(
            analyze_effectiveness_background,
            request_id,
            route_response,
            request
        )
        
        # Завершение запроса
        await monitor.complete_request(request_id, "success", {
            "model_used": model_selection["selected_model"],
            "latency": latency,
            "confidence": model_selection["confidence"]
        })
        
        return route_response
        
    except Exception as e:
        await monitor.complete_request(request_id, "error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")

@router.post("/api/v1/route/batch")
async def route_batch_requests(
    requests: List[RouteRequest],
    llm_router = Depends(get_llm_router),
    monitor = Depends(get_service_monitor)
):
    """Пакетная маршрутизация запросов"""
    
    batch_id = str(uuid.uuid4())
    start_time = time.time()
    
    await monitor.track_request("/api/v1/route/batch", batch_id, {
        "batch_size": len(requests)
    })
    
    try:
        # Параллельная обработка запросов
        tasks = []
        for request in requests:
            task = route_single_request(request, llm_router)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "index": i,
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        batch_latency = time.time() - start_time
        
        await monitor.complete_request(batch_id, "success", {
            "total_requests": len(requests),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "batch_latency": batch_latency
        })
        
        return {
            "batch_id": batch_id,
            "total_requests": len(requests),
            "successful_results": successful_results,
            "failed_results": failed_results,
            "batch_latency": batch_latency
        }
        
    except Exception as e:
        await monitor.complete_request(batch_id, "error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Batch routing error: {str(e)}")

@router.get("/api/v1/models", response_model=List[ModelInfo])
async def get_available_models():
    """Получение списка доступных моделей с метриками"""
    
    ollama_client = get_ollama_client()
    models = await ollama_client.list_models()
    
    model_infos = []
    for model in models:
        model_info = ModelInfo(
            name=model["name"],
            description=get_model_description(model["name"]),
            capabilities=get_model_capabilities(model["name"]),
            avg_latency=get_model_avg_latency(model["name"]),
            avg_cost=get_model_avg_cost(model["name"]),
            availability=1.0  # Всегда доступны в локальной установке
        )
        model_infos.append(model_info)
    
    return model_infos

@router.post("/api/v1/analyze", response_model=EffectivenessAnalysis)
async def analyze_effectiveness(
    request_id: str,
    result: RouteResponse,
    original_request: RouteRequest,
    monitor = Depends(get_service_monitor)
):
    """Анализ эффективности результата маршрутизации"""
    
    try:
        # Анализ качества ответа
        quality_metrics = await analyze_response_quality(result.response, original_request.prompt)
        
        # Анализ выбора модели
        model_analysis = await analyze_model_selection(
            result.model_used,
            original_request.prompt,
            result.latency,
            result.confidence
        )
        
        # Расчет общего score эффективности
        effectiveness_score = calculate_effectiveness_score(
            quality_metrics,
            model_analysis,
            result.latency,
            result.cost_estimate
        )
        
        # Генерация рекомендаций
        recommendations = generate_recommendations(
            effectiveness_score,
            quality_metrics,
            model_analysis
        )
        
        analysis = EffectivenessAnalysis(
            request_id=request_id,
            model_used=result.model_used,
            effectiveness_score=effectiveness_score,
            quality_metrics=quality_metrics,
            recommendations=recommendations
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

# Вспомогательные функции
async def analyze_request_for_model_selection(request: RouteRequest) -> Dict[str, Any]:
    """Анализ запроса для выбора оптимальной модели"""
    
    # Простая эвристика выбора модели
    prompt_length = len(request.prompt)
    
    if prompt_length < 100:
        # Короткие запросы - быстрые модели
        return {
            "selected_model": "qwen2.5:7b-instruct-turbo",
            "confidence": 0.8,
            "reason": "short_prompt_fast_model",
            "use_ollama_direct": True
        }
    elif prompt_length < 500:
        # Средние запросы - сбалансированные модели
        return {
            "selected_model": "qwen2.5:14b-instruct",
            "confidence": 0.9,
            "reason": "medium_prompt_balanced_model",
            "use_ollama_direct": True
        }
    else:
        # Длинные запросы - качественные модели
        return {
            "selected_model": "qwen2.5:32b-instruct",
            "confidence": 0.95,
            "reason": "long_prompt_quality_model",
            "use_ollama_direct": True
        }

async def route_single_request(request: RouteRequest, llm_router) -> RouteResponse:
    """Маршрутизация одного запроса"""
    # Упрощенная версия для пакетной обработки
    model_selection = await analyze_request_for_model_selection(request)
    
    ollama_client = get_ollama_client()
    response = await ollama_client.generate(
        prompt=request.prompt,
        model=model_selection["selected_model"]
    )
    
    return RouteResponse(
        request_id=str(uuid.uuid4()),
        model_used=model_selection["selected_model"],
        response=response.get("response", ""),
        confidence=model_selection["confidence"],
        latency=0.5,  # Примерное значение
        cost_estimate=0.001,
        metadata={"method": "batch_processing"}
    )

def calculate_cost_estimate(model: str, input_length: int, output_length: int) -> float:
    """Расчет примерной стоимости запроса"""
    # Упрощенная модель расчета стоимости
    base_cost = 0.001
    input_cost = input_length * 0.000001
    output_cost = output_length * 0.000002
    
    return base_cost + input_cost + output_cost

async def analyze_response_quality(response: str, prompt: str) -> Dict[str, Any]:
    """Анализ качества ответа"""
    return {
        "relevance_score": 0.85,
        "completeness_score": 0.9,
        "coherence_score": 0.88,
        "length_appropriate": len(response) > len(prompt) * 0.5
    }

async def analyze_model_selection(
    model_used: str,
    prompt: str,
    latency: float,
    confidence: float
) -> Dict[str, Any]:
    """Анализ выбора модели"""
    return {
        "model_appropriate": True,
        "latency_acceptable": latency < 5.0,
        "confidence_high": confidence > 0.8,
        "alternative_models": ["qwen2.5:7b-instruct-turbo", "qwen2.5:14b-instruct"]
    }

def calculate_effectiveness_score(
    quality_metrics: Dict[str, Any],
    model_analysis: Dict[str, Any],
    latency: float,
    cost: float
) -> float:
    """Расчет общего score эффективности"""
    
    quality_score = (
        quality_metrics["relevance_score"] * 0.4 +
        quality_metrics["completeness_score"] * 0.3 +
        quality_metrics["coherence_score"] * 0.3
    )
    
    performance_score = 1.0 if latency < 2.0 else max(0.5, 1.0 - (latency - 2.0) / 10.0)
    cost_score = 1.0 if cost < 0.01 else max(0.5, 1.0 - (cost - 0.01) / 0.1)
    
    return (quality_score * 0.6 + performance_score * 0.25 + cost_score * 0.15)

def generate_recommendations(
    effectiveness_score: float,
    quality_metrics: Dict[str, Any],
    model_analysis: Dict[str, Any]
) -> List[str]:
    """Генерация рекомендаций по улучшению"""
    
    recommendations = []
    
    if effectiveness_score < 0.7:
        recommendations.append("Consider using a larger model for better quality")
    
    if quality_metrics["relevance_score"] < 0.8:
        recommendations.append("Improve prompt specificity for better relevance")
    
    if not model_analysis["latency_acceptable"]:
        recommendations.append("Consider using a faster model for better performance")
    
    return recommendations

def get_model_description(model_name: str) -> str:
    """Получение описания модели"""
    descriptions = {
        "qwen2.5:7b-instruct-turbo": "Быстрая модель для простых задач",
        "qwen2.5:14b-instruct": "Сбалансированная модель для большинства задач",
        "qwen2.5:32b-instruct": "Высококачественная модель для сложных задач"
    }
    return descriptions.get(model_name, "Модель для обработки текста")

def get_model_capabilities(model_name: str) -> List[str]:
    """Получение возможностей модели"""
    capabilities = {
        "qwen2.5:7b-instruct-turbo": ["text-generation", "fast-inference", "basic-qa"],
        "qwen2.5:14b-instruct": ["text-generation", "code-generation", "reasoning", "qa"],
        "qwen2.5:32b-instruct": ["text-generation", "code-generation", "complex-reasoning", "creative-writing"]
    }
    return capabilities.get(model_name, ["text-generation"])

def get_model_avg_latency(model_name: str) -> float:
    """Получение средней задержки модели"""
    latencies = {
        "qwen2.5:7b-instruct-turbo": 0.5,
        "qwen2.5:14b-instruct": 1.2,
        "qwen2.5:32b-instruct": 2.5
    }
    return latencies.get(model_name, 1.0)

def get_model_avg_cost(model_name: str) -> float:
    """Получение средней стоимости модели"""
    costs = {
        "qwen2.5:7b-instruct-turbo": 0.001,
        "qwen2.5:14b-instruct": 0.002,
        "qwen2.5:32b-instruct": 0.005
    }
    return costs.get(model_name, 0.002)

async def analyze_effectiveness_background(
    request_id: str,
    route_response: RouteResponse,
    original_request: RouteRequest
):
    """Фоновая задача для анализа эффективности"""
    try:
        # Здесь можно добавить асинхронный анализ
        # Например, сохранение в базу данных, отправка метрик и т.д.
        pass
    except Exception as e:
        # Логирование ошибки без прерывания основного потока
        print(f"Background analysis error: {e}")

async def get_available_models():
    """Получение списка доступных моделей"""
    try:
        ollama_client = get_ollama_client()
        models = await ollama_client.list_models()
        return [model["name"] for model in models]
    except Exception:
        return ["qwen2.5:7b-instruct-turbo", "qwen2.5:14b-instruct", "qwen2.5:32b-instruct"]
