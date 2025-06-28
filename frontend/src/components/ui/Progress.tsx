import React from 'react'

interface ProgressProps {
  value: number
  max?: number
  className?: string
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  className = '',
  color = 'blue',
  size = 'md',
  showLabel = false
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
  
  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    yellow: 'bg-yellow-600',
    red: 'bg-red-600',
    purple: 'bg-purple-600'
  }
  
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className={`w-full bg-gray-200 rounded-full ${sizeClasses[size]}`}>
        <div
          className={`${colorClasses[color]} rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      {showLabel && (
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Прогресс</span>
          <span>{Math.round(percentage)}%</span>
        </div>
      )}
    </div>
  )
}

Progress.displayName = 'Progress' 