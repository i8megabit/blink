"""
Приоритизатор запросов для централизованной LLM архитектуры
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Priority(Enum):
    """Уровни приоритета запросов"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4

@dataclass
class PriorityConfig:
    """Конфигурация приоритетов"""
    critical_timeout: float = 30.0  # 30 секунд
    high_timeout: float = 60.0      # 1 минута
    normal_timeout: float = 120.0   # 2 минуты
    low_timeout: float = 300.0      # 5 минут
    background_timeout: float = 600.0  # 10 минут
    
    # Веса для расчета приоритета
    critical_weight: int = 100
    high_weight: int = 80
    normal_weight: int = 50
    low_weight: int = 20
    background_weight: int = 10

@dataclass
class UserTier:
    """Уровень пользователя"""
    tier: str
    priority_boost: float
    max_concurrent_requests: int
    rate_limit: int  # запросов в минуту

class RequestPrioritizer:
    """Приоритизатор запросов"""
    
    def __init__(self, config: Optional[PriorityConfig] = None):
        self.config = config or PriorityConfig()
        
        # Словарь приоритетов
        self.priority_map = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "normal": Priority.NORMAL,
            "low": Priority.LOW,
            "background": Priority.BACKGROUND
        }
        
        # Веса приоритетов
        self.priority_weights = {
            Priority.CRITICAL: self.config.critical_weight,
            Priority.HIGH: self.config.high_weight,
            Priority.NORMAL: self.config.normal_weight,
            Priority.LOW: self.config.low_weight,
            Priority.BACKGROUND: self.config.background_weight
        }
        
        # Таймауты по приоритетам
        self.priority_timeouts = {
            Priority.CRITICAL: self.config.critical_timeout,
            Priority.HIGH: self.config.high_timeout,
            Priority.NORMAL: self.config.normal_timeout,
            Priority.LOW: self.config.low_timeout,
            Priority.BACKGROUND: self.config.background_timeout
        }
        
        # Уровни пользователей
        self.user_tiers = {
            "premium": UserTier("premium", 1.5, 5, 100),
            "standard": UserTier("standard", 1.0, 3, 50),
            "basic": UserTier("basic", 0.8, 2, 20),
            "free": UserTier("free", 0.5, 1, 10)
        }
        
        # История запросов пользователей
        self.user_request_history: Dict[int, list] = {}
        
        # Статистика приоритетов
        self.priority_stats = {priority: 0 for priority in Priority}
        
        logger.info("RequestPrioritizer инициализирован")
    
    def get_priority(self, priority_str: str, user_id: Optional[int] = None, 
                    user_tier: str = "standard") -> int:
        """Получение числового приоритета для запроса"""
        # Получаем базовый приоритет
        base_priority = self.priority_map.get(priority_str.lower(), Priority.NORMAL)
        
        # Получаем базовый вес
        base_weight = self.priority_weights[base_priority]
        
        # Применяем буст пользователя
        user_boost = self.user_tiers.get(user_tier, self.user_tiers["standard"]).priority_boost
        adjusted_weight = int(base_weight * user_boost)
        
        # Добавляем временной фактор (более новые запросы имеют небольшой буст)
        time_boost = int(time.time() % 100)  # Небольшой буст на основе времени
        
        final_priority = adjusted_weight + time_boost
        
        # Обновляем статистику
        self.priority_stats[base_priority] += 1
        
        logger.debug(f"Приоритет для {priority_str} (пользователь {user_id}, tier {user_tier}): {final_priority}")
        return final_priority
    
    def get_timeout(self, priority_str: str) -> float:
        """Получение таймаута для приоритета"""
        priority = self.priority_map.get(priority_str.lower(), Priority.NORMAL)
        return self.priority_timeouts[priority]
    
    def can_process_request(self, user_id: int, user_tier: str = "standard") -> bool:
        """Проверка возможности обработки запроса пользователя"""
        tier = self.user_tiers.get(user_tier, self.user_tiers["standard"])
        
        # Проверяем лимит одновременных запросов
        current_requests = self._get_user_active_requests(user_id)
        if current_requests >= tier.max_concurrent_requests:
            logger.warning(f"Пользователь {user_id} превысил лимит одновременных запросов")
            return False
        
        # Проверяем rate limit
        if not self._check_rate_limit(user_id, tier.rate_limit):
            logger.warning(f"Пользователь {user_id} превысил rate limit")
            return False
        
        return True
    
    def record_request(self, user_id: int, priority: str, timestamp: Optional[datetime] = None):
        """Запись запроса пользователя"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if user_id not in self.user_request_history:
            self.user_request_history[user_id] = []
        
        self.user_request_history[user_id].append({
            "priority": priority,
            "timestamp": timestamp
        })
        
        # Очищаем старые записи (старше 1 часа)
        cutoff_time = timestamp - timedelta(hours=1)
        self.user_request_history[user_id] = [
            req for req in self.user_request_history[user_id]
            if req["timestamp"] > cutoff_time
        ]
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики пользователя"""
        if user_id not in self.user_request_history:
            return {
                "total_requests": 0,
                "requests_by_priority": {},
                "avg_requests_per_hour": 0
            }
        
        requests = self.user_request_history[user_id]
        total_requests = len(requests)
        
        # Группируем по приоритетам
        requests_by_priority = {}
        for req in requests:
            priority = req["priority"]
            requests_by_priority[priority] = requests_by_priority.get(priority, 0) + 1
        
        # Среднее количество запросов в час
        if requests:
            time_span = (requests[-1]["timestamp"] - requests[0]["timestamp"]).total_seconds() / 3600
            avg_requests_per_hour = total_requests / max(time_span, 1)
        else:
            avg_requests_per_hour = 0
        
        return {
            "total_requests": total_requests,
            "requests_by_priority": requests_by_priority,
            "avg_requests_per_hour": avg_requests_per_hour
        }
    
    def get_priority_stats(self) -> Dict[str, Any]:
        """Получение статистики приоритетов"""
        total_requests = sum(self.priority_stats.values())
        
        stats = {}
        for priority, count in self.priority_stats.items():
            percentage = (count / total_requests * 100) if total_requests > 0 else 0
            stats[priority.name.lower()] = {
                "count": count,
                "percentage": percentage,
                "timeout": self.priority_timeouts[priority]
            }
        
        return {
            "total_requests": total_requests,
            "priorities": stats
        }
    
    def optimize_priorities(self):
        """Оптимизация приоритетов на основе статистики"""
        stats = self.get_priority_stats()
        
        # Если слишком много критических запросов, снижаем их приоритет
        critical_percentage = stats["priorities"].get("critical", {}).get("percentage", 0)
        if critical_percentage > 20:  # Больше 20% критических запросов
            logger.warning(f"Слишком много критических запросов: {critical_percentage:.1f}%")
            # Можно добавить логику для динамической настройки приоритетов
        
        # Очищаем старые записи пользователей
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        for user_id in list(self.user_request_history.keys()):
            self.user_request_history[user_id] = [
                req for req in self.user_request_history[user_id]
                if req["timestamp"] > cutoff_time
            ]
            
            # Удаляем пустые записи
            if not self.user_request_history[user_id]:
                del self.user_request_history[user_id]
    
    def _get_user_active_requests(self, user_id: int) -> int:
        """Получение количества активных запросов пользователя"""
        if user_id not in self.user_request_history:
            return 0
        
        # Считаем запросы за последние 5 минут как активные
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        active_requests = [
            req for req in self.user_request_history[user_id]
            if req["timestamp"] > cutoff_time
        ]
        
        return len(active_requests)
    
    def _check_rate_limit(self, user_id: int, rate_limit: int) -> bool:
        """Проверка rate limit пользователя"""
        if user_id not in self.user_request_history:
            return True
        
        # Считаем запросы за последнюю минуту
        cutoff_time = datetime.utcnow() - timedelta(minutes=1)
        recent_requests = [
            req for req in self.user_request_history[user_id]
            if req["timestamp"] > cutoff_time
        ]
        
        return len(recent_requests) < rate_limit
    
    def get_priority_info(self, priority_str: str) -> Dict[str, Any]:
        """Получение информации о приоритете"""
        priority = self.priority_map.get(priority_str.lower(), Priority.NORMAL)
        
        return {
            "priority": priority.name,
            "weight": self.priority_weights[priority],
            "timeout": self.priority_timeouts[priority],
            "description": self._get_priority_description(priority)
        }
    
    def _get_priority_description(self, priority: Priority) -> str:
        """Получение описания приоритета"""
        descriptions = {
            Priority.CRITICAL: "Критически важные запросы, требующие немедленной обработки",
            Priority.HIGH: "Высокоприоритетные запросы с ограниченным временем ожидания",
            Priority.NORMAL: "Стандартные запросы с обычным приоритетом",
            Priority.LOW: "Низкоприоритетные запросы, могут быть отложены",
            Priority.BACKGROUND: "Фоновые запросы, выполняются при наличии ресурсов"
        }
        
        return descriptions.get(priority, "Неизвестный приоритет")
    
    def update_user_tier(self, user_id: int, new_tier: str):
        """Обновление уровня пользователя"""
        if new_tier not in self.user_tiers:
            logger.warning(f"Неизвестный уровень пользователя: {new_tier}")
            return
        
        logger.info(f"Пользователь {user_id} переведен на уровень {new_tier}")
    
    def get_system_load(self) -> Dict[str, Any]:
        """Получение информации о нагрузке системы"""
        total_users = len(self.user_request_history)
        total_requests = sum(len(requests) for requests in self.user_request_history.values())
        
        # Активные пользователи (за последние 10 минут)
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        active_users = 0
        for requests in self.user_request_history.values():
            if any(req["timestamp"] > cutoff_time for req in requests):
                active_users += 1
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_requests": total_requests,
            "priority_distribution": self.get_priority_stats()
        } 