import React from 'react'
import Logo from './ui/Logo'

interface HeaderProps {
  title?: string
  onMenuClick?: () => void
  subtitle?: string
  actions?: React.ReactNode
  showLogo?: boolean
  logoSize?: 'sm' | 'md' | 'lg' | 'xl'
}

const Header: React.FC<HeaderProps> = ({ 
  title, 
  onMenuClick, 
  subtitle, 
  actions,
  showLogo = true,
  logoSize = 'md'
}) => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {onMenuClick && (
            <button
              onClick={onMenuClick}
              className="p-2 rounded-md hover:bg-gray-100 transition-colors lg:hidden"
              aria-label="Открыть меню"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          )}
          
          {showLogo && <Logo size={logoSize} />}
          
          {title && (
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
              {subtitle && (
                <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
              )}
            </div>
          )}
        </div>
        
        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>
    </header>
  )
}

export default Header 