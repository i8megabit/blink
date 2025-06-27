import React from 'react'

function AnalysisProgress({ analysisStats, currentThought, aiThoughts }) {
  if (!analysisStats && !currentThought) {
    return null
  }

  return (
    <div className="step-card">
      <div className="step-number">3</div>
      <h3 className="step-title">Прогресс анализа</h3>
      
      {analysisStats && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span>{analysisStats.step}</span>
            <span>{analysisStats.percentage}%</span>
          </div>
          <div className="progress-container">
            <div 
              className="progress-bar" 
              style={{ width: `${analysisStats.percentage}%` }}
            ></div>
          </div>
          {analysisStats.details && (
            <div style={{ fontSize: '14px', color: '#666', marginTop: '8px' }}>
              {analysisStats.details}
            </div>
          )}
        </div>
      )}
      
      {currentThought && (
        <div className="ai-thinking">
          <div style={{ fontWeight: '600', marginBottom: '4px' }}>
            {currentThought.emoji || '🧠'} {currentThought.stage || 'Анализ'}
          </div>
          <div>{currentThought.content}</div>
        </div>
      )}
      
      {aiThoughts.length > 0 && (
        <div style={{ marginTop: '16px' }}>
          <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
            История мыслей ИИ
          </h4>
          <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {aiThoughts.slice(-3).map((thought, index) => (
              <div 
                key={thought.id || index}
                style={{ 
                  fontSize: '12px', 
                  padding: '8px', 
                  background: 'rgba(255,255,255,0.1)', 
                  borderRadius: '6px',
                  marginBottom: '4px'
                }}
              >
                <div style={{ fontWeight: '500', marginBottom: '2px' }}>
                  {thought.emoji || '💭'} {thought.stage || 'Анализ'}
                </div>
                <div>{thought.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default AnalysisProgress 