import { Domain, AnalysisHistory } from '../types'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Badge } from './ui/Badge'
import { cn } from '../lib/utils'
import { 
  Globe, 
  FileText, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Activity,
  Target
} from 'lucide-react'

interface StatsProps {
  domain?: Domain | null
  analysisHistory?: AnalysisHistory[]
  className?: string
}

export function Stats({ domain, analysisHistory, className }: StatsProps) {
  const lastAnalysis = analysisHistory?.[0]
  const totalAnalyses = analysisHistory?.length || 0
  const totalConnections = analysisHistory?.reduce((sum, analysis) => sum + analysis.connections_found, 0) || 0
  const totalRecommendations = analysisHistory?.reduce((sum, analysis) => sum + analysis.recommendations_generated, 0) || 0

  const stats = [
    {
      title: 'Всего постов',
      value: domain?.total_posts || 0,
      icon: FileText,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20'
    },
    {
      title: 'Анализов',
      value: totalAnalyses,
      icon: Activity,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-50 dark:bg-green-900/20'
    },
    {
      title: 'Связей найдено',
      value: totalConnections,
      icon: TrendingUp,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20'
    },
    {
      title: 'Рекомендаций',
      value: totalRecommendations,
      icon: Target,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-50 dark:bg-orange-900/20'
    }
  ]

  return (
    <div className={cn('space-y-6', className)}>
      {/* Основная статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <Card key={index} className="p-4">
            <div className="flex items-center space-x-3">
              <div className={cn('p-2 rounded-lg', stat.bgColor)}>
                <stat.icon className={cn('w-5 h-5', stat.color)} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </p>
                <p className="text-2xl font-bold text-foreground">
                  {stat.value.toLocaleString()}
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Статус домена */}
      {domain && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Globe className="w-5 h-5" />
              <span>Статус домена</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="font-medium">Индексация:</span>
                <Badge 
                  variant={domain.is_indexed ? 'success' : 'warning'}
                  className="flex items-center space-x-1"
                >
                  {domain.is_indexed ? (
                    <>
                      <CheckCircle className="w-3 h-3" />
                      <span>Индексирован</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-3 h-3" />
                      <span>Не индексирован</span>
                    </>
                  )}
                </Badge>
              </div>
              
              <div className="text-sm text-muted-foreground">
                Язык: {domain.language}
              </div>
            </div>

            {domain.last_analysis_at && (
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span>
                  Последний анализ: {new Date(domain.last_analysis_at).toLocaleDateString('ru-RU', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Последний анализ */}
      {lastAnalysis && (
        <Card>
          <CardHeader>
            <CardTitle>Последний анализ</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-foreground">
                  {lastAnalysis.posts_analyzed}
                </p>
                <p className="text-sm text-muted-foreground">Постов проанализировано</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-foreground">
                  {lastAnalysis.connections_found}
                </p>
                <p className="text-sm text-muted-foreground">Связей найдено</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-foreground">
                  {lastAnalysis.recommendations_generated}
                </p>
                <p className="text-sm text-muted-foreground">Рекомендаций сгенерировано</p>
              </div>
            </div>
            
            {lastAnalysis.processing_time_seconds && (
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Время обработки:</span>
                  <span className="font-medium">
                    {lastAnalysis.processing_time_seconds.toFixed(1)}с
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Модель ИИ:</span>
                  <span className="font-medium">{lastAnalysis.llm_model_used}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
} 