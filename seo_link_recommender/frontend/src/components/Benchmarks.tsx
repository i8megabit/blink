import { useState, useEffect } from 'react';
import { BenchmarkHistory } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';
import { Progress } from './ui/Progress';
import { 
  BarChart3,
  Play,
  Pause,
  RotateCcw,
  Download,
  Eye,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  Target,
  TrendingUp
} from 'lucide-react';

interface BenchmarksProps {
  className?: string;
  onViewBenchmark?: (benchmark: BenchmarkHistory) => void;
  onRunBenchmark?: () => void;
}

export function Benchmarks({ 
  className,
  onViewBenchmark,
  onRunBenchmark
}: BenchmarksProps) {
  const [benchmarks, setBenchmarks] = useState<BenchmarkHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBenchmarks();
  }, []);

  const loadBenchmarks = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/benchmarks');
      if (response.ok) {
        const data = await response.json();
        setBenchmarks(data.benchmarks || []);
      } else {
        throw new Error('Не удалось загрузить бенчмарки');
      }
    } catch (err) {
      console.error('Ошибка загрузки бенчмарков:', err);
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'running':
        return <Play className="w-4 h-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <Badge variant="success" className="flex items-center gap-1">
            <CheckCircle className="w-3 h-3" />
            Завершен
          </Badge>
        );
      case 'running':
        return (
          <Badge variant="warning" className="flex items-center gap-1">
            <Play className="w-3 h-3" />
            В процессе
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            Ошибка
          </Badge>
        );
      case 'pending':
        return (
          <Badge variant="warning" className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Ожидает
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            Неизвестно
          </Badge>
        );
    }
  };

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

  if (loading) {
    return (
      <div className={cn("space-y-4", className)}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Бенчмарки моделей
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[...Array(3)].map((_, index) => (
                <div key={index} className="animate-pulse">
                  <div className="bg-gray-200 h-20 rounded-lg"></div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("space-y-4", className)}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Бенчмарки моделей
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={loadBenchmarks} variant="outline">
                Попробовать снова
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Бенчмарки моделей ({benchmarks.length})
            </CardTitle>
            {onRunBenchmark && (
              <Button onClick={onRunBenchmark} className="flex items-center gap-2">
                <Play className="w-4 h-4" />
                Запустить бенчмарк
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {benchmarks.length === 0 ? (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">Бенчмарки не найдены</p>
              <p className="text-sm text-gray-400">
                Запустите первый бенчмарк для оценки производительности моделей
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {benchmarks.map((benchmark) => (
                <div
                  key={benchmark.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        {getStatusIcon(benchmark.status)}
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {benchmark.name}
                          </span>
                          {getStatusBadge(benchmark.status)}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                        <div className="text-center">
                          <div className={cn(
                            "text-lg font-bold",
                            getScoreColor(benchmark.overall_score)
                          )}>
                            {benchmark.overall_score ? (benchmark.overall_score * 100).toFixed(1) : 'N/A'}%
                          </div>
                          <div className="text-xs text-gray-500">Общий балл</div>
                        </div>
                        <div className="text-center">
                          <div className={cn(
                            "text-lg font-bold",
                            getScoreColor(benchmark.quality_score)
                          )}>
                            {benchmark.quality_score ? (benchmark.quality_score * 100).toFixed(1) : 'N/A'}%
                          </div>
                          <div className="text-xs text-gray-500">Качество</div>
                        </div>
                        <div className="text-center">
                          <div className={cn(
                            "text-lg font-bold",
                            getScoreColor(benchmark.performance_score)
                          )}>
                            {benchmark.performance_score ? (benchmark.performance_score * 100).toFixed(1) : 'N/A'}%
                          </div>
                          <div className="text-xs text-gray-500">Производительность</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-orange-600">
                            {benchmark.duration_seconds?.toFixed(1) || 'N/A'}с
                          </div>
                          <div className="text-xs text-gray-500">Время</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          <span>
                            {new Date(benchmark.created_at).toLocaleDateString('ru-RU', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Zap className="w-4 h-4" />
                          <span>{benchmark.benchmark_type}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Award className="w-4 h-4" />
                          <span>{getScoreBadge(benchmark.overall_score)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      {onViewBenchmark && benchmark.status === 'completed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onViewBenchmark(benchmark)}
                          className="flex items-center gap-1"
                        >
                          <Eye className="w-4 h-4" />
                          Детали
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 