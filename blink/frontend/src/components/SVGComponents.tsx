import React from 'react'

// 🎨 ЛОГОТИП Blink
export const Logo: React.FC<{ className?: string; size?: number }> = ({ 
  className = "", 
  size = 32 
}) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 64 64" 
    className={className}
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
  >
    {/* Фон */}
    <rect width="64" height="64" rx="12" fill="url(#logoGradient)" />
    
    {/* Ссылка */}
    <path 
      d="M16 32C16 23.1634 23.1634 16 32 16C40.8366 16 48 23.1634 48 32C48 40.8366 40.8366 48 32 48C23.1634 48 16 40.8366 16 32Z" 
      fill="white" 
      fillOpacity="0.1"
    />
    
    {/* Цепочка ссылок */}
    <path 
      d="M24 28L32 36L40 28M24 36L32 44L40 36" 
      stroke="white" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    />
    
    {/* Точки соединения */}
    <circle cx="32" cy="32" r="2" fill="white" />
    <circle cx="24" cy="28" r="1.5" fill="white" />
    <circle cx="40" cy="28" r="1.5" fill="white" />
    <circle cx="24" cy="36" r="1.5" fill="white" />
    <circle cx="40" cy="36" r="1.5" fill="white" />
    
    {/* Градиент */}
    <defs>
      <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#3B82F6" />
        <stop offset="50%" stopColor="#8B5CF6" />
        <stop offset="100%" stopColor="#06B6D4" />
      </linearGradient>
    </defs>
  </svg>
)

// 📊 ДИАГРАММА ТРАФИКА
export const TrafficChart: React.FC<{ 
  data: number[]; 
  width?: number; 
  height?: number;
  color?: string;
}> = ({ 
  data, 
  width = 300, 
  height = 150, 
  color = "#3B82F6" 
}) => {
  const maxValue = Math.max(...data)
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * (width - 40) + 20
    const y = height - 20 - ((value / maxValue) * (height - 40))
    return `${x},${y}`
  }).join(' ')

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Фон */}
      <rect width={width} height={height} fill="transparent" />
      
      {/* Сетка */}
      {Array.from({ length: 5 }).map((_, i) => (
        <line
          key={i}
          x1="20"
          y1={20 + (i * (height - 40) / 4)}
          x2={width - 20}
          y2={20 + (i * (height - 40) / 4)}
          stroke="#E5E7EB"
          strokeWidth="1"
          strokeDasharray="2,2"
        />
      ))}
      
      {/* Линия графика */}
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      
      {/* Точки данных */}
      {data.map((value, index) => {
        const x = (index / (data.length - 1)) * (width - 40) + 20
        const y = height - 20 - ((value / maxValue) * (height - 40))
        return (
          <circle
            key={index}
            cx={x}
            cy={y}
            r="4"
            fill={color}
            stroke="white"
            strokeWidth="2"
          />
        )
      })}
    </svg>
  )
}

