import { useState, useEffect } from 'react';
import { BenchmarkHistory, BenchmarkRequest } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';
import { 
  BarChart3,
  Play,
  CheckCircle,
  AlertCircle,
  Clock,
  Target,
  Eye,
  Plus,
  Loader2
} from 'lucide-react';

interface BenchmarksProps {
  className?: string;
  onViewBenchmark?: (benchmark: BenchmarkHistory) => void;
}

export function Benchmarks({ 
  className,
  onViewBenchmark
}: BenchmarksProps) {
  const [benchmarks, setBenchmarks] = useState<BenchmarkHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningBenchmark, setRunningBenchmark] = useState(false);

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

  const runBenchmark = async (benchmarkType: string) => {
    try {
      setRunningBenchmark(true);
      const request: BenchmarkRequest = {
        name: `${benchmarkType} Benchmark`,
        description: `Автоматический запуск ${benchmarkType} бенчмарка`,
        benchmark_type: benchmarkType,
        models: ['qwen2.5:7b-turbo', 'qwen2.5:7b-instruct-turbo'],
        iterations: 3,
        client_id: `benchmark_${Date.now()}`
      };

      const response = await fetch('/api/v1/benchmarks/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Бенчмарк запущен:', result);
        // Перезагружаем список бенчмарков
        setTimeout(loadBenchmarks, 2000);
      } else {
        throw new Error('Не удалось запустить бенчмарк');
      }
    } catch (err) {
      console.error('Ошибка запуска бенчмарка:', err);
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
    } finally {
      setRunningBenchmark(false);
    }
  };

  const runAllBenchmarks = async () => {
    const benchmarkTypes = ['seo_basic', 'seo_advanced', 'performance'];
    for (const type of benchmarkTypes) {
      await runBenchmark(type);
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

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid Date';
    }
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
            <div className="flex items-center gap-2">
              <Button 
                onClick={runAllBenchmarks} 
                disabled={runningBenchmark}
                className="flex items-center gap-2"
              >
                {runningBenchmark ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {runningBenchmark ? 'Запуск...' : 'Запустить все'}
              </Button>
              <Button 
                onClick={() => runBenchmark('seo_basic')} 
                disabled={runningBenchmark}
                variant="outline"
                size="sm"
              >
                <Plus className="w-4 h-4" />
                SEO Basic
              </Button>
              <Button 
                onClick={() => runBenchmark('seo_advanced')} 
                disabled={runningBenchmark}
                variant="outline"
                size="sm"
              >
                <Plus className="w-4 h-4" />
                SEO Advanced
              </Button>
              <Button 
                onClick={() => runBenchmark('performance')} 
                disabled={runningBenchmark}
                variant="outline"
                size="sm"
              >
                <Plus className="w-4 h-4" />
                Performance
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {benchmarks.length === 0 ? (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">Бенчмарки не найдены</p>
              <p className="text-sm text-gray-400 mb-4">
                Запустите первый бенчмарк для оценки производительности моделей
              </p>
              <div className="flex items-center justify-center gap-2">
                <Button onClick={() => runBenchmark('seo_basic')} size="sm">
                  <Play className="w-4 h-4 mr-2" />
                  Запустить SEO Basic
                </Button>
                <Button onClick={() => runBenchmark('seo_advanced')} size="sm" variant="outline">
                  <Play className="w-4 h-4 mr-2" />
                  Запустить SEO Advanced
                </Button>
              </div>
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
                            {getBenchmarkTypeName(benchmark.benchmark_type)}
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
                          <Clock className="w-4 h-4" />
                          <span>
                            {formatDate(benchmark.created_at)}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Target className="w-4 h-4" />
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