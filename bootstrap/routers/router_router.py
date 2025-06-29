"""
🚀 Роутер для управления RAG и ChromaDB
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import httpx

from ..rag_service import get_rag_service
from ..llm_router import get_llm_router
from ..ollama_client import get_ollama_client
from ..config import get_settings

router = APIRouter(prefix="/api/v1", tags=["router"])

# Модели данных
class Document(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class SearchQuery(BaseModel):
    query: str
    collection: str = "default"
    top_k: int = 5

class CollectionInfo(BaseModel):
    name: str
    count: int
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

@router.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "router",
        "description": "Центральный роутер для микросервисов reLink",
        "version": "1.0.0"
    }

@router.get("/services")
async def list_services():
    """Список доступных сервисов"""
    return {
        "services": [
            {
                "name": "router",
                "port": 8001,
                "description": "Центральный роутер",
                "status": "active"
            },
            {
                "name": "chromadb", 
                "port": 8000,
                "description": "Векторная база данных",
                "status": "active"
            },
            {
                "name": "ollama",
                "port": 11434,
                "description": "LLM сервис",
                "status": "active"
            }
        ]
    }

@router.post("/route")
async def route_request(
    request: Dict[str, Any],
    llm_router = Depends(get_llm_router)
):
    """Маршрутизация запроса к соответствующему сервису"""
    try:
        service = request.get("service", "default")
        prompt = request.get("prompt", "")
        
        if service == "llm":
            result = await llm_router.route_request(prompt)
            return result
        else:
            return {
                "status": "routed",
                "service": service,
                "message": f"Request routed to {service}"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rag/search")
async def rag_search(
    query: str,
    collection: str = "default",
    top_k: int = 5,
    rag_service = Depends(get_rag_service)
):
    """Поиск в RAG системе"""
    try:
        results = await rag_service.search(query, collection, top_k)
        return {
            "query": query,
            "collection": collection,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag/add")
async def add_documents(
    documents: List[Document],
    collection: str = Query("default", description="Имя коллекции")
) -> Dict[str, Any]:
    """Добавление документов в RAG"""
    
    rag_service = get_rag_service()
    
    # Конвертируем в формат для RAG сервиса
    docs = []
    for doc in documents:
        doc_dict = {
            "text": doc.text,
            "metadata": doc.metadata or {},
            "id": doc.id
        }
        docs.append(doc_dict)
    
    result = await rag_service.add_documents(docs, collection)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/rag/search")
async def search_documents(query: SearchQuery) -> Dict[str, Any]:
    """Поиск документов в RAG"""
    
    rag_service = get_rag_service()
    results = await rag_service.search(
        query=query.query,
        collection=query.collection,
        top_k=query.top_k
    )
    
    return {
        "query": query.query,
        "collection": query.collection,
        "results": results,
        "count": len(results)
    }

@router.get("/rag/collections")
async def get_collections() -> Dict[str, Any]:
    """Получение списка коллекций"""
    
    rag_service = get_rag_service()
    collections = await rag_service.get_collections()
    
    return {
        "collections": collections,
        "count": len(collections)
    }

@router.delete("/rag/collections/{collection_name}")
async def delete_collection(collection_name: str) -> Dict[str, Any]:
    """Удаление коллекции"""
    
    rag_service = get_rag_service()
    result = await rag_service.delete_collection(collection_name)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.post("/rag/cleanup")
async def cleanup_collections(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Автоматическая очистка старых коллекций"""
    
    rag_service = get_rag_service()
    
    # Запускаем очистку в фоне
    background_tasks.add_task(rag_service.cleanup_old_collections)
    
    return {
        "message": "Cleanup started in background",
        "status": "processing"
    }

@router.get("/rag/cleanup/status")
async def get_cleanup_status() -> Dict[str, Any]:
    """Получение статуса очистки"""
    
    rag_service = get_rag_service()
    health = await rag_service.health_check()
    
    return {
        "needs_cleanup": health.get("needs_cleanup", False),
        "collections_count": health.get("collections_count", 0),
        "status": health.get("status", "unknown")
    }

@router.delete("/rag/documents")
async def delete_documents(
    document_ids: List[str],
    collection: str = Query("default", description="Имя коллекции")
) -> Dict[str, Any]:
    """Удаление документов из коллекции"""
    
    rag_service = get_rag_service()
    result = await rag_service.delete_documents(document_ids, collection)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Проверка здоровья роутера и ChromaDB"""
    
    settings = get_settings()
    rag_service = get_rag_service()
    
    # Проверяем RAG сервис
    rag_health = await rag_service.health_check()
    
    # Проверяем Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ollama_response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            ollama_models = ollama_response.json().get("models", [])
    except Exception as e:
        ollama_models = []
    
    return {
        "status": "healthy" if rag_health["status"] == "healthy" else "degraded",
        "service": "router",
        "chromadb": rag_health["status"],
        "chromadb_connected": rag_health.get("chromadb_connected", False),
        "collections_count": rag_health.get("collections_count", 0),
        "ollama_models_count": len(ollama_models),
        "warnings": [] if rag_health["status"] == "healthy" else ["ChromaDB not connected"],
        "chromadb_error": rag_health.get("error") if rag_health["status"] != "healthy" else None
    }

@router.get("/endpoints")
async def get_endpoints() -> Dict[str, Any]:
    """Получение списка доступных эндпоинтов"""
    
    return {
        "service": "router",
        "endpoints": [
            "/health",
            "/endpoints",
            "/rag/add",
            "/rag/search", 
            "/rag/collections",
            "/rag/collections/{collection_name}",
            "/rag/cleanup",
            "/rag/cleanup/status",
            "/rag/documents"
        ],
        "description": "Router service for RAG and ChromaDB management"
    }

@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Получение статистики роутера"""
    
    rag_service = get_rag_service()
    collections = await rag_service.get_collections()
    
    total_documents = sum(collection.get("count", 0) for collection in collections)
    
    return {
        "service": "router",
        "collections_count": len(collections),
        "total_documents": total_documents,
        "collections": collections
    }

@router.get("/ollama/models")
async def list_ollama_models(
    ollama_client = Depends(get_ollama_client)
):
    """Список доступных моделей Ollama"""
    try:
        models = await ollama_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ollama/generate")
async def generate_with_ollama(
    request: Dict[str, Any],
    ollama_client = Depends(get_ollama_client)
):
    """Генерация через Ollama"""
    try:
        prompt = request.get("prompt", "")
        model = request.get("model", "qwen2.5:7b-instruct-turbo")
        
        result = await ollama_client.generate(prompt, model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 