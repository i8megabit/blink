import React from 'react'

function DomainInput({ domain, setDomain, onAnalyze, isAnalyzing }) {
  const handleSubmit = (e) => {
    e.preventDefault()
    if (domain.trim() && !isAnalyzing) {
      onAnalyze()
    }
  }

  return (
    <div className="step-card">
      <div className="step-number">1</div>
      <h3 className="step-title">Анализ домена</h3>
      <p className="step-description">
        Введите домен WordPress сайта для анализа внутренних ссылок
      </p>
      
      <form onSubmit={handleSubmit} style={{ marginTop: '16px' }}>
        <input
          type="text"
          className="input-apple"
          placeholder="example.com"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          disabled={isAnalyzing}
        />
        
        <button
          type="submit"
          className="btn-apple btn-primary btn-large"
          style={{ marginTop: '12px', width: '100%' }}
          disabled={!domain.trim() || isAnalyzing}
        >
          {isAnalyzing ? (
            <>
              <span className="loading-spinner"></span>
              Анализируем...
            </>
          ) : (
            '🔍 Начать анализ'
          )}
        </button>
      </form>
    </div>
  )
}

export default DomainInput 