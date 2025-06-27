"""
Тесты сервисов микросервиса мониторинга
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from datetime import datetime

from app.services import (
    MetricsCollector, AlertService, HealthCheckService, DashboardService
)
from app.models import (
    SystemMetric, DatabaseMetric, CacheMetric, OllamaMetric,
    Alert, AlertSeverity, AlertStatus, Service, ServiceStatus
)


class TestMetricsCollector:
    """Тесты сборщика метрик"""
    
    @pytest.fixture
    def collector(self):
        """Фикстура сборщика метрик"""
        return MetricsCollector()
    
    @pytest.mark.asyncio
    async def test_initialize(self, collector):
        """Тест инициализации сборщика"""
        redis_client = AsyncMock()
        session = AsyncMock()
        
        await collector.initialize(redis_client, session)
        
        assert collector.redis_client == redis_client
        assert collector.session == session
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, collector):
        """Тест сбора системных метрик"""
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.cpu_count', return_value=8), \
             patch('psutil.getloadavg', return_value=(1.0, 1.5, 2.0)), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk, \
             patch('psutil.net_io_counters') as mock_network:
            
            # Настройка моков
            mock_memory.return_value.percent = 60.0
            mock_disk.return_value.percent = 70.0
            mock_network.return_value.bytes_recv = 1000
            mock_network.return_value.bytes_sent = 500
            
            metrics = await collector.collect_system_metrics()
            
            assert isinstance(metrics, SystemMetric)
            assert metrics.cpu_usage == 50.0
            assert metrics.memory_usage == 60.0
            assert metrics.disk_usage == 70.0
            assert metrics.network_in == 1000
            assert metrics.network_out == 500
            assert metrics.load_average == [1.0, 1.5, 2.0]
    
    @pytest.mark.asyncio
    async def test_collect_database_metrics(self, collector):
        """Тест сбора метрик базы данных"""
        # Настройка моков
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock(
            active_connections=5,
            total_connections=10
        )
        mock_session.execute.return_value = mock_result
        
        collector.session = mock_session
        
        metrics = await collector.collect_database_metrics()
        
        assert isinstance(metrics, DatabaseMetric)
        assert metrics.active_connections == 5
        assert metrics.total_connections == 10
    
    @pytest.mark.asyncio
    async def test_collect_cache_metrics(self, collector):
        """Тест сбора метрик кеша"""
        # Настройка моков
        mock_redis = AsyncMock()
        mock_redis.info.return_value = {
            'keyspace_hits': 100,
            'keyspace_misses': 20,
            'used_memory_human': '50B',
            'evicted_keys': 5
        }
        mock_redis.dbsize.return_value = 1000
        
        collector.redis_client = mock_redis
        
        metrics = await collector.collect_cache_metrics()
        
        assert isinstance(metrics, CacheMetric)
        assert metrics.hit_rate == 83.33  # 100/(100+20)*100
        assert metrics.miss_rate == 16.67  # 100 - hit_rate
        assert metrics.keys_count == 1000
        assert metrics.evictions == 5
    
    @pytest.mark.asyncio
    async def test_collect_ollama_metrics(self, collector):
        """Тест сбора метрик Ollama"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Мок для /api/tags
            mock_response_tags = AsyncMock()
            mock_response_tags.status = 200
            mock_response_tags.json = AsyncMock(return_value={
                'models': [{'name': 'qwen2.5:7b-turbo'}]
            })
            
            # Мок для /api/show
            mock_response_show = AsyncMock()
            mock_response_show.status = 200
            mock_response_show.json = AsyncMock(return_value={
                'size': 2048
            })
            
            mock_session.get.return_value.__aenter__.return_value = mock_response_tags
            mock_session.post.return_value.__aenter__.return_value = mock_response_show
            
            metrics = await collector.collect_ollama_metrics()
            
            assert isinstance(metrics, OllamaMetric)
            assert metrics.model == 'qwen2.5:7b-turbo'
            assert metrics.memory_usage == 2048.0
            assert metrics.value == 1  # количество моделей
    
    @pytest.mark.asyncio
    async def test_collect_all_metrics(self, collector):
        """Тест сбора всех метрик"""
        with patch.object(collector, 'collect_system_metrics') as mock_system, \
             patch.object(collector, 'collect_database_metrics') as mock_db, \
             patch.object(collector, 'collect_cache_metrics') as mock_cache, \
             patch.object(collector, 'collect_ollama_metrics') as mock_ollama:
            
            # Настройка возвращаемых значений
            mock_system.return_value = SystemMetric(
                name="test", value=50.0, cpu_usage=50.0, memory_usage=60.0,
                disk_usage=70.0, network_in=1000, network_out=500, load_average=[1.0]
            )
            mock_db.return_value = DatabaseMetric(
                name="test", value=5, active_connections=5, total_connections=10,
                query_time=0.1, slow_queries=0, errors=0
            )
            mock_cache.return_value = CacheMetric(
                name="test", value=85.0, hit_rate=85.0, miss_rate=15.0,
                memory_usage=50.0, keys_count=1000, evictions=0
            )
            mock_ollama.return_value = OllamaMetric(
                name="test", value=1, model="test", response_time=1.5,
                tokens_per_second=100.0, memory_usage=2048.0,
                requests_per_minute=10, errors=0
            )
            
            metrics = await collector.collect_all_metrics()
            
            assert 'system' in metrics
            assert 'database' in metrics
            assert 'cache' in metrics
            assert 'ollama' in metrics


