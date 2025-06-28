"""
Модуль валидации и обработки ошибок для reLink
Pydantic модели, кастомные валидаторы и централизованная обработка ошибок
"""

import re
import ipaddress
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator, ValidationError
from fastapi import HTTPException, status
import logging

from .exceptions import ValidationException, RelinkBaseException

logger = logging.getLogger(__name__)


class BaseValidationModel(BaseModel):
    """Базовая модель для валидации"""
    
    class Config:
        extra = "forbid"  # Запрещаем дополнительные поля
        validate_assignment = True  # Валидация при присвоении
        json_encoders = {
            # Кастомные энкодеры для JSON
        }


class URLValidator:
    """Валидатор URL"""
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Валидация URL"""
        if not url:
            raise ValidationException("URL не может быть пустым")
        
        # Проверяем формат URL
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValidationException("Неверный формат URL")
            
            # Проверяем схему
            if parsed.scheme not in ['http', 'https']:
                raise ValidationException("URL должен использовать HTTP или HTTPS")
            
            # Проверяем домен
            if not parsed.netloc or '.' not in parsed.netloc:
                raise ValidationException("Неверный домен в URL")
            
            return url
        except Exception as e:
            raise ValidationException(f"Ошибка валидации URL: {str(e)}")
    
    @staticmethod
    def validate_domain(domain: str) -> str:
        """Валидация домена"""
        if not domain:
            raise ValidationException("Домен не может быть пустым")
        
        # Убираем протокол если есть
        domain = domain.replace('http://', '').replace('https://', '')
        
        # Убираем путь если есть
        domain = domain.split('/')[0]
        
        # Проверяем формат домена
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, domain):
            raise ValidationException("Неверный формат домена")
        
        return domain


class EmailValidator:
    """Валидатор email"""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Валидация email"""
        if not email:
            raise ValidationException("Email не может быть пустым")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationException("Неверный формат email")
        
        return email.lower()


class PasswordValidator:
    """Валидатор пароля"""
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Валидация пароля"""
        if not password:
            raise ValidationException("Пароль не может быть пустым")
        
        if len(password) < 8:
            raise ValidationException("Пароль должен содержать минимум 8 символов")
        
        if not re.search(r'[A-Z]', password):
            raise ValidationException("Пароль должен содержать хотя бы одну заглавную букву")
        
        if not re.search(r'[a-z]', password):
            raise ValidationException("Пароль должен содержать хотя бы одну строчную букву")
        
        if not re.search(r'\d', password):
            raise ValidationException("Пароль должен содержать хотя бы одну цифру")
        
        return password


class IPValidator:
    """Валидатор IP адресов"""
    
    @staticmethod
    def validate_ip(ip: str) -> str:
        """Валидация IP адреса"""
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValidationException("Неверный формат IP адреса")
    
    @staticmethod
    def validate_ip_range(ip_range: str) -> str:
        """Валидация диапазона IP адресов"""
        try:
            ipaddress.ip_network(ip_range, strict=False)
            return ip_range
        except ValueError:
            raise ValidationException("Неверный формат диапазона IP адресов")


# Pydantic модели для валидации
class UserRegistrationModel(BaseValidationModel):
    """Модель для регистрации пользователя"""
    email: str = Field(..., description="Email пользователя")
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=8, description="Пароль")
    
    @validator('email')
    def validate_email(cls, v):
        return EmailValidator.validate_email(v)
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValidationException("Имя пользователя может содержать только буквы, цифры и подчеркивания")
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        return PasswordValidator.validate_password(v)


class UserLoginModel(BaseValidationModel):
    """Модель для входа пользователя"""
    email: str = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль")
    
    @validator('email')
    def validate_email(cls, v):
        return EmailValidator.validate_email(v)


class DomainAnalysisModel(BaseValidationModel):
    """Модель для анализа домена"""
    url: str = Field(..., description="URL для анализа")
    depth: int = Field(default=2, ge=1, le=5, description="Глубина анализа")
    include_subdomains: bool = Field(default=False, description="Включить поддомены")
    
    @validator('url')
    def validate_url(cls, v):
        return URLValidator.validate_url(v)
    
    @validator('depth')
    def validate_depth(cls, v):
        if v < 1 or v > 5:
            raise ValidationException("Глубина анализа должна быть от 1 до 5")
        return v


class SEORecommendationModel(BaseValidationModel):
    """Модель для SEO рекомендаций"""
    domain: str = Field(..., description="Домен для анализа")
    keywords: List[str] = Field(default=[], description="Ключевые слова")
    competitor_urls: List[str] = Field(default=[], description="URL конкурентов")
    
    @validator('domain')
    def validate_domain(cls, v):
        return URLValidator.validate_domain(v)
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if len(v) > 20:
            raise ValidationException("Максимум 20 ключевых слов")
        return [kw.strip().lower() for kw in v if kw.strip()]
    
    @validator('competitor_urls')
    def validate_competitor_urls(cls, v):
        validated_urls = []
        for url in v:
            try:
                validated_urls.append(URLValidator.validate_url(url))
            except ValidationException as e:
                logger.warning(f"Invalid competitor URL: {url} - {e}")
        return validated_urls


class ExportModel(BaseValidationModel):
    """Модель для экспорта данных"""
    format: str = Field(..., description="Формат экспорта")
    include_metadata: bool = Field(default=True, description="Включить метаданные")
    compression: bool = Field(default=False, description="Сжатие файла")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'csv', 'xml', 'pdf']
        if v.lower() not in allowed_formats:
            raise ValidationException(f"Поддерживаемые форматы: {', '.join(allowed_formats)}")
        return v.lower()


class PaginationModel(BaseValidationModel):
    """Модель для пагинации"""
    page: int = Field(default=1, ge=1, description="Номер страницы")
    per_page: int = Field(default=20, ge=1, le=100, description="Элементов на странице")
    sort_by: str = Field(default="created_at", description="Поле для сортировки")
    sort_order: str = Field(default="desc", description="Порядок сортировки")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValidationException("Порядок сортировки должен быть 'asc' или 'desc'")
        return v.lower()


# Декораторы для валидации
def validate_request(model_class: type[BaseValidationModel]):
    """Декоратор для валидации запросов"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Валидируем данные
                validated_data = model_class(**kwargs)
                
                # Заменяем kwargs на валидированные данные
                validated_kwargs = validated_data.dict()
                
                # Вызываем функцию с валидированными данными
                return await func(*args, **validated_kwargs)
                
            except ValidationError as e:
                # Преобразуем Pydantic ошибки в наши исключения
                error_messages = []
                for error in e.errors():
                    field = " -> ".join(str(loc) for loc in error["loc"])
                    message = error["msg"]
                    error_messages.append(f"{field}: {message}")
                
                raise ValidationException(
                    message="Ошибка валидации данных",
                    field="request_data",
                    value=error_messages
                )
            except RelinkBaseException:
                raise
            except Exception as e:
                logger.error(f"Unexpected error in validation: {e}")
                raise ValidationException("Внутренняя ошибка валидации")
        
        return wrapper
    return decorator


