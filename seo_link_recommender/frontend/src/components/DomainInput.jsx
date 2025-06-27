import React from 'react'

function DomainInput({ domain, setDomain, onAnalyze, isAnalyzing }) {
  const handleSubmit = (e) => {
    e.preventDefault()
    if (domain.trim() && !isAnalyzing) {
      onAnalyze()
    }
  }

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <span className="text-2xl">🌐</span>
        Анализ WordPress сайта
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-2">
            Домен сайта
          </label>
          <input
            id="domain"
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="example.com"
            className="input-field"
            disabled={isAnalyzing}
            aria-describedby="domain-help"
          />
          <p id="domain-help" className="text-sm text-gray-600 mt-1">
            Введите домен без протокола (http/https)
          </p>
        </div>
        
        <button
          type="submit"
          disabled={!domain.trim() || isAnalyzing}
          className={`
            w-full button-primary disabled:opacity-50 disabled:cursor-not-allowed
            ${isAnalyzing ? 'animate-pulse' : ''}
          `}
        >
          {isAnalyzing ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              Анализирую...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <span>🔍</span>
              Начать анализ
            </span>
          )}
        </button>
      </form>
      
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-800 mb-2">📋 Что анализируется:</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Структура сайта и статьи WordPress</li>
          <li>• Семантические связи между контентом</li>
          <li>• Возможности для внутренней перелинковки</li>
          <li>• Рекомендации анкорных текстов</li>
        </ul>
      </div>
    </div>
  )
}

export default DomainInput 