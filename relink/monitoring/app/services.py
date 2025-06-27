"""
Сервисы микросервиса мониторинга
Сбор метрик, управление алертами, дашборд
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
import aiohttp
import asyncpg
import redis.asyncio as redis
import prometheus_client as prometheus
from prometheus_client import Counter, Histogram, Gauge, Summary
import structlog

from .config import settings
from .models import (
    SystemMetrics, DatabaseMetrics, OllamaMetrics, CacheMetrics, HTTPMetrics,
    Alert, ServiceHealth, DashboardData, MetricData, AlertRule,
    AlertSeverity, AlertStatus, ServiceStatus
)

# Настройка логирования
logger = structlog.get_logger()

# Prometheus метрики
SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU usage percentage')
SYSTEM_MEMORY = Gauge('system_memory_bytes', 'System memory usage in bytes', ['type'])
SYSTEM_DISK = Gauge('system_disk_bytes', 'System disk usage in bytes', ['type'])
SYSTEM_LOAD = Gauge('system_load_average', 'System load average', ['period'])

DATABASE_CONNECTIONS = Gauge('database_connections', 'Database connections', ['status'])
DATABASE_QUERIES = Counter('database_queries_total', 'Database queries', ['operation', 'status'])
DATABASE_QUERY_TIME = Histogram('database_query_duration_seconds', 'Database query duration')

OLLAMA_REQUESTS = Counter('ollama_requests_total', 'Ollama requests', ['model', 'status'])
OLLAMA_RESPONSE_TIME = Histogram('ollama_response_duration_seconds', 'Ollama response time')
OLLAMA_MEMORY = Gauge('ollama_memory_bytes', 'Ollama memory usage')

CACHE_OPERATIONS = Counter('cache_operations_total', 'Cache operations', ['operation', 'status'])
CACHE_HIT_RATIO = Gauge('cache_hit_ratio', 'Cache hit ratio')
CACHE_MEMORY = Gauge('cache_memory_bytes', 'Cache memory usage')

HTTP_REQUESTS = Counter('http_requests_total', 'HTTP requests', ['method', 'endpoint', 'status'])
HTTP_RESPONSE_TIME = Histogram('http_response_duration_seconds', 'HTTP response time')
HTTP_ACTIVE_REQUESTS = Gauge('http_active_requests', 'Active HTTP requests')

ALERTS_TOTAL = Counter('alerts_total', 'Total alerts', ['severity', 'status'])


class MetricsCollector:
    """Сборщик метрик системы"""
    
    def __init__(self):
        self.start_time = time.time()
        self._cache = {}
        self._last_collection = {}
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Сбор системных метрик"""
        try:
            import psutil
            
            # CPU метрики
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else None
            
            # Память
            memory = psutil.virtual_memory()
            
            # Диск
            disk = psutil.disk_usage('/')
            
            # Сеть
            network = psutil.net_io_counters()
            
            # Загрузка системы
            load_avg = psutil.getloadavg()
            
            # Обновление Prometheus метрик
            SYSTEM_CPU.set(cpu_percent)
            SYSTEM_MEMORY.labels(type="total").set(memory.total)
            SYSTEM_MEMORY.labels(type="used").set(memory.used)
            SYSTEM_MEMORY.labels(type="available").set(memory.available)
            SYSTEM_DISK.labels(type="total").set(disk.total)
            SYSTEM_DISK.labels(type="used").set(disk.used)
            SYSTEM_DISK.labels(type="free").set(disk.free)
            SYSTEM_LOAD.labels(period="1m").set(load_avg[0])
            SYSTEM_LOAD.labels(period="5m").set(load_avg[1])
            SYSTEM_LOAD.labels(period="15m").set(load_avg[2])
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                cpu_freq=cpu_freq,
                memory_total=memory.total,
                memory_available=memory.available,
                memory_used=memory.used,
                memory_percent=memory.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_free=disk.free,
                disk_percent=(disk.used / disk.total) * 100,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                network_packets_sent=network.packets_sent,
                network_packets_recv=network.packets_recv,
                load_average_1m=load_avg[0],
                load_average_5m=load_avg[1],
                load_average_15m=load_avg[2]
            )
            
            logger.debug("System metrics collected", cpu_percent=cpu_percent, memory_percent=memory.percent)
            return metrics
            
        except ImportError:
            logger.warning("psutil not available, system metrics disabled")
            return None
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    async def collect_database_metrics(self) -> DatabaseMetrics:
        """Сбор метрик базы данных"""
        try:
            # Подключение к БД
            conn = await asyncpg.connect(settings.database.url)
            
            # Активные подключения
            active_connections = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )
            
            # Максимальные подключения
            max_connections = await conn.fetchval("SHOW max_connections")
            
            # Статистика запросов
            queries_stats = await conn.fetchrow("""
                SELECT 
                    sum(calls) as total_calls,
                    sum(total_time) as total_time,
                    avg(mean_time) as avg_time
                FROM pg_stat_statements
            """)
            
            # Размер БД
            db_size = await conn.fetchval("""
                SELECT pg_database_size(current_database())
            """)
            
            # Размеры таблиц
            table_sizes = await conn.fetch("""
                SELECT 
                    schemaname || '.' || tablename as table_name,
                    pg_total_relation_size(schemaname || '.' || tablename) as size
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY size DESC
                LIMIT 10
            """)
            
            await conn.close()
            
            # Обновление Prometheus метрик
            DATABASE_CONNECTIONS.labels(status="active").set(active_connections)
            DATABASE_CONNECTIONS.labels(status="max").set(int(max_connections))
            
            metrics = DatabaseMetrics(
                active_connections=active_connections,
                max_connections=int(max_connections),
                connection_usage_percent=(active_connections / int(max_connections)) * 100,
                queries_per_second=queries_stats['total_calls'] / 60 if queries_stats['total_calls'] else 0,
                slow_queries=0,  # TODO: реализовать отслеживание медленных запросов
                avg_query_time=queries_stats['avg_time'] or 0,
                database_size=db_size,
                table_sizes={row['table_name']: row['size'] for row in table_sizes},
                cache_hit_ratio=0,  # TODO: реализовать отслеживание кэша БД
                cache_size=0
            )
            
            logger.debug("Database metrics collected", active_connections=active_connections)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return None
    
    async def collect_ollama_metrics(self) -> OllamaMetrics:
        """Сбор метрик Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                # Проверка статуса
                try:
                    async with session.get(f"{settings.ollama.url}/api/tags") as response:
                        if response.status == 200:
                            status = ServiceStatus.HEALTHY
                            models_data = await response.json()
                            models_loaded = [model['name'] for model in models_data.get('models', [])]
                        else:
                            status = ServiceStatus.DOWN
                            models_loaded = []
                except Exception:
                    status = ServiceStatus.DOWN
                    models_loaded = []
                
                # Метрики производительности (упрощенные)
                requests_per_second = 0  # TODO: реализовать отслеживание
                avg_response_time = 0
                total_requests = 0
                failed_requests = 0
                
                # Ресурсы (упрощенные)
                memory_usage = 0  # TODO: получить через API
                cpu_usage = 0
                
                # Обновление Prometheus метрик
                OLLAMA_MEMORY.set(memory_usage)
                
                metrics = OllamaMetrics(
                    status=status,
                    models_loaded=models_loaded,
                    requests_per_second=requests_per_second,
                    avg_response_time=avg_response_time,
                    total_requests=total_requests,
                    failed_requests=failed_requests,
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                    model_metrics={}
                )
                
                logger.debug("Ollama metrics collected", status=status, models_count=len(models_loaded))
                return metrics
                
        except Exception as e:
            logger.error(f"Error collecting Ollama metrics: {e}")
            return None
    
    async def collect_cache_metrics(self) -> CacheMetrics:
        """Сбор метрик кэша"""
        try:
            # Подключение к Redis
            redis_client = redis.from_url(settings.redis.url)
            
            # Базовая информация
            info = await redis_client.info()
            
            # Статистика памяти
            memory_used = info.get('used_memory', 0)
            memory_peak = info.get('used_memory_peak', 0)
            keys_total = info.get('db0', {}).get('keys', 0) if 'db0' in info else 0
            evicted_keys = info.get('evicted_keys', 0)
            
            # Hit/Miss статистика (упрощенно)
            cache_hits = 0  # TODO: реализовать отслеживание
            cache_misses = 0
            cache_hit_ratio = 0 if (cache_hits + cache_misses) == 0 else (cache_hits / (cache_hits + cache_misses)) * 100
            
            # Операции
            operations_per_second = info.get('instantaneous_ops_per_sec', 0)
            avg_operation_time = 0  # TODO: реализовать отслеживание
            
            await redis_client.close()
            
            # Обновление Prometheus метрик
            CACHE_MEMORY.set(memory_used)
            CACHE_HIT_RATIO.set(cache_hit_ratio)
            
            metrics = CacheMetrics(
                redis_connected=True,
                redis_memory_used=memory_used,
                redis_memory_peak=memory_peak,
                redis_keys_total=keys_total,
                redis_evicted_keys=evicted_keys,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                cache_hit_ratio=cache_hit_ratio,
                operations_per_second=operations_per_second,
                avg_operation_time=avg_operation_time
            )
            
            logger.debug("Cache metrics collected", memory_used=memory_used, hit_ratio=cache_hit_ratio)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
            return None
    
    async def collect_http_metrics(self) -> HTTPMetrics:
        """Сбор HTTP метрик"""
        try:
            # Получение метрик из Prometheus
            metrics_data = prometheus.generate_latest().decode()
            
            # Парсинг метрик (упрощенно)
            total_requests = 0
            requests_per_second = 0
            active_requests = 0
            status_codes = {}
            error_rate = 0
            avg_response_time = 0
            p95_response_time = 0
            p99_response_time = 0
            avg_request_size = 0
            avg_response_size = 0
            
            # Обновление метрик
            metrics = HTTPMetrics(
                total_requests=total_requests,
                requests_per_second=requests_per_second,
                active_requests=active_requests,
                status_codes=status_codes,
                error_rate=error_rate,
                avg_response_time=avg_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                avg_request_size=avg_request_size,
                avg_response_size=avg_response_size
            )
            
            logger.debug("HTTP metrics collected")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting HTTP metrics: {e}")
            return None


class AlertManager:
    """Менеджер алертов"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.rules: List[AlertRule] = []
        self._alert_cooldowns: Dict[str, float] = {}
    
    def add_rule(self, rule: AlertRule):
        """Добавление правила алерта"""
        self.rules.append(rule)
        logger.info(f"Alert rule added: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Удаление правила алерта"""
        self.rules = [rule for rule in self.rules if rule.id != rule_id]
        logger.info(f"Alert rule removed: {rule_id}")
    
    def check_alerts(self, metrics: Dict[str, Any]):
        """Проверка условий алертов"""
        current_time = time.time()
        new_alerts = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Проверка cooldown
            cooldown_key = f"{rule.metric_name}_{rule.condition}_{rule.threshold}"
            if cooldown_key in self._alert_cooldowns:
                if current_time - self._alert_cooldowns[cooldown_key] < settings.monitoring.alert_cooldown:
                    continue
            
            # Получение значения метрики
            metric_value = self._get_metric_value(rule.metric_name, metrics)
            if metric_value is None:
                continue
            
            # Проверка условия
            if self._check_condition(metric_value, rule.condition, rule.threshold):
                # Создание алерта
                alert = Alert(
                    title=f"Alert: {rule.name}",
                    message=f"Metric {rule.metric_name} = {metric_value} {rule.condition} {rule.threshold}",
                    severity=rule.severity,
                    source="monitoring",
                    service="system",
                    metric_name=rule.metric_name,
                    metric_value=metric_value,
                    threshold=rule.threshold,
                    labels={"rule_id": rule.id}
                )
                
                new_alerts.append(alert)
                self._alert_cooldowns[cooldown_key] = current_time
                
                # Обновление Prometheus метрик
                ALERTS_TOTAL.labels(severity=rule.severity.value, status="active").inc()
                
                logger.warning(
                    f"Alert triggered: {rule.name}",
                    metric=rule.metric_name,
                    value=metric_value,
                    threshold=rule.threshold
                )
        
        self.alerts.extend(new_alerts)
        return new_alerts
    
    def _get_metric_value(self, metric_name: str, metrics: Dict[str, Any]) -> Optional[float]:
        """Получение значения метрики"""
        # Простая реализация - можно расширить
        if metric_name == "cpu_percent" and "system" in metrics:
            return metrics["system"].cpu_percent
        elif metric_name == "memory_percent" and "system" in metrics:
            return metrics["system"].memory_percent
        elif metric_name == "disk_percent" and "system" in metrics:
            return metrics["system"].disk_percent
        return None
    
    def _check_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Проверка условия"""
        if condition == ">":
            return value > threshold
        elif condition == "<":
            return value < threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        return False
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "system"):
        """Разрешение алерта"""
        for alert in self.alerts:
            if alert.id == alert_id and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.acknowledged_by = resolved_by
                
                # Обновление Prometheus метрик
                ALERTS_TOTAL.labels(severity=alert.severity.value, status="resolved").inc()
                
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Подтверждение алерта"""
        for alert in self.alerts:
            if alert.id == alert_id and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = acknowledged_by
                
                # Обновление Prometheus метрик
                ALERTS_TOTAL.labels(severity=alert.severity.value, status="acknowledged").inc()
                
                logger.info(f"Alert acknowledged: {alert_id}")
                return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Получение активных алертов"""
        return [alert for alert in self.alerts if alert.status == AlertStatus.ACTIVE]
    
    def cleanup_old_alerts(self, days: int = 30):
        """Очистка старых алертов"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_date]
        logger.info(f"Cleaned up alerts older than {days} days")


class ServiceHealthChecker:
    """Проверка здоровья сервисов"""
    
    def __init__(self):
        self.services = {
            "backend": {"url": "http://backend:8000/api/v1/health", "timeout": 5},
            "docs": {"url": "http://docs:8001/api/v1/health", "timeout": 5},
            "ollama": {"url": "http://ollama:11434/api/tags", "timeout": 10},
            "redis": {"url": "redis://redis:6379", "timeout": 5},
            "database": {"url": settings.database.url, "timeout": 5}
        }
    
    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Проверка здоровья конкретного сервиса"""
        if service_name not in self.services:
            return ServiceHealth(
                service=service_name,
                status=ServiceStatus.UNKNOWN
            )
        
        service_config = self.services[service_name]
        start_time = time.time()
        
        try:
            if service_name == "redis":
                # Проверка Redis
                redis_client = redis.from_url(service_config["url"])
                await redis_client.ping()
                await redis_client.close()
                status = ServiceStatus.HEALTHY
                response_time = time.time() - start_time
                
            elif service_name == "database":
                # Проверка базы данных
                conn = await asyncpg.connect(service_config["url"])
                await conn.fetchval("SELECT 1")
                await conn.close()
                status = ServiceStatus.HEALTHY
                response_time = time.time() - start_time
                
            else:
                # HTTP проверка
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        service_config["url"],
                        timeout=aiohttp.ClientTimeout(total=service_config["timeout"])
                    ) as response:
                        if response.status == 200:
                            status = ServiceStatus.HEALTHY
                        else:
                            status = ServiceStatus.DEGRADED
                        response_time = time.time() - start_time
                        
        except asyncio.TimeoutError:
            status = ServiceStatus.DOWN
            response_time = service_config["timeout"]
        except Exception as e:
            status = ServiceStatus.DOWN
            response_time = time.time() - start_time
            logger.error(f"Service health check failed for {service_name}: {e}")
        
        return ServiceHealth(
            service=service_name,
            status=status,
            response_time=response_time,
            last_check=datetime.utcnow()
        )
    
    async def check_all_services(self) -> List[ServiceHealth]:
        """Проверка всех сервисов"""
        tasks = [self.check_service_health(service) for service in self.services.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_checks = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = list(self.services.keys())[i]
                health_checks.append(ServiceHealth(
                    service=service_name,
                    status=ServiceStatus.UNKNOWN,
                    last_check=datetime.utcnow()
                ))
            else:
                health_checks.append(result)
        
        return health_checks


class DashboardService:
    """Сервис дашборда"""
    
    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager, health_checker: ServiceHealthChecker):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.health_checker = health_checker
        self.start_time = time.time()
    
    async def get_dashboard_data(self) -> DashboardData:
        """Получение данных для дашборда"""
        # Сбор всех метрик
        system_metrics = await self.metrics_collector.collect_system_metrics()
        database_metrics = await self.metrics_collector.collect_database_metrics()
        ollama_metrics = await self.metrics_collector.collect_ollama_metrics()
        cache_metrics = await self.metrics_collector.collect_cache_metrics()
        http_metrics = await self.metrics_collector.collect_http_metrics()
        
        # Проверка здоровья сервисов
        services_health = await self.health_checker.check_all_services()
        
        # Проверка алертов
        metrics_dict = {
            "system": system_metrics,
            "database": database_metrics,
            "ollama": ollama_metrics,
            "cache": cache_metrics,
            "http": http_metrics
        }
        self.alert_manager.check_alerts(metrics_dict)
        
        # Подсчет статистики
        services_healthy = sum(1 for service in services_health if service.status == ServiceStatus.HEALTHY)
        services_total = len(services_health)
        
        # Определение общего статуса
        if services_healthy == services_total:
            overall_status = ServiceStatus.HEALTHY
        elif services_healthy > 0:
            overall_status = ServiceStatus.DEGRADED
        else:
            overall_status = ServiceStatus.DOWN
        
        # Подсчет алертов по важности
        active_alerts = self.alert_manager.get_active_alerts()
        alerts_count = {}
        for severity in AlertSeverity:
            alerts_count[severity] = sum(1 for alert in active_alerts if alert.severity == severity)
        
        return DashboardData(
            overall_status=overall_status,
            services_healthy=services_healthy,
            services_total=services_total,
            system=system_metrics,
            database=database_metrics,
            ollama=ollama_metrics,
            cache=cache_metrics,
            http=http_metrics,
            active_alerts=active_alerts,
            alerts_count=alerts_count,
            services=services_health
        )


# Создание экземпляров сервисов
metrics_collector = MetricsCollector()
alert_manager = AlertManager()
health_checker = ServiceHealthChecker()
dashboard_service = DashboardService(metrics_collector, alert_manager, health_checker)

# Экспорт для удобства
__all__ = [
    "MetricsCollector",
    "AlertManager", 
    "ServiceHealthChecker",
    "DashboardService",
    "metrics_collector",
    "alert_manager",
    "health_checker",
    "dashboard_service"
] 