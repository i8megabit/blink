"""
📊 Мониторинг и анализ эффективности для всех микросервисов
"""

import time
import asyncio
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge
import structlog

from .config import get_settings

logger = structlog.get_logger()

# Глобальный экземпляр монитора
_service_monitor: Optional['ServiceMonitor'] = None

class ServiceMonitor:
    """Мониторинг эффективности сервиса"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Метрики Prometheus
        self.request_counter = Counter(
            'service_requests_total',
            'Total number of requests',
            ['service', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'service_request_duration_seconds',
            'Request duration in seconds',
            ['service', 'endpoint']
        )
        
        self.active_connections = Gauge(
            'service_active_connections',
            'Number of active connections',
            ['service']
        )
        
        # Внутренние метрики
        self._request_times: Dict[str, float] = {}
        self._effectiveness_scores: Dict[str, float] = {}
        
        logger.info("Service monitor initialized", service=self.settings.SERVICE_NAME)
    
    async def track_request(
        self, 
        endpoint: str, 
        request_id: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Отслеживание запроса"""
        
        start_time = time.time()
        self._request_times[request_id] = start_time
        
        # Увеличение счетчика активных соединений
        self.active_connections.labels(service=self.settings.SERVICE_NAME).inc()
        
        logger.debug(
            "Request tracking started",
            request_id=request_id,
            endpoint=endpoint,
            service=self.settings.SERVICE_NAME
        )
        
        return {
            "request_id": request_id,
            "start_time": start_time,
            "endpoint": endpoint,
            "context": context
        }
    
    async def complete_request(
        self, 
        request_id: str, 
        status: str = "success",
        result: Optional[Dict[str, Any]] = None
    ):
        """Завершение запроса"""
        
        if request_id in self._request_times:
            duration = time.time() - self._request_times[request_id]
            
            # Запись метрик
            self.request_counter.labels(
                service=self.settings.SERVICE_NAME,
                endpoint="all",
                status=status
            ).inc()
            
            self.request_duration.labels(
                service=self.settings.SERVICE_NAME,
                endpoint="all"
            ).observe(duration)
            
            # Уменьшение счетчика активных соединений
            self.active_connections.labels(
                service=self.settings.SERVICE_NAME
            ).dec()
            
            # Анализ эффективности
            if result:
                effectiveness = await self._analyze_effectiveness(result)
                self._effectiveness_scores[request_id] = effectiveness
            
            logger.debug(
                "Request completed",
                request_id=request_id,
                duration=duration,
                status=status,
                effectiveness=self._effectiveness_scores.get(request_id, 0.0)
            )
            
            del self._request_times[request_id]
    
    async def _analyze_effectiveness(self, result: Dict[str, Any]) -> float:
        """Анализ эффективности результата"""
        
        # Простая эвристика эффективности
        score = 0.0
        
        # Проверка наличия ответа
        if "response" in result:
            score += 0.3
        
        # Проверка времени ответа
        if "duration" in result and result["duration"] < 5.0:
            score += 0.2
        
        # Проверка качества ответа
        if "quality_score" in result:
            score += result["quality_score"] * 0.5
        
        return min(score, 1.0)
    
    def get_effectiveness_report(self) -> Dict[str, Any]:
        """Получение отчета об эффективности"""
        
        if not self._effectiveness_scores:
            return {"average_effectiveness": 0.0}
        
        avg_effectiveness = sum(self._effectiveness_scores.values()) / len(self._effectiveness_scores)
        
        return {
            "average_effectiveness": avg_effectiveness,
            "total_requests": len(self._effectiveness_scores),
            "effectiveness_distribution": {
                "high": len([s for s in self._effectiveness_scores.values() if s >= 0.8]),
                "medium": len([s for s in self._effectiveness_scores.values() if 0.5 <= s < 0.8]),
                "low": len([s for s in self._effectiveness_scores.values() if s < 0.5])
            }
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        
        return {
            "service": self.settings.SERVICE_NAME,
            "active_connections": self.active_connections.labels(
                service=self.settings.SERVICE_NAME
            )._value.get(),
            "total_requests": self.request_counter.labels(
                service=self.settings.SERVICE_NAME,
                endpoint="all",
                status="success"
            )._value.get(),
            "effectiveness_report": self.get_effectiveness_report()
        }

def get_service_monitor() -> ServiceMonitor:
    """Получение глобального экземпляра монитора"""
    global _service_monitor
    if _service_monitor is None:
        _service_monitor = ServiceMonitor()
    return _service_monitor 