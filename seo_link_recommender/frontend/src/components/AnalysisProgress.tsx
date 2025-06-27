import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Progress } from './ui/Progress';
import { 
  Activity,
  CheckCircle,
  Clock,
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
  X,
  Brain,
  Zap,
  Target,
  TrendingUp
} from 'lucide-react';

interface AnalysisProgressProps {
  isVisible: boolean;
  onClose: () => void;
  currentStep: string;
  progress: number;
  current: number;
  total: number;
  details: string;
  className?: string;
}

export function AnalysisProgress({
  isVisible,
  onClose,
  currentStep,
  progress,
  current,
  total,
  details,
  className
}: AnalysisProgressProps) {
  if (!isVisible) {
    return null;
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Основной прогресс */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            {details}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {current}
              </div>
              <div className="text-xs text-muted-foreground">Статей проанализировано</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {total}
              </div>
              <div className="text-xs text-muted-foreground">Связей найдено</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onClose}>
          Закрыть
        </Button>
      </div>
    </div>
  );
} 