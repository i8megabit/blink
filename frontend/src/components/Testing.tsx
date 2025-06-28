import React, { useState, useEffect, useCallback } from 'react';
import { useNotifications } from '../hooks/useNotifications';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Input } from './ui/Input';
import { Progress } from './ui/Progress';
import { Badge } from './ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/Tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/Dialog';
import { Textarea } from './ui/Textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select';
import { Label } from './ui/Label';
import { ScrollArea } from './ui/ScrollArea';
import { Alert, AlertDescription } from './ui/Alert';
import { 
  Play, 
  Square, 
  Plus, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  Info,
  FileText,
  BarChart3
} from 'lucide-react';

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
  test_id: string;
  test_request: Test;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'error' | 'cancelled';
  progress: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  results: TestResult[];
  user_id: number;
  metadata: Record<string, any>;
  duration?: number;
  error_message?: string;
}

interface TestResult {
  id: string;
  execution_id: string;
  status: 'passed' | 'failed' | 'error';
  message: string;
  details: Record<string, any>;
  duration: number;
  timestamp: string;
  error_details?: string;
  stack_trace?: string;
}

interface TestMetrics {
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  success_rate: number;
  average_duration: number;
  total_executions: number;
  running_executions: number;
  execution_trends: Record<string, any>;
  performance_metrics: Record<string, any>;
  error_distribution: Record<string, any>;
  environment_stats: Record<string, any>;
}

interface CreateTestForm {
  name: string;
  description: string;
  test_type: 'unit' | 'api' | 'performance' | 'seo' | 'llm' | 'generic';
  priority: 'low' | 'medium' | 'high' | 'critical';
  environment: 'development' | 'staging' | 'production';
  timeout: number;
  parameters: Record<string, any>;
  retry_count: number;
  parallel: boolean;
  dependencies: string[];
  tags: string[];
}

