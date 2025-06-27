"""
Сервисы для микросервиса мониторинга
"""

import asyncio
import time
import psutil
import aiohttp
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .config import settings
from .models import (
    SystemMetric, DatabaseMetric, CacheMetric, OllamaMetric, HTTPMetric,
    Alert, Service, ServiceStatus, AlertSeverity, AlertStatus
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Сборщик метрик"""
    
    def __init__(self):
        self.redis_client = None
        self.session = None
    
    async def initialize(self, redis_client, session: AsyncSession):
        """Инициализация сервиса"""
        self.redis_client = redis_client
        self.session = session
    
    async def collect_system_metrics(self) -> SystemMetric:
        """Сбор системных метрик"""
        try:
            # CPU метрики
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg()
            
            # Память
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Диск
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Сеть
            network = psutil.net_io_counters()
            network_in = network.bytes_recv
            network_out = network.bytes_sent
            
            return SystemMetric(
                name="system_metrics",
                value=cpu_percent,
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                disk_usage=disk_percent,
                network_in=network_in,
                network_out=network_out,
                load_average=list(load_avg),
                labels={
                    "host": "monitoring-service",
                    "cpu_count": str(cpu_count)
                }
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            raise
    
    async def collect_database_metrics(self) -> DatabaseMetric:
        """Сбор метрик базы данных"""
        try:
            if not self.session:
                raise ValueError("Database session not initialized")
            
            # Проверка подключения
            result = await self.session.execute(text("SELECT 1"))
            await result.fetchone()
            
            # Получение статистики подключений
            result = await self.session.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """))
            stats = result.fetchone()
            
            # Получение статистики запросов
            result = await self.session.execute(text("""
                SELECT 
                    avg(total_time) as avg_query_time,
                    count(*) FILTER (WHERE total_time > 1000) as slow_queries
                FROM pg_stat_statements 
                WHERE calls > 0
            """))
            query_stats = result.fetchone()
            
            return DatabaseMetric(
                name="database_metrics",
                value=stats.active_connections,
                active_connections=stats.active_connections,
                total_connections=stats.total_connections,
                query_time=query_stats.avg_query_time or 0.0,
                slow_queries=query_stats.slow_queries or 0,
                errors=0,  # TODO: добавить подсчет ошибок
                labels={"database": "seo_db"}
            )
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            raise
    
    async def collect_cache_metrics(self) -> CacheMetric:
        """Сбор метрик кеша"""
        try:
            if not self.redis_client:
                raise ValueError("Redis client not initialized")
            
            # Получение статистики Redis
            info = await self.redis_client.info()
            
            # Расчет hit rate
            keyspace_hits = int(info.get('keyspace_hits', 0))
            keyspace_misses = int(info.get('keyspace_misses', 0))
            total_requests = keyspace_hits + keyspace_misses
            
            hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0
            miss_rate = 100 - hit_rate
            
            # Использование памяти
            memory_usage = float(info.get('used_memory_human', '0B').replace('B', ''))
            
            # Количество ключей
            keys_count = await self.redis_client.dbsize()
            
            # Количество вытеснений
            evictions = int(info.get('evicted_keys', 0))
            
            return CacheMetric(
                name="cache_metrics",
                value=hit_rate,
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                memory_usage=memory_usage,
                keys_count=keys_count,
                evictions=evictions,
                labels={"cache": "redis"}
            )
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
            raise
    
    async def collect_ollama_metrics(self) -> OllamaMetric:
        """Сбор метрик Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                # Получение информации о моделях
                async with session.get(f"{settings.ollama.url}/api/tags") as response:
                    if response.status == 200:
                        models_data = await response.json()
                        models = models_data.get('models', [])
                        
                        if models:
                            model = models[0]  # Берем первую модель
                            model_name = model.get('name', 'unknown')
                            
                            # Получение детальной информации о модели
                            async with session.post(
                                f"{settings.ollama.url}/api/show",
                                json={"name": model_name}
                            ) as show_response:
                                if show_response.status == 200:
                                    model_info = await show_response.json()
                                    
                                    return OllamaMetric(
                                        name="ollama_metrics",
                                        value=len(models),
                                        model=model_name,
                                        response_time=0.0,  # TODO: измерить реальное время
                                        tokens_per_second=0.0,  # TODO: измерить
                                        memory_usage=float(model_info.get('size', 0)),
                                        requests_per_minute=0,  # TODO: подсчитать
                                        errors=0,
                                        labels={"ollama_url": settings.ollama.url}
                                    )
            
            # Если не удалось получить данные
            return OllamaMetric(
                name="ollama_metrics",
                value=0,
                model="unknown",
                response_time=0.0,
                tokens_per_second=0.0,
                memory_usage=0.0,
                requests_per_minute=0,
                errors=1,
                labels={"ollama_url": settings.ollama.url}
            )
        except Exception as e:
            logger.error(f"Error collecting Ollama metrics: {e}")
            raise
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Сбор всех метрик"""
        try:
            metrics = {}
            
            # Системные метрики
            metrics['system'] = await self.collect_system_metrics()
            
            # Метрики базы данных
            try:
                metrics['database'] = await self.collect_database_metrics()
            except Exception as e:
                logger.warning(f"Failed to collect database metrics: {e}")
            
            # Метрики кеша
            try:
                metrics['cache'] = await self.collect_cache_metrics()
            except Exception as e:
                logger.warning(f"Failed to collect cache metrics: {e}")
            
            # Метрики Ollama
            try:
                metrics['ollama'] = await self.collect_ollama_metrics()
            except Exception as e:
                logger.warning(f"Failed to collect Ollama metrics: {e}")
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting all metrics: {e}")
            raise


