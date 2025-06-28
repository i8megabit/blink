"""
Утилиты для микросервиса LLM Tuning
"""
import asyncio
import json
import hashlib
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import aiohttp
import redis.asyncio as redis
from pydantic import BaseModel, ValidationError
import logging
from functools import wraps
import jwt
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class OllamaClient:
    """Клиент для работы с Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Получение списка доступных моделей"""
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("models", [])
        except Exception as e:
            logger.error(f"Ошибка получения списка моделей: {e}")
            return []
    
    async def generate(
        self, 
        model: str, 
        prompt: str, 
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Генерация ответа от модели"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if system:
            payload["system"] = system
        
        if options:
            payload["options"] = options
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Ошибка генерации: {e}")
            raise
    
    async def create_model(
        self, 
        name: str, 
        modelfile: str
    ) -> bool:
        """Создание новой модели"""
        try:
            async with self.session.post(
                f"{self.base_url}/api/create",
                json={"name": name, "modelfile": modelfile}
            ) as response:
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Ошибка создания модели: {e}")
            return False
    
    async def delete_model(self, name: str) -> bool:
        """Удаление модели"""
        try:
            async with self.session.delete(
                f"{self.base_url}/api/delete",
                json={"name": name}
            ) as response:
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Ошибка удаления модели: {e}")
            return False


class CacheManager:
    """Менеджер кэширования с Redis"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Подключение к Redis"""
        if not self.redis:
            self.redis = redis.from_url(self.redis_url)
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis:
            await self.redis.close()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерация ключа кэша"""
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        try:
            await self.connect()
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Ошибка получения из кэша: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """Установка значения в кэш"""
        try:
            await self.connect()
            serialized = json.dumps(value, default=str)
            return await self.redis.set(key, serialized, ex=expire)
        except Exception as e:
            logger.error(f"Ошибка установки в кэш: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        try:
            await self.connect()
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Очистка кэша по паттерну"""
        try:
            await self.connect()
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return 0


class SecurityUtils:
    """Утилиты безопасности"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.cipher = Fernet(Fernet.generate_key())
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Проверка пароля"""
        return self.hash_password(password) == hashed
    
    def create_token(self, data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """Создание JWT токена"""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка JWT токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError:
            return None
    
    def encrypt_data(self, data: str) -> str:
        """Шифрование данных"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Расшифровка данных"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class ValidationUtils:
    """Утилиты валидации"""
    
    @staticmethod
    def validate_model_name(name: str) -> bool:
        """Валидация имени модели"""
        import re
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, name)) and len(name) <= 100
    
    @staticmethod
    def validate_prompt(prompt: str) -> bool:
        """Валидация промпта"""
        return len(prompt.strip()) > 0 and len(prompt) <= 10000
    
    @staticmethod
    def validate_model_options(options: Dict[str, Any]) -> bool:
        """Валидация опций модели"""
        valid_keys = {
            'temperature', 'top_p', 'top_k', 'repeat_penalty',
            'num_ctx', 'num_predict', 'stop', 'seed'
        }
        
        for key in options:
            if key not in valid_keys:
                return False
        
        return True
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Очистка входного текста"""
        import html
        return html.escape(text.strip())


class MetricsCollector:
    """Сборщик метрик"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
    
    def increment_counter(self, name: str, value: int = 1):
        """Увеличение счетчика"""
        if name not in self.metrics:
            self.metrics[name] = 0
        self.metrics[name] += value
    
    def set_gauge(self, name: str, value: float):
        """Установка значения gauge"""
        self.metrics[name] = value
    
    def record_histogram(self, name: str, value: float):
        """Запись в гистограмму"""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Сброс метрик"""
        self.metrics.clear()


def retry_async(max_attempts: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток асинхронных функций"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
                    logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
            
            raise last_exception
        return wrapper
    return decorator


def cache_result(expire: int = 300):
    """Декоратор для кэширования результатов"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Здесь можно добавить логику кэширования
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def measure_time(func):
    """Декоратор для измерения времени выполнения"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} выполнился за {execution_time:.2f} секунд")
    
    return wrapper


class ConfigValidator:
    """Валидатор конфигурации"""
    
    @staticmethod
    def validate_database_url(url: str) -> bool:
        """Валидация URL базы данных"""
        return url.startswith(('postgresql://', 'postgresql+asyncpg://'))
    
    @staticmethod
    def validate_redis_url(url: str) -> bool:
        """Валидация URL Redis"""
        return url.startswith(('redis://', 'rediss://'))
    
    @staticmethod
    def validate_ollama_url(url: str) -> bool:
        """Валидация URL Ollama"""
        return url.startswith(('http://', 'https://'))


class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Безопасное имя файла"""
        import re
        return re.sub(r'[^\w\-_\.]', '_', filename)
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Получение расширения файла"""
        return filename.split('.')[-1].lower()
    
    @staticmethod
    def is_supported_file_type(filename: str) -> bool:
        """Проверка поддерживаемого типа файла"""
        supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.json'}
        return FileUtils.get_file_extension(filename) in supported_extensions


class TextProcessor:
    """Обработчик текста"""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Разбиение текста на чанки"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            if end < len(text):
                # Ищем ближайший пробел для красивого разбиения
                last_space = chunk.rfind(' ')
                if last_space > chunk_size - 200:  # Если пробел не слишком далеко
                    end = start + last_space
                    chunk = text[start:end]
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Извлечение ключевых слов"""
        import re
        from collections import Counter
        
        # Удаляем пунктуацию и приводим к нижнему регистру
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Удаляем стоп-слова
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Подсчитываем частоту
        word_freq = Counter(words)
        
        return [word for word, freq in word_freq.most_common(max_keywords)]
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Вычисление схожести текстов"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio()


# Глобальные экземпляры
ollama_client = OllamaClient()
cache_manager = CacheManager("redis://localhost:6379")
security_utils = SecurityUtils("your-secret-key")
metrics_collector = MetricsCollector() 