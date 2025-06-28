import React, { useState } from 'react'
import { useBenchmarks, useLLMModels } from '../hooks/useMicroservices'
import { BenchmarkSuite, LLMModel } from '../types/microservices'
import { Card, Button, Badge, Progress } from './ui'

interface BenchmarksProps {
  className?: string
}

export const Benchmarks: React.FC<BenchmarksProps> = ({ className = '' }) => {
  const { benchmarkSuites, loading, error, createBenchmarkSuite, runBenchmarkSuite } = useBenchmarks()
  const { models } = useLLMModels()
  const [selectedSuite, setSelectedSuite] = useState<BenchmarkSuite | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [runningBenchmarks, setRunningBenchmarks] = useState<Set<string>>(new Set())

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'green'
      case 'running': return 'blue'
      case 'completed': return 'purple'
      case 'failed': return 'red'
      default: return 'gray'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ready': return '✅'
      case 'running': return '🔄'
      case 'completed': return '🏆'
      case 'failed': return '❌'
      default: return '❓'
    }
  }

  const formatScore = (score: number) => {
    return score.toFixed(2)
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
  }

  const handleCreateSuite = async (suiteData: Partial<BenchmarkSuite>) => {
    try {
      await createBenchmarkSuite(suiteData)
      setShowCreateForm(false)
    } catch (error) {
      console.error('Ошибка создания набора бенчмарков:', error)
    }
  }

  const handleRunBenchmark = async (suiteId: string, modelName: string) => {
    try {
      setRunningBenchmarks(prev => new Set(prev).add(`${suiteId}-${modelName}`))
      await runBenchmarkSuite(suiteId, modelName)
    } catch (error) {
      console.error('Ошибка запуска бенчмарка:', error)
    } finally {
      setRunningBenchmarks(prev => {
        const newSet = new Set(prev)
        newSet.delete(`${suiteId}-${modelName}`)
        return newSet
      })
    }
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка бенчмарков...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <Card className="border-red-200 bg-red-50">
          <div className="text-center">
            <p className="text-red-600 mb-2">❌ Ошибка загрузки бенчмарков</p>
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
            🏆 Бенчмарки
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Тестирование производительности LLM моделей
          </p>
        </div>
        <Button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          ➕ Создать набор
        </Button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{benchmarkSuites.length}</div>
            <div className="text-sm text-gray-600">Наборов бенчмарков</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {benchmarkSuites.filter(s => s.status === 'ready').length}
            </div>
            <div className="text-sm text-gray-600">Готовых</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {benchmarkSuites.filter(s => s.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-600">Завершенных</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {benchmarkSuites.reduce((total, suite) => total + suite.results.length, 0)}
            </div>
            <div className="text-sm text-gray-600">Результатов</div>
          </div>
        </Card>
      </div>

      {/* Список наборов бенчмарков */}
      <div className="space-y-4">
        {benchmarkSuites.map((suite) => (
          <Card key={suite.id} className="p-6 hover:shadow-lg transition-shadow">
            <div className="space-y-4">
              {/* Заголовок набора */}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {suite.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {suite.description}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getStatusIcon(suite.status)}</span>
                  <Badge color={getStatusColor(suite.status)}>
                    {suite.status}
                  </Badge>
                </div>
              </div>

              {/* Метрики */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Метрики:</h4>
                <div className="flex flex-wrap gap-2">
                  {suite.metrics.map((metric) => (
                    <Badge key={metric} color="blue" size="sm">
                      {metric}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Результаты */}
              {suite.results.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Результаты:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {suite.results.map((result) => {
                      const model = models.find(m => m.name === result.model_name)
                      return (
                        <div key={result.id} className="p-3 border border-gray-200 rounded">
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="font-medium text-sm">
                              {model ? model.display_name : result.model_name}
                            </h5>
                            <Badge color="green" size="sm">
                              {formatScore(result.overall_score)}
                            </Badge>
                          </div>
                          <div className="space-y-1 text-xs text-gray-600">
                            {Object.entries(result.metric_scores).map(([metric, score]) => (
                              <div key={metric} className="flex justify-between">
                                <span>{metric}:</span>
                                <span className="font-medium">{formatScore(score)}</span>
                              </div>
                            ))}
                            <div className="flex justify-between">
                              <span>Время:</span>
                              <span className="font-medium">{formatDuration(result.execution_time_seconds)}</span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Метаданные */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500">
                <div>
                  <span className="font-medium">Тестов:</span>
                  <div>{suite.test_cases.length}</div>
                </div>
                <div>
                  <span className="font-medium">Метрик:</span>
                  <div>{suite.metrics.length}</div>
                </div>
                <div>
                  <span className="font-medium">Создан:</span>
                  <div>{new Date(suite.created_at).toLocaleDateString()}</div>
                </div>
                {suite.last_run && (
                  <div>
                    <span className="font-medium">Последний запуск:</span>
                    <div>{new Date(suite.last_run).toLocaleDateString()}</div>
                  </div>
                )}
              </div>

              {/* Действия */}
              <div className="flex space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button
                  size="sm"
                  onClick={() => setSelectedSuite(suite)}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700"
                >
                  📊 Детали
                </Button>
                {models.map((model) => {
                  const isRunning = runningBenchmarks.has(`${suite.id}-${model.name}`)
                  return (
                    <Button
                      key={model.id}
                      size="sm"
                      onClick={() => handleRunBenchmark(suite.id, model.name)}
                      disabled={isRunning}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      {isRunning ? '🔄' : '▶️'} {model.display_name}
                    </Button>
                  )
                })}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Форма создания набора */}
      {showCreateForm && (
        <CreateBenchmarkForm
          onSubmit={handleCreateSuite}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {/* Детали набора */}
      {selectedSuite && (
        <BenchmarkDetailsModal
          suite={selectedSuite}
          models={models}
          onClose={() => setSelectedSuite(null)}
        />
      )}
    </div>
  )
}

// Форма создания набора бенчмарков
interface CreateBenchmarkFormProps {
  onSubmit: (data: Partial<BenchmarkSuite>) => void
  onCancel: () => void
}

const CreateBenchmarkForm: React.FC<CreateBenchmarkFormProps> = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    metrics: [] as string[],
    test_cases: [] as any[]
  })

  const [newTestCase, setNewTestCase] = useState({
    input: '',
    expected_output: '',
    category: 'general'
  })

  const availableMetrics = [
    'accuracy', 'precision', 'recall', 'f1_score', 'bleu_score', 'rouge_score',
    'perplexity', 'response_time', 'throughput', 'memory_usage', 'cpu_usage'
  ]

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

  const handleMetricToggle = (metric: string) => {
    setFormData({
      ...formData,
      metrics: formData.metrics.includes(metric)
        ? formData.metrics.filter(m => m !== metric)
        : [...formData.metrics, metric]
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (formData.metrics.length === 0) {
      alert('Выберите хотя бы одну метрику')
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
        <h3 className="text-lg font-semibold mb-4">Создать набор бенчмарков</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Название набора
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
              Выберите метрики
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {availableMetrics.map((metric) => (
                <label key={metric} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.metrics.includes(metric)}
                    onChange={() => handleMetricToggle(metric)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">{metric}</span>
                </label>
              ))}
            </div>
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
              Создать набор
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

// Модальное окно с деталями набора
interface BenchmarkDetailsModalProps {
  suite: BenchmarkSuite
  models: LLMModel[]
  onClose: () => void
}

const BenchmarkDetailsModal: React.FC<BenchmarkDetailsModalProps> = ({ suite, models, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-4xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Детали набора бенчмарков: {suite.name}
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
              <Badge color={getStatusColor(suite.status)}>{suite.status}</Badge>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Создан</label>
              <div className="text-sm text-gray-900">{new Date(suite.created_at).toLocaleString()}</div>
            </div>
          </div>

          {/* Описание */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
            <div className="text-sm text-gray-900">{suite.description}</div>
          </div>

          {/* Метрики */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Метрики</label>
            <div className="flex flex-wrap gap-2">
              {suite.metrics.map((metric) => (
                <Badge key={metric} color="blue">{metric}</Badge>
              ))}
            </div>
          </div>

          {/* Результаты */}
          {suite.results.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Результаты</label>
              <div className="space-y-3">
                {suite.results.map((result) => {
                  const model = models.find(m => m.name === result.model_name)
                  return (
                    <div key={result.id} className="p-4 border border-gray-200 rounded">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium">{model ? model.display_name : result.model_name}</h4>
                        <Badge color="green">{formatScore(result.overall_score)}</Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                        {Object.entries(result.metric_scores).map(([metric, score]) => (
                          <div key={metric} className="flex justify-between">
                            <span className="text-gray-600">{metric}:</span>
                            <span className="font-medium">{formatScore(score)}</span>
                          </div>
                        ))}
                        <div className="flex justify-between">
                          <span className="text-gray-600">Время выполнения:</span>
                          <span className="font-medium">{formatDuration(result.execution_time_seconds)}</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Тестовые случаи */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тестовые случаи ({suite.test_cases.length})
            </label>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {suite.test_cases.map((testCase, index) => (
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
        </div>
      </Card>
    </div>
  )
} 