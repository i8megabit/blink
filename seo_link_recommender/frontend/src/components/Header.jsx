import React from 'react'

function Header({ title, onMenuClick }) {
  return (
    <header className="content-header">
      <div className="flex items-center gap-4">
        <button
          className="btn btn-ghost btn-sm"
          onClick={onMenuClick}
          aria-label="Открыть меню"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 className="text-xl font-semibold">{title}</h1>
      </div>
      
      <div className="flex items-center gap-2">
        <div className="text-sm text-muted">
          SEO Link Recommender v2.0
        </div>
      </div>
    </header>
  )
}

export default Header 