class TestAlertService:
    """Тесты сервиса алертов"""
    
    @pytest.fixture
    def alert_service(self):
        """Фикстура сервиса алертов"""
        return AlertService()
    
    @pytest.mark.asyncio
    async def test_initialize(self, alert_service):
        """Тест инициализации сервиса алертов"""
        redis_client = AsyncMock()
        
        await alert_service.initialize(redis_client)
        
        assert alert_service.redis_client == redis_client
    
    @pytest.mark.asyncio
    async def test_check_thresholds_cpu_high(self, alert_service):
        """Тест проверки порогов для высокого CPU"""
        metrics = {
            'system': SystemMetric(
                name="test", value=85.0, cpu_usage=85.0, memory_usage=60.0,
                disk_usage=70.0, network_in=1000, network_out=500, load_average=[1.0]
            )
        }
        
        alerts = await alert_service.check_thresholds(metrics)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.name == "High CPU Usage"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.current_value == 85.0
    
    @pytest.mark.asyncio
    async def test_check_thresholds_memory_high(self, alert_service):
        """Тест проверки порогов для высокой памяти"""
        metrics = {
            'system': SystemMetric(
                name="test", value=90.0, cpu_usage=50.0, memory_usage=90.0,
                disk_usage=70.0, network_in=1000, network_out=500, load_average=[1.0]
            )
        }
        
        alerts = await alert_service.check_thresholds(metrics)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.name == "High Memory Usage"
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.current_value == 90.0
    
    @pytest.mark.asyncio
    async def test_check_thresholds_disk_high(self, alert_service):
        """Тест проверки порогов для высокого использования диска"""
        metrics = {
            'system': SystemMetric(
                name="test", value=95.0, cpu_usage=50.0, memory_usage=60.0,
                disk_usage=95.0, network_in=1000, network_out=500, load_average=[1.0]
            )
        }
        
        alerts = await alert_service.check_thresholds(metrics)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.name == "High Disk Usage"
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.current_value == 95.0
    
    @pytest.mark.asyncio
    async def test_check_thresholds_slow_db(self, alert_service):
        """Тест проверки порогов для медленных запросов БД"""
        metrics = {
            'database': DatabaseMetric(
                name="test", value=3.0, active_connections=5, total_connections=10,
                query_time=3.0, slow_queries=0, errors=0
            )
        }
        
        alerts = await alert_service.check_thresholds(metrics)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.name == "Slow Database Queries"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.current_value == 3.0
    
    @pytest.mark.asyncio
    async def test_check_thresholds_low_cache_hit(self, alert_service):
        """Тест проверки порогов для низкого hit rate кеша"""
        metrics = {
            'cache': CacheMetric(
                name="test", value=75.0, hit_rate=75.0, miss_rate=25.0,
                memory_usage=50.0, keys_count=1000, evictions=0
            )
        }
        
        alerts = await alert_service.check_thresholds(metrics)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.name == "Low Cache Hit Rate"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.current_value == 75.0
    
    @pytest.mark.asyncio
    async def test_check_thresholds_ollama_errors(self, alert_service):
        """Тест проверки порогов для ошибок Ollama"""
        metrics = {
            'ollama': OllamaMetric(
                name="test", value=1, model="test", response_time=1.5,
                tokens_per_second=100.0, memory_usage=2048.0,
                requests_per_minute=10, errors=5
            )
        }
        
        alerts = await alert_service.check_thresholds(metrics)
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.name == "Ollama Errors"
        assert alert.severity == AlertSeverity.ERROR
        assert alert.current_value == 5
    
    @pytest.mark.asyncio
    async def test_save_alerts(self, alert_service):
        """Тест сохранения алертов"""
        redis_client = AsyncMock()
        alert_service.redis_client = redis_client
        
        alert = Alert(
            name="Test Alert",
            description="Test description",
            severity=AlertSeverity.WARNING,
            source="system",
            metric_name="cpu_usage",
            threshold=80.0,
            current_value=85.0
        )
        
        await alert_service.save_alerts([alert])
        
        # Проверяем, что Redis методы были вызваны
        assert redis_client.hset.called
        assert redis_client.expire.called
    
    @pytest.mark.asyncio
    async def test_get_alerts(self, alert_service):
        """Тест получения алертов"""
        redis_client = AsyncMock()
        alert_service.redis_client = redis_client
        
        # Мок данных из Redis
        alert_data = {
            'alert:123:test': str({
                'id': 'alert:123:test',
                'name': 'Test Alert',
                'description': 'Test description',
                'severity': 'warning',
                'status': 'active',
                'source': 'system',
                'metric_name': 'cpu_usage',
                'threshold': 80.0,
                'current_value': 85.0,
                'created_at': '2023-01-01T00:00:00'
            })
        }
        redis_client.hgetall.return_value = alert_data
        
        alerts = await alert_service.get_alerts()
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.name == "Test Alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_update_alert_status(self, alert_service):
        """Тест обновления статуса алерта"""
        redis_client = AsyncMock()
        alert_service.redis_client = redis_client
        
        # Мок данных из Redis
        alert_data = {
            'alert:123:test': str({
                'id': 'alert:123:test',
                'name': 'Test Alert',
                'description': 'Test description',
                'severity': 'warning',
                'status': 'active',
                'source': 'system',
                'metric_name': 'cpu_usage',
                'threshold': 80.0,
                'current_value': 85.0,
                'created_at': '2023-01-01T00:00:00'
            })
        }
        redis_client.hgetall.return_value = alert_data
        
        await alert_service.update_alert_status(
            'alert:123:test',
            AlertStatus.RESOLVED
        )
        
        # Проверяем, что Redis метод был вызван для обновления
        assert redis_client.hset.called


