#!/usr/bin/env python3
"""
Тесты для расширенных API эндпоинтов LLM Tuning Microservice

Этот файл содержит тесты для новых возможностей:
- A/B тестирование
- Автоматическая оптимизация
- Оценка качества
- Мониторинг здоровья системы
- Расширенная статистика
"""

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from app.main import app
from app.models import (
    LLMModel, ABTest, ModelOptimization, QualityAssessment, 
    SystemHealth, PerformanceMetrics
)
from app.schemas import (
    ABTestCreate, ABTestUpdate, ModelOptimizationCreate,
    QualityAssessmentCreate
)


@pytest.fixture
async def async_client():
    """Асинхронный клиент для тестирования"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_model():
    """Тестовая модель"""
    return LLMModel(
        id=1,
        name="test-model",
        base_model="llama2:7b",
        provider="ollama",
        description="Test model",
        is_available=True,
        avg_response_time=2.0,
        avg_quality_score=8.0
    )


@pytest.fixture
def sample_ab_test():
    """Тестовый A/B тест"""
    return ABTest(
        id=1,
        name="Test AB Test",
        description="Test description",
        model_id=1,
        variant_a="llama2:7b",
        variant_b="llama2:13b",
        traffic_split=0.5,
        test_duration_days=7,
        success_metrics=["response_time", "quality_score"],
        minimum_sample_size=100,
        status="active",
        created_at=datetime.utcnow(),
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=7)
    )


@pytest.fixture
def sample_optimization():
    """Тестовая оптимизация"""
    return ModelOptimization(
        id=1,
        model_id=1,
        optimization_type="performance",
        target_metrics={"response_time": 1.5, "quality_score": 8.0},
        optimization_strategies=["quantization", "pruning"],
        status="running",
        progress=50,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow()
    )


@pytest.fixture
def sample_quality_assessment():
    """Тестовая оценка качества"""
    return QualityAssessment(
        id=1,
        model_id=1,
        request_text="Test request",
        response_text="Test response",
        overall_score=8.5,
        detailed_scores={"relevance": 9.0, "accuracy": 8.0},
        assessment_criteria=["relevance", "accuracy"],
        assessed_at=datetime.utcnow(),
        assessor="automated"
    )


@pytest.fixture
def sample_system_health():
    """Тестовое состояние здоровья системы"""
    return SystemHealth(
        id=1,
        timestamp=datetime.utcnow(),
        cpu_usage=45.2,
        memory_usage=67.8,
        disk_usage=23.4,
        ollama_status="healthy",
        rag_status="healthy",
        response_time_avg=2.1,
        error_rate=0.02,
        total_requests=1250,
        active_models=3,
        active_routes=5,
        alerts=["Memory usage is high"],
        overall_status="healthy"
    )


class TestABTestingAPI:
    """Тесты для A/B тестирования API"""
    
    @pytest.mark.asyncio
    async def test_create_ab_test(self, async_client, sample_ab_test):
        """Тест создания A/B теста"""
        with patch('app.services.ABTestingService.create_ab_test') as mock_create:
            mock_create.return_value = sample_ab_test
            
            test_data = {
                "name": "Test AB Test",
                "description": "Test description",
                "model_id": 1,
                "variant_a": "llama2:7b",
                "variant_b": "llama2:13b",
                "traffic_split": 0.5,
                "test_duration_days": 7,
                "success_metrics": ["response_time", "quality_score"],
                "minimum_sample_size": 100
            }
            
            response = await async_client.post("/api/v1/ab-tests", json=test_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test AB Test"
            assert data["model_id"] == 1
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_ab_tests(self, async_client, sample_ab_test):
        """Тест получения списка A/B тестов"""
        with patch('app.services.ABTestingService.list_ab_tests') as mock_list:
            mock_list.return_value = [sample_ab_test]
            
            response = await async_client.get("/api/v1/ab-tests")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "Test AB Test"
            mock_list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_ab_test(self, async_client, sample_ab_test):
        """Тест получения A/B теста по ID"""
        with patch('app.services.ABTestingService.get_ab_test') as mock_get:
            mock_get.return_value = sample_ab_test
            
            response = await async_client.get("/api/v1/ab-tests/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "Test AB Test"
            mock_get.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_ab_test_not_found(self, async_client):
        """Тест получения несуществующего A/B теста"""
        with patch('app.services.ABTestingService.get_ab_test') as mock_get:
            mock_get.return_value = None
            
            response = await async_client.get("/api/v1/ab-tests/999")
            
            assert response.status_code == 404
            mock_get.assert_called_once_with(999)
    
    @pytest.mark.asyncio
    async def test_select_model_for_ab_test(self, async_client, sample_ab_test):
        """Тест выбора модели для A/B теста"""
        with patch('app.services.ABTestingService.select_model_for_request') as mock_select:
            mock_select.return_value = ("llama2:13b", "variant_b")
            
            data = {
                "request_type": "seo_content_generation",
                "user_id": "user_123"
            }
            
            response = await async_client.post("/api/v1/ab-tests/1/select-model", json=data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_name"] == "llama2:13b"
            assert data["variant"] == "variant_b"
            mock_select.assert_called_once_with(1, "seo_content_generation", "user_123")
    
    @pytest.mark.asyncio
    async def test_record_ab_test_result(self, async_client):
        """Тест записи результатов A/B теста"""
        with patch('app.services.ABTestingService.record_ab_test_result') as mock_record:
            mock_record.return_value = None
            
            data = {
                "model_variant": "llama2:13b",
                "metrics": {
                    "response_time": 2.5,
                    "quality_score": 8.5,
                    "success": True
                }
            }
            
            response = await async_client.post("/api/v1/ab-tests/1/record-result", json=data)
            
            assert response.status_code == 200
            mock_record.assert_called_once_with(1, "llama2:13b", data["metrics"])


class TestOptimizationAPI:
    """Тесты для API автоматической оптимизации"""
    
    @pytest.mark.asyncio
    async def test_optimize_model(self, async_client, sample_optimization):
        """Тест запуска оптимизации модели"""
        with patch('app.services.AutoOptimizationService.optimize_model') as mock_optimize:
            mock_optimize.return_value = sample_optimization
            
            optimization_data = {
                "model_id": 1,
                "optimization_type": "performance",
                "target_metrics": {
                    "response_time": 1.5,
                    "quality_score": 8.0
                },
                "optimization_strategies": ["quantization", "pruning"]
            }
            
            response = await async_client.post("/api/v1/optimization", json=optimization_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_id"] == 1
            assert data["optimization_type"] == "performance"
            assert data["status"] == "running"
            mock_optimize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_optimization(self, async_client, sample_optimization):
        """Тест получения информации об оптимизации"""
        with patch('app.services.AutoOptimizationService._get_optimization') as mock_get:
            mock_get.return_value = sample_optimization
            
            response = await async_client.get("/api/v1/optimization/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["model_id"] == 1
            mock_get.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_optimization_not_found(self, async_client):
        """Тест получения несуществующей оптимизации"""
        with patch('app.services.AutoOptimizationService._get_optimization') as mock_get:
            mock_get.return_value = None
            
            response = await async_client.get("/api/v1/optimization/999")
            
            assert response.status_code == 404
            mock_get.assert_called_once_with(999)


class TestQualityAssessmentAPI:
    """Тесты для API оценки качества"""
    
    @pytest.mark.asyncio
    async def test_assess_quality(self, async_client, sample_quality_assessment):
        """Тест оценки качества ответа"""
        with patch('app.services.QualityAssessmentService.assess_quality') as mock_assess:
            mock_assess.return_value = sample_quality_assessment
            
            assessment_data = {
                "model_id": 1,
                "request_text": "Test request",
                "response_text": "Test response",
                "context_documents": ["Context 1", "Context 2"],
                "assessment_criteria": ["relevance", "accuracy"]
            }
            
            response = await async_client.post("/api/v1/quality/assess", json=assessment_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_id"] == 1
            assert data["overall_score"] == 8.5
            assert "relevance" in data["detailed_scores"]
            mock_assess.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_quality_stats(self, async_client):
        """Тест получения статистики качества"""
        with patch('app.services.QualityAssessmentService.get_quality_stats') as mock_stats:
            mock_stats.return_value = {
                "model_id": 1,
                "model_name": "test-model",
                "avg_score": 8.2,
                "total_assessments": 150,
                "trend": "improving"
            }
            
            response = await async_client.get("/api/v1/quality/stats/1?days=30")
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_id"] == 1
            assert data["avg_score"] == 8.2
            assert data["trend"] == "improving"
            mock_stats.assert_called_once_with(1, 30)


class TestSystemHealthAPI:
    """Тесты для API мониторинга здоровья системы"""
    
    @pytest.mark.asyncio
    async def test_get_system_health(self, async_client, sample_system_health):
        """Тест получения состояния здоровья системы"""
        with patch('app.services.SystemHealthService.collect_system_health') as mock_health:
            mock_health.return_value = sample_system_health
            
            response = await async_client.get("/api/v1/health/system")
            
            assert response.status_code == 200
            data = response.json()
            assert data["cpu_usage"] == 45.2
            assert data["memory_usage"] == 67.8
            assert data["ollama_status"] == "healthy"
            assert data["overall_status"] == "healthy"
            mock_health.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_system_health_history(self, async_client, sample_system_health):
        """Тест получения истории здоровья системы"""
        with patch('app.database.get_db') as mock_db:
            mock_db.return_value = Mock()
            
            # Мокаем запрос к базе данных
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [sample_system_health]
            mock_db.return_value.execute.return_value = mock_result
            
            response = await async_client.get("/api/v1/health/system/history?hours=24")
            
            assert response.status_code == 200
            data = response.json()
            assert "records" in data
            assert len(data["records"]) == 1
            assert data["records"][0]["cpu_usage"] == 45.2


class TestExtendedStatsAPI:
    """Тесты для API расширенной статистики"""
    
    @pytest.mark.asyncio
    async def test_get_model_stats(self, async_client, sample_model):
        """Тест получения статистики модели"""
        with patch('app.database.get_db') as mock_db:
            mock_db.return_value = Mock()
            
            # Мокаем модель
            mock_db.return_value.get.return_value = sample_model
            
            # Мокаем метрики
            mock_metrics = [
                PerformanceMetrics(
                    id=1,
                    model_id=1,
                    response_time=2.0,
                    tokens_generated=100,
                    tokens_processed=50,
                    success=True,
                    user_feedback=8.0,
                    timestamp=datetime.utcnow()
                )
            ]
            
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = mock_metrics
            mock_db.return_value.execute.return_value = mock_result
            
            response = await async_client.get("/api/v1/stats/models/1?days=30")
            
            assert response.status_code == 200
            data = response.json()
            assert data["model_id"] == 1
            assert data["model_name"] == "test-model"
            assert data["total_requests"] == 1
            assert data["successful_requests"] == 1
            assert data["avg_response_time"] == 2.0
    
    @pytest.mark.asyncio
    async def test_get_model_stats_not_found(self, async_client):
        """Тест получения статистики несуществующей модели"""
        with patch('app.database.get_db') as mock_db:
            mock_db.return_value = Mock()
            mock_db.return_value.get.return_value = None
            
            response = await async_client.get("/api/v1/stats/models/999?days=30")
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_system_stats(self, async_client, sample_system_health):
        """Тест получения общей статистики системы"""
        with patch('app.services.SystemHealthService.collect_system_health') as mock_health:
            mock_health.return_value = sample_system_health
            
            with patch('app.database.get_db') as mock_db:
                mock_db.return_value = Mock()
                
                # Мокаем подсчеты
                mock_db.return_value.execute.return_value.scalar.return_value = 5
                
                response = await async_client.get("/api/v1/stats/system")
                
                assert response.status_code == 200
                data = response.json()
                assert "total_models" in data
                assert "active_models" in data
                assert "system_health" in data
                assert data["system_health"]["cpu_usage"] == 45.2


class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    @pytest.mark.asyncio
    async def test_create_ab_test_error(self, async_client):
        """Тест обработки ошибки при создании A/B теста"""
        with patch('app.services.ABTestingService.create_ab_test') as mock_create:
            mock_create.side_effect = Exception("Test error")
            
            test_data = {
                "name": "Test AB Test",
                "model_id": 1,
                "variant_a": "llama2:7b",
                "variant_b": "llama2:13b"
            }
            
            response = await async_client.post("/api/v1/ab-tests", json=test_data)
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_optimize_model_error(self, async_client):
        """Тест обработки ошибки при оптимизации"""
        with patch('app.services.AutoOptimizationService.optimize_model') as mock_optimize:
            mock_optimize.side_effect = Exception("Optimization failed")
            
            optimization_data = {
                "model_id": 1,
                "optimization_type": "performance"
            }
            
            response = await async_client.post("/api/v1/optimization", json=optimization_data)
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_assess_quality_error(self, async_client):
        """Тест обработки ошибки при оценке качества"""
        with patch('app.services.QualityAssessmentService.assess_quality') as mock_assess:
            mock_assess.side_effect = Exception("Assessment failed")
            
            assessment_data = {
                "model_id": 1,
                "request_text": "Test",
                "response_text": "Test"
            }
            
            response = await async_client.post("/api/v1/quality/assess", json=assessment_data)
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data


class TestValidation:
    """Тесты валидации данных"""
    
    @pytest.mark.asyncio
    async def test_create_ab_test_validation(self, async_client):
        """Тест валидации данных A/B теста"""
        # Неполные данные
        test_data = {
            "name": "Test"  # Отсутствуют обязательные поля
        }
        
        response = await async_client.post("/api/v1/ab-tests", json=test_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_optimize_model_validation(self, async_client):
        """Тест валидации данных оптимизации"""
        # Неверные данные
        optimization_data = {
            "model_id": "invalid",  # Должно быть int
            "optimization_type": "invalid_type"
        }
        
        response = await async_client.post("/api/v1/optimization", json=optimization_data)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_assess_quality_validation(self, async_client):
        """Тест валидации данных оценки качества"""
        # Пустые данные
        assessment_data = {
            "model_id": 1,
            "request_text": "",  # Пустой текст
            "response_text": ""
        }
        
        response = await async_client.post("/api/v1/quality/assess", json=assessment_data)
        
        assert response.status_code == 422


class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_ab_test_workflow(self, async_client):
        """Тест полного workflow A/B тестирования"""
        # 1. Создание A/B теста
        with patch('app.services.ABTestingService.create_ab_test') as mock_create:
            mock_create.return_value = sample_ab_test
            
            test_data = {
                "name": "Integration Test",
                "model_id": 1,
                "variant_a": "llama2:7b",
                "variant_b": "llama2:13b",
                "traffic_split": 0.5
            }
            
            response = await async_client.post("/api/v1/ab-tests", json=test_data)
            assert response.status_code == 200
            test_id = response.json()["id"]
        
        # 2. Выбор модели
        with patch('app.services.ABTestingService.select_model_for_request') as mock_select:
            mock_select.return_value = ("llama2:13b", "variant_b")
            
            data = {"request_type": "test", "user_id": "user_123"}
            response = await async_client.post(f"/api/v1/ab-tests/{test_id}/select-model", json=data)
            assert response.status_code == 200
        
        # 3. Запись результатов
        with patch('app.services.ABTestingService.record_ab_test_result') as mock_record:
            mock_record.return_value = None
            
            data = {
                "model_variant": "llama2:13b",
                "metrics": {"response_time": 2.0, "success": True}
            }
            response = await async_client.post(f"/api/v1/ab-tests/{test_id}/record-result", json=data)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_optimization_and_quality_workflow(self, async_client):
        """Тест workflow оптимизации и оценки качества"""
        # 1. Запуск оптимизации
        with patch('app.services.AutoOptimizationService.optimize_model') as mock_optimize:
            mock_optimize.return_value = sample_optimization
            
            optimization_data = {
                "model_id": 1,
                "optimization_type": "performance"
            }
            
            response = await async_client.post("/api/v1/optimization", json=optimization_data)
            assert response.status_code == 200
            optimization_id = response.json()["id"]
        
        # 2. Оценка качества
        with patch('app.services.QualityAssessmentService.assess_quality') as mock_assess:
            mock_assess.return_value = sample_quality_assessment
            
            assessment_data = {
                "model_id": 1,
                "request_text": "Test request",
                "response_text": "Test response"
            }
            
            response = await async_client.post("/api/v1/quality/assess", json=assessment_data)
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 