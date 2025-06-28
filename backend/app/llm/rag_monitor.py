"""
Мониторинг RAG операций
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
import threading

logger = logging.getLogger(__name__)

@dataclass
class RAGMetrics:
    """Метрики RAG операций"""
    embedding_generations: int = 0
    similarity_searches: int = 0
    context_quality_score: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    errors: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

class RAGMonitor:
    """Мониторинг RAG операций"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = RAGMetrics()
        
        # Детальные метрики
        self.response_times: List[float] = []
        self.error_log: List[Dict[str, Any]] = []
        self.performance_history: List[Dict[str, Any]] = []
        
        # Блокировка для потокобезопасности
        self._lock = threading.Lock()
        
        # Конфигурация мониторинга
        self.max_history_size = 1000
        self.metrics_retention_hours = 24
        
        logger.info("RAGMonitor инициализирован")
    
    def increment_metric(self, metric_name: str, value: int = 1):
        """Увеличение счетчика метрики"""
        with self._lock:
            if hasattr(self.metrics, metric_name):
                current_value = getattr(self.metrics, metric_name)
                if isinstance(current_value, (int, float)):
                    setattr(self.metrics, metric_name, current_value + value)
                else:
                    logger.warning(f"Метрика {metric_name} не является числовой")
            else:
                logger.warning(f"Неизвестная метрика: {metric_name}")
            
            self.metrics.last_updated = datetime.utcnow()
    
    def update_metric(self, metric_name: str, value: Any):
        """Обновление метрики"""
        with self._lock:
            if hasattr(self.metrics, metric_name):
                setattr(self.metrics, metric_name, value)
            else:
                logger.warning(f"Неизвестная метрика: {metric_name}")
            
            self.metrics.last_updated = datetime.utcnow()
    
    def get_metric(self, metric_name: str) -> Any:
        """Получение значения метрики"""
        with self._lock:
            if hasattr(self.metrics, metric_name):
                return getattr(self.metrics, metric_name)
            else:
                logger.warning(f"Неизвестная метрика: {metric_name}")
                return None
    
    def record_response_time(self, response_time: float):
        """Запись времени ответа"""
        with self._lock:
            self.response_times.append(response_time)
            
            # Ограничиваем размер истории
            if len(self.response_times) > self.max_history_size:
                self.response_times = self.response_times[-self.max_history_size:]
            
            # Обновляем среднее время ответа
            if self.response_times:
                self.metrics.avg_response_time = statistics.mean(self.response_times)
            
            self.metrics.last_updated = datetime.utcnow()
    
    def record_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """Запись ошибки"""
        with self._lock:
            error_record = {
                "timestamp": datetime.utcnow(),
                "type": error_type,
                "message": error_message,
                "context": context or {}
            }
            
            self.error_log.append(error_record)
            self.metrics.errors += 1
            
            # Ограничиваем размер лога ошибок
            if len(self.error_log) > self.max_history_size:
                self.error_log = self.error_log[-self.max_history_size:]
            
            self.metrics.last_updated = datetime.utcnow()
            
            logger.error(f"RAG ошибка [{error_type}]: {error_message}")
    
    def record_performance_snapshot(self):
        """Запись снимка производительности"""
        with self._lock:
            snapshot = {
                "timestamp": datetime.utcnow(),
                "metrics": {
                    "embedding_generations": self.metrics.embedding_generations,
                    "similarity_searches": self.metrics.similarity_searches,
                    "cache_hits": self.metrics.cache_hits,
                    "cache_misses": self.metrics.cache_misses,
                    "total_requests": self.metrics.total_requests,
                    "avg_response_time": self.metrics.avg_response_time,
                    "errors": self.metrics.errors
                },
                "uptime": time.time() - self.start_time
            }
            
            self.performance_history.append(snapshot)
            
            # Ограничиваем размер истории
            if len(self.performance_history) > self.max_history_size:
                self.performance_history = self.performance_history[-self.max_history_size:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получение сводки производительности"""
        with self._lock:
            # Вычисляем статистики
            response_time_stats = {}
            if self.response_times:
                response_time_stats = {
                    "min": min(self.response_times),
                    "max": max(self.response_times),
                    "mean": statistics.mean(self.response_times),
                    "median": statistics.median(self.response_times),
                    "p95": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
                    "p99": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else max(self.response_times)
                }
            
            # Вычисляем hit rate
            total_cache_requests = self.metrics.cache_hits + self.metrics.cache_misses
            cache_hit_rate = (self.metrics.cache_hits / total_cache_requests * 100) if total_cache_requests > 0 else 0
            
            # Вычисляем error rate
            total_operations = self.metrics.total_requests + self.metrics.errors
            error_rate = (self.metrics.errors / total_operations * 100) if total_operations > 0 else 0
            
            return {
                "uptime_seconds": time.time() - self.start_time,
                "uptime_human": self._format_uptime(time.time() - self.start_time),
                "total_requests": self.metrics.total_requests,
                "embedding_generations": self.metrics.embedding_generations,
                "similarity_searches": self.metrics.similarity_searches,
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "cache_hit_rate": cache_hit_rate,
                "errors": self.metrics.errors,
                "error_rate": error_rate,
                "response_time_stats": response_time_stats,
                "context_quality_score": self.metrics.context_quality_score,
                "last_updated": self.metrics.last_updated.isoformat()
            }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Получение сводки ошибок"""
        with self._lock:
            if not self.error_log:
                return {
                    "total_errors": 0,
                    "error_types": {},
                    "recent_errors": []
                }
            
            # Группируем ошибки по типам
            error_types = {}
            for error in self.error_log:
                error_type = error["type"]
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Получаем последние ошибки
            recent_errors = self.error_log[-10:]  # Последние 10 ошибок
            
            return {
                "total_errors": len(self.error_log),
                "error_types": error_types,
                "recent_errors": recent_errors
            }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Получение трендов производительности"""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Фильтруем снимки по времени
            recent_snapshots = [
                snapshot for snapshot in self.performance_history
                if snapshot["timestamp"] > cutoff_time
            ]
            
            if not recent_snapshots:
                return {
                    "period_hours": hours,
                    "snapshots_count": 0,
                    "trends": {}
                }
            
            # Вычисляем тренды
            response_times = [s["metrics"]["avg_response_time"] for s in recent_snapshots]
            request_counts = [s["metrics"]["total_requests"] for s in recent_snapshots]
            error_counts = [s["metrics"]["errors"] for s in recent_snapshots]
            
            trends = {
                "response_time": {
                    "min": min(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "trend": "stable"  # Можно добавить логику определения тренда
                },
                "requests": {
                    "total": sum(request_counts),
                    "avg_per_hour": sum(request_counts) / hours if hours > 0 else 0
                },
                "errors": {
                    "total": sum(error_counts),
                    "rate": (sum(error_counts) / sum(request_counts) * 100) if sum(request_counts) > 0 else 0
                }
            }
            
            return {
                "period_hours": hours,
                "snapshots_count": len(recent_snapshots),
                "trends": trends
            }
    
    def reset_metrics(self):
        """Сброс метрик"""
        with self._lock:
            self.metrics = RAGMetrics()
            self.response_times.clear()
            self.error_log.clear()
            self.performance_history.clear()
            self.start_time = time.time()
            
            logger.info("Метрики RAG сброшены")
    
    def cleanup_old_data(self):
        """Очистка старых данных"""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.metrics_retention_hours)
            
            # Очищаем историю производительности
            self.performance_history = [
                snapshot for snapshot in self.performance_history
                if snapshot["timestamp"] > cutoff_time
            ]
            
            # Очищаем лог ошибок
            self.error_log = [
                error for error in self.error_log
                if error["timestamp"] > cutoff_time
            ]
            
            logger.debug(f"Очищены данные старше {self.metrics_retention_hours} часов")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья"""
        with self._lock:
            # Определяем статус на основе метрик
            error_rate = 0
            if self.metrics.total_requests + self.metrics.errors > 0:
                error_rate = self.metrics.errors / (self.metrics.total_requests + self.metrics.errors)
            
            # Определяем статус
            if error_rate > 0.1:  # Больше 10% ошибок
                status = "critical"
            elif error_rate > 0.05:  # Больше 5% ошибок
                status = "warning"
            elif self.metrics.avg_response_time > 10.0:  # Больше 10 секунд
                status = "degraded"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "error_rate": error_rate,
                "avg_response_time": self.metrics.avg_response_time,
                "uptime": time.time() - self.start_time,
                "last_updated": self.metrics.last_updated.isoformat()
            }
    
    def _format_uptime(self, seconds: float) -> str:
        """Форматирование времени работы"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def export_metrics(self) -> Dict[str, Any]:
        """Экспорт всех метрик"""
        with self._lock:
            return {
                "summary": self.get_performance_summary(),
                "errors": self.get_error_summary(),
                "trends": self.get_performance_trends(),
                "health": self.get_health_status(),
                "raw_metrics": {
                    "embedding_generations": self.metrics.embedding_generations,
                    "similarity_searches": self.metrics.similarity_searches,
                    "context_quality_score": self.metrics.context_quality_score,
                    "cache_hits": self.metrics.cache_hits,
                    "cache_misses": self.metrics.cache_misses,
                    "total_requests": self.metrics.total_requests,
                    "avg_response_time": self.metrics.avg_response_time,
                    "errors": self.metrics.errors,
                    "last_updated": self.metrics.last_updated.isoformat()
                }
            } 