class TestHealthCheckService:
    """Тесты сервиса проверки здоровья"""
    
    @pytest.fixture
    def health_checker(self):
        """Фикстура сервиса проверки здоровья"""
        return HealthCheckService()
    
    @pytest.mark.asyncio
    async def test_check_service_health_database(self, health_checker):
        """Тест проверки здоровья базы данных"""
        service_config = {
            "url": "postgresql://test",
            "name": "Test Database"
        }
        
        service = await health_checker.check_service_health("database", service_config)
        
        assert isinstance(service, Service)
        assert service.name == "Test Database"
        assert service.url == "postgresql://test"
        # Пока что возвращает HEALTHY по умолчанию
        assert service.status == ServiceStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_check_service_health_redis(self, health_checker):
        """Тест проверки здоровья Redis"""
        service_config = {
            "url": "redis://redis:6379",
            "name": "Test Redis"
        }
        
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis_class.return_value = mock_redis
            mock_redis.ping = AsyncMock()
            mock_redis.close = AsyncMock()
            
            service = await health_checker.check_service_health("redis", service_config)
            
            assert isinstance(service, Service)
            assert service.name == "Test Redis"
            assert service.status == ServiceStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_check_service_health_ollama(self, health_checker):
        """Тест проверки здоровья Ollama"""
        service_config = {
            "url": "http://ollama:11434/api/tags",
            "name": "Test Ollama"
        }
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            service = await health_checker.check_service_health("ollama", service_config)
            
            assert isinstance(service, Service)
            assert service.name == "Test Ollama"
            assert service.status == ServiceStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_check_all_services(self, health_checker):
        """Тест проверки всех сервисов"""
        with patch.object(health_checker, 'check_service_health') as mock_check:
            mock_check.return_value = Service(
                name="Test Service",
                status=ServiceStatus.HEALTHY,
                url="http://test",
                last_check=datetime.utcnow()
            )
            
            services = await health_checker.check_all_services()
            
            assert len(services) == 3  # database, redis, ollama
            assert all(isinstance(service, Service) for service in services)


