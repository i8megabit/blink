import React from 'react'

function OllamaStatus({ ollamaStatus, onRefresh }) {
  const getStatusClass = () => {
    switch (ollamaStatus.status) {
      case 'ready':
        return 'status-success'
      case 'connecting':
        return 'status-warning'
      case 'error':
        return 'status-error'
      default:
        return 'status-warning'
    }
  }

  const getStatusIcon = () => {
    switch (ollamaStatus.status) {
      case 'ready':
        return '✅'
      case 'connecting':
        return '⏳'
      case 'error':
        return '❌'
      default:
        return '❓'
    }
  }

  return (
    <div className="step-card">
      <div className="step-number">0</div>
      <h3 className="step-title">Статус Ollama</h3>
      <p className="step-description">
        Состояние подключения к ИИ модели
      </p>
      
      <div style={{ marginTop: '16px' }}>
        <div className={`status-indicator ${getStatusClass()}`}>
          {getStatusIcon()} {ollamaStatus.message}
        </div>
        
        {ollamaStatus.models_count > 0 && (
          <div style={{ marginTop: '8px', fontSize: '14px', color: '#666' }}>
            Доступно моделей: {ollamaStatus.models_count}
          </div>
        )}
        
        {ollamaStatus.available_models && ollamaStatus.available_models.length > 0 && (
          <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
            Модели: {ollamaStatus.available_models.slice(0, 3).join(', ')}
            {ollamaStatus.available_models.length > 3 && '...'}
          </div>
        )}
        
        <button
          onClick={onRefresh}
          className="btn-apple btn-secondary"
          style={{ marginTop: '12px' }}
        >
          🔄 Обновить статус
        </button>
      </div>
    </div>
  )
}

export default OllamaStatus 