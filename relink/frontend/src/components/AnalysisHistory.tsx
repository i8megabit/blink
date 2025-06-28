import { useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { History, Timer, CheckCircle, AlertCircle, Eye, Link } from 'lucide-react';
import { cn } from '../lib/utils';
import { AnalysisHistory as AnalysisHistoryType } from '../types';
import { useAnalysisHistory } from '../hooks/useApi';

// SEO-оптимизированные заголовки
const COMPONENT_TITLE = 'История SEO анализов';
const COMPONENT_DESCRIPTION = 'Просмотр результатов предыдущих SEO анализов доменов';

interface AnalysisHistoryProps {
  className?: string;
  onViewAnalysis?: (analysis: AnalysisHistoryType) => void;
  onRerunAnalysis?: (analysis: AnalysisHistoryType) => void;
}

export function AnalysisHistory({ 
  className,
  onViewAnalysis,
  onRerunAnalysis
}: AnalysisHistoryProps) {
  const { data: history = [], loading, error, execute: loadHistory } = useAnalysisHistory();

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const getStatusIcon = (completedAt: string | null) => {
    if (completedAt) {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    }
    return <Timer className="w-4 h-4 text-blue-500 animate-pulse" />;
  };

  const getStatusBadge = (completedAt: string | null) => {
    if (completedAt) {
      return (
        <Badge variant="success" className="flex items-center gap-1">
          <CheckCircle className="w-3 h-3" />
          Завершен
        </Badge>
      );
    }
    return (
      <Badge variant="warning" className="flex items-center gap-1">
        <Timer className="w-3 h-3" />
        В процессе
      </Badge>
    );
  };

  // Общий компонент заголовка для SEO
  const renderHeader = (count?: number) => (
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <History className="w-5 h-5" />
        {count !== undefined ? `${COMPONENT_TITLE} (${count})` : COMPONENT_TITLE}
      </CardTitle>
    </CardHeader>
  );

  if (loading) {
    return (
      <section className={cn("space-y-4", className)} aria-label={COMPONENT_DESCRIPTION}>
        <Card>
          {renderHeader()}
          <CardContent>
            <div className="space-y-3">
              {[...Array(5)].map((_, index) => (
                <div key={index} className="animate-pulse">
                  <div className="bg-gray-200 h-16 rounded-lg"></div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    );
  }

  if (error) {
    return (
      <section className={cn("space-y-4", className)} aria-label={COMPONENT_DESCRIPTION}>
        <Card>
          {renderHeader()}
          <CardContent>
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={loadHistory} variant="outline">
                Попробовать снова
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    );
  }

  if (history.length === 0) {
    return (
      <section className={cn("space-y-4", className)} aria-label={COMPONENT_DESCRIPTION}>
        <Card>
          {renderHeader()}
          <CardContent>
            <div className="text-center py-8">
              <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">История анализов пуста</p>
              <p className="text-sm text-gray-400">
                Запустите первый анализ, чтобы увидеть историю
              </p>
            </div>
          </CardContent>
        </Card>
      </section>
    );
  }

  return (
    <section className={cn("space-y-4", className)} aria-label={COMPONENT_DESCRIPTION}>
      <Card>
        {renderHeader(history.length)}
        <CardContent>
          <div className="space-y-3">
            {history.map((analysis: AnalysisHistoryType) => (
              <article
                key={analysis.id}
                className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {getStatusIcon(analysis.completed_at)}
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          Анализ #{analysis.id}
                        </span>
                        {getStatusBadge(analysis.completed_at)}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                      <div className="text-center">
                        <div className="text-lg font-bold text-blue-600">
                          {analysis.posts_analyzed}
                        </div>
                        <div className="text-xs text-gray-500">Постов</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-600">
                          {analysis.connections_found}
                        </div>
                        <div className="text-xs text-gray-500">Связей</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-purple-600">
                          {analysis.recommendations_generated}
                        </div>
                        <div className="text-xs text-gray-500">Рекомендаций</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-orange-600">
                          {analysis.processing_time_seconds?.toFixed(1) || 'N/A'}с
                        </div>
                        <div className="text-xs text-gray-500">Время</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Timer className="w-4 h-4" />
                        <time dateTime={analysis.created_at}>
                          {new Date(analysis.created_at).toLocaleDateString('ru-RU', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </time>
                      </div>
                      <div className="flex items-center gap-1">
                        <Link className="w-4 h-4" />
                        <span>{analysis.llm_model_used}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {onViewAnalysis && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewAnalysis(analysis)}
                        className="flex items-center gap-1"
                        aria-label={`Просмотреть анализ #${analysis.id}`}
                      >
                        <Eye className="w-4 h-4" />
                        Просмотр
                      </Button>
                    )}
                    {onRerunAnalysis && analysis.completed_at && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onRerunAnalysis(analysis)}
                        className="flex items-center gap-1"
                        aria-label={`Повторить анализ #${analysis.id}`}
                      >
                        <Timer className="w-4 h-4" />
                        Повторить
                      </Button>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </CardContent>
      </Card>
    </section>
  );
} 