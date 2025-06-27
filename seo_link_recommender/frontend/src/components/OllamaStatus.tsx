import { useState, useEffect } from 'react';
import { OllamaStatus as OllamaStatusType } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';
import { Progress } from './ui/Progress';
import { 
  Server, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  RefreshCw,
  Play,
  Pause,
  Settings,
  Zap,
  Brain,
  Activity
} from 'lucide-react';

interface OllamaStatusProps {
  status: OllamaStatusType;
  onRefresh?: () => void;
  className?: string;
}

export function OllamaStatus({ status, onRefresh, className }: OllamaStatusProps) {
  const getStatusIcon = () => {
    if (status.ready_for_work) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (status.server_available) {
      return <Clock className="w-5 h-5 text-yellow-500" />;
    } else {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusBadge = () => {
    if (status.ready_for_work) {
      return <Badge variant="default" className="bg-green-100 text-green-800">Готов к работе</Badge>;
    } else if (status.server_available) {
      return <Badge variant="outline" className="text-yellow-600">Подключается</Badge>;
    } else {
      return <Badge variant="destructive">Недоступен</Badge>;
    }
  };

  const getStatusColor = () => {
    if (status.ready_for_work) return 'text-green-600';
    if (status.server_available) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card className={cn("", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Статус Ollama
          </div>
          {onRefresh && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              disabled={status.ready_for_work}
              title="Обновить статус"
            >
              <RefreshCw className={cn(
                "w-4 h-4",
                status.ready_for_work && "animate-spin"
              )} />
            </Button>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Основной статус */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <p className={cn("font-medium", getStatusColor())}>
                {status.message || 'Проверка статуса...'}
              </p>
              <p className="text-sm text-muted-foreground">
                Последняя проверка: {new Date(status.last_check).toLocaleTimeString('ru-RU')}
              </p>
            </div>
          </div>
          {getStatusBadge()}
        </div>

        {/* Детальная информация */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Server className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-medium">Сервер</span>
            </div>
            <Badge 
              variant={status.server_available ? "default" : "destructive"}
              className="text-xs"
            >
              {status.server_available ? 'Доступен' : 'Недоступен'}
            </Badge>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Activity className="w-4 h-4" />
              <span className="text-sm font-medium">Модель</span>
            </div>
            <Badge 
              variant={status.model_loaded ? "default" : "destructive"}
              className="text-xs"
            >
              {status.model_loaded ? 'Загружена' : 'Не загружена'}
            </Badge>
          </div>
        </div>

        {/* Дополнительная информация */}
        {status.available_models && status.available_models.length > 0 && (
          <div className="pt-4 border-t">
            <h4 className="text-sm font-medium mb-2">Доступные модели:</h4>
            <div className="flex flex-wrap gap-1">
              {status.available_models.slice(0, 3).map((model, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {model}
                </Badge>
              ))}
              {status.available_models.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{status.available_models.length - 3}
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Рекомендации */}
        {!status.ready_for_work && (
          <div className="pt-4 border-t">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-orange-500 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-orange-700">Рекомендации:</p>
                <ul className="text-muted-foreground mt-1 space-y-1">
                  {!status.server_available && (
                    <li>• Проверьте, что Ollama запущена и доступна</li>
                  )}
                  {status.server_available && !status.model_loaded && (
                    <li>• Дождитесь загрузки модели или перезапустите Ollama</li>
                  )}
                  <li>• Убедитесь, что порт 11434 открыт</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Статистика производительности */}
        {status.ready_for_work && (
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Готов к работе</span>
              <div className="flex items-center gap-1">
                <Activity className="w-3 h-3 text-green-500" />
                <span className="text-green-600 font-medium">Активен</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 