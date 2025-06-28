// ===== A/B ТЕСТИРОВАНИЕ КОМПОНЕНТ =====

import React, { useState } from 'react'
import { useABTests, useLLMModels } from '../hooks/useMicroservices'
import { ABTestConfig, ABTestCase, LLMModel } from '../types/microservices'
import { Card, Button, Badge, Progress } from './ui'

interface ABTestingProps {
  className?: string
}

export const ABTesting: React.FC<ABTestingProps> = ({ className = '' }) => {
  const { tests, loading, error, createTest, startTest, stopTest } = useABTests()
  const { models } = useLLMModels()
  const [selectedTest, setSelectedTest] = useState<ABTestConfig | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showResults, setShowResults] = useState<string | null>(null)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'gray'
      case 'running': return 'green'
      case 'completed': return 'blue'
      case 'paused': return 'yellow'
      default: return 'gray'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'draft': return '📝'
      case 'running': return '▶️'
      case 'completed': return '✅'
      case 'paused': return '⏸️'
      default: return '❓'
    }
  }

  const formatDuration = (hours: number) => {
    if (hours < 24) return `${hours}ч`
    const days = Math.floor(hours / 24)
    const remainingHours = hours % 24
    return `${days}д ${remainingHours}ч`
  }

  const calculateProgress = (test: ABTestConfig) => {
    if (test.status === 'completed') return 100
    if (test.status === 'draft') return 0
    
    const startTime = new Date(test.started_at!).getTime()
    const endTime = startTime + (test.duration_hours * 60 * 60 * 1000)
    const currentTime = Date.now()
    
    if (currentTime >= endTime) return 100
    
    const progress = ((currentTime - startTime) / (endTime - startTime)) * 100
    return Math.min(progress, 100)
  }

  const handleCreateTest = async (testData: Partial<ABTestConfig>) => {
    try {
      await createTest(testData)
      setShowCreateForm(false)
    } catch (error) {
      console.error('Ошибка создания A/B теста:', error)
    }
  }

  const handleStartTest = async (testId: string) => {
    try {
      await startTest(testId)
    } catch (error) {
      console.error('Ошибка запуска A/B теста:', error)
    }
  }

  const handleStopTest = async (testId: string) => {
    try {
      await stopTest(testId)
    } catch (error) {
      console.error('Ошибка остановки A/B теста:', error)
    }
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка A/B тестов...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <Card className="border-red-200 bg-red-50">
          <div className="text-center">
            <p className="text-red-600 mb-2">❌ Ошибка загрузки A/B тестов</p>
            <p className="text-red-500 text-sm">{error}</p>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Заголовок и кнопки */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            🧪 A/B Тестирование
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Сравнение производительности LLM моделей
          </p>
        </div>
        <Button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          ➕ Создать тест
        </Button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{tests.length}</div>
            <div className="text-sm text-gray-600">Всего тестов</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {tests.filter(t => t.status === 'running').length}
            </div>
            <div className="text-sm text-gray-600">Активных</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {tests.filter(t => t.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-600">Завершенных</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">
              {tests.filter(t => t.status === 'draft').length}
            </div>
            <div className="text-sm text-gray-600">Черновиков</div>
          </div>
        </Card>
      </div>

      {/* Список тестов */}
      <div className="space-y-4">
        {tests.map((test) => (
          <Card key={test.id} className="p-6 hover:shadow-lg transition-shadow">
            <div className="space-y-4">
              {/* Заголовок теста */}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {test.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {test.description}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getStatusIcon(test.status)}</span>
                  <Badge color={getStatusColor(test.status)}>
                    {test.status}
                  </Badge>
                </div>
              </div>

              {/* Прогресс теста */}
              {test.status !== 'draft' && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Прогресс:</span>
                    <span className="font-medium">{calculateProgress(test).toFixed(1)}%</span>
                  </div>
                  <Progress 
                    value={calculateProgress(test)} 
                    max={100}
                    className="h-2"
                    color={test.status === 'completed' ? 'green' : 'blue'}
                  />
                </div>
              )}

              {/* Модели в тесте */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Модели в тесте:</h4>
                <div className="flex flex-wrap gap-2">
                  {test.models.map((modelId) => {
                    const model = models.find(m => m.id === modelId)
                    return (
                      <Badge key={modelId} color="blue" size="sm">
                        {model ? model.display_name : modelId}
                      </Badge>
                    )
                  })}
                </div>
              </div>

              {/* Распределение трафика */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Распределение трафика:</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {Object.entries(test.traffic_split).map(([modelId, percentage]) => {
                    const model = models.find(m => m.id === modelId)
                    return (
                      <div key={modelId} className="text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">
                            {model ? model.display_name : modelId}:
                          </span>
                          <span className="font-medium">{percentage}%</span>
                        </div>
                        <Progress 
                          value={percentage} 
                          max={100}
                          className="h-1 mt-1"
                        />
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Тестовые случаи */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Тестовые случаи ({test.test_cases.length}):
                </h4>
                <div className="space-y-1">
                  {test.test_cases.slice(0, 3).map((testCase, index) => (
                    <div key={index} className="text-sm text-gray-600">
                      • {testCase.input.substring(0, 100)}...
                    </div>
                  ))}
                  {test.test_cases.length > 3 && (
                    <div className="text-sm text-gray-500">
                      ... и еще {test.test_cases.length - 3} случаев
                    </div>
                  )}
                </div>
              </div>

              {/* Метаданные */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500">
                <div>
                  <span className="font-medium">Длительность:</span>
                  <div>{formatDuration(test.duration_hours)}</div>
                </div>
                <div>
                  <span className="font-medium">Метрики:</span>
                  <div>{test.metrics.length}</div>
                </div>
                <div>
                  <span className="font-medium">Создан:</span>
                  <div>{new Date(test.created_at).toLocaleDateString()}</div>
                </div>
                {test.started_at && (
                  <div>
                    <span className="font-medium">Запущен:</span>
                    <div>{new Date(test.started_at).toLocaleDateString()}</div>
                  </div>
                )}
              </div>

              {/* Действия */}
              <div className="flex space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button
                  size="sm"
                  onClick={() => setSelectedTest(test)}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700"
                >
                  📊 Детали
                </Button>
                {test.status === 'draft' && (
                  <Button
                    size="sm"
                    onClick={() => handleStartTest(test.id)}
                    className="bg-green-600 hover:bg-green-700 text-white"
                  >
                    ▶️ Запустить
                  </Button>
                )}
                {test.status === 'running' && (
                  <Button
                    size="sm"
                    onClick={() => handleStopTest(test.id)}
                    className="bg-red-600 hover:bg-red-700 text-white"
                  >
                    ⏹️ Остановить
                  </Button>
                )}
                {test.status === 'completed' && (
                  <Button
                    size="sm"
                    onClick={() => setShowResults(test.id)}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                  >
                    📈 Результаты
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Форма создания теста */}
      {showCreateForm && (
        <CreateTestForm
          models={models}
          onSubmit={handleCreateTest}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {/* Детали теста */}
      {selectedTest && (
        <TestDetailsModal
          test={selectedTest}
          models={models}
          onClose={() => setSelectedTest(null)}
        />
      )}

      {/* Результаты теста */}
      {showResults && (
        <TestResultsModal
          testId={showResults}
          onClose={() => setShowResults(null)}
        />
      )}
    </div>
  )
}

// Форма создания A/B теста
interface CreateTestFormProps {
  models: LLMModel[]
  onSubmit: (data: Partial<ABTestConfig>) => void
  onCancel: () => void
}

const CreateTestForm: React.FC<CreateTestFormProps> = ({ models, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    models: [] as string[],
    test_cases: [] as ABTestCase[],
    traffic_split: {} as Record<string, number>,
    metrics: [] as string[],
    duration_hours: 24
  })

  const [newTestCase, setNewTestCase] = useState({
    input: '',
    expected_output: '',
    category: 'general'
  })

  const handleAddTestCase = () => {
    if (newTestCase.input.trim()) {
      setFormData({
        ...formData,
        test_cases: [...formData.test_cases, { ...newTestCase, id: Date.now().toString() }]
      })
      setNewTestCase({ input: '', expected_output: '', category: 'general' })
    }
  }

  const handleRemoveTestCase = (index: number) => {
    setFormData({
      ...formData,
      test_cases: formData.test_cases.filter((_, i) => i !== index)
    })
  }

  const handleModelSelection = (modelId: string, checked: boolean) => {
    let newModels: string[]
    if (checked) {
      newModels = [...formData.models, modelId]
    } else {
      newModels = formData.models.filter(id => id !== modelId)
    }
    
    // Автоматически распределяем трафик
    const trafficSplit: Record<string, number> = {}
    newModels.forEach((modelId, index) => {
      trafficSplit[modelId] = Math.round(100 / newModels.length)
    })
    
    setFormData({
      ...formData,
      models: newModels,
      traffic_split: trafficSplit
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (formData.models.length < 2) {
      alert('Выберите минимум 2 модели для сравнения')
      return
    }
    if (formData.test_cases.length === 0) {
      alert('Добавьте хотя бы один тестовый случай')
      return
    }
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4">Создать A/B тест</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Название теста
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Описание
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Выберите модели для сравнения
            </label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {models.map((model) => (
                <label key={model.id} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.models.includes(model.id)}
                    onChange={(e) => handleModelSelection(model.id, e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">{model.display_name}</span>
                  <Badge color="gray" size="sm">{model.model_type}</Badge>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Длительность теста (часы)
            </label>
            <input
              type="number"
              min="1"
              max="168"
              value={formData.duration_hours}
              onChange={(e) => setFormData({ ...formData, duration_hours: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тестовые случаи
            </label>
            <div className="space-y-2">
              {formData.test_cases.map((testCase, index) => (
                <div key={index} className="p-2 border border-gray-200 rounded">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium">Случай {index + 1}</span>
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => handleRemoveTestCase(index)}
                      className="bg-red-100 hover:bg-red-200 text-red-700"
                    >
                      ✕
                    </Button>
                  </div>
                  <div className="text-sm text-gray-600">
                    <div><strong>Ввод:</strong> {testCase.input}</div>
                    {testCase.expected_output && (
                      <div><strong>Ожидаемый вывод:</strong> {testCase.expected_output}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-2 p-3 border border-gray-200 rounded">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
                <input
                  type="text"
                  placeholder="Ввод для теста"
                  value={newTestCase.input}
                  onChange={(e) => setNewTestCase({ ...newTestCase, input: e.target.value })}
                  className="px-2 py-1 border border-gray-300 rounded text-sm"
                />
                <input
                  type="text"
                  placeholder="Ожидаемый вывод (опционально)"
                  value={newTestCase.expected_output}
                  onChange={(e) => setNewTestCase({ ...newTestCase, expected_output: e.target.value })}
                  className="px-2 py-1 border border-gray-300 rounded text-sm"
                />
              </div>
              <Button
                type="button"
                size="sm"
                onClick={handleAddTestCase}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                ➕ Добавить случай
              </Button>
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700 text-white">
              Создать тест
            </Button>
            <Button type="button" onClick={onCancel} className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700">
              Отмена
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

// Модальное окно с деталями теста
interface TestDetailsModalProps {
  test: ABTestConfig
  models: LLMModel[]
  onClose: () => void
}

const TestDetailsModal: React.FC<TestDetailsModalProps> = ({ test, models, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-4xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Детали A/B теста: {test.name}
          </h3>
          <Button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </Button>
        </div>

        <div className="space-y-6">
          {/* Основная информация */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Статус</label>
              <Badge color={getStatusColor(test.status)}>{test.status}</Badge>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Длительность</label>
              <div className="text-sm text-gray-900">{formatDuration(test.duration_hours)}</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Создан</label>
              <div className="text-sm text-gray-900">{new Date(test.created_at).toLocaleString()}</div>
            </div>
            {test.started_at && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Запущен</label>
                <div className="text-sm text-gray-900">{new Date(test.started_at).toLocaleString()}</div>
              </div>
            )}
          </div>

          {/* Описание */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
            <div className="text-sm text-gray-900">{test.description}</div>
          </div>

          {/* Модели */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Модели в тесте</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {test.models.map((modelId) => {
                const model = models.find(m => m.id === modelId)
                return (
                  <div key={modelId} className="p-3 border border-gray-200 rounded">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{model ? model.display_name : modelId}</h4>
                      <Badge color="blue">{test.traffic_split[modelId]}% трафика</Badge>
                    </div>
                    {model && (
                      <div className="text-sm text-gray-600">
                        <div>Тип: {model.model_type}</div>
                        <div>Параметры: {model.parameters.toLocaleString()}</div>
                        <div>Контекст: {model.context_length.toLocaleString()}</div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Тестовые случаи */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тестовые случаи ({test.test_cases.length})
            </label>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {test.test_cases.map((testCase, index) => (
                <div key={index} className="p-3 border border-gray-200 rounded">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-medium">Случай {index + 1}</span>
                    <Badge color="gray" size="sm">{testCase.category}</Badge>
                  </div>
                  <div className="text-sm space-y-1">
                    <div><strong>Ввод:</strong> {testCase.input}</div>
                    {testCase.expected_output && (
                      <div><strong>Ожидаемый вывод:</strong> {testCase.expected_output}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Метрики */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Метрики</label>
            <div className="flex flex-wrap gap-2">
              {test.metrics.map((metric) => (
                <Badge key={metric} color="green">{metric}</Badge>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

// Модальное окно с результатами теста
interface TestResultsModalProps {
  testId: string
  onClose: () => void
}

const TestResultsModal: React.FC<TestResultsModalProps> = ({ testId, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-4xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Результаты A/B теста
          </h3>
          <Button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </Button>
        </div>

        <div className="text-center py-8">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-gray-600">Результаты теста будут доступны после завершения</p>
        </div>
      </Card>
    </div>
  )
} 