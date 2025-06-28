import React, { useState, useEffect } from 'react';
import { useNotifications } from '../hooks/useNotifications';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Input } from './ui/Input';
import { Progress } from './ui/Progress';

interface Test {
  id: string;
  name: string;
  description: string;
  test_type: 'unit' | 'api' | 'performance' | 'seo' | 'llm' | 'generic';
  priority: 'low' | 'medium' | 'high' | 'critical';
  environment: 'development' | 'staging' | 'production';
  status: 'pending' | 'running' | 'passed' | 'failed' | 'error' | 'cancelled';
  created_at: string;
  updated_at: string;
  tags: string[];
  metadata: Record<string, any>;
}

interface TestExecution {
  id: string;
  test_request: any;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'error' | 'cancelled';
  progress: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  results: any[];
  user_id: number;
  metadata: Record<string, any>;
}

interface TestMetrics {
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  success_rate: number;
  average_duration: number;
  total_executions: number;
  running_executions: number;
}

const Testing: React.FC = () => {
  const [tests, setTests] = useState<Test[]>([]);
  const [executions, setExecutions] = useState<TestExecution[]>([]);
  const [metrics, setMetrics] = useState<TestMetrics | null>(null);
  const [selectedTest, setSelectedTest] = useState<Test | null>(null);
  const [isCreatingTest, setIsCreatingTest] = useState(false);
  const [filters, setFilters] = useState({
    test_type: '',
    status: '',
    priority: '',
    environment: ''
  });

  const { showNotification } = useNotifications();

  // Загрузка тестов
  const loadTests = async () => {
    try {
      const params = new URLSearchParams({
        limit: '100',
        ...filters
      });
      const response = await fetch(`/api/v1/tests/?${params}`);
      const data = await response.json();
      setTests(data);
    } catch (error) {
      showNotification('error', 'Ошибка загрузки тестов');
    }
  };

  // Загрузка выполнений
  const loadExecutions = async () => {
    try {
      const response = await fetch('/api/v1/test-executions/?limit=50');
      const data = await response.json();
      setExecutions(data);
    } catch (error) {
      showNotification('error', 'Ошибка загрузки выполнений');
    }
  };

  // Загрузка метрик
  const loadMetrics = async () => {
    try {
      const response = await fetch('/api/v1/testing/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      showNotification('error', 'Ошибка загрузки метрик');
    }
  };

  // Выполнение теста
  const executeTest = async (testId: string) => {
    try {
      await fetch(`/api/v1/tests/${testId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      showNotification('success', 'Тест запущен');
      loadExecutions();
    } catch (error) {
      showNotification('error', 'Ошибка выполнения теста');
    }
  };

  // Отмена выполнения
  const cancelExecution = async (executionId: string) => {
    try {
      await fetch(`/api/v1/test-executions/${executionId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      showNotification('success', 'Выполнение отменено');
      loadExecutions();
    } catch (error) {
      showNotification('error', 'Ошибка отмены выполнения');
    }
  };

  useEffect(() => {
    loadTests();
    loadExecutions();
    loadMetrics();

    // Обновляем данные каждые 5 секунд
    const interval = setInterval(() => {
      loadExecutions();
      loadMetrics();
    }, 5000);

    return () => clearInterval(interval);
  }, [filters]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      case 'running': return 'text-blue-500';
      case 'pending': return 'text-yellow-500';
      case 'error': return 'text-red-600';
      case 'cancelled': return 'text-gray-500';
      default: return 'text-gray-400';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-orange-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-green-500';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Система тестирования
        </h1>
        <Button onClick={() => setIsCreatingTest(true)}>
          Создать тест
        </Button>
      </div>

      {/* Метрики */}
      {metrics && (
        <Card>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {metrics.total_tests}
              </div>
              <div className="text-sm text-gray-600">Всего тестов</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {metrics.passed_tests}
              </div>
              <div className="text-sm text-gray-600">Пройдено</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {metrics.failed_tests}
              </div>
              <div className="text-sm text-gray-600">Провалено</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-500">
                {metrics.running_executions}
              </div>
              <div className="text-sm text-gray-600">Выполняется</div>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Успешность: {metrics.success_rate.toFixed(1)}%</span>
              <span>Среднее время: {metrics.average_duration.toFixed(2)}s</span>
            </div>
          </div>
        </Card>
      )}

      {/* Фильтры */}
      <Card>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Тип теста
            </label>
            <select
              value={filters.test_type}
              onChange={(e) => setFilters({ ...filters, test_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все типы</option>
              <option value="unit">Unit</option>
              <option value="api">API</option>
              <option value="performance">Performance</option>
              <option value="seo">SEO</option>
              <option value="llm">LLM</option>
              <option value="generic">Generic</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Статус
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все статусы</option>
              <option value="pending">Ожидает</option>
              <option value="running">Выполняется</option>
              <option value="passed">Пройден</option>
              <option value="failed">Провален</option>
              <option value="error">Ошибка</option>
              <option value="cancelled">Отменен</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Приоритет
            </label>
            <select
              value={filters.priority}
              onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все приоритеты</option>
              <option value="low">Низкий</option>
              <option value="medium">Средний</option>
              <option value="high">Высокий</option>
              <option value="critical">Критический</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Среда
            </label>
            <select
              value={filters.environment}
              onChange={(e) => setFilters({ ...filters, environment: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все среды</option>
              <option value="development">Development</option>
              <option value="staging">Staging</option>
              <option value="production">Production</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Список тестов */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Тесты ({tests.length})
        </h2>
        <div className="space-y-3">
          {tests.map((test) => (
            <div
              key={test.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {test.name}
                  </h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(test.status)}`}>
                    {test.status}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(test.priority)}`}>
                    {test.priority}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {test.description}
                </p>
                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                  <span>Тип: {test.test_type}</span>
                  <span>Среда: {test.environment}</span>
                  <span>Создан: {new Date(test.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  onClick={() => executeTest(test.id)}
                  disabled={test.status === 'running'}
                >
                  {test.status === 'running' ? 'Выполняется...' : 'Запустить'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedTest(test)}
                >
                  Детали
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Список выполнений */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Выполнения ({executions.length})
        </h2>
        <div className="space-y-3">
          {executions.map((execution) => (
            <div
              key={execution.id}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <span className="font-medium text-gray-900 dark:text-white">
                    {execution.test_request?.name || 'Неизвестный тест'}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(execution.status)}`}>
                    {execution.status}
                  </span>
                </div>
                <div className="flex space-x-2">
                  {execution.status === 'running' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => cancelExecution(execution.id)}
                    >
                      Отменить
                    </Button>
                  )}
                </div>
              </div>
              
              {execution.status === 'running' && (
                <div className="mb-2">
                  <Progress value={execution.progress} />
                  <div className="text-xs text-gray-500 mt-1">
                    Прогресс: {execution.progress.toFixed(1)}%
                  </div>
                </div>
              )}
              
              <div className="text-xs text-gray-500 space-y-1">
                <div>ID: {execution.id}</div>
                <div>Создано: {new Date(execution.created_at).toLocaleString()}</div>
                {execution.started_at && (
                  <div>Начато: {new Date(execution.started_at).toLocaleString()}</div>
                )}
                {execution.finished_at && (
                  <div>Завершено: {new Date(execution.finished_at).toLocaleString()}</div>
                )}
                {execution.results.length > 0 && (
                  <div>Результатов: {execution.results.length}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Модальное окно создания теста */}
      {isCreatingTest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Создать новый тест
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Название
                </label>
                <Input placeholder="Введите название теста" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Описание
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Введите описание теста"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Тип теста
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="unit">Unit</option>
                    <option value="api">API</option>
                    <option value="performance">Performance</option>
                    <option value="seo">SEO</option>
                    <option value="llm">LLM</option>
                    <option value="generic">Generic</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Приоритет
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="low">Низкий</option>
                    <option value="medium">Средний</option>
                    <option value="high">Высокий</option>
                    <option value="critical">Критический</option>
                  </select>
                </div>
              </div>
              <div className="flex space-x-3">
                <Button onClick={() => setIsCreatingTest(false)}>
                  Создать
                </Button>
                <Button variant="outline" onClick={() => setIsCreatingTest(false)}>
                  Отмена
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Testing; 