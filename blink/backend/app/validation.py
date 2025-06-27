"""
Модуль валидации и обработки ошибок для Blink
Pydantic модели, кастомные валидаторы и централизованная обработка ошибок
"""

import re
import ipaddress
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator, root_validator, ValidationError
from pydantic.types import constr
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from .monitoring import monitoring

# Кастомные типы данных
DomainName = constr(regex=r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$')
EmailStr = constr(regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
URLStr = constr(regex=r'^https?://[^\s/$.?#].[^\s]*$')

class ValidationErrorResponse(BaseModel):
    """Модель ответа для ошибок валидации"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """Модель ответа для ошибок"""
    error: str
    message: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Базовые модели валидации
class BaseRequestModel(BaseModel):
    """Базовая модель для всех запросов"""
    
    class Config:
        extra = "forbid"  # Запрещаем дополнительные поля
        validate_assignment = True  # Валидируем при присваивании
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BaseResponseModel(BaseModel):
    """Базовая модель для всех ответов"""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Модели для SEO анализа
class DomainAnalysisRequest(BaseRequestModel):
    """Модель запроса для анализа домена"""
    domain: DomainName = Field(..., description="Домен для анализа")
    depth: int = Field(default=3, ge=1, le=10, description="Глубина анализа")
    include_competitors: bool = Field(default=False, description="Включить анализ конкурентов")
    analysis_type: str = Field(default="comprehensive", regex="^(basic|comprehensive|advanced)$")
    
    @validator('domain')
    def validate_domain(cls, v):
        """Валидация домена"""
        if not v:
            raise ValueError("Домен не может быть пустым")
        
        # Проверяем длину
        if len(v) > 253:
            raise ValueError("Домен слишком длинный")
        
        # Проверяем, что домен не является IP адресом
        try:
            ipaddress.ip_address(v)
            raise ValueError("Домен не может быть IP адресом")
        except ValueError:
            pass
        
        return v.lower()
    
    @root_validator
    def validate_analysis_config(cls, values):
        """Валидация конфигурации анализа"""
        depth = values.get('depth')
        analysis_type = values.get('analysis_type')
        
        if analysis_type == "basic" and depth > 5:
            raise ValueError("Для базового анализа глубина не может превышать 5")
        
        return values

class SEOAnalysisResult(BaseResponseModel):
    """Модель результата SEO анализа"""
    domain: str
    analysis_date: datetime
    score: float = Field(ge=0, le=100)
    recommendations: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    status: str = Field(regex="^(pending|processing|completed|failed)$")
    
    @validator('score')
    def validate_score(cls, v):
        """Валидация SEO score"""
        if v < 0 or v > 100:
            raise ValueError("SEO score должен быть от 0 до 100")
        return round(v, 2)

class CompetitorAnalysisRequest(BaseRequestModel):
    """Модель запроса для анализа конкурентов"""
    domain: DomainName
    competitors: List[DomainName] = Field(..., min_items=1, max_items=10)
    metrics: List[str] = Field(default=["traffic", "backlinks", "keywords"])
    
    @validator('competitors')
    def validate_competitors(cls, v):
        """Валидация списка конкурентов"""
        if not v:
            raise ValueError("Список конкурентов не может быть пустым")
        
        # Проверяем уникальность
        if len(set(v)) != len(v):
            raise ValueError("Конкуренты должны быть уникальными")
        
        return [domain.lower() for domain in v]
    
    @validator('metrics')
    def validate_metrics(cls, v):
        """Валидация метрик"""
        allowed_metrics = ["traffic", "backlinks", "keywords", "rankings", "content"]
        for metric in v:
            if metric not in allowed_metrics:
                raise ValueError(f"Неподдерживаемая метрика: {metric}")
        return v

# Модели для пользователей
class UserRegistrationRequest(BaseRequestModel):
    """Модель запроса регистрации пользователя"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    
    @validator('username')
    def validate_username(cls, v):
        """Валидация имени пользователя"""
        if not v.isalnum() and '_' not in v:
            raise ValueError("Имя пользователя может содержать только буквы, цифры и подчеркивания")
        return v.lower()
    
    @root_validator
    def validate_passwords(cls, values):
        """Валидация паролей"""
        password = values.get('password')
        confirm_password = values.get('confirm_password')
        
        if password != confirm_password:
            raise ValueError("Пароли не совпадают")
        
        # Проверяем сложность пароля
        if not re.search(r'[A-Z]', password):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not re.search(r'[a-z]', password):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not re.search(r'\d', password):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ")
        
        return values

class UserLoginRequest(BaseRequestModel):
    """Модель запроса входа пользователя"""
    email: EmailStr
    password: str = Field(..., min_length=1)

class UserProfileUpdateRequest(BaseRequestModel):
    """Модель запроса обновления профиля пользователя"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=200)
    website: Optional[URLStr]
    
    @validator('website')
    def validate_website(cls, v):
        """Валидация веб-сайта"""
        if v:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Некорректный URL")
        return v

# Модели для истории и экспорта
class AnalysisHistoryRequest(BaseRequestModel):
    """Модель запроса истории анализов"""
    user_id: int = Field(..., gt=0)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    status: Optional[str] = Field(None, regex="^(pending|processing|completed|failed)$")
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    
    @root_validator
    def validate_date_range(cls, values):
        """Валидация диапазона дат"""
        date_from = values.get('date_from')
        date_to = values.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValueError("Дата начала не может быть позже даты окончания")
        
        if date_from and date_from > datetime.utcnow():
            raise ValueError("Дата начала не может быть в будущем")
        
        return values

class ExportRequest(BaseRequestModel):
    """Модель запроса экспорта данных"""
    analysis_ids: List[int] = Field(..., min_items=1, max_items=50)
    format: str = Field(..., regex="^(json|csv|pdf|excel)$")
    include_recommendations: bool = Field(default=True)
    include_metrics: bool = Field(default=True)
    
    @validator('analysis_ids')
    def validate_analysis_ids(cls, v):
        """Валидация ID анализов"""
        if not all(isinstance(id, int) and id > 0 for id in v):
            raise ValueError("Все ID анализов должны быть положительными целыми числами")
        return v

# Кастомные валидаторы
class Validators:
    """Класс с кастомными валидаторами"""
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Валидация URL"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Некорректный URL")
            return url
        except Exception as e:
            raise ValueError(f"Ошибка валидации URL: {e}")
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Валидация номера телефона"""
        # Удаляем все нецифровые символы
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Номер телефона должен содержать от 10 до 15 цифр")
        
        return digits
    
    @staticmethod
    def validate_postal_code(postal_code: str) -> str:
        """Валидация почтового индекса"""
        # Российский формат: 6 цифр
        if not re.match(r'^\d{6}$', postal_code):
            raise ValueError("Почтовый индекс должен содержать 6 цифр")
        
        return postal_code
    
    @staticmethod
    def validate_inn(inn: str) -> str:
        """Валидация ИНН"""
        # Удаляем пробелы и дефисы
        inn_clean = re.sub(r'[\s-]', '', inn)
        
        if not inn_clean.isdigit():
            raise ValueError("ИНН должен содержать только цифры")
        
        if len(inn_clean) not in [10, 12]:
            raise ValueError("ИНН должен содержать 10 или 12 цифр")
        
        return inn_clean

# Обработчики ошибок
class ValidationErrorHandler:
    """Обработчик ошибок валидации"""
    
    @staticmethod
    def handle_validation_error(exc: ValidationError) -> JSONResponse:
        """Обработка ошибок валидации Pydantic"""
        errors = []
        
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        error_response = ValidationErrorResponse(
            error="validation_error",
            message="Ошибка валидации данных",
            details={"errors": errors}
        )
        
        # Логируем ошибку
        monitoring.log_error(
            ValueError(f"Validation error: {errors}"),
            {"validation_errors": errors}
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.dict()
        )
    
    @staticmethod
    def handle_http_error(exc: HTTPException) -> JSONResponse:
        """Обработка HTTP ошибок"""
        error_response = ErrorResponse(
            error="http_error",
            message=exc.detail,
            code=str(exc.status_code)
        )
        
        # Логируем ошибку
        monitoring.log_error(
            exc,
            {"status_code": exc.status_code, "detail": exc.detail}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )

# Декораторы для валидации
def validate_request(model_class: type[BaseRequestModel]):
    """Декоратор для валидации запросов"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                # Валидируем данные запроса
                if 'request_data' in kwargs:
                    validated_data = model_class(**kwargs['request_data'])
                    kwargs['request_data'] = validated_data
                
                return await func(*args, **kwargs)
                
            except ValidationError as e:
                return ValidationErrorHandler.handle_validation_error(e)
            except Exception as e:
                monitoring.log_error(e, {"function": func.__name__})
                raise
        
        return wrapper
    return decorator

def validate_response(model_class: type[BaseResponseModel]):
    """Декоратор для валидации ответов"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Валидируем ответ
                if isinstance(result, dict):
                    validated_result = model_class(**result)
                    return validated_result.dict()
                
                return result
                
            except ValidationError as e:
                return ValidationErrorHandler.handle_validation_error(e)
            except Exception as e:
                monitoring.log_error(e, {"function": func.__name__})
                raise
        
        return wrapper
    return decorator

# Утилиты для валидации
class ValidationUtils:
    """Утилиты для валидации"""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Очистка пользовательского ввода"""
        if not text:
            return ""
        
        # Удаляем потенциально опасные символы
        text = re.sub(r'[<>"\']', '', text)
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """Валидация расширения файла"""
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return extension in allowed_extensions
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> bool:
        """Валидация размера файла"""
        return file_size <= max_size
    
    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime, max_days: int = 365) -> bool:
        """Валидация диапазона дат"""
        if start_date >= end_date:
            return False
        
        delta = end_date - start_date
        return delta.days <= max_days 