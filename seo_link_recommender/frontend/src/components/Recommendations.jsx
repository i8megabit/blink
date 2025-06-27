import React, { useState } from 'react'

function Recommendations({ recommendations }) {
  const [selectedRecommendation, setSelectedRecommendation] = useState(null)

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-muted mb-4">
          <div className="text-4xl mb-2">🔗</div>
          <div className="text-lg font-medium">Рекомендации не найдены</div>
          <div className="text-sm">Попробуйте проанализировать другой домен</div>
        </div>
      </div>
    )
  }

  const handleRecommendationClick = (recommendation) => {
    setSelectedRecommendation(recommendation)
  }

  const closeModal = () => {
    setSelectedRecommendation(null)
  }

  return (
    <div className="space-y-4">
      {/* Статистика */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted">
          Найдено рекомендаций: {recommendations.length}
        </div>
        <div className="flex items-center gap-2">
          <div className="badge badge-primary">
            {recommendations.length} ссылок
          </div>
        </div>
      </div>

      {/* Сетка рекомендаций */}
      <div className="recommendations-grid">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className="recommendation-card"
            onClick={() => handleRecommendationClick(rec)}
          >
            <div className="recommendation-header">
              <div className="recommendation-title">
                Рекомендация #{index + 1}
              </div>
              <div className="recommendation-score">
                {Math.round((rec.quality_score || 0.5) * 100)}%
              </div>
            </div>
            
            <div className="recommendation-anchor">
              "{rec.anchor || 'Без анкора'}"
            </div>
            
            <div className="recommendation-reasoning">
              {rec.comment || 'Обоснование не предоставлено'}
            </div>
            
            <div className="mt-4 pt-4 border-t border-border-primary">
              <div className="flex items-center justify-between text-xs text-muted">
                <div className="flex items-center gap-1">
                  <span>📄</span>
                  {rec.from?.split('/').pop() || 'Источник'}
                </div>
                <div className="flex items-center gap-1">
                  <span>🎯</span>
                  {rec.to?.split('/').pop() || 'Цель'}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Модальное окно с деталями */}
      {selectedRecommendation && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">Детали рекомендации</div>
              <button className="modal-close" onClick={closeModal}>
                ✕
              </button>
            </div>
            
            <div className="modal-body">
              <div className="space-y-4">
                {/* Анкор */}
                <div>
                  <div className="form-label">Анкорный текст</div>
                  <div className="form-input bg-bg-tertiary">
                    {selectedRecommendation.anchor || 'Не указан'}
                  </div>
                </div>

                {/* Обоснование */}
                <div>
                  <div className="form-label">Обоснование</div>
                  <div className="form-input bg-bg-tertiary min-h-[100px]">
                    {selectedRecommendation.comment || 'Обоснование не предоставлено'}
                  </div>
                </div>

                {/* Ссылки */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="form-label">Источник</div>
                    <div className="form-input bg-bg-tertiary text-sm">
                      {selectedRecommendation.from || 'Не указан'}
                    </div>
                  </div>
                  
                  <div>
                    <div className="form-label">Цель</div>
                    <div className="form-input bg-bg-tertiary text-sm">
                      {selectedRecommendation.to || 'Не указана'}
                    </div>
                  </div>
                </div>

                {/* Качество */}
                <div>
                  <div className="form-label">Оценка качества</div>
                  <div className="flex items-center gap-3">
                    <div className="progress-container flex-1">
                      <div 
                        className="progress-bar" 
                        style={{ width: `${(selectedRecommendation.quality_score || 0.5) * 100}%` }}
                      ></div>
                    </div>
                    <div className="text-sm font-medium">
                      {Math.round((selectedRecommendation.quality_score || 0.5) * 100)}%
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={closeModal}>
                Закрыть
              </button>
              <button 
                className="btn btn-primary"
                onClick={() => {
                  // Здесь можно добавить функционал копирования или экспорта
                  navigator.clipboard.writeText(
                    `Анкор: "${selectedRecommendation.anchor}"\n` +
                    `От: ${selectedRecommendation.from}\n` +
                    `К: ${selectedRecommendation.to}\n` +
                    `Обоснование: ${selectedRecommendation.comment}`
                  )
                  closeModal()
                }}
              >
                Копировать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Recommendations 