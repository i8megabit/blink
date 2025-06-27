import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'

interface ChartData {
  label: string
  value: number
  color?: string
}

interface LineChartProps {
  title: string
  data: Array<{ date: string; value: number }>
  height?: number
}

const LineChart: React.FC<LineChartProps> = ({ title, data, height = 200 }) => {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            Нет данных для отображения
          </div>
        </CardContent>
      </Card>
    )
  }

  const maxValue = Math.max(...data.map(d => d.value))
  const minValue = Math.min(...data.map(d => d.value))
  const range = maxValue - minValue

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative" style={{ height }}>
          <svg
            className="w-full h-full"
            viewBox={`0 0 ${data.length * 60} ${height}`}
            preserveAspectRatio="none"
          >
            {/* Сетка */}
            {Array.from({ length: 5 }).map((_, i) => (
              <line
                key={i}
                x1="0"
                y1={(height / 4) * i}
                x2={data.length * 60}
                y2={(height / 4) * i}
                stroke="currentColor"
                strokeOpacity="0.1"
                strokeWidth="1"
              />
            ))}

            {/* Линия графика */}
            <polyline
              fill="none"
              stroke="hsl(var(--primary))"
              strokeWidth="2"
              points={data
                .map((d, i) => `${i * 60},${height - ((d.value - minValue) / range) * height}`)
                .join(' ')}
            />

            {/* Точки */}
            {data.map((d, i) => (
              <circle
                key={i}
                cx={i * 60}
                cy={height - ((d.value - minValue) / range) * height}
                r="3"
                fill="hsl(var(--primary))"
              />
            ))}
          </svg>

          {/* Подписи осей */}
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            {data.map((d, i) => (
              <span key={i} className="text-center">
                {new Date(d.date).toLocaleDateString('ru-RU', { 
                  month: 'short', 
                  day: 'numeric' 
                })}
              </span>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface BarChartProps {
  title: string
  data: ChartData[]
  height?: number
}

const BarChart: React.FC<BarChartProps> = ({ title, data, height = 200 }) => {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            Нет данных для отображения
          </div>
        </CardContent>
      </Card>
    )
  }

  const maxValue = Math.max(...data.map(d => d.value))
  const barWidth = Math.max(20, 300 / data.length)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.map((item, index) => (
            <div key={index} className="flex items-center gap-3">
              <div className="w-24 text-sm text-muted-foreground truncate">
                {item.label}
              </div>
              <div className="flex-1 bg-muted rounded-full h-6 overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{
                    width: `${(item.value / maxValue) * 100}%`,
                    backgroundColor: item.color || 'hsl(var(--primary))'
                  }}
                />
              </div>
              <div className="w-12 text-sm font-medium text-right">
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

interface PieChartProps {
  title: string
  data: ChartData[]
  size?: number
}

const PieChart: React.FC<PieChartProps> = ({ title, data, size = 200 }) => {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            Нет данных для отображения
          </div>
        </CardContent>
      </Card>
    )
  }

  const total = data.reduce((sum, item) => sum + item.value, 0)
  const colors = [
    'hsl(var(--primary))',
    'hsl(var(--secondary))',
    'hsl(var(--accent))',
    'hsl(var(--destructive))',
    'hsl(var(--muted))'
  ]

  let currentAngle = 0
  const radius = size / 2 - 20

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center">
          <svg width={size} height={size} className="mr-6">
            <g transform={`translate(${size / 2}, ${size / 2})`}>
              {data.map((item, index) => {
                const percentage = item.value / total
                const angle = percentage * 360
                const startAngle = currentAngle
                currentAngle += angle

                const x1 = radius * Math.cos((startAngle * Math.PI) / 180)
                const y1 = radius * Math.sin((startAngle * Math.PI) / 180)
                const x2 = radius * Math.cos((currentAngle * Math.PI) / 180)
                const y2 = radius * Math.sin((currentAngle * Math.PI) / 180)

                const largeArcFlag = angle > 180 ? 1 : 0

                const pathData = [
                  `M 0 0`,
                  `L ${x1} ${y1}`,
                  `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                  'Z'
                ].join(' ')

                return (
                  <path
                    key={index}
                    d={pathData}
                    fill={item.color || colors[index % colors.length]}
                    stroke="white"
                    strokeWidth="2"
                  />
                )
              })}
            </g>
          </svg>

          <div className="space-y-2">
            {data.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor: item.color || colors[index % colors.length]
                  }}
                />
                <span className="text-sm">{item.label}</span>
                <span className="text-sm font-medium">
                  {((item.value / total) * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface ChartsProps {
  analysisHistory?: Array<{ date: string; value: number }>
  domainStats?: ChartData[]
  modelPerformance?: ChartData[]
}

const Charts: React.FC<ChartsProps> = ({
  analysisHistory = [],
  domainStats = [],
  modelPerformance = []
}) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LineChart
          title="Динамика рекомендаций"
          data={analysisHistory}
        />
        <BarChart
          title="Статистика по доменам"
          data={domainStats}
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PieChart
          title="Производительность моделей"
          data={modelPerformance}
        />
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Активность системы</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Анализы сегодня</span>
                <span className="text-sm font-medium">12</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Рекомендаций создано</span>
                <span className="text-sm font-medium">156</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Среднее время</span>
                <span className="text-sm font-medium">2.3с</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export { LineChart, BarChart, PieChart }
export default Charts 