import React from 'react'

function OllamaStatus({ status, onRefresh }) {
  const getStatusColor = () => {
    if (status.ready_for_work) return 'status-success'
    if (status.server_available) return 'status-warning'
    return 'status-error'
  }

  const getStatusText = () => {
    if (status.ready_for_work) return 'Готов к работе'
    if (status.server_available) return 'Сервер доступен'
    return 'Недоступен'
  }

  const getStatusIcon = () => {
    if (status.ready_for_work) return '✅'
    if (status.server_available) return '⚠️'
    return '❌'
  }

  return (
    <div className="space-y-4">
      {/* Основной статус */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`status-indicator ${getStatusColor()}`}>
            <span>{getStatusIcon()}</span>
            {getStatusText()}
          </div>
        </div>
        
        <button 
          className="btn btn-ghost btn-sm"
          onClick={onRefresh}
        >
          🔄 Обновить
        </button>
      </div>

      {/* Детальная информация */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <div className="card-header">
            <div className="card-title">Подключение</div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">Сервер:</span>
              <span className={`text-sm ${status.server_available ? 'text-green-500' : 'text-red-500'}`}>
                {status.server_available ? 'Доступен' : 'Недоступен'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">Модель:</span>
              <span className={`text-sm ${status.model_loaded ? 'text-green-500' : 'text-yellow-500'}`}>
                {status.model_loaded ? 'Загружена' : 'Загружается...'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">Готовность:</span>
              <span className={`text-sm ${status.ready_for_work ? 'text-green-500' : 'text-yellow-500'}`}>
                {status.ready_for_work ? 'Готов' : 'Не готов'}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">Информация</div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">Последняя проверка:</span>
              <span className="text-sm text-muted">
                {status.last_check ? new Date(status.last_check).toLocaleTimeString('ru-RU') : 'Неизвестно'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">Моделей:</span>
              <span className="text-sm text-muted">
                {status.models_count || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">Статус:</span>
              <span className="text-sm text-muted">
                {status.connection || 'Неизвестно'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Сообщение */}
      {status.message && (
        <div className="card">
          <div className="text-sm text-muted">
            {status.message}
          </div>
        </div>
      )}

      {/* Доступные модели */}
      {status.available_models && status.available_models.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">Доступные модели</div>
          </div>
          <div className="space-y-2">
            {status.available_models.slice(0, 5).map((model, index) => (
              <div key={index} className="flex items-center gap-2 text-sm">
                <span className="text-muted">🤖</span>
                <span className="text-primary">{model}</span>
              </div>
            ))}
            {status.available_models.length > 5 && (
              <div className="text-sm text-muted">
                ... и еще {status.available_models.length - 5} моделей
              </div>
            )}
          </div>
        </div>
      )}

      {/* Рекомендации */}
      {!status.ready_for_work && (
        <div className="card bg-yellow-900/20 border-yellow-500/30">
          <div className="flex items-start gap-3">
            <div className="text-yellow-500 text-lg">💡</div>
            <div>
              <div className="font-medium text-yellow-100 mb-1">Рекомендации</div>
              <div className="text-sm text-yellow-200 space-y-1">
                {!status.server_available && (
                  <div>• Проверьте, что Ollama запущена и доступна</div>
                )}
                {status.server_available && !status.model_loaded && (
                  <div>• Дождитесь загрузки модели или загрузите её вручную</div>
                )}
                <div>• Убедитесь, что у вас достаточно памяти для работы модели</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default OllamaStatus 