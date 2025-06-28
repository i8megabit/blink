"""
Основной модуль FastAPI приложения для микросервиса тестирования reLink.
Предоставляет REST API для управления тестами, выполнениями и отчетами.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import logging
import time
from typing import List, Optional, Dict, Any
import uvicorn

from .config import settings
from .models import (
    TestRequest, TestResponse, TestSuiteRequest, TestSuiteResponse,
    TestExecution, TestExecutionResponse, TestReport, TestMetrics,
    TestFilter, TestStatus, TestType, TestPriority, TestEnvironment
)
from .services import TestingService
from .database import get_database, Database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация сервисов
testing_service = TestingService()
security = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("🚀 Запуск микросервиса тестирования reLink...")
    # await testing_service.initialize()  # временно убрано
    logger.info("✅ Микросервис тестирования успешно запущен")
    yield
    # await testing_service.cleanup()  # временно убрано
    logger.info("🛑 Микросервис тестирования остановлен")

# Создание FastAPI приложения
app = FastAPI(
    title="reLink Testing Service",
    description="Микросервис для управления и выполнения тестов платформы reLink",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# Dependency для получения базы данных
async def get_db() -> Database:
    """Получение подключения к базе данных"""
    return await get_database()

# Dependency для аутентификации (заглушка)
async def get_current_user(token: str = Depends(security)):
    """Получение текущего пользователя"""
    if not settings.auth_required:
        return {"user_id": "anonymous", "role": "tester"}
    
    # TODO: Реализовать реальную аутентификацию
    if not token:
        raise HTTPException(status_code=401, detail="Требуется аутентификация")
    
    return {"user_id": "test_user", "role": "tester"}

# Обработчики ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "detail": str(exc) if settings.debug else "Произошла неожиданная ошибка"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

# Health check
@app.get("/health", tags=["Система"])
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "reLink Testing Service",
        "version": "1.0.0",
        "timestamp": time.time()
    }

# API роуты для тестов
@app.post("/tests/", response_model=TestResponse, tags=["Тесты"])
async def create_test(
    test_request: TestRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Создание нового теста"""
    try:
        test = await testing_service.create_test(test_request, current_user["user_id"])
        logger.info(f"Создан тест: {test.id}")
        return test
    except Exception as e:
        logger.error(f"Ошибка создания теста: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tests/", response_model=List[TestResponse], tags=["Тесты"])
