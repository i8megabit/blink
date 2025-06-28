import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'

interface AnalyticsProps {
  domain?: string
}

interface MetricData {
  label: string
  value: number
  change?: number
  trend?: 'up' | 'down' | 'stable'
  color?: string
}

interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string
    borderColor?: string
  }[]
}

const Analytics: React.FC<AnalyticsProps> = ({ domain }) => {
  const [isLoading, setIsLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d')

  // Моковые данные для демонстрации
  const mockMetrics: MetricData[] = [
    { label: 'Общий трафик', value: 15420, change: 12.5, trend: 'up', color: 'text-blue-600' },
    { label: 'Конверсии', value: 234, change: 8.2, trend: 'up', color: 'text-green-600' },
    { label: 'Время на сайте', value: 4.2, change: -2.1, trend: 'down', color: 'text-yellow-600' },
    { label: 'Отказы', value: 32.1, change: -5.3, trend: 'up', color: 'text-red-600' },
    { label: 'SEO позиции', value: 15.3, change: 18.7, trend: 'up', color: 'text-purple-600' },
    { label: 'Внутренние ссылки', value: 89, change: 25.4, trend: 'up', color: 'text-indigo-600' }
  ]

  const mockChartData: ChartData = {
    labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
    datasets: [
      {
        label: 'Трафик',
        data: [1200, 1350, 1100, 1400, 1600, 1800, 1700],
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderColor: 'rgba(59, 130, 246, 1)'
      },
      {
        label: 'Конверсии',
        data: [12, 15, 8, 18, 22, 25, 20],
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderColor: 'rgba(34, 197, 94, 1)'
      }
    ]
  }

  useEffect(() => {
    loadAnalytics()
  }, [domain, timeRange])

  const loadAnalytics = async () => {
    setIsLoading(true)
    try {
      // Имитируем задержку загрузки
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (error) {
      console.error('Ошибка загрузки аналитики:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '📈'
      case 'down': return '📉'
      case 'stable': return '➡️'
      default: return '➡️'
    }
  }

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up': return 'text-green-600'
      case 'down': return 'text-red-600'
      case 'stable': return 'text-gray-600'
      default: return 'text-gray-600'
    }
  }

  const formatValue = (value: number, type: string) => {
    if (type === 'percentage') return `${value}%`
    if (type === 'time') return `${value} мин`
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
    return value.toString()
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="h-4 bg-muted rounded animate-pulse mb-2" />
                <div className="h-8 bg-muted rounded animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Заголовок и фильтры */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Расширенная аналитика</h2>
          <p className="text-muted-foreground">
            Детальный анализ производительности и SEO метрик
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-1 text-sm border rounded-md bg-background"
          >
            <option value="7d">7 дней</option>
            <option value="30d">30 дней</option>
            <option value="90d">90 дней</option>
          </select>
          <Button variant="outline" onClick={loadAnalytics}>
            Обновить
          </Button>
        </div>
      </div>

      {/* Основные метрики */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockMetrics.map((metric, index) => (
          <Card key={index} className="hover:shadow-lg transition-all duration-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-muted-foreground">
                  {metric.label}
                </h3>
                <Badge className={getTrendColor(metric.trend || 'stable')}>
                  {getTrendIcon(metric.trend || 'stable')}
                </Badge>
              </div>
              <div className="space-y-2">
                <div className={`text-3xl font-bold ${metric.color}`}>
                  {formatValue(metric.value, metric.label.toLowerCase())}
                </div>
                {metric.change && (
                  <div className={`text-sm ${getTrendColor(metric.trend || 'stable')}`}>
                    {metric.change > 0 ? '+' : ''}{metric.change}% с прошлого периода
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Графики и визуализация */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* График трафика */}
        <Card>
          <CardHeader>
            <CardTitle>Динамика трафика</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-end justify-between gap-2">
              {mockChartData.datasets[0]?.data.map((value, index) => (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div 
                    className="w-full bg-blue-500 rounded-t"
                    style={{ 
                      height: `${(value / Math.max(...(mockChartData.datasets[0]?.data || []))) * 200}px`,
                      minHeight: '4px'
                    }}
                  />
                  <span className="text-xs text-muted-foreground mt-2">
                    {mockChartData.labels[index]}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 text-center text-sm text-muted-foreground">
              Трафик за последние 7 дней
            </div>
          </CardContent>
        </Card>

        {/* График конверсий */}
        <Card>
          <CardHeader>
            <CardTitle>Конверсии</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-end justify-between gap-2">
              {mockChartData.datasets[1]?.data.map((value, index) => (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div 
                    className="w-full bg-green-500 rounded-t"
                    style={{ 
                      height: `${(value / Math.max(...(mockChartData.datasets[1]?.data || []))) * 200}px`,
                      minHeight: '4px'
                    }}
                  />
                  <span className="text-xs text-muted-foreground mt-2">
                    {mockChartData.labels[index]}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 text-center text-sm text-muted-foreground">
              Конверсии за последние 7 дней
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Детальная аналитика */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Топ страниц */}
        <Card>
          <CardHeader>
            <CardTitle>Топ страниц по трафику</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { page: '/glavnaya', traffic: 2340, change: 12.5 },
                { page: '/o-kompanii', traffic: 1890, change: 8.2 },
                { page: '/uslugi', traffic: 1560, change: -2.1 },
                { page: '/kontakty', traffic: 1230, change: 15.3 },
                { page: '/blog', traffic: 980, change: 25.4 }
              ].map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{item.page}</div>
                    <div className="text-xs text-muted-foreground">
                      {item.traffic.toLocaleString()} просмотров
                    </div>
                  </div>
                  <div className={`text-sm ${item.change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {item.change > 0 ? '+' : ''}{item.change}%
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Источники трафика */}
        <Card>
          <CardHeader>
            <CardTitle>Источники трафика</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { source: 'Поиск', percentage: 45, color: 'bg-blue-500' },
                { source: 'Прямой', percentage: 25, color: 'bg-green-500' },
                { source: 'Социальные сети', percentage: 20, color: 'bg-purple-500' },
                { source: 'Рефералы', percentage: 10, color: 'bg-yellow-500' }
              ].map((item, index) => (
                <div key={index}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{item.source}</span>
                    <span className="text-sm text-muted-foreground">{item.percentage}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${item.color}`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* SEO метрики */}
        <Card>
          <CardHeader>
            <CardTitle>SEO метрики</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { metric: 'Индекс страниц', value: 156, status: 'good' },
                { metric: 'Ошибки 404', value: 3, status: 'warning' },
                { metric: 'Дубли контента', value: 0, status: 'good' },
                { metric: 'Скорость загрузки', value: '2.3с', status: 'good' },
                { metric: 'Мобильная адаптация', value: '100%', status: 'good' }
              ].map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm">{item.metric}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{item.value}</span>
                    <div className={`w-2 h-2 rounded-full ${
                      item.status === 'good' ? 'bg-green-500' : 
                      item.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Рекомендации по улучшению */}
      <Card>
        <CardHeader>
          <CardTitle>Рекомендации по улучшению</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="font-medium text-green-600">✅ Что работает хорошо</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">•</span>
                  <span>Высокий рост органического трафика (+12.5%)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">•</span>
                  <span>Отличная мобильная адаптация (100%)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500 mt-1">•</span>
                  <span>Низкий процент дублей контента</span>
                </li>
              </ul>
            </div>
            <div className="space-y-4">
              <h4 className="font-medium text-yellow-600">⚠️ Требует внимания</h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-yellow-500 mt-1">•</span>
                  <span>Увеличить время на сайте (сейчас 4.2 мин)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-500 mt-1">•</span>
                  <span>Исправить 3 ошибки 404</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-500 mt-1">•</span>
                  <span>Улучшить контент на странице /uslugi</span>
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Analytics 