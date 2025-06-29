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

class CollectionVersion(BaseModel):
    version_id: str
    timestamp: float
    description: Optional[str] = None
    data_hash: Optional[str] = None

class CollectionInfo(BaseModel):
    name: str
    created_at: float
    updated_at: float
    versions: List[CollectionVersion] = []
    current_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CreateCollectionRequest(BaseModel):
    name: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class UpdateCollectionRequest(BaseModel):
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RollbackRequest(BaseModel):
    version_id: str

# --- ПРОСТОЙ ИНМЕМОРИ СЛОЙ ДЛЯ КОЛЛЕКЦИЙ ---
collections_db: Dict[str, CollectionInfo] = {}

# --- ДОБАВЛЕНО: МОДЕЛИ И ЭНДПОИНТЫ ДЛЯ FINE-TUNING ---
class FineTuneJob(BaseModel):
    job_id: str
    collection: str
    status: str  # pending, running, completed, failed, cancelled
    started_at: float
    finished_at: Optional[float] = None
    progress: float = 0.0
    logs: Optional[List[str]] = None
    error: Optional[str] = None
    model_version: Optional[str] = None

fine_tune_jobs: Dict[str, FineTuneJob] = {}

# --- ДОПОЛНИТЕЛЬНЫЕ МЕТРИКИ ДЛЯ КОЛЛЕКЦИЙ И FINE-TUNE ---
collection_metrics: Dict[str, List[Dict[str, Any]]] = {}  # {collection: [{latency, quality, timestamp}]}
fine_tune_metrics: Dict[str, Dict[str, Any]] = {}  # {job_id: {latency, quality, ...}}

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
            "/api/v1/route/batch",
            "/api/v1/collections",
            "/api/v1/collections/{name}",
            "/api/v1/collections/{name}/version",
            "/api/v1/collections/{name}/versions",
            "/api/v1/collections/{name}/rollback",
            "/api/v1/fine-tune/start",
            "/api/v1/fine-tune/{job_id}",
            "/api/v1/fine-tune/{job_id}/cancel",
            "/api/v1/collections/{name}/metrics",
            "/api/v1/fine-tune/{job_id}/metrics"
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

# --- ЭНДПОИНТЫ ДЛЯ КОЛЛЕКЦИЙ ---
@router.post("/api/v1/collections", response_model=CollectionInfo)
async def create_collection(request: CreateCollectionRequest):
    """Создать новую коллекцию"""
    if request.name in collections_db:
        raise HTTPException(status_code=400, detail="Collection already exists")
    now = time.time()
    version_id = str(uuid.uuid4())
    version = CollectionVersion(version_id=version_id, timestamp=now, description=request.description)
    info = CollectionInfo(
        name=request.name,
        created_at=now,
        updated_at=now,
        versions=[version],
        current_version=version_id,
        metadata=request.metadata or {}
    )
    collections_db[request.name] = info
    return info

@router.get("/api/v1/collections", response_model=List[CollectionInfo])
async def list_collections():
    """Список всех коллекций"""
    return list(collections_db.values())

@router.get("/api/v1/collections/{name}", response_model=CollectionInfo)
async def get_collection(name: str):
    """Получить инфо о коллекции"""
    if name not in collections_db:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collections_db[name]

@router.delete("/api/v1/collections/{name}")
async def delete_collection(name: str):
    """Удалить коллекцию"""
    if name not in collections_db:
        raise HTTPException(status_code=404, detail="Collection not found")
    del collections_db[name]
    return {"status": "deleted", "name": name}

@router.post("/api/v1/collections/{name}/version", response_model=CollectionVersion)
async def create_collection_version(name: str, request: UpdateCollectionRequest):
    """Создать новую версию коллекции (например, после fine-tune или обновления датасета)"""
    if name not in collections_db:
        raise HTTPException(status_code=404, detail="Collection not found")
    now = time.time()
    version_id = str(uuid.uuid4())
    version = CollectionVersion(version_id=version_id, timestamp=now, description=request.description)
    collections_db[name].versions.append(version)
    collections_db[name].updated_at = now
    collections_db[name].current_version = version_id
    if request.metadata:
        collections_db[name].metadata = request.metadata
    return version

@router.get("/api/v1/collections/{name}/versions", response_model=List[CollectionVersion])
async def list_collection_versions(name: str):
    """Список версий коллекции"""
    if name not in collections_db:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collections_db[name].versions

