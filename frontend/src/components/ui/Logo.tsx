import React from 'react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'white' | 'dark';
  className?: string;
  showText?: boolean;
}

const Logo: React.FC<LogoProps> = ({ 
  size = 'md', 
  variant = 'default', 
  className = '',
  showText = true 
}) => {
  const sizeClasses = {
    sm: 'w-16 h-8',
    md: 'w-24 h-10',
    lg: 'w-32 h-12',
    xl: 'w-40 h-16',
  };

  const variantClasses = {
    default: 'text-gray-900',
    white: 'text-white',
    dark: 'text-gray-100',
  };

  const iconSize = {
    sm: 16,
    md: 20,
    lg: 24,
    xl: 32,
  };

  const textSize = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  return (
    <div className={`flex items-center gap-2 ${sizeClasses[size]} ${className}`}>
      {/* Иконка */}
      <div className="relative">
        <svg 
          width={iconSize[size]} 
          height={iconSize[size]} 
          viewBox="0 0 24 24" 
          className="flex-shrink-0"
        >
          <defs>
            <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#0ea5e9', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#0284c7', stopOpacity: 1 }} />
            </linearGradient>
            <filter id="logoShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="1" stdDeviation="2" floodColor="#000000" floodOpacity="0.1"/>
            </filter>
          </defs>
          
          {/* Фоновая форма */}
          <circle 
            cx="12" 
            cy="12" 
            r="10" 
            fill="url(#logoGradient)" 
            filter="url(#logoShadow)"
          />
          
          {/* Иконка ссылки */}
          <g transform="translate(4, 4)">
            <path 
              d="M8 4C5.79 4 4 5.79 4 8s1.79 4 4 4h2v-2H8c-1.1 0-2-.9-2-2s.9-2 2-2h2V4H8z" 
              fill="white" 
              opacity="0.9"
            />
            <path 
              d="M16 4h-2v2h2c1.1 0 2 .9 2 2s-.9 2-2 2h-2v2h2c2.21 0 4-1.79 4-4s-1.79-4-4-4z" 
              fill="white" 
              opacity="0.9"
            />
            <path 
              d="M12 6l-2 2 2 2" 
              stroke="white" 
              strokeWidth="1.5" 
              fill="none" 
              strokeLinecap="round"
            />
          </g>
        </svg>
      </div>

      {/* Текст */}
      {showText && (
        <span className={`font-semibold ${textSize[size]} ${variantClasses[variant]} tracking-tight`}>
          reLink
        </span>
      )}
    </div>
  );
};

export default Logo; 