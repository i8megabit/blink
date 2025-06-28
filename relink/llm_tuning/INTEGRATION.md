# 🔗 Интеграция LLM Tuning с reLink

## 📋 Обзор интеграции

LLM Tuning Microservice интегрируется с основным проектом reLink для предоставления расширенных возможностей управления языковыми моделями. Интеграция обеспечивает A/B тестирование, автоматическую оптимизацию, оценку качества и RAG функциональность.

---

## 🏗️ Архитектура интеграции

```
┌─────────────────────────────────────────────────────────────┐
│                        reLink Frontend                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   SEO App   │  │ Content Gen │  │ Analytics   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     reLink Backend                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   API GW    │  │   Cache     │  │   Auth      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLM Tuning Microservice                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ A/B Testing │  │ Optimization│  │ Quality     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ RAG Service │  │ Monitoring  │  │ Utils       │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Ollama    │  │ PostgreSQL  │  │   Redis     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Qdrant    │  │ Prometheus  │  │   Grafana   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Настройка интеграции

### 1. Конфигурация reLink Backend

Обновите конфигурацию основного backend для интеграции с LLM Tuning:

```python
# relink/backend/app/config.py

class Settings(BaseSettings):
    # Существующие настройки...
    
    # LLM Tuning интеграция
    llm_tuning_enabled: bool = True
    llm_tuning_url: str = "http://localhost:8000"
    llm_tuning_api_key: str = "your-api-key"
    
    # A/B тестирование
    ab_testing_enabled: bool = True
    default_ab_test_traffic_split: float = 0.5
    
    # RAG интеграция
    rag_enabled: bool = True
    rag_collection_name: str = "relink_docs"
    
    # Качество контента
    quality_assessment_enabled: bool = True
    min_quality_score: float = 7.0
```

### 2. Обновление переменных окружения

```bash
# relink/backend/.env

# LLM Tuning интеграция
LLM_TUNING_ENABLED=true
LLM_TUNING_URL=http://localhost:8000
LLM_TUNING_API_KEY=your-api-key

# A/B тестирование
AB_TESTING_ENABLED=true
DEFAULT_AB_TEST_TRAFFIC_SPLIT=0.5

# RAG интеграция
RAG_ENABLED=true
RAG_COLLECTION_NAME=relink_docs

# Качество контента
QUALITY_ASSESSMENT_ENABLED=true
MIN_QUALITY_SCORE=7.0
```

### 3. Docker Compose интеграция

```yaml
# relink/docker-compose.yml

version: '3.8'

services:
  # Существующие сервисы...
  
  llm_tuning:
    build: ./llm_tuning
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/llm_tuning
      - OLLAMA_BASE_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379
      - VECTOR_DB_URL=http://qdrant:6333
    depends_on:
      - db
      - redis
      - ollama
      - qdrant
    networks:
      - relink_network

  # Обновление backend для интеграции
  backend:
    build: ./backend
    environment:
      - LLM_TUNING_URL=http://llm_tuning:8000
      - LLM_TUNING_API_KEY=your-api-key
    depends_on:
      - llm_tuning
    networks:
      - relink_network

networks:
  relink_network:
    driver: bridge
```

---

## 🔌 Клиент для интеграции

### Создание клиента

```python
# relink/backend/app/llm_client.py

