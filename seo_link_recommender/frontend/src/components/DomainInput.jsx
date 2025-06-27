import React from 'react'

function DomainInput({ domain, setDomain, onAnalyze, isAnalyzing, ollamaStatus }) {
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!isAnalyzing && ollamaStatus.ready_for_work) {
      onAnalyze()
    }
  }

  const isDisabled = isAnalyzing || !ollamaStatus.ready_for_work

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="form-group">
        <label className="form-label">
          Домен WordPress
        </label>
        <input
          type="text"
          className="form-input"
          placeholder="example.com"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          disabled={isAnalyzing}
        />
        <div className="text-muted text-sm mt-2">
          Введите домен без протокола (http/https)
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`status-indicator ${
            ollamaStatus.ready_for_work ? 'status-success' : 'status-loading'
          }`}>
            {ollamaStatus.ready_for_work ? (
              <>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Готов к работе
              </>
            ) : (
              <>
                <div className="loading-spinner"></div>
                {ollamaStatus.message}
              </>
            )}
          </div>
        </div>

        <button
          type="submit"
          className={`btn btn-primary btn-lg ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          disabled={isDisabled}
        >
          {isAnalyzing ? (
            <>
              <div className="loading-spinner"></div>
              Анализирую...
            </>
          ) : (
            <>
              🔍
              Анализировать домен
            </>
          )}
        </button>
      </div>

      {!ollamaStatus.ready_for_work && (
        <div className="card bg-yellow-900/20 border-yellow-500/30">
          <div className="flex items-center gap-3">
            <div className="text-yellow-500">⚠️</div>
            <div>
              <div className="font-medium text-yellow-100">Ollama не готова</div>
              <div className="text-sm text-yellow-200">
                Дождитесь загрузки модели для начала анализа
              </div>
            </div>
          </div>
        </div>
      )}
    </form>
  )
}

export default DomainInput 