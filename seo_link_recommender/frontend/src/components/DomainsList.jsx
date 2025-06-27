import React from 'react'

function DomainsList({ domains, onSelectDomain }) {
  if (!domains.length) {
    return (
      <div className="step-card">
        <div className="step-number">2</div>
        <h3 className="step-title">Домены</h3>
        <div className="status-indicator status-warning">
          Домены не найдены
        </div>
      </div>
    )
  }

  return (
    <div className="step-card">
      <div className="step-number">2</div>
      <h3 className="step-title">Домены ({domains.length})</h3>
      <p className="step-description">
        Проанализированные домены и их статистика
      </p>
      
      <div style={{ marginTop: '16px' }}>
        {domains.map((domain) => (
          <div
            key={domain.id}
            className="domain-card"
            onClick={() => onSelectDomain && onSelectDomain(domain)}
            style={{ cursor: onSelectDomain ? 'pointer' : 'default' }}
          >
            <div className="domain-name">{domain.name}</div>
            <div className="domain-stats">
              <div className="stat-item">
                📄 {domain.total_posts} статей
              </div>
              <div className="stat-item">
                📊 {domain.total_analyses} анализов
              </div>
              <div className="stat-item">
                🕒 {domain.updated_at ? new Date(domain.updated_at).toLocaleString('ru-RU') : 'Не обновлялся'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default DomainsList 