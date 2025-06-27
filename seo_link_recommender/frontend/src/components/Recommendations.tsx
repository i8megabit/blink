import { useState } from 'react';
import { Recommendation } from '../types';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';

interface RecommendationsProps {
  recommendations: Recommendation[];
  domain: string;
  isLoading?: boolean;
  onCopy?: (recommendation: Recommendation) => void;
}

export function Recommendations({ 
  recommendations, 
  domain, 
  isLoading = false,
  onCopy 
}: RecommendationsProps) {
  const [expandedRecommendation, setExpandedRecommendation] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = async (recommendation: Recommendation) => {
    const sourceUrl = recommendation.source_post?.link || '';
    const targetUrl = recommendation.target_post?.link || '';
    const text = `[${recommendation.anchor_text}](${targetUrl})`;
    
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(sourceUrl + targetUrl);
      
      setTimeout(() => {
        setCopiedId(null);
      }, 2000);
      
      if (onCopy) {
        onCopy(recommendation);
      }
    } catch (err) {
      console.error('Ошибка копирования:', err);
    }
  };

  const formatUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.pathname;
    } catch {
      return url;
    }
  };

  const getQualityColor = (qualityScore?: number) => {
    if (!qualityScore) return 'text-gray-500';
    if (qualityScore >= 0.8) return 'text-green-600 dark:text-green-400';
    if (qualityScore >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getQualityLabel = (qualityScore?: number) => {
    if (!qualityScore) return 'Не оценено';
    if (qualityScore >= 0.8) return 'Отличное';
    if (qualityScore >= 0.6) return 'Хорошее';
    return 'Требует улучшения';
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Рекомендации
          </h2>
          <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-4 w-20 rounded"></div>
        </div>
        
        <div className="grid gap-4">
          {[...Array(5)].map((_, index) => (
            <Card key={index} className="p-4">
              <div className="animate-pulse space-y-3">
                <div className="bg-gray-200 dark:bg-gray-700 h-4 w-3/4 rounded"></div>
                <div className="bg-gray-200 dark:bg-gray-700 h-3 w-1/2 rounded"></div>
                <div className="bg-gray-200 dark:bg-gray-700 h-3 w-2/3 rounded"></div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <Card className="p-8 text-center">
        <div className="text-gray-500 dark:text-gray-400">
          <div className="text-4xl mb-4">🔍</div>
          <h3 className="text-lg font-medium mb-2">Рекомендации не найдены</h3>
          <p className="text-sm">
            Для домена {domain} пока нет сгенерированных рекомендаций.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Рекомендации ({recommendations.length})
        </h2>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Домен: {domain}
        </div>
      </div>

      <div className="grid gap-4">
        {recommendations.map((recommendation, index) => {
          const sourceUrl = recommendation.source_post?.link || '';
          const targetUrl = recommendation.target_post?.link || '';
          const recommendationId = `${sourceUrl}-${targetUrl}`;
          const isExpanded = expandedRecommendation === recommendationId;
          const isCopied = copiedId === recommendationId;

          return (
            <Card
              key={recommendationId}
              className={cn(
                'p-4 transition-all duration-200',
                isExpanded && 'ring-2 ring-blue-500'
              )}
            >
              <div className="space-y-3">
                {/* Заголовок с номером */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-xs font-medium">
                      {index + 1}
                    </span>
                    <h3 className="font-medium text-gray-900 dark:text-gray-100">
                      Рекомендация #{index + 1}
                    </h3>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {recommendation.quality_score !== undefined && (
                      <span className={cn(
                        'text-xs px-2 py-1 rounded-full',
                        getQualityColor(recommendation.quality_score),
                        'bg-opacity-10'
                      )}>
                        {getQualityLabel(recommendation.quality_score)}
                      </span>
                    )}
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(recommendation)}
                      className={cn(
                        'text-xs',
                        isCopied && 'text-green-600 dark:text-green-400'
                      )}
                    >
                      {isCopied ? 'Скопировано!' : 'Копировать'}
                    </Button>
                  </div>
                </div>

                {/* Анкор и ссылки */}
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Анкор:
                    </span>
                    <span className="text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
                      {recommendation.anchor_text}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Откуда:</span>
                      <div className="text-gray-700 dark:text-gray-300 font-mono text-xs break-all">
                        {formatUrl(sourceUrl)}
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Куда:</span>
                      <div className="text-gray-700 dark:text-gray-300 font-mono text-xs break-all">
                        {formatUrl(targetUrl)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Обоснование */}
                {recommendation.reasoning && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Обоснование:
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandedRecommendation(
                          isExpanded ? null : recommendationId
                        )}
                        className="text-xs"
                      >
                        {isExpanded ? 'Скрыть' : 'Показать'}
                      </Button>
                    </div>
                    
                    {isExpanded && (
                      <div className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
                        {recommendation.reasoning}
                      </div>
                    )}
                  </div>
                )}

                {/* Дополнительная информация */}
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                  <div className="flex items-center space-x-4">
                    <span>Статус: {recommendation.status}</span>
                    <span>Качество: {recommendation.quality_score?.toFixed(2) || 'N/A'}</span>
                  </div>
                  <span>
                    {new Date(recommendation.created_at).toLocaleDateString('ru-RU')}
                  </span>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Статистика */}
      <Card className="p-4 bg-gray-50 dark:bg-gray-800">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {recommendations.length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Всего рекомендаций
            </div>
          </div>
          
          <div>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {recommendations.filter(r => (r.quality_score || 0) >= 0.8).length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Высокого качества
            </div>
          </div>
          
          <div>
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {recommendations.filter(r => (r.quality_score || 0) >= 0.6 && (r.quality_score || 0) < 0.8).length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Хорошего качества
            </div>
          </div>
          
          <div>
            <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
              {recommendations.filter(r => !r.quality_score).length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Без оценки
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
} 