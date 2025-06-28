// ===== LLM МОДЕЛИ КОМПОНЕНТ =====

import React, { useState } from 'react'
import { useLLMModels } from '../hooks/useMicroservices'
import { LLMModel } from '../types/microservices'
import { Card, Button, Badge, Progress } from './ui'

interface LLMModelsProps {
  className?: string
}

export const LLMModels: React.FC<LLMModelsProps> = ({ className = '' }) => {
  const { models, loading, error, createModel, updateModel, deleteModel } = useLLMModels()
  const [selectedModel, setSelectedModel] = useState<LLMModel | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'green'
      case 'loading': return 'yellow'
      case 'error': return 'red'
      case 'unavailable': return 'gray'
      default: return 'gray'
    }
  }

  const getModelTypeColor = (type: string) => {
    switch (type) {
      case 'base': return 'blue'
      case 'tuned': return 'purple'
      case 'custom': return 'orange'
      default: return 'gray'
    }
  }

  const formatParameters = (params: number) => {
    if (params >= 1e9) return `${(params / 1e9).toFixed(1)}B`
    if (params >= 1e6) return `${(params / 1e6).toFixed(1)}M`
    if (params >= 1e3) return `${(params / 1e3).toFixed(1)}K`
    return params.toString()
  }

  const handleCreateModel = async (modelData: Partial<LLMModel>) => {
    try {
      await createModel(modelData)
      setShowCreateForm(false)
    } catch (error) {
      console.error('Ошибка создания модели:', error)
    }
  }

  const handleUpdateModel = async (modelId: string, modelData: Partial<LLMModel>) => {
    try {
      await updateModel(modelId, modelData)
      setShowEditForm(false)
      setSelectedModel(null)
    } catch (error) {
      console.error('Ошибка обновления модели:', error)
    }
  }

  const handleDeleteModel = async (modelId: string) => {
    if (window.confirm('Вы уверены, что хотите удалить эту модель?')) {
      try {
        await deleteModel(modelId)
      } catch (error) {
        console.error('Ошибка удаления модели:', error)
      }
    }
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка моделей...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <Card className="border-red-200 bg-red-50">
          <div className="text-center">
            <p className="text-red-600 mb-2">❌ Ошибка загрузки моделей</p>
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
            🧠 LLM Модели
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Управление моделями машинного обучения
          </p>
        </div>
        <Button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          ➕ Добавить модель
        </Button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{models.length}</div>
            <div className="text-sm text-gray-600">Всего моделей</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {models.filter(m => m.status === 'available').length}
            </div>
            <div className="text-sm text-gray-600">Доступно</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {models.filter(m => m.model_type === 'tuned').length}
            </div>
            <div className="text-sm text-gray-600">Настроенных</div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {models.filter(m => m.model_type === 'custom').length}
            </div>
            <div className="text-sm text-gray-600">Кастомных</div>
          </div>
        </Card>
      </div>

      {/* Список моделей */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {models.map((model) => (
          <Card key={model.id} className="p-6 hover:shadow-lg transition-shadow">
            <div className="space-y-4">
              {/* Заголовок модели */}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {model.display_name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {model.name} v{model.version}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <Badge color={getStatusColor(model.status)}>
                    {model.status}
                  </Badge>
                  <Badge color={getModelTypeColor(model.model_type)}>
                    {model.model_type}
                  </Badge>
                </div>
              </div>

              {/* Параметры модели */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Параметры:</span>
                  <span className="font-medium">{formatParameters(model.parameters)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Контекст:</span>
                  <span className="font-medium">{model.context_length.toLocaleString()}</span>
                </div>
              </div>

              {/* Оценки качества */}
              {model.quality_score && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Качество:</span>
                    <span className="font-medium">{model.quality_score.toFixed(2)}</span>
                  </div>
                  <Progress 
                    value={model.quality_score * 100} 
                    max={100}
                    className="h-2"
                  />
                </div>
              )}

              {model.performance_score && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Производительность:</span>
                    <span className="font-medium">{model.performance_score.toFixed(2)}</span>
                  </div>
                  <Progress 
                    value={model.performance_score * 100} 
                    max={100}
                    className="h-2"
                  />
                </div>
              )}

              {/* Метаданные */}
              <div className="text-xs text-gray-500 space-y-1">
                <div>Создано: {new Date(model.created_at).toLocaleDateString()}</div>
                {model.last_used && (
                  <div>Использовано: {new Date(model.last_used).toLocaleDateString()}</div>
                )}
              </div>

              {/* Действия */}
              <div className="flex space-x-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                <Button
                  size="sm"
                  onClick={() => {
                    setSelectedModel(model)
                    setShowEditForm(true)
                  }}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700"
                >
                  ✏️ Редактировать
                </Button>
                <Button
                  size="sm"
                  onClick={() => handleDeleteModel(model.id)}
                  className="bg-red-100 hover:bg-red-200 text-red-700"
                >
                  🗑️
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Форма создания модели */}
      {showCreateForm && (
        <CreateModelForm
          onSubmit={handleCreateModel}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {/* Форма редактирования модели */}
      {showEditForm && selectedModel && (
        <EditModelForm
          model={selectedModel}
          onSubmit={(data) => handleUpdateModel(selectedModel.id, data)}
          onCancel={() => {
            setShowEditForm(false)
            setSelectedModel(null)
          }}
        />
      )}
    </div>
  )
}

// Форма создания модели
interface CreateModelFormProps {
  onSubmit: (data: Partial<LLMModel>) => void
  onCancel: () => void
}

const CreateModelForm: React.FC<CreateModelFormProps> = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    version: '1.0.0',
    model_type: 'base' as const,
    parameters: 0,
    context_length: 4096
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md p-6">
        <h3 className="text-lg font-semibold mb-4">Создать новую модель</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Название модели
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
              Отображаемое название
            </label>
            <input
              type="text"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Версия
              </label>
              <input
                type="text"
                value={formData.version}
                onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Тип модели
              </label>
              <select
                value={formData.model_type}
                onChange={(e) => setFormData({ ...formData, model_type: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="base">Базовая</option>
                <option value="tuned">Настроенная</option>
                <option value="custom">Кастомная</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Параметры
              </label>
              <input
                type="number"
                value={formData.parameters}
                onChange={(e) => setFormData({ ...formData, parameters: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Размер контекста
              </label>
              <input
                type="number"
                value={formData.context_length}
                onChange={(e) => setFormData({ ...formData, context_length: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>
          <div className="flex space-x-3 pt-4">
            <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700 text-white">
              Создать
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

// Форма редактирования модели
interface EditModelFormProps {
  model: LLMModel
  onSubmit: (data: Partial<LLMModel>) => void
  onCancel: () => void
}

const EditModelForm: React.FC<EditModelFormProps> = ({ model, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    display_name: model.display_name,
    version: model.version,
    model_type: model.model_type,
    parameters: model.parameters,
    context_length: model.context_length,
    quality_score: model.quality_score || 0,
    performance_score: model.performance_score || 0
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md p-6">
        <h3 className="text-lg font-semibold mb-4">Редактировать модель</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Название модели
            </label>
            <input
              type="text"
              value={model.name}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Отображаемое название
            </label>
            <input
              type="text"
              value={formData.display_name}
              onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Версия
              </label>
              <input
                type="text"
                value={formData.version}
                onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Тип модели
              </label>
              <select
                value={formData.model_type}
                onChange={(e) => setFormData({ ...formData, model_type: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="base">Базовая</option>
                <option value="tuned">Настроенная</option>
                <option value="custom">Кастомная</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Параметры
              </label>
              <input
                type="number"
                value={formData.parameters}
                onChange={(e) => setFormData({ ...formData, parameters: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Размер контекста
              </label>
              <input
                type="number"
                value={formData.context_length}
                onChange={(e) => setFormData({ ...formData, context_length: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Оценка качества
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={formData.quality_score}
                onChange={(e) => setFormData({ ...formData, quality_score: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Оценка производительности
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={formData.performance_score}
                onChange={(e) => setFormData({ ...formData, performance_score: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex space-x-3 pt-4">
            <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700 text-white">
              Сохранить
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