@router.post("/api/v1/collections/{name}/rollback", response_model=CollectionInfo)
async def rollback_collection(name: str, request: RollbackRequest):
    """Откатить коллекцию к указанной версии"""
    if name not in collections_db:
        raise HTTPException(status_code=404, detail="Collection not found")
    versions = collections_db[name].versions
    found = next((v for v in versions if v.version_id == request.version_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Version not found")
    collections_db[name].current_version = found.version_id
    collections_db[name].updated_at = time.time()
    return collections_db[name]

@router.post("/api/v1/fine-tune/start", response_model=FineTuneJob)
async def start_fine_tune(collection: str):
    """Запустить fine-tuning для коллекции"""
    if collection not in collections_db:
        raise HTTPException(status_code=404, detail="Collection not found")
    job_id = str(uuid.uuid4())
    now = time.time()
    job = FineTuneJob(
        job_id=job_id,
        collection=collection,
        status="pending",
        started_at=now,
        logs=[f"Fine-tune job {job_id} created for collection {collection}"]
    )
    fine_tune_jobs[job_id] = job
    # Фоновая задача для симуляции fine-tune
    asyncio.create_task(_run_fine_tune_job(job_id, collection))
    return job

@router.get("/api/v1/fine-tune/{job_id}", response_model=FineTuneJob)
async def get_fine_tune_status(job_id: str):
    """Статус fine-tune job"""
    if job_id not in fine_tune_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return fine_tune_jobs[job_id]

@router.post("/api/v1/fine-tune/{job_id}/cancel", response_model=FineTuneJob)
async def cancel_fine_tune(job_id: str):
    """Отменить fine-tune job"""
    if job_id not in fine_tune_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    fine_tune_jobs[job_id].status = "cancelled"
    fine_tune_jobs[job_id].finished_at = time.time()
    fine_tune_jobs[job_id].logs.append("Job cancelled by user")
    return fine_tune_jobs[job_id]

async def _run_fine_tune_job(job_id: str, collection: str):
    # Симуляция процесса fine-tune (замени на реальный pipeline)
    job = fine_tune_jobs[job_id]
    job.status = "running"
    job.logs.append("Fine-tuning started")
    await asyncio.sleep(2)  # имитация работы
    job.progress = 0.5
    job.logs.append("50% complete")
    await asyncio.sleep(2)
    job.progress = 1.0
    job.status = "completed"
    job.finished_at = time.time()
    job.model_version = f"model-{collection}-{int(job.finished_at)}"
    job.logs.append("Fine-tuning completed")
    # --- Автоматическая синхронизация между RAG и LLM ---
    await _sync_rag_llm(collection, job.model_version)

# --- СИНХРОНИЗАЦИЯ RAG И LLM ---
async def _sync_rag_llm(collection: str, model_version: str):
    # Здесь можно реализовать пуш в LLM роутер или обновление метаданных
    # Например, отправить событие или обновить коллекцию в RAG
    # Пока просто логируем
    print(f"[SYNC] Collection {collection} synced with LLM model version {model_version}")
    # TODO: интеграция с реальным сервисом

# --- РАСШИРЕННЫЙ МОНИТОРИНГ ---
# (добавить историю по коллекциям, latency, качество)
# Можно расширить get_service_monitor и добавить новые метрики

@router.post("/api/v1/collections/{name}/metrics")
async def add_collection_metric(name: str, latency: float, quality: float):
    """Добавить метрику latency/качества для коллекции (вызывается из бизнес-логики)"""
    if name not in collections_db:
        raise HTTPException(status_code=404, detail="Collection not found")
    if name not in collection_metrics:
        collection_metrics[name] = []
    collection_metrics[name].append({
        "latency": latency,
        "quality": quality,
        "timestamp": time.time()
    })
    return {"status": "ok"}

@router.get("/api/v1/collections/{name}/metrics")
async def get_collection_metrics(name: str):
    """Получить историю метрик по коллекции"""
    if name not in collections_db:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection_metrics.get(name, [])

@router.post("/api/v1/fine-tune/{job_id}/metrics")
async def add_fine_tune_metric(job_id: str, latency: float, quality: float):
    """Добавить метрику latency/качества для fine-tune job"""
    if job_id not in fine_tune_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    fine_tune_metrics[job_id] = {
        "latency": latency,
        "quality": quality,
        "timestamp": time.time()
    }
    return {"status": "ok"}

@router.get("/api/v1/fine-tune/{job_id}/metrics")
async def get_fine_tune_metrics(job_id: str):
    """Получить метрики по fine-tune job"""
    if job_id not in fine_tune_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return fine_tune_metrics.get(job_id, {})
