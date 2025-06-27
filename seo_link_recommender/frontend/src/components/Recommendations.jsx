import React from 'react'

function Recommendations({ recommendations }) {
  if (!recommendations.length) {
    return null
  }

  return (
    <div className="step-card">
      <div className="step-number">4</div>
      <h3 className="step-title">Рекомендации ({recommendations.length})</h3>
      <p className="step-description">
        Найденные возможности для внутренней перелинковки
      </p>
      
      <div style={{ marginTop: '16px' }}>
        {recommendations.map((rec, index) => (
          <div key={index} className="recommendation-item">
            <div className="recommendation-anchor">
              {rec.anchor || 'Рекомендуемый анкор'}
            </div>
            <div className="recommendation-links">
              <div>От: {rec.from}</div>
              <div>К: {rec.to}</div>
              {rec.comment && (
                <div style={{ marginTop: '4px', fontSize: '12px', color: '#666' }}>
                  💡 {rec.comment}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Recommendations 