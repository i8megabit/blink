import { BenchmarkHistory } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { 
  X,
  BarChart3,
  Clock,
  Target,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Zap,
  Award
} from 'lucide-react';

interface BenchmarkDetailsProps {
  benchmark: BenchmarkHistory | null;
  onClose: () => void;
}

export function BenchmarkDetails({ benchmark, onClose }: BenchmarkDetailsProps) {
  if (!benchmark) return null;

  const getScoreColor = (score: number | null) => {
    if (!score) return 'text-gray-500';
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadge = (score: number | null) => {
    if (!score) return 'Не оценено';
    if (score >= 0.8) return 'Отлично';
    if (score >= 0.6) return 'Хорошо';
    return 'Требует улучшения';
  };

  const getBenchmarkTypeName = (type: string) => {
    switch (type) {
      case 'seo_basic':
        return 'Базовый SEO бенчмарк';
      case 'seo_advanced':
        return 'Продвинутый SEO бенчмарк';
      case 'performance':
        return 'Бенчмарк производительности';
      default:
        return type;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid Date';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <BarChart3 className="w-6 h-6" />
              Детали бенчмарка
            </h2>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="p-2"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          <div className="space-y-6">
            {/* Основная информация */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Основная информация
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Название</label>
                    <p className="text-lg font-semibold">{getBenchmarkTypeName(benchmark.benchmark_type)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Статус</label>
                    <div className="flex items-center gap-2 mt-1">
                      {benchmark.status === 'completed' ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : benchmark.status === 'failed' ? (
                        <AlertCircle className="w-5 h-5 text-red-500" />
                      ) : (
                        <Clock className="w-5 h-5 text-yellow-500" />
                      )}
                      <Badge variant={benchmark.status === 'completed' ? 'success' : 'warning'}>
                        {benchmark.status === 'completed' ? 'Завершен' : 
                         benchmark.status === 'failed' ? 'Ошибка' : 'В процессе'}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Создан</label>
                    <p className="text-sm">{formatDate(benchmark.created_at)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Завершен</label>
                    <p className="text-sm">
                      {benchmark.completed_at ? formatDate(benchmark.completed_at) : 'Не завершен'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Результаты */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Результаты
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center p-4 border rounded-lg">
                    <div className={cn(
                      "text-3xl font-bold mb-2",
                      getScoreColor(benchmark.overall_score)
                    )}>
                      {benchmark.overall_score ? (benchmark.overall_score * 100).toFixed(1) : 'N/A'}%
                    </div>
                    <div className="text-sm text-gray-500 mb-2">Общий балл</div>
                    <Badge variant="outline">{getScoreBadge(benchmark.overall_score)}</Badge>
                  </div>
                  
                  <div className="text-center p-4 border rounded-lg">
                    <div className={cn(
                      "text-3xl font-bold mb-2",
                      getScoreColor(benchmark.quality_score)
                    )}>
                      {benchmark.quality_score ? (benchmark.quality_score * 100).toFixed(1) : 'N/A'}%
                    </div>
                    <div className="text-sm text-gray-500 mb-2">Качество</div>
                    <Badge variant="outline">{getScoreBadge(benchmark.quality_score)}</Badge>
                  </div>
                  
                  <div className="text-center p-4 border rounded-lg">
                    <div className={cn(
                      "text-3xl font-bold mb-2",
                      getScoreColor(benchmark.performance_score)
                    )}>
                      {benchmark.performance_score ? (benchmark.performance_score * 100).toFixed(1) : 'N/A'}%
                    </div>
                    <div className="text-sm text-gray-500 mb-2">Производительность</div>
                    <Badge variant="outline">{getScoreBadge(benchmark.performance_score)}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Временные метрики */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Временные метрики
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-orange-600 mb-2">
                      {benchmark.duration_seconds?.toFixed(1) || 'N/A'}с
                    </div>
                    <div className="text-sm text-gray-500">Общее время выполнения</div>
                  </div>
                  
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-blue-600 mb-2">
                      {benchmark.duration_seconds && benchmark.overall_score 
                        ? (benchmark.duration_seconds / benchmark.overall_score).toFixed(1) 
                        : 'N/A'}с/%
                    </div>
                    <div className="text-sm text-gray-500">Эффективность</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Рекомендации */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="w-5 h-5" />
                  Рекомендации
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {benchmark.overall_score && benchmark.overall_score < 0.6 && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <h4 className="font-medium text-red-800 mb-1">Требуется улучшение</h4>
                      <p className="text-sm text-red-600">
                        Общий балл ниже 60%. Рекомендуется проверить конфигурацию модели и параметры.
                      </p>
                    </div>
                  )}
                  
                  {benchmark.quality_score && benchmark.quality_score < 0.7 && (
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <h4 className="font-medium text-yellow-800 mb-1">Качество контента</h4>
                      <p className="text-sm text-yellow-600">
                        Качество генерируемого контента можно улучшить. Рассмотрите использование более качественной модели.
                      </p>
                    </div>
                  )}
                  
                  {benchmark.performance_score && benchmark.performance_score < 0.7 && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <h4 className="font-medium text-blue-800 mb-1">Производительность</h4>
                      <p className="text-sm text-blue-600">
                        Производительность ниже ожидаемой. Проверьте ресурсы системы и настройки модели.
                      </p>
                    </div>
                  )}
                  
                  {benchmark.overall_score && benchmark.overall_score >= 0.8 && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <h4 className="font-medium text-green-800 mb-1">Отличный результат</h4>
                      <p className="text-sm text-green-600">
                        Бенчмарк показывает отличные результаты. Модель работает эффективно.
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-end gap-3 mt-6 pt-6 border-t">
            <Button onClick={onClose} variant="outline">
              Закрыть
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
} 