import aiohttp
import asyncio
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class LLMTuningClient:
    """Клиент для интеграции с LLM Tuning Microservice"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Выполнение HTTP запроса"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.request(method, url, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"LLM Tuning request failed: {e}")
            raise
    
    # A/B тестирование
    async def create_ab_test(self, test_config: Dict) -> Dict:
        """Создание A/B теста"""
        return await self._make_request("POST", "/api/v1/ab-tests", test_config)
    
    async def select_model_for_ab_test(self, test_id: int, request_type: str, user_id: str) -> Dict:
        """Выбор модели для A/B теста"""
        data = {
            "request_type": request_type,
            "user_id": user_id
        }
        return await self._make_request("POST", f"/api/v1/ab-tests/{test_id}/select-model", data)
    
    async def record_ab_test_result(self, test_id: int, session_id: str, variant: str, metrics: Dict) -> Dict:
        """Запись результатов A/B теста"""
        data = {
            "session_id": session_id,
            "variant": variant,
            "metrics": metrics
        }
        return await self._make_request("POST", f"/api/v1/ab-tests/{test_id}/results", data)
    
    # Автоматическая оптимизация
    async def optimize_model(self, optimization_config: Dict) -> Dict:
        """Запуск оптимизации модели"""
        return await self._make_request("POST", "/api/v1/optimization", optimization_config)
    
    async def get_optimization_status(self, optimization_id: int) -> Dict:
        """Получение статуса оптимизации"""
        return await self._make_request("GET", f"/api/v1/optimization/{optimization_id}")
    
    # Оценка качества
    async def assess_quality(self, assessment_data: Dict) -> Dict:
        """Оценка качества контента"""
        return await self._make_request("POST", "/api/v1/quality/assess", assessment_data)
    
    async def get_quality_stats(self, model_id: int, days: int = 30) -> Dict:
        """Получение статистики качества"""
        return await self._make_request("GET", f"/api/v1/quality/stats?model_id={model_id}&days={days}")
    
    # RAG операции
    async def search_documents(self, query: str, collection: str = "relink_docs", top_k: int = 5) -> Dict:
        """Поиск документов в RAG"""
        data = {
            "query": query,
            "collection": collection,
            "top_k": top_k
        }
        return await self._make_request("POST", "/api/v1/rag/search", data)
    
    async def generate_with_context(self, query: str, context_docs: List[Dict], model_name: str) -> Dict:
        """Генерация с контекстом"""
        data = {
            "query": query,
            "context_docs": context_docs,
            "model_name": model_name
        }
        return await self._make_request("POST", "/api/v1/rag/generate", data)
    
    # Мониторинг
    async def get_system_health(self) -> Dict:
        """Получение состояния здоровья системы"""
        return await self._make_request("GET", "/api/v1/health")
    
    async def get_model_stats(self, model_id: int, days: int = 30) -> Dict:
        """Получение статистики модели"""
        return await self._make_request("GET", f"/api/v1/stats/model/{model_id}?days={days}")
```

### Интеграция в сервисы

```python
# relink/backend/app/services/seo_service.py

from app.llm_client import LLMTuningClient
from app.config import settings
import asyncio

class SEOService:
    """Сервис для SEO анализа с интеграцией LLM Tuning"""
    
    def __init__(self):
        self.llm_client = None
    
    async def get_llm_client(self) -> LLMTuningClient:
        """Получение клиента LLM Tuning"""
        if not self.llm_client:
            self.llm_client = LLMTuningClient(
                settings.llm_tuning_url,
                settings.llm_tuning_api_key
            )
        return self.llm_client
    
    async def analyze_website_seo(self, domain: str, user_id: str) -> Dict:
        """Анализ SEO сайта с A/B тестированием"""
        async with await self.get_llm_client() as client:
            # Создание A/B теста для анализа
            ab_test = await client.create_ab_test({
                "name": f"SEO Analysis - {domain}",
                "description": f"Анализ SEO для домена {domain}",
                "model_id": 1,
                "variant_a": {"name": "llama2:7b", "parameters": {"temperature": 0.7}},
                "variant_b": {"name": "llama2:13b", "parameters": {"temperature": 0.7}},
                "traffic_split": settings.default_ab_test_traffic_split,
                "test_duration_days": 1,
                "success_metrics": ["analysis_quality", "response_time", "user_satisfaction"]
            })
            
            # Выбор модели для анализа
            model_info = await client.select_model_for_ab_test(
                test_id=ab_test['id'],
                request_type="seo_analysis",
                user_id=user_id
            )
            
            # Выполнение анализа
            analysis_result = await self._perform_seo_analysis(domain, model_info)
            
            # Запись результатов
            await client.record_ab_test_result(
                test_id=ab_test['id'],
                session_id=model_info['session_id'],
                variant=model_info['selected_variant'],
                metrics={
                    "analysis_quality": analysis_result['quality_score'],
                    "response_time": analysis_result['response_time'],
                    "user_satisfaction": analysis_result['user_satisfaction']
                }
            )
            
            return analysis_result
    
    async def generate_seo_content(self, topic: str, keywords: List[str], user_id: str) -> Dict:
        """Генерация SEO контента с RAG"""
        async with await self.get_llm_client() as client:
            # Поиск релевантных документов
            search_results = await client.search_documents(
                query=f"{topic} {' '.join(keywords)}",
                collection=settings.rag_collection_name,
                top_k=5
            )
            
            # Генерация контента с контекстом
            generation_result = await client.generate_with_context(
                query=f"Создай SEO-оптимизированную статью о {topic} с ключевыми словами: {', '.join(keywords)}",
                context_docs=search_results['results'],
                model_name="llama2:7b"
            )
            
            # Оценка качества
            if settings.quality_assessment_enabled:
                quality_assessment = await client.assess_quality({
                    "model_id": 1,
                    "request_text": f"Создай SEO-оптимизированную статью о {topic}",
                    "response_text": generation_result['answer'],
                    "assessment_criteria": ["relevance", "accuracy", "seo_optimization", "readability"]
                })
                
                # Проверка минимального качества
                if quality_assessment['overall_score'] < settings.min_quality_score:
                    logger.warning(f"Generated content quality below threshold: {quality_assessment['overall_score']}")
            
            return {
                "content": generation_result['answer'],
                "sources": generation_result['sources'],
                "quality_score": quality_assessment['overall_score'] if settings.quality_assessment_enabled else None,
                "metadata": generation_result['metadata']
            }
    
    async def optimize_content_quality(self, content: str, target_score: float = 8.0) -> Dict:
        """Оптимизация качества контента"""
        async with await self.get_llm_client() as client:
            # Запуск оптимизации
            optimization = await client.optimize_model({
                "model_id": 1,
                "optimization_type": "quality",
                "target_metrics": {
                    "quality_score": target_score
                },
                "optimization_strategies": [
                    "prompt_engineering",
                    "parameter_tuning"
                ]
            })
            
            return optimization
```

---

## 🎨 Интеграция в Frontend

### React компоненты

```typescript
// relink/frontend/src/components/LLMTuningIntegration.tsx

import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

interface ABTestResult {
  test_id: number;
  variant: string;
  metrics: {
    response_time: number;
    quality_score: number;
    user_satisfaction: number;
  };
}

interface QualityAssessment {
  overall_score: number;
  detailed_scores: Record<string, number>;
  feedback: {
    strengths: string[];
    improvements: string[];
  };
}

export const LLMTuningIntegration: React.FC = () => {
  const [abTestResults, setAbTestResults] = useState<ABTestResult[]>([]);
  const [qualityAssessments, setQualityAssessments] = useState<QualityAssessment[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  
  const { get, post } = useApi();
  
  // Получение результатов A/B тестов
  const fetchABTestResults = async () => {
    try {
      const response = await get('/api/llm-tuning/ab-tests/results');
      setAbTestResults(response.data);
    } catch (error) {
      console.error('Failed to fetch A/B test results:', error);
    }
  };
  
  // Получение оценок качества
  const fetchQualityAssessments = async () => {
    try {
      const response = await get('/api/llm-tuning/quality/assessments');
      setQualityAssessments(response.data);
    } catch (error) {
      console.error('Failed to fetch quality assessments:', error);
    }
  };
  
  // Получение состояния здоровья системы
  const fetchSystemHealth = async () => {
    try {
      const response = await get('/api/llm-tuning/health');
      setSystemHealth(response.data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    }
  };
  
  useEffect(() => {
    fetchABTestResults();
    fetchQualityAssessments();
    fetchSystemHealth();
    
    // Обновление каждые 30 секунд
    const interval = setInterval(() => {
      fetchSystemHealth();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="space-y-6">
      {/* A/B тестирование */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">A/B Тестирование</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {abTestResults.map((result) => (
            <div key={result.test_id} className="border rounded p-4">
              <h4 className="font-medium">Тест #{result.test_id}</h4>
              <p className="text-sm text-gray-600">Вариант: {result.variant}</p>
              <div className="mt-2 space-y-1">
                <p className="text-xs">Время ответа: {result.metrics.response_time}s</p>
                <p className="text-xs">Качество: {result.metrics.quality_score}/10</p>
                <p className="text-xs">Удовлетворенность: {result.metrics.user_satisfaction}/5</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Оценка качества */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Оценка качества</h3>
        <div className="space-y-4">
          {qualityAssessments.map((assessment, index) => (
            <div key={index} className="border rounded p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">Общий балл: {assessment.overall_score}/10</span>
                <div className={`px-2 py-1 rounded text-xs ${
                  assessment.overall_score >= 8 ? 'bg-green-100 text-green-800' :
                  assessment.overall_score >= 6 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {assessment.overall_score >= 8 ? 'Отлично' :
                   assessment.overall_score >= 6 ? 'Хорошо' : 'Требует улучшения'}
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                {Object.entries(assessment.detailed_scores).map(([criterion, score]) => (
                  <div key={criterion}>
                    <span className="text-gray-600">{criterion}:</span>
                    <span className="ml-1 font-medium">{score}/10</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Состояние системы */}
      {systemHealth && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Состояние системы</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {systemHealth.components?.ollama?.status === 'healthy' ? '✅' : '❌'}
              </div>
              <p className="text-sm text-gray-600">Ollama</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {systemHealth.components?.database?.status === 'healthy' ? '✅' : '❌'}
              </div>
              <p className="text-sm text-gray-600">База данных</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {systemHealth.components?.vector_db?.status === 'healthy' ? '✅' : '❌'}
              </div>
              <p className="text-sm text-gray-600">Vector DB</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {systemHealth.components?.redis?.status === 'healthy' ? '✅' : '❌'}
              </div>
              <p className="text-sm text-gray-600">Redis</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">CPU:</span>
              <span className="ml-1 font-medium">{systemHealth.system_metrics?.cpu_usage?.toFixed(1)}%</span>
            </div>
            <div>
              <span className="text-gray-600">Память:</span>
              <span className="ml-1 font-medium">{systemHealth.system_metrics?.memory_usage?.toFixed(0)}MB</span>
            </div>
            <div>
              <span className="text-gray-600">Запросов/сек:</span>
              <span className="ml-1 font-medium">{systemHealth.application_metrics?.requests_per_second?.toFixed(0)}</span>
            </div>
            <div>
              <span className="text-gray-600">Ошибок:</span>
              <span className="ml-1 font-medium">{systemHealth.application_metrics?.error_rate?.toFixed(2)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

### API хуки

```typescript
// relink/frontend/src/hooks/useLLMTuning.ts

import { useState, useCallback } from 'react';
import { useApi } from './useApi';

export const useLLMTuning = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { get, post } = useApi();
  
  // A/B тестирование
  const createABTest = useCallback(async (testConfig: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await post('/api/llm-tuning/ab-tests', testConfig);
      return response.data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [post]);
  
  const selectModelForABTest = useCallback(async (testId: number, requestType: string, userId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await post(`/api/llm-tuning/ab-tests/${testId}/select-model`, {
        request_type: requestType,
        user_id: userId
      });
      return response.data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [post]);
  
  // Оценка качества
  const assessQuality = useCallback(async (assessmentData: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await post('/api/llm-tuning/quality/assess', assessmentData);
      return response.data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [post]);
  
  // RAG операции
  const searchDocuments = useCallback(async (query: string, collection: string = 'relink_docs') => {
    setLoading(true);
    setError(null);
    try {
      const response = await post('/api/llm-tuning/rag/search', {
        query,
        collection,
        top_k: 5
      });
      return response.data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [post]);
  
  const generateWithContext = useCallback(async (query: string, contextDocs: any[], modelName: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await post('/api/llm-tuning/rag/generate', {
        query,
        context_docs: contextDocs,
        model_name: modelName
      });
      return response.data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [post]);
  
  // Мониторинг
  const getSystemHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await get('/api/llm-tuning/health');
      return response.data;
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [get]);
  
  return {
    loading,
    error,
    createABTest,
    selectModelForABTest,
    assessQuality,
    searchDocuments,
    generateWithContext,
    getSystemHealth
  };
};
```

---

## 🧪 Тестирование интеграции

### Интеграционные тесты

```python
# relink/backend/tests/test_llm_tuning_integration.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.llm_client import LLMTuningClient
from app.services.seo_service import SEOService

class TestLLMTuningIntegration:
    """Тесты интеграции с LLM Tuning"""
    
    @pytest.fixture
    async def llm_client(self):
        """Фикстура клиента LLM Tuning"""
        async with LLMTuningClient("http://localhost:8000", "test-key") as client:
            yield client
    
    @pytest.fixture
    def seo_service(self):
        """Фикстура SEO сервиса"""
        return SEOService()
    
    @pytest.mark.asyncio
    async def test_ab_test_creation(self, llm_client):
        """Тест создания A/B теста"""
        test_config = {
            "name": "Test SEO Analysis",
            "description": "Test description",
            "model_id": 1,
            "variant_a": {"name": "llama2:7b"},
            "variant_b": {"name": "llama2:13b"},
            "traffic_split": 0.5,
            "test_duration_days": 1,
            "success_metrics": ["response_time", "quality_score"]
        }
        
        result = await llm_client.create_ab_test(test_config)
        
        assert result["name"] == "Test SEO Analysis"
        assert result["status"] == "active"
        assert "id" in result
    
    @pytest.mark.asyncio
    async def test_model_selection(self, llm_client):
        """Тест выбора модели для A/B теста"""
        test_id = 1
        
        result = await llm_client.select_model_for_ab_test(
            test_id=test_id,
            request_type="seo_analysis",
            user_id="test_user"
        )
        
        assert "selected_variant" in result
        assert "model_name" in result
        assert "session_id" in result
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, llm_client):
        """Тест оценки качества"""
        assessment_data = {
            "model_id": 1,
            "request_text": "Test request",
            "response_text": "Test response",
            "assessment_criteria": ["relevance", "accuracy"]
        }
        
        result = await llm_client.assess_quality(assessment_data)
        
        assert "overall_score" in result
        assert "detailed_scores" in result
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 10
    
    @pytest.mark.asyncio
    async def test_rag_search(self, llm_client):
        """Тест поиска в RAG"""
        query = "SEO optimization"
        
        result = await llm_client.search_documents(query)
        
        assert "results" in result
        assert "total_found" in result
        assert isinstance(result["results"], list)
    
    @pytest.mark.asyncio
    async def test_seo_service_integration(self, seo_service):
        """Тест интеграции в SEO сервис"""
        with patch.object(seo_service, 'get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Мокаем ответы клиента
            mock_client.create_ab_test.return_value = {
                "id": 1, "name": "Test", "status": "active"
            }
            mock_client.select_model_for_ab_test.return_value = {
                "selected_variant": "a", "model_name": "llama2:7b", "session_id": "session_123"
            }
            
            result = await seo_service.analyze_website_seo("example.com", "user_123")
            
            assert result is not None
            mock_client.create_ab_test.assert_called_once()
            mock_client.select_model_for_ab_test.assert_called_once()
```

---

## 📊 Мониторинг интеграции

### Метрики интеграции

```python
# relink/backend/app/monitoring/llm_tuning_metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Метрики интеграции
llm_tuning_requests_total = Counter(
    'llm_tuning_requests_total',
    'Total number of LLM Tuning requests',
    ['endpoint', 'method', 'status']
)

llm_tuning_request_duration = Histogram(
    'llm_tuning_request_duration_seconds',
    'Duration of LLM Tuning requests',
    ['endpoint']
)

llm_tuning_ab_test_results = Counter(
    'llm_tuning_ab_test_results_total',
    'Total number of A/B test results',
    ['test_id', 'variant', 'metric']
)

llm_tuning_quality_scores = Histogram(
    'llm_tuning_quality_scores',
    'Quality assessment scores',
    ['model_id', 'criteria']
)

llm_tuning_rag_operations = Counter(
    'llm_tuning_rag_operations_total',
    'Total number of RAG operations',
    ['operation_type', 'collection']
)

llm_tuning_system_health = Gauge(
    'llm_tuning_system_health',
    'System health status',
    ['component']
)

class LLMTuningMetrics:
    """Метрики для мониторинга интеграции с LLM Tuning"""
    
    @staticmethod
    def record_request(endpoint: str, method: str, status: str, duration: float):
        """Запись метрики запроса"""
        llm_tuning_requests_total.labels(endpoint=endpoint, method=method, status=status).inc()
        llm_tuning_request_duration.labels(endpoint=endpoint).observe(duration)
    
    @staticmethod
    def record_ab_test_result(test_id: int, variant: str, metric: str, value: float):
        """Запись результата A/B теста"""
        llm_tuning_ab_test_results.labels(
            test_id=str(test_id), 
            variant=variant, 
            metric=metric
        ).inc()
    
    @staticmethod
    def record_quality_score(model_id: int, criteria: str, score: float):
        """Запись оценки качества"""
        llm_tuning_quality_scores.labels(
            model_id=str(model_id), 
            criteria=criteria
        ).observe(score)
    
    @staticmethod
    def record_rag_operation(operation_type: str, collection: str):
        """Запись RAG операции"""
        llm_tuning_rag_operations.labels(
            operation_type=operation_type, 
            collection=collection
        ).inc()
    
    @staticmethod
    def update_system_health(component: str, status: int):
        """Обновление состояния здоровья системы"""
        llm_tuning_system_health.labels(component=component).set(status)
```

### Middleware для метрик

```python
# relink/backend/app/middleware/llm_tuning_metrics.py

from fastapi import Request
import time
from app.monitoring.llm_tuning_metrics import LLMTuningMetrics

async def llm_tuning_metrics_middleware(request: Request, call_next):
    """Middleware для сбора метрик LLM Tuning"""
    start_time = time.time()
    
    # Определяем, является ли запрос к LLM Tuning
    is_llm_tuning_request = request.url.path.startswith('/api/llm-tuning')
    
    response = await call_next(request)
    
    if is_llm_tuning_request:
        duration = time.time() - start_time
        LLMTuningMetrics.record_request(
            endpoint=request.url.path,
            method=request.method,
            status=str(response.status_code),
            duration=duration
        )
    
    return response
```

---

## 🚀 Развертывание

### Docker Compose для продакшена

```yaml
# relink/docker-compose.prod.yml

version: '3.8'

services:
  llm_tuning:
    build: ./llm_tuning
    image: relink/llm-tuning:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/llm_tuning
      - OLLAMA_BASE_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379
      - VECTOR_DB_URL=http://qdrant:6333
      - LOG_LEVEL=INFO
    depends_on:
      - db
      - redis
      - ollama
      - qdrant
    networks:
      - relink_network
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 1G
          cpus: '1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: ./backend
    image: relink/backend:latest
    environment:
      - LLM_TUNING_URL=http://llm_tuning:8000
      - LLM_TUNING_API_KEY=${LLM_TUNING_API_KEY}
      - LOG_LEVEL=INFO
    depends_on:
      llm_tuning:
        condition: service_healthy
    networks:
      - relink_network
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  relink_network:
    driver: bridge
```

### Kubernetes развертывание

```yaml
# relink/k8s/llm-tuning-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-tuning
  namespace: relink
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-tuning
  template:
    metadata:
      labels:
        app: llm-tuning
    spec:
      containers:
      - name: llm-tuning
        image: relink/llm-tuning:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: llm-tuning-secrets
              key: database-url
        - name: OLLAMA_BASE_URL
          value: "http://ollama:11434"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: VECTOR_DB_URL
          value: "http://qdrant:6333"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: llm-tuning-service
  namespace: relink
spec:
  selector:
    app: llm-tuning
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

---

## 🔧 Устранение неполадок

### Частые проблемы интеграции

1. **LLM Tuning недоступен**
   ```bash
   # Проверка доступности
   curl http://localhost:8000/health
   
   # Проверка логов
   docker-compose logs llm_tuning
   
   # Перезапуск сервиса
   docker-compose restart llm_tuning
   ```

2. **Ошибки аутентификации**
   ```bash
   # Проверка API ключа
   echo $LLM_TUNING_API_KEY
   
   # Обновление ключа
   export LLM_TUNING_API_KEY="new-api-key"
   docker-compose restart backend
   ```

3. **Проблемы с RAG**
   ```bash
   # Проверка Vector DB
   curl http://localhost:6333/collections
   
   # Проверка коллекций
   curl http://localhost:6333/collections/relink_docs
   
   # Перезапуск Qdrant
   docker-compose restart qdrant
   ```

### Диагностика

```bash
# Полная диагностика интеграции
curl -X POST http://localhost:8000/api/v1/health/diagnostic \
  -H "Authorization: Bearer YOUR_TOKEN"

# Проверка метрик
curl http://localhost:8000/metrics | grep llm_tuning

# Тест интеграции
python -m pytest tests/test_llm_tuning_integration.py -v
```

---

## 📚 Дополнительные ресурсы

- [📖 Основная документация LLM Tuning](README.md)
- [🔗 API документация](docs/API_EXTENDED.md)
- [🔗 Примеры использования](examples/)
- [🔗 Конфигурация](config.py)
- [🔗 Тесты](tests/)

---

*Документация по интеграции обновлена: 2024-01-01* 