import { useState, useEffect } from 'react';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { Progress } from './ui/Progress';
import { 
  Brain, 
  Zap, 
  Target, 
  Lightbulb,
  TrendingUp,
  Activity,
  CheckCircle,
  AlertCircle,
  X
} from 'lucide-react';
import { AIThought } from '../types';

interface AIAnalysisFlowProps {
  isOpen: boolean;
  onClose: () => void;
  aiThoughts: AIThought[];
  analysisProgress: number;
  analysisStep: string;
}

interface StageInfo {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
}

export const AIAnalysisFlow: React.FC<AIAnalysisFlowProps> = ({
  isOpen,
  onClose,
  aiThoughts,
  analysisProgress,
  analysisStep
}) => {
  const [selectedThought, setSelectedThought] = useState<AIThought | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Автоскролл к новым мыслям
  useEffect(() => {
    if (autoScroll && aiThoughts.length > 0) {
      const lastThought = aiThoughts[aiThoughts.length - 1];
      if (lastThought) {
        setSelectedThought(lastThought);
      }
    }
  }, [aiThoughts, autoScroll]);

  const getStageInfo = (stage: string): StageInfo => {
    switch (stage) {
      case 'analyzing':
        return {
          icon: <Brain className="w-5 h-5" />,
          title: 'Анализ',
          description: 'Изучение контента и извлечение ключевых концепций',
          color: 'bg-blue-500'
        };
      case 'connecting':
        return {
          icon: <Zap className="w-5 h-5" />,
          title: 'Связывание',
          description: 'Поиск семантических связей между статьями',
          color: 'bg-green-500'
        };
      case 'evaluating':
        return {
          icon: <Target className="w-5 h-5" />,
          title: 'Оценка',
          description: 'Анализ качества и релевантности связей',
          color: 'bg-yellow-500'
        };
      case 'optimizing':
        return {
          icon: <TrendingUp className="w-5 h-5" />,
          title: 'Оптимизация',
          description: 'Улучшение рекомендаций и финальная обработка',
          color: 'bg-purple-500'
        };
      default:
        return {
          icon: <Activity className="w-5 h-5" />,
          title: 'Обработка',
          description: 'Выполнение анализа',
          color: 'bg-gray-500'
        };
    }
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'text-green-500';
    if (confidence >= 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getSemanticWeightColor = (weight: number): string => {
    if (weight >= 0.7) return 'text-blue-500';
    if (weight >= 0.4) return 'text-purple-500';
    return 'text-gray-500';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                AI Анализ в реальном времени
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Отслеживание процесса анализа ИИ
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setAutoScroll(!autoScroll)}
              className={autoScroll ? 'bg-green-100 text-green-700' : ''}
            >
              {autoScroll ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              Автоскролл
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Progress Section */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              {(() => {
                const stageInfo = getStageInfo(analysisStep);
                return (
                  <>
                    <div className={`p-2 rounded-lg ${stageInfo.color} bg-opacity-10`}>
                      {stageInfo.icon}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {stageInfo.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {stageInfo.description}
                      </p>
                    </div>
                  </>
                );
              })()}
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {analysisProgress}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Прогресс анализа
              </div>
            </div>
          </div>
          <Progress value={analysisProgress} className="w-full" />
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Thoughts List */}
          <div className="w-1/2 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
            <div className="p-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Мысли ИИ ({aiThoughts.length})
              </h3>
              <div className="space-y-3">
                {aiThoughts.map((thought, index) => (
                  <div
                    key={thought.id || index}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      selectedThought?.id === thought.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                    onClick={() => setSelectedThought(thought)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div className={`p-1 rounded ${getStageInfo(thought.stage).color} bg-opacity-10`}>
                          {getStageInfo(thought.stage).icon}
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {thought.stage}
                        </Badge>
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(thought.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
                      {thought.content || thought.thought}
                    </p>
                    <div className="flex items-center space-x-4 mt-2 text-xs">
                      <span className={`${getConfidenceColor(thought.confidence)}`}>
                        Уверенность: {(thought.confidence * 100).toFixed(0)}%
                      </span>
                      <span className={`${getSemanticWeightColor(thought.semantic_weight)}`}>
                        Вес: {(thought.semantic_weight * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Thought Details */}
          <div className="w-1/2 p-4 overflow-y-auto">
            {selectedThought ? (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    Детальный анализ мысли
                  </h3>
                  <div className="flex items-center space-x-2 mb-4">
                    <Badge variant="outline">{selectedThought.stage}</Badge>
                    <span className="text-sm text-gray-500">
                      {new Date(selectedThought.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                      Содержание
                    </h4>
                    <p className="text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                      {selectedThought.content || selectedThought.thought}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                        Уверенность
                      </h4>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${getConfidenceColor(selectedThought.confidence).replace('text-', 'bg-')}`}
                            style={{ width: `${selectedThought.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">
                          {(selectedThought.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                        Семантический вес
                      </h4>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${getSemanticWeightColor(selectedThought.semantic_weight).replace('text-', 'bg-')}`}
                            style={{ width: `${selectedThought.semantic_weight * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">
                          {(selectedThought.semantic_weight * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {selectedThought.related_concepts && selectedThought.related_concepts.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                        Связанные концепции
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedThought.related_concepts.map((concept, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {concept}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedThought.reasoning_chain && selectedThought.reasoning_chain.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                        Цепочка рассуждений
                      </h4>
                      <div className="space-y-2">
                        {selectedThought.reasoning_chain.map((step, index) => (
                          <div key={index} className="flex items-start space-x-2">
                            <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-xs font-medium text-blue-600 dark:text-blue-400 mt-0.5">
                              {index + 1}
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                              {step}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Lightbulb className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">
                    Выберите мысль ИИ для детального просмотра
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}; 