class AlertService:
    """Сервис управления алертами"""
    
    def __init__(self):
        self.redis_client = None
        self.alerts: List[Alert] = []
    
    async def initialize(self, redis_client):
        """Инициализация сервиса"""
        self.redis_client = redis_client
    
    async def check_thresholds(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Проверка пороговых значений и создание алертов"""
        alerts = []
        thresholds = settings.monitoring.alert_thresholds
        
        # Проверка системных метрик
        if 'system' in metrics:
            system = metrics['system']
            
            # CPU
            if system.cpu_usage > thresholds['cpu_usage']:
                alerts.append(Alert(
                    name="High CPU Usage",
                    description=f"CPU usage is {system.cpu_usage:.1f}% (threshold: {thresholds['cpu_usage']}%)",
                    severity=AlertSeverity.WARNING if system.cpu_usage < 90 else AlertSeverity.CRITICAL,
                    source="system",
                    metric_name="cpu_usage",
                    threshold=thresholds['cpu_usage'],
                    current_value=system.cpu_usage
                ))
            
            # Память
            if system.memory_usage > thresholds['memory_usage']:
                alerts.append(Alert(
                    name="High Memory Usage",
                    description=f"Memory usage is {system.memory_usage:.1f}% (threshold: {thresholds['memory_usage']}%)",
                    severity=AlertSeverity.WARNING if system.memory_usage < 95 else AlertSeverity.CRITICAL,
                    source="system",
                    metric_name="memory_usage",
                    threshold=thresholds['memory_usage'],
                    current_value=system.memory_usage
                ))
            
            # Диск
            if system.disk_usage > thresholds['disk_usage']:
                alerts.append(Alert(
                    name="High Disk Usage",
                    description=f"Disk usage is {system.disk_usage:.1f}% (threshold: {thresholds['disk_usage']}%)",
                    severity=AlertSeverity.WARNING if system.disk_usage < 95 else AlertSeverity.CRITICAL,
                    source="system",
                    metric_name="disk_usage",
                    threshold=thresholds['disk_usage'],
                    current_value=system.disk_usage
                ))
        
        # Проверка метрик базы данных
        if 'database' in metrics:
            db = metrics['database']
            
            if db.query_time > thresholds['response_time']:
                alerts.append(Alert(
                    name="Slow Database Queries",
                    description=f"Average query time is {db.query_time:.2f}s (threshold: {thresholds['response_time']}s)",
                    severity=AlertSeverity.WARNING,
                    source="database",
                    metric_name="query_time",
                    threshold=thresholds['response_time'],
                    current_value=db.query_time
                ))
        
        # Проверка метрик кеша
        if 'cache' in metrics:
            cache = metrics['cache']
            
            if cache.hit_rate < 80:  # Низкий hit rate
                alerts.append(Alert(
                    name="Low Cache Hit Rate",
                    description=f"Cache hit rate is {cache.hit_rate:.1f}% (threshold: 80%)",
                    severity=AlertSeverity.WARNING,
                    source="cache",
                    metric_name="hit_rate",
                    threshold=80.0,
                    current_value=cache.hit_rate
                ))
        
        # Проверка метрик Ollama
        if 'ollama' in metrics:
            ollama = metrics['ollama']
            
            if ollama.errors > 0:
                alerts.append(Alert(
                    name="Ollama Errors",
                    description=f"Ollama has {ollama.errors} errors",
                    severity=AlertSeverity.ERROR,
                    source="ollama",
                    metric_name="errors",
                    threshold=0,
                    current_value=ollama.errors
                ))
        
        return alerts
    
    async def save_alerts(self, alerts: List[Alert]):
        """Сохранение алертов в Redis"""
        try:
            if not self.redis_client:
                return
            
            for alert in alerts:
                alert.id = f"alert:{int(time.time())}:{alert.name}"
                alert_data = alert.dict()
                alert_data['created_at'] = alert.created_at.isoformat()
                
                # Сохранение в Redis с TTL
                await self.redis_client.hset(
                    f"{settings.redis.prefix}alerts",
                    alert.id,
                    str(alert_data)
                )
                
                # Установка TTL для алерта (30 дней)
                await self.redis_client.expire(
                    f"{settings.redis.prefix}alerts",
                    30 * 24 * 3600
                )
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")
    
    async def get_alerts(self, status: Optional[AlertStatus] = None) -> List[Alert]:
        """Получение алертов из Redis"""
        try:
            if not self.redis_client:
                return []
            
            alerts_data = await self.redis_client.hgetall(f"{settings.redis.prefix}alerts")
            alerts = []
            
            for alert_id, alert_str in alerts_data.items():
                try:
                    alert_dict = eval(alert_str)  # Простой способ для демо
                    alert = Alert(**alert_dict)
                    
                    if status is None or alert.status == status:
                        alerts.append(alert)
                except Exception as e:
                    logger.warning(f"Error parsing alert {alert_id}: {e}")
            
            return sorted(alerts, key=lambda x: x.created_at, reverse=True)
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    async def update_alert_status(self, alert_id: str, status: AlertStatus, acknowledged_by: Optional[str] = None):
        """Обновление статуса алерта"""
        try:
            if not self.redis_client:
                return
            
            alerts_data = await self.redis_client.hgetall(f"{settings.redis.prefix}alerts")
            
            if alert_id in alerts_data:
                alert_str = alerts_data[alert_id]
                alert_dict = eval(alert_str)
                alert = Alert(**alert_dict)
                
                alert.status = status
                if status == AlertStatus.RESOLVED:
                    alert.resolved_at = datetime.utcnow()
                elif status == AlertStatus.ACKNOWLEDGED:
                    alert.acknowledged_by = acknowledged_by
                    alert.acknowledged_at = datetime.utcnow()
                
                # Сохранение обновленного алерта
                await self.redis_client.hset(
                    f"{settings.redis.prefix}alerts",
                    alert_id,
                    str(alert.dict())
                )
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")


class HealthCheckService:
    """Сервис проверки здоровья"""
    
    def __init__(self):
        self.services = {
            "database": {
                "url": settings.database.url,
                "name": "PostgreSQL Database"
            },
            "redis": {
                "url": f"redis://{settings.redis.host}:{settings.redis.port}",
                "name": "Redis Cache"
            },
            "ollama": {
                "url": f"{settings.ollama.url}/api/tags",
                "name": "Ollama LLM"
            }
        }
    
    async def check_service_health(self, service_name: str, service_config: Dict[str, str]) -> Service:
        """Проверка здоровья конкретного сервиса"""
        start_time = time.time()
        
        try:
            if service_name == "database":
                # Проверка базы данных
                # TODO: реализовать проверку через SQLAlchemy
                status = ServiceStatus.HEALTHY
                response_time = time.time() - start_time
                
            elif service_name == "redis":
                # Проверка Redis
                try:
                    r = redis.Redis(
                        host=settings.redis.host,
                        port=settings.redis.port,
                        db=settings.redis.db,
                        password=settings.redis.password
                    )
                    await r.ping()
                    status = ServiceStatus.HEALTHY
                    response_time = time.time() - start_time
                    await r.close()
                except Exception:
                    status = ServiceStatus.DOWN
                    response_time = None
            
            elif service_name == "ollama":
                # Проверка Ollama
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(service_config["url"], timeout=5) as response:
                            if response.status == 200:
                                status = ServiceStatus.HEALTHY
                                response_time = time.time() - start_time
                            else:
                                status = ServiceStatus.DEGRADED
                                response_time = None
                except Exception:
                    status = ServiceStatus.DOWN
                    response_time = None
            
            else:
                status = ServiceStatus.UNKNOWN
                response_time = None
            
            return Service(
                name=service_config["name"],
                status=status,
                url=service_config["url"],
                response_time=response_time,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error checking {service_name} health: {e}")
            return Service(
                name=service_config["name"],
                status=ServiceStatus.DOWN,
                url=service_config["url"],
                last_check=datetime.utcnow()
            )
    
    async def check_all_services(self) -> List[Service]:
        """Проверка всех сервисов"""
        tasks = []
        for service_name, service_config in self.services.items():
            task = self.check_service_health(service_name, service_config)
            tasks.append(task)
        
        services = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтрация исключений
        valid_services = []
        for service in services:
            if isinstance(service, Service):
                valid_services.append(service)
            else:
                logger.error(f"Service check failed: {service}")
        
        return valid_services


class DashboardService:
    """Сервис дашборда"""
    
    def __init__(self):
        self.redis_client = None
    
    async def initialize(self, redis_client):
        """Инициализация сервиса"""
        self.redis_client = redis_client
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Получение данных для дашборда"""
        try:
            # Получение последних метрик
            metrics_data = await self.redis_client.get(f"{settings.redis.prefix}latest_metrics")
            
            # Получение алертов
            alerts_data = await self.redis_client.hgetall(f"{settings.redis.prefix}alerts")
            
            # Получение статистики сервисов
            services_data = await self.redis_client.get(f"{settings.redis.prefix}services_status")
            
            return {
                "metrics": metrics_data,
                "alerts_count": len(alerts_data),
                "services": services_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                "metrics": None,
                "alerts_count": 0,
                "services": None,
                "timestamp": datetime.utcnow().isoformat()
            } 