import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'

interface Insight {
  id: string
  type: string
  title: string
  description: string
  severity: 'info' | 'warning' | 'error' | 'success'
  recommendation: string
  impact_score?: number
  confidence_level?: number
  actionability?: number
  evidence?: any
  created_at?: string
  category?: string
}

interface InsightsProps {
  domain?: string
  onApplyInsight?: (insight: Insight) => void
}

const Insights: React.FC<InsightsProps> = ({ domain, onApplyInsight }) => {
  const [insights, setInsights] = useState<Insight[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [expandedInsight, setExpandedInsight] = useState<string | null>(null)

  // Моковые данные для демонстрации расширенной аналитики
  const mockInsights: Insight[] = [
    {
      id: '1',
      type: 'semantic_network',
      title: 'Низкая плотность семантической сети',
      description: 'Обнаружено только 15 связей между 45 статьями. Это указывает на недостаточную внутреннюю перелинковку.',
      severity: 'warning',
      recommendation: 'Увеличить количество внутренних ссылок между тематически связанными статьями',
      impact_score: 0.85,
      confidence_level: 0.92,
      actionability: 0.78,
      category: 'semantic',
      evidence: {
        total_connections: 15,
        total_posts: 45,
        connection_density: 0.33,
        avg_connections_per_post: 0.67
      }
    },
    {
      id: '2',
      type: 'content_gaps',
      title: 'Обнаружены тематические пробелы',
      description: 'Анализ выявил 8 тематических кластеров с недостаточным контентом для полноценной перелинковки.',
      severity: 'info',
      recommendation: 'Создать дополнительный контент для заполнения тематических пробелов',
      impact_score: 0.72,
      confidence_level: 0.88,
      actionability: 0.65,
      category: 'content',
      evidence: {
        clusters_with_gaps: 8,
        total_clusters: 12,
        gap_percentage: 67,
        suggested_topics: ['SEO оптимизация', 'Контент маркетинг', 'Аналитика']
      }
    },
    {
      id: '3',
      type: 'performance_optimization',
      title: 'Высокий потенциал для оптимизации',
      description: 'Модель показывает 94% точность в рекомендациях, но есть возможности для улучшения скорости обработки.',
      severity: 'success',
      recommendation: 'Оптимизировать параметры модели для баланса качества и скорости',
      impact_score: 0.68,
      confidence_level: 0.95,
      actionability: 0.82,
      category: 'performance',
      evidence: {
        accuracy: 0.94,
        avg_response_time: 2.3,
        optimization_potential: 0.15,
        suggested_improvements: ['Увеличить batch_size', 'Оптимизировать контекст']
      }
    },
    {
      id: '4',
      type: 'user_experience',
      title: 'Отличное качество анкоров',
      description: 'Анализ показал, что 87% рекомендованных анкоров имеют высокое качество и релевантность.',
      severity: 'success',
      recommendation: 'Продолжать использовать текущую стратегию генерации анкоров',
      impact_score: 0.91,
      confidence_level: 0.89,
      actionability: 0.95,
      category: 'ux',
      evidence: {
        high_quality_anchors: 87,
        total_anchors: 100,
        avg_anchor_length: 4.2,
        semantic_relevance: 0.89
      }
    },
    {
      id: '5',
      type: 'seo_strategy',
      title: 'Недостаточное использование LSI ключевых слов',
      description: 'Только 23% статей содержат LSI ключевые слова в анкорах, что снижает SEO эффективность.',
      severity: 'warning',
      recommendation: 'Включить больше LSI ключевых слов в анкоры для улучшения SEO',
      impact_score: 0.76,
      confidence_level: 0.84,
      actionability: 0.71,
      category: 'seo',
      evidence: {
        lsi_usage: 23,
        total_articles: 100,
        suggested_lsi_keywords: ['поисковая оптимизация', 'внутренние ссылки', 'семантическое ядро']
      }
    },
    {
      id: '6',
      type: 'content_quality',
      title: 'Высокая семантическая связность',
      description: 'Анализ показал отличную семантическую связность между рекомендованными статьями (92%).',
      severity: 'success',
      recommendation: 'Использовать текущую стратегию для дальнейшего развития',
      impact_score: 0.88,
      confidence_level: 0.91,
      actionability: 0.85,
      category: 'semantic',
      evidence: {
        semantic_coherence: 92,
        avg_similarity_score: 0.87,
        coherence_trend: 'increasing'
      }
    }
  ]

  useEffect(() => {
    loadInsights()
  }, [domain])

  const loadInsights = async () => {
    setIsLoading(true)
    try {
      // В реальном приложении здесь был бы API запрос
      // const response = await fetch(`/api/v1/ai_insights/semantic_network?domain=${domain}`)
      // const data = await response.json()
      
      // Имитируем задержку загрузки
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setInsights(mockInsights)
    } catch (error) {
      console.error('Ошибка загрузки инсайтов:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'bg-red-100 text-red-800 border-red-200'
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'success': return 'bg-green-100 text-green-800 border-green-200'
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'semantic': return '🧠'
      case 'content': return '📝'
      case 'performance': return '⚡'
      case 'ux': return '👥'
      case 'seo': return '🎯'
      default: return '📊'
    }
  }

  const getCategoryName = (category: string) => {
    switch (category) {
      case 'semantic': return 'Семантика'
      case 'content': return 'Контент'
      case 'performance': return 'Производительность'
      case 'ux': return 'UX'
      case 'seo': return 'SEO'
      default: return 'Общее'
    }
  }

  const filteredInsights = insights.filter(insight => {
    const categoryMatch = selectedCategory === 'all' || insight.category === selectedCategory
    const severityMatch = selectedSeverity === 'all' || insight.severity === selectedSeverity
    return categoryMatch && severityMatch
  })

  const categories = ['all', 'semantic', 'content', 'performance', 'ux', 'seo']
  const severities = ['all', 'info', 'warning', 'error', 'success']

  const handleApplyInsight = (insight: Insight) => {
    if (onApplyInsight) {
      onApplyInsight(insight)
    }
  }

  const toggleInsightExpansion = (insightId: string) => {
    setExpandedInsight(expandedInsight === insightId ? null : insightId)
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
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={loadInsights}>
            Обновить
          </Button>
          <Button 
            variant="outline" 
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            {viewMode === 'grid' ? '📋 Список' : '📊 Сетка'}
          </Button>
        </div>
      </div>

      {/* Фильтры */}
      <div className="flex flex-wrap gap-4 p-4 bg-muted/50 rounded-lg">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Категория:</span>
          <select 
            value={selectedCategory} 
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1 text-sm border rounded-md bg-background"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat === 'all' ? 'Все' : getCategoryName(cat)}
              </option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Важность:</span>
          <select 
            value={selectedSeverity} 
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-1 text-sm border rounded-md bg-background"
          >
            {severities.map(sev => (
              <option key={sev} value={sev}>
                {sev === 'all' ? 'Все' : sev.charAt(0).toUpperCase() + sev.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-primary">{insights.length}</div>
            <div className="text-sm text-muted-foreground">Всего инсайтов</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">
              {insights.filter(i => i.severity === 'success').length}
            </div>
            <div className="text-sm text-muted-foreground">Успешных</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {insights.filter(i => i.severity === 'warning').length}
            </div>
            <div className="text-sm text-muted-foreground">Предупреждений</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">
              {Math.round(insights.reduce((acc, i) => acc + (i.impact_score || 0), 0) / insights.length * 100)}%
            </div>
            <div className="text-sm text-muted-foreground">Среднее влияние</div>
          </CardContent>
        </Card>
      </div>

      {/* Инсайты */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-6' : 'space-y-4'}>
        {filteredInsights.map((insight) => (
          <Card key={insight.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getCategoryIcon(insight.category || '')}</span>
                  <div>
                    <CardTitle className="text-lg">{insight.title}</CardTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className={getSeverityColor(insight.severity)}>
                        {insight.severity.toUpperCase()}
                      </Badge>
                      {insight.category && (
                        <Badge variant="outline">
                          {getCategoryName(insight.category)}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleInsightExpansion(insight.id)}
                >
                  {expandedInsight === insight.id ? '📖' : '📄'}
                </Button>
              </div>
            </CardHeader>
            
            <CardContent>
              <p className="text-muted-foreground mb-4">{insight.description}</p>
              
              {/* Метрики инсайта */}
              {insight.impact_score && (
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">
                      {Math.round(insight.impact_score * 100)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Влияние</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {Math.round((insight.confidence_level || 0) * 100)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Уверенность</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round((insight.actionability || 0) * 100)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Применимость</div>
                  </div>
                </div>
              )}

              {/* Доказательства */}
              {expandedInsight === insight.id && insight.evidence && (
                <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                  <h4 className="font-medium mb-2">📊 Доказательства:</h4>
                  <div className="text-sm space-y-1">
                    {Object.entries(insight.evidence).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-muted-foreground">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                        </span>
                        <span className="font-medium">
                          {typeof value === 'number' ? value.toFixed(2) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Рекомендация */}
              <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded-lg">
                <h4 className="font-medium text-primary mb-1">💡 Рекомендация:</h4>
                <p className="text-sm">{insight.recommendation}</p>
              </div>

              {/* Действия */}
              <div className="flex items-center gap-2 mt-4">
                <Button 
                  size="sm" 
                  onClick={() => handleApplyInsight(insight)}
                  className="flex-1"
                >
                  Применить
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => toggleInsightExpansion(insight.id)}
                >
                  {expandedInsight === insight.id ? 'Скрыть детали' : 'Показать детали'}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredInsights.length === 0 && (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-lg font-medium mb-2">Нет инсайтов</h3>
          <p className="text-muted-foreground">
            Попробуйте изменить фильтры или проведите анализ домена
          </p>
        </div>
      )}
    </div>
  )
}

export default Insights 