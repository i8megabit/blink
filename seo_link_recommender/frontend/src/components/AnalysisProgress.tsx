import React from 'react';
import { AIThought } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Progress } from './ui/Progress';
import { Badge } from './ui/Badge';
import { cn } from '../lib/utils';
import { 
  Brain, 
  Activity, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Lightbulb,
  TrendingUp,
  Zap
} from 'lucide-react';

interface AnalysisProgressProps {
  isActive: boolean;
  currentStep: string;
  progress: number;
  totalSteps: number;
  aiThoughts: AIThought[];
  analysisStats?: {
    postsAnalyzed?: number;
    connectionsFound?: number;
    recommendationsGenerated?: number;
    processingTime?: number;
  };
  error?: string;
  className?: string;
}

export function AnalysisProgress({
  isActive,
  currentStep,
  progress,
  totalSteps,
  aiThoughts,
  analysisStats,
  error,
  className
}: AnalysisProgressProps) {
  if (!isActive && !error && !analysisStats) {
    return null;
  }

  const getStageIcon = (stage: string) => {
    switch (stage) {
      case 'analyzing': return <Brain className="w-4 h-4" />;
      case 'connecting': return <Activity className="w-4 h-4" />;
      case 'evaluating': return <TrendingUp className="w-4 h-4" />;
      case 'optimizing': return <Zap className="w-4 h-4" />;
      case 'vectorizing': return <Lightbulb className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'analyzing': return 'bg-blue-500';
      case 'connecting': return 'bg-green-500';
      case 'evaluating': return 'bg-yellow-500';
      case 'optimizing': return 'bg-purple-500';
      case 'vectorizing': return 'bg-indigo-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Основной прогресс */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {error ? (
              <AlertCircle className="w-5 h-5 text-red-500" />
            ) : isActive ? (
              <Activity className="w-5 h-5 text-blue-500 animate-pulse" />
            ) : (
              <CheckCircle className="w-5 h-5 text-green-500" />
            )}
            {error ? 'Ошибка анализа' : isActive ? 'Анализ в процессе' : 'Анализ завершен'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {error ? (
            <div className="text-red-600 bg-red-50 p-3 rounded-lg">
              <p className="font-medium">Произошла ошибка:</p>
              <p className="text-sm">{error}</p>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Прогресс</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} max={100} className="h-2" />
              </div>

              {currentStep && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="w-4 h-4" />
                  <span>{currentStep}</span>
                </div>
              )}

              {/* Статистика анализа */}
              {analysisStats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                  {analysisStats.postsAnalyzed !== undefined && (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {analysisStats.postsAnalyzed}
                      </div>
                      <div className="text-xs text-muted-foreground">Статей проанализировано</div>
                    </div>
                  )}
                  {analysisStats.connectionsFound !== undefined && (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {analysisStats.connectionsFound}
                      </div>
                      <div className="text-xs text-muted-foreground">Связей найдено</div>
                    </div>
                  )}
                  {analysisStats.recommendationsGenerated !== undefined && (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {analysisStats.recommendationsGenerated}
                      </div>
                      <div className="text-xs text-muted-foreground">Рекомендаций</div>
                    </div>
                  )}
                  {analysisStats.processingTime !== undefined && (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {analysisStats.processingTime.toFixed(1)}с
                      </div>
                      <div className="text-xs text-muted-foreground">Время обработки</div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* AI Мысли */}
      {aiThoughts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              Мысли ИИ
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {aiThoughts.slice(-5).reverse().map((thought) => {
                const thoughtId = thought.id || thought.thought_id || `thought_${Date.now()}`;
                
                return (
                  <div
                    key={thoughtId}
                    className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-100"
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "p-2 rounded-full text-white",
                        getStageColor(thought.stage)
                      )}>
                        {getStageIcon(thought.stage)}
                      </div>
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {thought.stage}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            Уверенность: {Math.round(thought.confidence * 100)}%
                          </span>
                        </div>
                        <p className="text-sm">{thought.content}</p>
                        {thought.related_concepts.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {thought.related_concepts.slice(0, 3).map((concept, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {concept}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 