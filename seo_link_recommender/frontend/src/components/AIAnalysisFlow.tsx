import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';
import { 
  Brain, 
  X, 
  Activity, 
  CheckCircle, 
  Clock,
  TrendingUp,
  Zap,
  Lightbulb,
  Target,
  BarChart3
} from 'lucide-react';

interface AIThought {
  thought_id: string;
  stage: string;
  content: string;
  confidence: number;
  semantic_weight: number;
  related_concepts: string[];
  reasoning_chain: string[];
  timestamp: string;
}

interface AIAnalysisFlowProps {
  isVisible: boolean;
  onClose: () => void;
  aiThoughts: AIThought[];
  currentStage: string;
  progress: number;
  className?: string;
}

export function AIAnalysisFlow({ 
  isVisible, 
  onClose, 
  aiThoughts, 
  currentStage, 
  progress, 
  className 
}: AIAnalysisFlowProps) {
  if (!isVisible) return null;

  const getStageInfo = (stage: string) => {
    const stages = {
      'analyzing': {
        title: 'Анализ контента',
        description: 'Извлечение ключевых концепций и семантический анализ',
        icon: <Brain className="w-5 h-5" />,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50'
      },
      'connecting': {
        title: 'Поиск связей',
        description: 'Установление семантических связей между статьями',
        icon: <Activity className="w-5 h-5" />,
        color: 'text-green-600',
        bgColor: 'bg-green-50'
      },
      'evaluating': {
        title: 'Оценка качества',
        description: 'Анализ релевантности и SEO-ценности связей',
        icon: <TrendingUp className="w-5 h-5" />,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50'
      },
      'optimizing': {
        title: 'Оптимизация',
        description: 'Формирование финальных рекомендаций',
        icon: <Zap className="w-5 h-5" />,
        color: 'text-purple-600',
        bgColor: 'bg-purple-50'
      },
      'vectorizing': {
        title: 'Векторизация',
        description: 'Создание семантических представлений',
        icon: <Lightbulb className="w-5 h-5" />,
        color: 'text-indigo-600',
        bgColor: 'bg-indigo-50'
      }
    };
    
    return stages[stage as keyof typeof stages] || {
      title: 'Обработка',
      description: 'Выполнение задачи',
      icon: <Activity className="w-5 h-5" />,
      color: 'text-gray-600',
      bgColor: 'bg-gray-50'
    };
  };

  const currentStageInfo = getStageInfo(currentStage);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className={cn(
        "w-full max-w-4xl max-h-[90vh] overflow-hidden bg-white rounded-lg shadow-2xl",
        className
      )}>
        {/* Заголовок */}
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-6 h-6 text-purple-600" />
              AI Анализ в процессе
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>
        </CardHeader>

        <div className="flex h-[calc(90vh-80px)]">
          {/* Левая панель - текущий этап */}
          <div className="w-1/3 border-r p-6">
            <div className="space-y-6">
              {/* Текущий этап */}
              <div className={cn(
                "p-4 rounded-lg border",
                currentStageInfo.bgColor
              )}>
                <div className="flex items-center gap-3 mb-3">
                  {currentStageInfo.icon}
                  <div>
                    <h3 className={cn("font-semibold", currentStageInfo.color)}>
                      {currentStageInfo.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {currentStageInfo.description}
                    </p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Прогресс</span>
                    <span>{Math.round(progress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Статистика */}
              <div className="space-y-3">
                <h4 className="font-medium">Статистика анализа</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {aiThoughts.length}
                    </div>
                    <div className="text-xs text-muted-foreground">Мыслей ИИ</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {Math.round(progress)}
                    </div>
                    <div className="text-xs text-muted-foreground">% готово</div>
                  </div>
                </div>
              </div>

              {/* Этапы процесса */}
              <div className="space-y-3">
                <h4 className="font-medium">Этапы процесса</h4>
                <div className="space-y-2">
                  {Object.entries({
                    'analyzing': 'Анализ контента',
                    'vectorizing': 'Векторизация',
                    'connecting': 'Поиск связей',
                    'evaluating': 'Оценка качества',
                    'optimizing': 'Оптимизация'
                  }).map(([stage, title]) => {
                    const stageInfo = getStageInfo(stage);
                    const isActive = currentStage === stage;
                    const isCompleted = aiThoughts.some(thought => thought.stage === stage);
                    
                    return (
                      <div
                        key={stage}
                        className={cn(
                          "flex items-center gap-3 p-2 rounded-lg border",
                          isActive && "bg-blue-50 border-blue-200",
                          isCompleted && !isActive && "bg-green-50 border-green-200",
                          !isActive && !isCompleted && "bg-gray-50 border-gray-200"
                        )}
                      >
                        {isCompleted ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : isActive ? (
                          <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
                        ) : (
                          <Clock className="w-4 h-4 text-gray-400" />
                        )}
                        <span className={cn(
                          "text-sm",
                          isActive && "font-medium text-blue-700",
                          isCompleted && !isActive && "text-green-700",
                          !isActive && !isCompleted && "text-gray-500"
                        )}>
                          {title}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Правая панель - мысли ИИ */}
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Мысли ИИ</h3>
                <Badge variant="outline">
                  {aiThoughts.length} мыслей
                </Badge>
              </div>

              {aiThoughts.length === 0 ? (
                <div className="text-center py-12">
                  <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">Ожидание мыслей ИИ...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {aiThoughts.slice().reverse().map((thought) => {
                    const stageInfo = getStageInfo(thought.stage);
                    
                    return (
                      <div
                        key={thought.thought_id}
                        className={cn(
                          "p-4 rounded-lg border",
                          stageInfo.bgColor
                        )}
                      >
                        <div className="flex items-start gap-3 mb-3">
                          <div className={cn(
                            "p-2 rounded-full text-white",
                            stageInfo.color.replace('text-', 'bg-')
                          )}>
                            {stageInfo.icon}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline" className="text-xs">
                                {thought.stage}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                Уверенность: {Math.round(thought.confidence * 100)}%
                              </span>
                            </div>
                            <p className="text-sm leading-relaxed">
                              {thought.content}
                            </p>
                          </div>
                        </div>

                        {/* Связанные концепции */}
                        {thought.related_concepts.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs text-muted-foreground mb-1">
                              Связанные концепции:
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {thought.related_concepts.slice(0, 5).map((concept, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {concept}
                                </Badge>
                              ))}
                              {thought.related_concepts.length > 5 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{thought.related_concepts.length - 5}
                                </Badge>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Цепочка рассуждений */}
                        {thought.reasoning_chain.length > 0 && (
                          <div>
                            <p className="text-xs text-muted-foreground mb-1">
                              Цепочка рассуждений:
                            </p>
                            <div className="space-y-1">
                              {thought.reasoning_chain.slice(0, 3).map((reason, idx) => (
                                <div key={idx} className="text-xs text-gray-600 flex items-start gap-2">
                                  <span className="text-gray-400">•</span>
                                  <span>{reason}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="text-xs text-muted-foreground mt-3">
                          {new Date(thought.timestamp).toLocaleTimeString('ru-RU')}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 