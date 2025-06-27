import React from 'react'

function DomainsList({ domains, onRefresh }) {
  if (!domains || domains.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-muted mb-4">
          <div className="text-4xl mb-2">🌐</div>
          <div className="text-lg font-medium">Домены не найдены</div>
          <div className="text-sm">Начните с анализа первого домена</div>
        </div>
        <button 
          className="btn btn-secondary"
          onClick={onRefresh}
        >
          Обновить список
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted">
          Всего доменов: {domains.length}
        </div>
        <button 
          className="btn btn-ghost btn-sm"
          onClick={onRefresh}
        >
          🔄 Обновить
        </button>
      </div>

      <div className="space-y-3">
        {domains.map((domain) => (
          <div key={domain.id} className="card hover:border-accent-primary transition-all">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="font-medium text-primary">
                    {domain.display_name || domain.name}
                  </div>
                  {domain.is_indexed && (
                    <div className="badge badge-primary">
                      Индексирован
                    </div>
                  )}
                </div>
                
                <div className="text-sm text-muted mb-2">
                  {domain.name}
                </div>
                
                <div className="flex items-center gap-4 text-xs text-muted">
                  <div className="flex items-center gap-1">
                    <span>📄</span>
                    {domain.total_posts} статей
                  </div>
                  <div className="flex items-center gap-1">
                    <span>📊</span>
                    {domain.total_analyses} анализов
                  </div>
                  {domain.last_analysis_at && (
                    <div className="flex items-center gap-1">
                      <span>🕒</span>
                      {new Date(domain.last_analysis_at).toLocaleDateString('ru-RU')}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  domain.is_active ? 'bg-green-500' : 'bg-gray-500'
                }`}></div>
                <span className="text-xs text-muted">
                  {domain.is_active ? 'Активен' : 'Неактивен'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default DomainsList 