const Testing: React.FC = () => {
  const [tests, setTests] = useState<Test[]>([]);
  const [executions, setExecutions] = useState<TestExecution[]>([]);
  const [metrics, setMetrics] = useState<TestMetrics | null>(null);
  const [isCreatingTest, setIsCreatingTest] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<TestExecution | null>(null);
  const [createTestForm, setCreateTestForm] = useState<CreateTestForm>({
    name: '',
    description: '',
    test_type: 'api',
    priority: 'medium',
    environment: 'development',
    timeout: 30,
    parameters: {},
    retry_count: 1,
    parallel: false,
    dependencies: [],
    tags: []
  });
  const [filters, setFilters] = useState({
    test_type: '',
    status: '',
    priority: '',
    environment: ''
  });

  const { showNotification } = useNotifications();

  // Загрузка тестов
  const loadTests = useCallback(async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams({
        limit: '100',
        ...filters
      });
      const response = await fetch(`/api/v1/tests/?${params}`);
      if (!response.ok) throw new Error('Ошибка загрузки тестов');
      const data = await response.json();
      setTests(data);
    } catch (error) {
      showNotification('error', 'Ошибка загрузки тестов');
      console.error('Error loading tests:', error);
    } finally {
      setIsLoading(false);
    }
  }, [filters, showNotification]);

  // Загрузка выполнений
  const loadExecutions = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/test-executions/?limit=50');
      if (!response.ok) throw new Error('Ошибка загрузки выполнений');
      const data = await response.json();
      setExecutions(data);
    } catch (error) {
      showNotification('error', 'Ошибка загрузки выполнений');
      console.error('Error loading executions:', error);
    }
  }, [showNotification]);

  // Загрузка метрик
  const loadMetrics = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/testing/metrics');
      if (!response.ok) throw new Error('Ошибка загрузки метрик');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      showNotification('error', 'Ошибка загрузки метрик');
      console.error('Error loading metrics:', error);
    }
  }, [showNotification]);

  // Выполнение теста
  const executeTest = async (testId: string) => {
    try {
      const response = await fetch(`/api/v1/tests/${testId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) throw new Error('Ошибка выполнения теста');
      
      const execution = await response.json();
      showNotification('success', `Тест "${execution.test_request?.name || 'Неизвестный'}" запущен`);
      loadExecutions();
    } catch (error) {
      showNotification('error', 'Ошибка выполнения теста');
      console.error('Error executing test:', error);
    }
  };

  // Отмена выполнения
  const cancelExecution = async (executionId: string) => {
    try {
      const response = await fetch(`/api/v1/test-executions/${executionId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) throw new Error('Ошибка отмены выполнения');
      
      showNotification('success', 'Выполнение отменено');
      loadExecutions();
    } catch (error) {
      showNotification('error', 'Ошибка отмены выполнения');
      console.error('Error canceling execution:', error);
    }
  };

  // Создание теста
  const createTest = async () => {
    try {
      const response = await fetch('/api/v1/tests/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(createTestForm)
      });
      
      if (!response.ok) throw new Error('Ошибка создания теста');
      
      const newTest = await response.json();
      showNotification('success', `Тест "${newTest.name}" создан`);
      setIsCreatingTest(false);
      setCreateTestForm({
        name: '',
        description: '',
        test_type: 'api',
        priority: 'medium',
        environment: 'development',
        timeout: 30,
        parameters: {},
        retry_count: 1,
        parallel: false,
        dependencies: [],
        tags: []
      });
      loadTests();
    } catch (error) {
      showNotification('error', 'Ошибка создания теста');
      console.error('Error creating test:', error);
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
  }, [loadTests, loadExecutions, loadMetrics]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'text-green-500 bg-green-50';
      case 'failed': return 'text-red-500 bg-red-50';
      case 'running': return 'text-blue-500 bg-blue-50';
      case 'pending': return 'text-yellow-500 bg-yellow-50';
      case 'error': return 'text-red-600 bg-red-50';
      case 'cancelled': return 'text-gray-500 bg-gray-50';
      default: return 'text-gray-400 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircle className="w-4 h-4" />;
      case 'failed': return <XCircle className="w-4 h-4" />;
      case 'running': return <RefreshCw className="w-4 h-4 animate-spin" />;
      case 'pending': return <Clock className="w-4 h-4" />;
      case 'error': return <AlertTriangle className="w-4 h-4" />;
      case 'cancelled': return <XCircle className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-500 bg-orange-50';
      case 'medium': return 'text-yellow-500 bg-yellow-50';
      case 'low': return 'text-green-500 bg-green-50';
      default: return 'text-gray-400 bg-gray-50';
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Система тестирования
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Управление тестами и мониторинг выполнения
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => { loadTests(); loadExecutions(); loadMetrics(); }}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Обновить
          </Button>
          <Dialog open={isCreatingTest} onOpenChange={setIsCreatingTest}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Создать тест
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Создать новый тест</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">Название</Label>
                    <Input
                      id="name"
                      value={createTestForm.name}
                      onChange={(e) => setCreateTestForm({ ...createTestForm, name: e.target.value })}
                      placeholder="Введите название теста"
                    />
                  </div>
                  <div>
                    <Label htmlFor="test_type">Тип теста</Label>
                    <Select
                      value={createTestForm.test_type}
                      onValueChange={(value: string) => setCreateTestForm({ ...createTestForm, test_type: value as any })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="unit">Unit</SelectItem>
                        <SelectItem value="api">API</SelectItem>
                        <SelectItem value="performance">Performance</SelectItem>
                        <SelectItem value="seo">SEO</SelectItem>
                        <SelectItem value="llm">LLM</SelectItem>
                        <SelectItem value="generic">Generic</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="description">Описание</Label>
                  <Textarea
                    id="description"
                    value={createTestForm.description}
                    onChange={(e) => setCreateTestForm({ ...createTestForm, description: e.target.value })}
                    placeholder="Введите описание теста"
                    rows={3}
                  />
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="priority">Приоритет</Label>
                    <Select
                      value={createTestForm.priority}
                      onValueChange={(value: string) => setCreateTestForm({ ...createTestForm, priority: value as any })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Низкий</SelectItem>
                        <SelectItem value="medium">Средний</SelectItem>
                        <SelectItem value="high">Высокий</SelectItem>
                        <SelectItem value="critical">Критический</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="environment">Среда</Label>
                    <Select
                      value={createTestForm.environment}
                      onValueChange={(value: string) => setCreateTestForm({ ...createTestForm, environment: value as any })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="development">Development</SelectItem>
                        <SelectItem value="staging">Staging</SelectItem>
                        <SelectItem value="production">Production</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="timeout">Таймаут (сек)</Label>
                    <Input
                      id="timeout"
                      type="number"
                      value={createTestForm.timeout}
                      onChange={(e) => setCreateTestForm({ ...createTestForm, timeout: parseInt(e.target.value) })}
                      min="1"
                      max="3600"
                    />
                  </div>
                </div>
                
                <div className="flex space-x-3">
                  <Button onClick={createTest} disabled={!createTestForm.name}>
                    Создать
                  </Button>
                  <Button variant="outline" onClick={() => setIsCreatingTest(false)}>
                    Отмена
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Метрики */}
      {metrics && (
        <Card>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {metrics.total_tests}
              </div>
              <div className="text-sm text-gray-600">Всего тестов</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {metrics.passed_tests}
              </div>
              <div className="text-sm text-gray-600">Пройдено</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {metrics.failed_tests}
              </div>
              <div className="text-sm text-gray-600">Провалено</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {metrics.running_executions}
              </div>
              <div className="text-sm text-gray-600">Выполняется</div>
            </div>
          </div>
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Успешность: {metrics.success_rate.toFixed(1)}%</span>
              <span>Среднее время: {formatDuration(metrics.average_duration)}</span>
              <span>Всего выполнений: {metrics.total_executions}</span>
            </div>
          </div>
        </Card>
      )}

      <Tabs defaultValue="tests" className="space-y-4">
        <TabsList>
          <TabsTrigger value="tests" className="flex items-center space-x-2">
            <FileText className="w-4 h-4" />
            <span>Тесты ({tests.length})</span>
          </TabsTrigger>
          <TabsTrigger value="executions" className="flex items-center space-x-2">
            <Play className="w-4 h-4" />
            <span>Выполнения ({executions.length})</span>
          </TabsTrigger>
          <TabsTrigger value="metrics" className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4" />
            <span>Метрики</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="tests" className="space-y-4">
          {/* Фильтры */}
          <Card>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <Label>Тип теста</Label>
                <Select
                  value={filters.test_type}
                  onValueChange={(value: string) => setFilters({ ...filters, test_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Все типы" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Все типы</SelectItem>
                    <SelectItem value="unit">Unit</SelectItem>
                    <SelectItem value="api">API</SelectItem>
                    <SelectItem value="performance">Performance</SelectItem>
                    <SelectItem value="seo">SEO</SelectItem>
                    <SelectItem value="llm">LLM</SelectItem>
                    <SelectItem value="generic">Generic</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Статус</Label>
                <Select
                  value={filters.status}
                  onValueChange={(value: string) => setFilters({ ...filters, status: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Все статусы" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Все статусы</SelectItem>
                    <SelectItem value="pending">Ожидает</SelectItem>
                    <SelectItem value="running">Выполняется</SelectItem>
                    <SelectItem value="passed">Пройден</SelectItem>
                    <SelectItem value="failed">Провален</SelectItem>
                    <SelectItem value="error">Ошибка</SelectItem>
                    <SelectItem value="cancelled">Отменен</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Приоритет</Label>
                <Select
                  value={filters.priority}
                  onValueChange={(value: string) => setFilters({ ...filters, priority: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Все приоритеты" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Все приоритеты</SelectItem>
                    <SelectItem value="low">Низкий</SelectItem>
                    <SelectItem value="medium">Средний</SelectItem>
                    <SelectItem value="high">Высокий</SelectItem>
                    <SelectItem value="critical">Критический</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Среда</Label>
                <Select
                  value={filters.environment}
                  onValueChange={(value: string) => setFilters({ ...filters, environment: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Все среды" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Все среды</SelectItem>
                    <SelectItem value="development">Development</SelectItem>
                    <SelectItem value="staging">Staging</SelectItem>
                    <SelectItem value="production">Production</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </Card>

          {/* Список тестов */}
          <Card>
            <div className="space-y-3">
              {isLoading ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400" />
                  <p className="text-gray-500 mt-2">Загрузка тестов...</p>
                </div>
              ) : tests.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 mx-auto text-gray-400" />
                  <p className="text-gray-500 mt-2">Тесты не найдены</p>
                </div>
              ) : (
                tests.map((test) => (
                  <div
                    key={test.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {test.name}
                        </h3>
                        <Badge variant="outline" className={getStatusColor(test.status)}>
                          {getStatusIcon(test.status)}
                          <span className="ml-1">{test.status}</span>
                        </Badge>
                        <Badge variant="outline" className={getPriorityColor(test.priority)}>
                          {test.priority}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {test.description}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>Тип: {test.test_type}</span>
                        <span>Среда: {test.environment}</span>
                        <span>Создан: {new Date(test.created_at).toLocaleDateString()}</span>
                        {test.tags.length > 0 && (
                          <span>Теги: {test.tags.join(', ')}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        onClick={() => executeTest(test.id)}
                        disabled={test.status === 'running'}
                      >
                        {test.status === 'running' ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Выполняется...
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 mr-2" />
                            Запустить
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          <Card>
            <div className="space-y-3">
              {executions.length === 0 ? (
                <div className="text-center py-8">
                  <Play className="w-12 h-12 mx-auto text-gray-400" />
                  <p className="text-gray-500 mt-2">Выполнения не найдены</p>
                </div>
              ) : (
                executions.map((execution) => (
                  <div
                    key={execution.id}
                    className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                    onClick={() => setSelectedExecution(execution)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {execution.test_request?.name || 'Неизвестный тест'}
                        </span>
                        <Badge variant="outline" className={getStatusColor(execution.status)}>
                          {getStatusIcon(execution.status)}
                          <span className="ml-1">{execution.status}</span>
                        </Badge>
                        {execution.duration && (
                          <span className="text-sm text-gray-500">
                            {formatDuration(execution.duration)}
                          </span>
                        )}
                      </div>
                      <div className="flex space-x-2">
                        {execution.status === 'running' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e: React.MouseEvent) => {
                              e.stopPropagation();
                              cancelExecution(execution.id);
                            }}
                          >
                            <Square className="w-4 h-4 mr-2" />
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
                      {execution.error_message && (
                        <div className="text-red-500">Ошибка: {execution.error_message}</div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          {metrics && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <h3 className="text-lg font-semibold mb-4">Тренды выполнения</h3>
                <div className="space-y-2">
                  {Object.entries(metrics.execution_trends || {}).map(([period, data]: [string, any]) => (
                    <div key={period} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{period}</span>
                      <div className="text-sm text-gray-600">
                        {data.total} всего, {data.successful} успешно
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
              
              <Card>
                <h3 className="text-lg font-semibold mb-4">Метрики производительности</h3>
                <div className="space-y-2">
                  {Object.entries(metrics.performance_metrics || {}).map(([metric, value]: [string, any]) => (
                    <div key={metric} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{metric}</span>
                      <span className="text-sm text-gray-600">{value}</span>
                    </div>
                  ))}
                </div>
              </Card>
              
              <Card>
                <h3 className="text-lg font-semibold mb-4">Распределение ошибок</h3>
                <div className="space-y-2">
                  {Object.entries(metrics.error_distribution || {}).map(([error, count]: [string, any]) => (
                    <div key={error} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{error}</span>
                      <span className="text-sm text-gray-600">{count}</span>
                    </div>
                  ))}
                </div>
              </Card>
              
              <Card>
                <h3 className="text-lg font-semibold mb-4">Статистика по средам</h3>
                <div className="space-y-2">
                  {Object.entries(metrics.environment_stats || {}).map(([env, stats]: [string, any]) => (
                    <div key={env} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium">{env}</span>
                      <div className="text-sm text-gray-600">
                        {stats.total} всего, {stats.successful} успешно
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Модальное окно с деталями выполнения */}
      {selectedExecution && (
        <Dialog open={!!selectedExecution} onOpenChange={() => setSelectedExecution(null)}>
          <DialogContent className="max-w-4xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>
                Детали выполнения: {selectedExecution.test_request?.name}
              </DialogTitle>
            </DialogHeader>
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium">Статус</Label>
                    <Badge variant="outline" className={getStatusColor(selectedExecution.status)}>
                      {getStatusIcon(selectedExecution.status)}
                      <span className="ml-1">{selectedExecution.status}</span>
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Прогресс</Label>
                    <div className="text-sm">{selectedExecution.progress.toFixed(1)}%</div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Создано</Label>
                    <div className="text-sm">{new Date(selectedExecution.created_at).toLocaleString()}</div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Длительность</Label>
                    <div className="text-sm">
                      {selectedExecution.duration ? formatDuration(selectedExecution.duration) : 'Не завершено'}
                    </div>
                  </div>
                </div>

                {selectedExecution.error_message && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Ошибка:</strong> {selectedExecution.error_message}
                    </AlertDescription>
                  </Alert>
                )}

                {selectedExecution.results.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Результаты тестов</h4>
                    <div className="space-y-2">
                      {selectedExecution.results.map((result) => (
                        <div key={result.id} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <Badge variant="outline" className={getStatusColor(result.status)}>
                              {getStatusIcon(result.status)}
                              <span className="ml-1">{result.status}</span>
                            </Badge>
                            <span className="text-sm text-gray-500">
                              {formatDuration(result.duration)}
                            </span>
                          </div>
                          <p className="text-sm mb-2">{result.message}</p>
                          {result.error_details && (
                            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                              {result.error_details}
                            </div>
                          )}
                          {result.stack_trace && (
                            <details className="mt-2">
                              <summary className="text-sm text-gray-500 cursor-pointer">
                                Stack trace
                              </summary>
                              <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                                {result.stack_trace}
                              </pre>
                            </details>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <h4 className="font-medium mb-2">Метаданные</h4>
                  <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                    {JSON.stringify(selectedExecution.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            </ScrollArea>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default Testing; 