class TestDashboardService:
    """Тесты сервиса дашборда"""
    
    @pytest.fixture
    def dashboard_service(self):
        """Фикстура сервиса дашборда"""
        return DashboardService()
    
    @pytest.mark.asyncio
    async def test_initialize(self, dashboard_service):
        """Тест инициализации сервиса дашборда"""
        redis_client = AsyncMock()
        
        await dashboard_service.initialize(redis_client)
        
        assert dashboard_service.redis_client == redis_client
    
    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, dashboard_service):
        """Тест получения данных дашборда"""
        redis_client = AsyncMock()
        dashboard_service.redis_client = redis_client
        
        # Мок данных из Redis
        redis_client.get.return_value = "test_metrics"
        redis_client.hgetall.return_value = {"alert1": "data1", "alert2": "data2"}
        
        data = await dashboard_service.get_dashboard_data()
        
        assert "metrics" in data
        assert "alerts_count" in data
        assert "services" in data
        assert "timestamp" in data
        assert data["alerts_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_dashboard_data_error(self, dashboard_service):
        """Тест получения данных дашборда при ошибке"""
        redis_client = AsyncMock()
        redis_client.get.side_effect = Exception("Redis error")
        dashboard_service.redis_client = redis_client
        
        data = await dashboard_service.get_dashboard_data()
        
        assert data["metrics"] is None
        assert data["alerts_count"] == 0
        assert data["services"] is None
        assert "timestamp" in data


# Интеграционные тесты
class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_metrics_collection_flow(self):
        """Тест полного цикла сбора метрик"""
        collector = MetricsCollector()
        alert_service = AlertService()
        
        # Инициализация
        redis_client = AsyncMock()
        await collector.initialize(redis_client, None)
        await alert_service.initialize(redis_client)
        
        # Сбор метрик
        with patch.object(collector, 'collect_system_metrics') as mock_system:
            mock_system.return_value = SystemMetric(
                name="test", value=85.0, cpu_usage=85.0, memory_usage=60.0,
                disk_usage=70.0, network_in=1000, network_out=500, load_average=[1.0]
            )
            
            metrics = await collector.collect_all_metrics()
            
            # Проверка алертов
            alerts = await alert_service.check_thresholds(metrics)
            
            assert len(alerts) == 1
            assert alerts[0].name == "High CPU Usage"
    
    @pytest.mark.asyncio
    async def test_alert_persistence_flow(self):
        """Тест цикла сохранения алертов"""
        alert_service = AlertService()
        redis_client = AsyncMock()
        await alert_service.initialize(redis_client)
        
        # Создание алерта
        alert = Alert(
            name="Test Alert",
            description="Test description",
            severity=AlertSeverity.WARNING,
            source="system",
            metric_name="cpu_usage",
            threshold=80.0,
            current_value=85.0
        )
        
        # Сохранение
        await alert_service.save_alerts([alert])
        
        # Получение
        redis_client.hgetall.return_value = {
            alert.id: str(alert.dict())
        }
        
        alerts = await alert_service.get_alerts()
        
        assert len(alerts) == 1
        assert alerts[0].name == "Test Alert" 