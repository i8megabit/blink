"""
Роутер для router сервиса
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import httpx

from ..rag_service import get_rag_service
from ..llm_router import get_llm_router
from ..ollama_client import get_ollama_client

router = APIRouter(tags=["router"])

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
async def rag_add_documents(
    documents: List[Dict[str, Any]],
    collection: str = "default",
    rag_service = Depends(get_rag_service)
):
    """Добавление документов в RAG"""
    try:
        result = await rag_service.add_documents(documents, collection)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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