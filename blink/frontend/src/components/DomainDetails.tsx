import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'

interface DomainPost {
  id: number
  title: string
  link: string
  content_type: string
  difficulty_level: string
  linkability_score: number
  semantic_richness: number
  created_at: string
  key_concepts: string[]
}

interface DomainDetailsProps {
  domain: string
  onBack: () => void
}

const DomainDetails: React.FC<DomainDetailsProps> = ({ domain, onBack }) => {
  const [posts, setPosts] = useState<DomainPost[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'posts' | 'analytics'>('overview')

  useEffect(() => {
    loadDomainPosts()
  }, [domain])

  const loadDomainPosts = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`/api/v1/domains/${domain}/posts?limit=100`)
      if (response.ok) {
        const data = await response.json()
        setPosts(data.posts || [])
      }
    } catch (error) {
      console.error('Ошибка загрузки постов домена:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getContentTypeIcon = (type: string) => {
    const icons = {
      guide: '📖',
      review: '🔍',
      news: '📰',
      article: '📄',
      short_article: '📝'
    }
    return icons[type as keyof typeof icons] || '📄'
  }

  const getDifficultyColor = (level: string) => {
    const colors = {
      easy: 'success',
      medium: 'warning',
      advanced: 'destructive'
    }
    return colors[level as keyof typeof colors] || 'secondary'
  }

  const getDifficultyLabel = (level: string) => {
    const labels = {
      easy: 'Легкий',
      medium: 'Средний',
      advanced: 'Сложный'
    }
    return labels[level as keyof typeof labels] || level
  }

  const calculateStats = () => {
    if (!posts.length) return null

    const totalPosts = posts.length
    const avgLinkability = posts.reduce((sum, post) => sum + post.linkability_score, 0) / totalPosts
    const avgSemanticRichness = posts.reduce((sum, post) => sum + post.semantic_richness, 0) / totalPosts
    
    const contentTypes = posts.reduce((acc, post) => {
      acc[post.content_type] = (acc[post.content_type] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const difficultyLevels = posts.reduce((acc, post) => {
      acc[post.difficulty_level] = (acc[post.difficulty_level] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return {
      totalPosts,
      avgLinkability: avgLinkability.toFixed(2),
      avgSemanticRichness: avgSemanticRichness.toFixed(2),
      contentTypes,
      difficultyLevels
    }
  }

  const stats = calculateStats()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={onBack}>
            ← Назад
          </Button>
          <h1 className="text-2xl font-bold">Загрузка...</h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="h-4 bg-muted rounded animate-pulse" />
              </CardHeader>
              <CardContent>
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
      {/* Заголовок */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={onBack}>
          ← Назад
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{domain}</h1>
          <p className="text-muted-foreground">
            {posts.length} статей • Последнее обновление: {new Date().toLocaleDateString('ru-RU')}
          </p>
        </div>
      </div>

      {/* Вкладки */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg">
        {[
          { id: 'overview', label: 'Обзор', icon: '📊' },
          { id: 'posts', label: 'Статьи', icon: '📄' },
          { id: 'analytics', label: 'Аналитика', icon: '📈' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Контент вкладок */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Основная статистика */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Всего статей</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.totalPosts}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Проиндексировано статей
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Средняя связность</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.avgLinkability}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Потенциал для внутренних ссылок
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Семантическая насыщенность</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.avgSemanticRichness}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Качество контента
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Типы контента */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Распределение по типам контента</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {stats?.contentTypes && Object.entries(stats.contentTypes).map(([type, count]) => (
                  <div key={type} className="text-center">
                    <div className="text-2xl mb-1">{getContentTypeIcon(type)}</div>
                    <div className="font-medium">{count}</div>
                    <div className="text-xs text-muted-foreground capitalize">
                      {type.replace('_', ' ')}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Уровни сложности */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Уровни сложности</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {stats?.difficultyLevels && Object.entries(stats.difficultyLevels).map(([level, count]) => (
                  <div key={level} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant={getDifficultyColor(level) as any}>
                        {getDifficultyLabel(level)}
                      </Badge>
                    </div>
                    <div className="font-medium">{count} статей</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'posts' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Статьи домена</h3>
            <Button variant="outline" onClick={loadDomainPosts}>
              Обновить
            </Button>
          </div>

          <div className="grid gap-4">
            {posts.map((post) => (
              <Card key={post.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">{getContentTypeIcon(post.content_type)}</span>
                        <h4 className="font-medium line-clamp-1">{post.title}</h4>
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
                        <span>{new Date(post.created_at).toLocaleDateString('ru-RU')}</span>
                        <Badge variant={getDifficultyColor(post.difficulty_level) as any}>
                          {getDifficultyLabel(post.difficulty_level)}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-4 text-sm">
                        <span>Связность: {post.linkability_score.toFixed(2)}</span>
                        <span>Насыщенность: {post.semantic_richness.toFixed(2)}</span>
                      </div>

                      {post.key_concepts.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {post.key_concepts.slice(0, 5).map((concept, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {concept}
                            </Badge>
                          ))}
                          {post.key_concepts.length > 5 && (
                            <Badge variant="outline" className="text-xs">
                              +{post.key_concepts.length - 5}
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <a 
                        href={post.link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="btn btn-ghost btn-sm"
                      >
                        Открыть
                      </a>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">SEO Аналитика</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Общий SEO-потенциал</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-muted rounded-full h-2">
                      <div 
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{ width: `${(parseFloat(stats?.avgLinkability || '0') * 100)}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {Math.round(parseFloat(stats?.avgLinkability || '0') * 100)}%
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Качество контента</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-muted rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all"
                        style={{ width: `${(parseFloat(stats?.avgSemanticRichness || '0') * 100)}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">
                      {Math.round(parseFloat(stats?.avgSemanticRichness || '0') * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Рекомендации по улучшению</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {parseFloat(stats?.avgLinkability || '0') < 0.5 && (
                  <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <span className="text-yellow-600">⚠️</span>
                    <div>
                      <div className="font-medium text-yellow-800 dark:text-yellow-200">
                        Низкий потенциал внутренних ссылок
                      </div>
                      <div className="text-sm text-yellow-700 dark:text-yellow-300">
                        Рекомендуется увеличить количество статей с высоким потенциалом для перелинковки
                      </div>
                    </div>
                  </div>
                )}

                {parseFloat(stats?.avgSemanticRichness || '0') < 0.6 && (
                  <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <span className="text-blue-600">💡</span>
                    <div>
                      <div className="font-medium text-blue-800 dark:text-blue-200">
                        Возможности улучшения контента
                      </div>
                      <div className="text-sm text-blue-700 dark:text-blue-300">
                        Добавьте больше семантически богатого контента для лучшего ранжирования
                      </div>
                    </div>
                  </div>
                )}

                {stats?.difficultyLevels && Object.keys(stats.difficultyLevels).length < 3 && (
                  <div className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <span className="text-green-600">🎯</span>
                    <div>
                      <div className="font-medium text-green-800 dark:text-green-200">
                        Диверсификация контента
                      </div>
                      <div className="text-sm text-green-700 dark:text-green-300">
                        Добавьте контент разных уровней сложности для охвата всей аудитории
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default DomainDetails 