async def get_tests(
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    test_type: Optional[TestType] = Query(None, description="Тип теста"),
    status: Optional[TestStatus] = Query(None, description="Статус теста"),
    priority: Optional[TestPriority] = Query(None, description="Приоритет теста"),
    environment: Optional[TestEnvironment] = Query(None, description="Окружение"),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Получение списка тестов с фильтрацией"""
    try:
        filters = TestFilter(
            test_type=test_type,
            status=status,
            priority=priority,
            environment=environment
        )
        tests = await testing_service.get_tests(filters, skip, limit)
        return tests
    except Exception as e:
        logger.error(f"Ошибка получения тестов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tests/{test_id}", response_model=TestResponse, tags=["Тесты"])
async def get_test(
    test_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Получение теста по ID"""
    try:
        test = await testing_service.get_test(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Тест не найден")
        return test
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения теста {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/tests/{test_id}", response_model=TestResponse, tags=["Тесты"])
async def update_test(
    test_id: str,
    test_request: TestRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Обновление теста"""
    try:
        test = await testing_service.update_test(test_id, test_request)
        if not test:
            raise HTTPException(status_code=404, detail="Тест не найден")
        logger.info(f"Обновлен тест: {test_id}")
        return test
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления теста {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/tests/{test_id}", tags=["Тесты"])
async def delete_test(
    test_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Удаление теста"""
    try:
        success = await testing_service.delete_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Тест не найден")
        logger.info(f"Удален тест: {test_id}")
        return {"message": "Тест успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления теста {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API роуты для выполнения тестов
@app.post("/tests/{test_id}/execute", response_model=TestExecutionResponse, tags=["Выполнение"])
async def execute_test(
    test_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Выполнение теста"""
    try:
        execution = await testing_service.execute_test(test_id, current_user["user_id"])
        if not execution:
            raise HTTPException(status_code=404, detail="Тест не найден")
        
        # Запуск выполнения в фоне
        background_tasks.add_task(testing_service.run_test_execution, execution.id)
        
        logger.info(f"Запущено выполнение теста: {execution.id}")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка выполнения теста {test_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/executions/", response_model=List[TestExecutionResponse], tags=["Выполнение"])
async def get_executions(
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    test_id: Optional[str] = Query(None, description="ID теста"),
    status: Optional[TestStatus] = Query(None, description="Статус выполнения"),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Получение списка выполнений тестов"""
    try:
        executions = await testing_service.get_executions(test_id, status, skip, limit)
        return executions
    except Exception as e:
        logger.error(f"Ошибка получения выполнений: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/executions/{execution_id}", response_model=TestExecutionResponse, tags=["Выполнение"])
async def get_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Получение выполнения теста по ID"""
    try:
        execution = await testing_service.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Выполнение не найдено")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения выполнения {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/executions/{execution_id}/cancel", tags=["Выполнение"])
async def cancel_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Отмена выполнения теста"""
    try:
        success = await testing_service.cancel_execution(execution_id)
        if not success:
            raise HTTPException(status_code=404, detail="Выполнение не найдено")
        logger.info(f"Отменено выполнение: {execution_id}")
        return {"message": "Выполнение успешно отменено"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отмены выполнения {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API роуты для наборов тестов
@app.post("/test-suites/", response_model=TestSuiteResponse, tags=["Наборы тестов"])
async def create_test_suite(
    suite_request: TestSuiteRequest,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Создание набора тестов"""
    try:
        suite = await testing_service.create_test_suite(suite_request, current_user["user_id"])
        logger.info(f"Создан набор тестов: {suite.id}")
        return suite
    except Exception as e:
        logger.error(f"Ошибка создания набора тестов: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/test-suites/{suite_id}/execute", response_model=List[TestExecutionResponse], tags=["Наборы тестов"])
async def execute_test_suite(
    suite_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Выполнение набора тестов"""
    try:
        executions = await testing_service.execute_test_suite(suite_id, current_user["user_id"])
        if not executions:
            raise HTTPException(status_code=404, detail="Набор тестов не найден")
        
        # Запуск выполнений в фоне
        for execution in executions:
            background_tasks.add_task(testing_service.run_test_execution, execution.id)
        
        logger.info(f"Запущено выполнение набора тестов: {suite_id}")
        return executions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка выполнения набора тестов {suite_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API роуты для отчетов
@app.get("/reports/", response_model=List[TestReport], tags=["Отчеты"])
async def get_reports(
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    test_id: Optional[str] = Query(None, description="ID теста"),
    execution_id: Optional[str] = Query(None, description="ID выполнения"),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Получение списка отчетов"""
    try:
        reports = await testing_service.get_reports(test_id, execution_id, skip, limit)
        return reports
    except Exception as e:
        logger.error(f"Ошибка получения отчетов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{report_id}", response_model=TestReport, tags=["Отчеты"])
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Получение отчета по ID"""
    try:
        report = await testing_service.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Отчет не найден")
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения отчета {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API роуты для метрик
@app.get("/metrics/", response_model=TestMetrics, tags=["Метрики"])
async def get_metrics(
    test_id: Optional[str] = Query(None, description="ID теста"),
    execution_id: Optional[str] = Query(None, description="ID выполнения"),
    time_range: Optional[str] = Query("24h", description="Временной диапазон"),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Получение метрик тестирования"""
    try:
        metrics = await testing_service.get_metrics(test_id, execution_id, time_range)
        return metrics
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket для real-time обновлений
@app.websocket("/ws/executions/{execution_id}")
async def websocket_execution_updates(websocket, execution_id: str):
    """WebSocket для получения обновлений выполнения теста в реальном времени"""
    try:
        await testing_service.subscribe_to_execution_updates(execution_id, websocket)
    except Exception as e:
        logger.error(f"Ошибка WebSocket для выполнения {execution_id}: {e}")
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
        workers=1
    ) 