// 🎯 КРУГОВАЯ ДИАГРАММА
export const PieChart: React.FC<{
  data: { label: string; value: number; color: string }[];
  size?: number;
}> = ({ data, size = 200 }) => {
  const total = data.reduce((sum, item) => sum + item.value, 0)
  let currentAngle = 0

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size / 2} cy={size / 2} r={size / 2 - 20} fill="none" />
      
      {data.map((item, index) => {
        const percentage = item.value / total
        const angle = percentage * 360
        const startAngle = currentAngle
        const endAngle = currentAngle + angle
        
        const x1 = size / 2 + (size / 2 - 20) * Math.cos((startAngle - 90) * Math.PI / 180)
        const y1 = size / 2 + (size / 2 - 20) * Math.sin((startAngle - 90) * Math.PI / 180)
        const x2 = size / 2 + (size / 2 - 20) * Math.cos((endAngle - 90) * Math.PI / 180)
        const y2 = size / 2 + (size / 2 - 20) * Math.sin((endAngle - 90) * Math.PI / 180)
        
        const largeArcFlag = angle > 180 ? 1 : 0
        
        const pathData = [
          `M ${size / 2} ${size / 2}`,
          `L ${x1} ${y1}`,
          `A ${size / 2 - 20} ${size / 2 - 20} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
          'Z'
        ].join(' ')
        
        currentAngle += angle
        
        return (
          <path
            key={index}
            d={pathData}
            fill={item.color}
            stroke="white"
            strokeWidth="2"
          />
        )
      })}
      
      {/* Легенда */}
      <g transform={`translate(10, ${size - 60})`}>
        {data.map((item, index) => (
          <g key={index} transform={`translate(0, ${index * 20})`}>
            <rect width="12" height="12" fill={item.color} rx="2" />
            <text x="20" y="10" fontSize="12" fill="#374151">
              {item.label} ({Math.round((item.value / total) * 100)}%)
            </text>
          </g>
        ))}
      </g>
    </svg>
  )
}

// 📈 СТОЛБЧАТАЯ ДИАГРАММА
export const BarChart: React.FC<{
  data: { label: string; value: number; color?: string }[];
  width?: number;
  height?: number;
}> = ({ data, width = 400, height = 200 }) => {
  const maxValue = Math.max(...data.map(d => d.value))
  const barWidth = (width - 60) / data.length - 10

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Сетка */}
      {Array.from({ length: 5 }).map((_, i) => (
        <line
          key={i}
          x1="40"
          y1={30 + (i * (height - 60) / 4)}
          x2={width - 20}
          y2={30 + (i * (height - 60) / 4)}
          stroke="#E5E7EB"
          strokeWidth="1"
          strokeDasharray="2,2"
        />
      ))}
      
      {/* Столбцы */}
      {data.map((item, index) => {
        const x = 50 + index * ((width - 60) / data.length)
        const barHeight = (item.value / maxValue) * (height - 80)
        const y = height - 30 - barHeight
        
        return (
          <g key={index}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              fill={item.color || "#3B82F6"}
              rx="4"
            />
            <text
              x={x + barWidth / 2}
              y={height - 10}
              textAnchor="middle"
              fontSize="10"
              fill="#6B7280"
            >
              {item.label}
            </text>
            <text
              x={x + barWidth / 2}
              y={y - 5}
              textAnchor="middle"
              fontSize="10"
              fill="#374151"
              fontWeight="bold"
            >
              {item.value}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

// 🎨 ИКОНКИ
export const Icons = {
  // Аналитика
  Analytics: ({ className = "", size = 24 }: { className?: string; size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} fill="none">
      <path d="M3 3v18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M18 17V9M12 17V5M6 17v-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  
  // Инсайты
  Insights: ({ className = "", size = 24 }: { className?: string; size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
      <path d="M12 16v-4M12 8h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  
  // SEO
  SEO: ({ className = "", size = 24 }: { className?: string; size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} fill="none">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  
  // Производительность
  Performance: ({ className = "", size = 24 }: { className?: string; size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} fill="none">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  
  // Контент
  Content: ({ className = "", size = 24 }: { className?: string; size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} fill="none">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <polyline points="14,2 14,8 20,8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <polyline points="10,9 9,9 8,9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  
  // UX
  UX: ({ className = "", size = 24 }: { className?: string; size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} fill="none">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  
  // Применить
  Apply: ({ className = "", size = 24 }: { className?: string; size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} fill="none">
      <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  
  // Подробнее
  Details: ({ className = "", size = 24 }: { className?: string; size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" className={className} fill="none">
      <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2"/>
      <path d="m21 21-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

// 🎨 ДЕКОРАТИВНЫЕ ЭЛЕМЕНТЫ
export const DecorativeElements = {
  // Волны
  Waves: ({ className = "", width = 200, height = 60 }: { className?: string; width?: number; height?: number }) => (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className}>
      <path
        d={`M0 ${height * 0.5} Q${width * 0.25} ${height * 0.2}, ${width * 0.5} ${height * 0.5} T${width} ${height * 0.5}`}
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        opacity="0.3"
      />
      <path
        d={`M0 ${height * 0.6} Q${width * 0.25} ${height * 0.3}, ${width * 0.5} ${height * 0.6} T${width} ${height * 0.6}`}
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.2"
      />
    </svg>
  ),
  
  // Точки
  Dots: ({ className = "", width = 100, height = 20 }: { className?: string; width?: number; height?: number }) => (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className}>
      {Array.from({ length: 5 }).map((_, i) => (
        <circle
          key={i}
          cx={10 + i * 20}
          cy={10}
          r="2"
          fill="currentColor"
          opacity="0.3"
        />
      ))}
    </svg>
  ),
  
  // Стрелки
  Arrows: ({ className = "", width = 60, height = 30 }: { className?: string; width?: number; height?: number }) => (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className={className}>
      <path
        d="M10 15L20 15M20 15L15 10M20 15L15 20"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
      />
      <path
        d="M30 15L40 15M40 15L35 10M40 15L35 20"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.4"
      />
    </svg>
  )
} 