def validate_response(model_class: type[BaseValidationModel]):
    """Декоратор для валидации ответов"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            try:
                # Валидируем ответ
                if isinstance(result, dict):
                    validated_result = model_class(**result)
                    return validated_result.dict()
                elif isinstance(result, list):
                    validated_results = []
                    for item in result:
                        if isinstance(item, dict):
                            validated_item = model_class(**item)
                            validated_results.append(validated_item.dict())
                        else:
                            validated_results.append(item)
                    return validated_results
                else:
                    return result
                    
            except ValidationError as e:
                logger.error(f"Response validation error: {e}")
                raise ValidationException("Ошибка валидации ответа")
            except Exception as e:
                logger.error(f"Unexpected error in response validation: {e}")
                return result  # Возвращаем исходный результат
        
        return wrapper
    return decorator


# Функции для валидации
def validate_and_clean_data(data: Dict[str, Any], model_class: type[BaseValidationModel]) -> Dict[str, Any]:
    """Валидация и очистка данных"""
    try:
        validated_model = model_class(**data)
        return validated_model.dict()
    except ValidationError as e:
        raise ValidationException(
            message="Ошибка валидации данных",
            field="data",
            value=str(e.errors())
        )


def validate_file_upload(filename: str, content_type: str, max_size: int = 10 * 1024 * 1024) -> bool:
    """Валидация загружаемого файла"""
    # Проверяем расширение файла
    allowed_extensions = ['.txt', '.html', '.xml', '.json', '.csv']
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if f'.{file_extension}' not in allowed_extensions:
        raise ValidationException(
            message="Неподдерживаемый тип файла",
            field="filename",
            value=filename
        )
    
    # Проверяем MIME тип
    allowed_mime_types = [
        'text/plain', 'text/html', 'application/xml', 
        'application/json', 'text/csv'
    ]
    
    if content_type not in allowed_mime_types:
        raise ValidationException(
            message="Неподдерживаемый MIME тип",
            field="content_type",
            value=content_type
        )
    
    return True


def validate_api_key(api_key: str) -> bool:
    """Валидация API ключа"""
    if not api_key:
        raise ValidationException("API ключ не может быть пустым")
    
    # Проверяем формат API ключа (пример)
    if len(api_key) < 32:
        raise ValidationException("API ключ должен содержать минимум 32 символа")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
        raise ValidationException("API ключ содержит недопустимые символы")
    
    return True


# Утилиты для валидации
class ValidationUtils:
    """Утилиты для валидации"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Очистка строки"""
        if not isinstance(value, str):
            raise ValidationException("Значение должно быть строкой")
        
        # Убираем лишние пробелы
        cleaned = ' '.join(value.split())
        
        # Ограничиваем длину
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned
    
    @staticmethod
    def validate_positive_integer(value: int, max_value: int = 1000000) -> int:
        """Валидация положительного целого числа"""
        if not isinstance(value, int):
            raise ValidationException("Значение должно быть целым числом")
        
        if value <= 0:
            raise ValidationException("Значение должно быть положительным")
        
        if value > max_value:
            raise ValidationException(f"Значение не может превышать {max_value}")
        
        return value
    
    @staticmethod
    def validate_percentage(value: float) -> float:
        """Валидация процента"""
        if not isinstance(value, (int, float)):
            raise ValidationException("Значение должно быть числом")
        
        if value < 0 or value > 100:
            raise ValidationException("Процент должен быть от 0 до 100")
        
        return float(value)


# Экспорт для обратной совместимости
RelinkValidation = {
    "UserRegistrationModel": UserRegistrationModel,
    "UserLoginModel": UserLoginModel,
    "DomainAnalysisModel": DomainAnalysisModel,
    "SEORecommendationModel": SEORecommendationModel,
    "ExportModel": ExportModel,
    "PaginationModel": PaginationModel,
    "validate_request": validate_request,
    "validate_response": validate_response,
    "validate_and_clean_data": validate_and_clean_data,
    "validate_file_upload": validate_file_upload,
    "validate_api_key": validate_api_key,
    "ValidationUtils": ValidationUtils,
} 