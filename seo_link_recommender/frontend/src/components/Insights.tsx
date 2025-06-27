import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'

interface Insight {
  id: string
  type: 'pattern' | 'gap' | 'opportunity' | 'trend'
  category: 'semantic' | 'structural' | 'thematic'
  title: string
  description: string
  impact_score: number
  confidence_level: number
  actionability: number
  evidence: Record<string, any>
  status: 'discovered' | 'validated' | 'applied'
  created_at: string
}

interface InsightsProps {
  domain: string
  onApplyInsight?: (insight: Insight) => void
}

const Insights: React.FC<InsightsProps> = ({ domain, onApplyInsight }) => {
  const [insights, setInsights] = useState<Insight[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState<string>('all')

  useEffect(() => {
    loadInsights()
  }, [domain])

  const loadInsights = async () => {
    try {
      setIsLoading(true)
      // Здесь будет реальный API вызов
      // Пока используем моковые данные
      const mockInsights: Insight[] = [
        {
          id: '1',
          type: 'opportunity',
          category: 'semantic',
          title: 'Высокий потенциал межтематических связей',
          description: 'Обнаружено 5 тематических кластеров с высоким потенциалом перелинковки. Рекомендуется создать связи между кластерами для улучшения SEO.',
          impact_score: 0.8,
          confidence_level: 0.9,
          actionability: 0.85,
          evidence: {
            clusters_count: 5,
            avg_linkability: 0.75,
            potential_connections: 23
          },
          status: 'discovered',
          created_at: new Date().toISOString()
        },
        {
          id: '2',
          type: 'gap',
          category: 'structural',
          title: 'Низкая плотность внутренних связей',
          description: 'Домен имеет только 12 связей между статьями. Рекомендуется увеличить внутреннюю перелинковку для лучшего распределения веса.',
          impact_score: 0.7,
          confidence_level: 0.95,
          actionability: 0.9,
          evidence: {
            connection_density: 0.08,
            total_connections: 12,
            recommended_minimum: 50
          },
          status: 'discovered',
          created_at: new Date().toISOString()
        },
        {
          id: '3',
          type: 'pattern',
          category: 'thematic',
          title: 'Доминирование одного типа контента',
          description: '78% контента относится к типу "статья". Рекомендуется диверсифицировать контент, добавив гайды, обзоры и новости.',
          impact_score: 0.6,
          confidence_level: 0.8,
          actionability: 0.7,
          evidence: {
            content_distribution: {
              article: 78,
              guide: 12,
              review: 8,
              news: 2
            }
          },
          status: 'validated',
          created_at: new Date().toISOString()
        },
        {
          id: '4',
          type: 'trend',
          category: 'semantic',
          title: 'Рост семантической насыщенности',
          description: 'За последние 30 дней семантическая насыщенность контента выросла на 15%. Это положительная тенденция для SEO.',
          impact_score: 0.5,
          confidence_level: 0.85,
          actionability: 0.3,
          evidence: {
            growth_percentage: 15,
            time_period: '30 дней',
            trend_direction: 'positive'
          },
          status: 'applied',
          created_at: new Date().toISOString()
        }
      ]
      
      setInsights(mockInsights)
    } catch (error) {
      console.error('Ошибка загрузки инсайтов:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getInsightIcon = (type: string) => {
    const icons = {
      opportunity: '🎯',
      gap: '⚠️',
      pattern: '📊',
      trend: '📈'
    }
    return icons[type as keyof typeof icons] || '💡'
  }

  const getInsightColor = (type: string) => {
    const colors = {
      opportunity: 'success',
      gap: 'warning',
      pattern: 'primary',
      trend: 'secondary'
    }
    return colors[type as keyof typeof colors] || 'default'
  }

  const getStatusColor = (status: string) => {
    const colors = {
      discovered: 'default',
      validated: 'warning',
      applied: 'success'
    }
    return colors[status as keyof typeof colors] || 'default'
  }

  const getStatusLabel = (status: string) => {
    const labels = {
      discovered: 'Обнаружен',
      validated: 'Подтвержден',
      applied: 'Применен'
    }
    return labels[status as keyof typeof labels] || status
  }

  const filteredInsights = insights.filter(insight => {
    if (activeFilter === 'all') return true
    return insight.type === activeFilter
  })

  const handleApplyInsight = (insight: Insight) => {
    if (onApplyInsight) {
      onApplyInsight(insight)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <div className="h-4 bg-muted rounded animate-pulse" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="h-4 bg-muted rounded animate-pulse" />
                <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Заголовок и фильтры */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">AI Инсайты</h2>
          <p className="text-muted-foreground">
            Интеллектуальные рекомендации для улучшения SEO
          </p>
        </div>
        <Button variant="outline" onClick={loadInsights}>
          Обновить
        </Button>
      </div>

      {/* Фильтры */}
      <div className="flex space-x-2">
        {[
          { id: 'all', label: 'Все', count: insights.length },
          { id: 'opportunity', label: 'Возможности', count: insights.filter(i => i.type === 'opportunity').length },
          { id: 'gap', label: 'Пробелы', count: insights.filter(i => i.type === 'gap').length },
          { id: 'pattern', label: 'Паттерны', count: insights.filter(i => i.type === 'pattern').length },
          { id: 'trend', label: 'Тренды', count: insights.filter(i => i.type === 'trend').length }
        ].map((filter) => (
          <button
            key={filter.id}
            onClick={() => setActiveFilter(filter.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeFilter === filter.id
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            }`}
          >
            {filter.label} ({filter.count})
          </button>
        ))}
      </div>

      {/* Список инсайтов */}
      <div className="space-y-4">
        {filteredInsights.map((insight) => (
          <Card key={insight.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="text-2xl">{getInsightIcon(insight.type)}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle className="text-lg">{insight.title}</CardTitle>
                      <Badge variant={getInsightColor(insight.type) as any}>
                        {insight.type}
                      </Badge>
                      <Badge variant={getStatusColor(insight.status) as any}>
                        {getStatusLabel(insight.status)}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground">{insight.description}</p>
                  </div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent>
              {/* Метрики инсайта */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">
                    {Math.round(insight.impact_score * 100)}%
                  </div>
                  <div className="text-xs text-muted-foreground">Влияние</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {Math.round(insight.confidence_level * 100)}%
                  </div>
                  <div className="text-xs text-muted-foreground">Уверенность</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {Math.round(insight.actionability * 100)}%
                  </div>
                  <div className="text-xs text-muted-foreground">Применимость</div>
                </div>
              </div>

              {/* Доказательства */}
              {Object.keys(insight.evidence).length > 0 && (
                <div className="bg-muted p-3 rounded-lg mb-4">
                  <div className="text-sm font-medium mb-2">Доказательства:</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    {Object.entries(insight.evidence).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-muted-foreground capitalize">
                          {key.replace('_', ' ')}:
                        </span>
                        <span className="font-medium">
                          {typeof value === 'object' ? JSON.stringify(value) : value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Действия */}
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground">
                  Обнаружен: {new Date(insight.created_at).toLocaleDateString('ru-RU')}
                </div>
                <div className="flex gap-2">
                  {insight.status === 'discovered' && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleApplyInsight(insight)}
                    >
                      Применить
                    </Button>
                  )}
                  <Button variant="ghost" size="sm">
                    Подробнее
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredInsights.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-lg font-medium mb-2">Инсайты не найдены</h3>
            <p className="text-muted-foreground">
              {activeFilter === 'all' 
                ? 'Попробуйте выполнить анализ домена для получения инсайтов'
                : `Нет инсайтов типа "${activeFilter}"`
              }
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Insights 