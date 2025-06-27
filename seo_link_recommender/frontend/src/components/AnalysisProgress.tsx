// import React from 'react'; // не нужен, если не используется напрямую
import { WebSocketMessage } from '../types';
import { cn } from '../lib/utils';
import { Card } from './ui/Card';

interface AnalysisProgressProps {
  messages: WebSocketMessage[];
  isActive: boolean;
  onClose?: () => void;
}

export function AnalysisProgress({ messages, isActive, onClose }: AnalysisProgressProps) {
  if (!isActive || messages.length === 0) {
    return null;
  }

  const latestMessage = messages[messages.length - 1];
  if (!latestMessage) {
    return null;
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="fixed bottom-4 right-4 z-40 max-w-lg w-full">
      <Card className="p-4 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border shadow-xl">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
            Анализ в процессе
          </h3>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ✕
            </button>
          )}
        </div>

        {/* Основной прогресс */}
        {latestMessage.type === 'progress' && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {latestMessage.step}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {latestMessage.current}/{latestMessage.total}
              </span>
            </div>
            
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-500 ease-out"
                style={{ 
                  width: `${latestMessage.percentage || 0}%` 
                }}
              />
            </div>
            
            {latestMessage.details && (
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                {latestMessage.details}
              </p>
            )}
          </div>
        )}

        {/* Последние мысли ИИ */}
        {latestMessage.type === 'ai_thinking' || latestMessage.type === 'enhanced_ai_thinking' && (
          <div className="mb-3">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Мысли ИИ
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {messages.filter(msg => 
                  msg.type === 'ai_thinking' || msg.type === 'enhanced_ai_thinking'
                ).length}
              </span>
            </div>
            
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {messages.filter(msg => 
                msg.type === 'ai_thinking' || msg.type === 'enhanced_ai_thinking'
              ).slice(-3).map((msg, index) => (
                <div
                  key={`${msg.timestamp}-${index}`}
                  className={cn(
                    'text-xs p-2 rounded-md border-l-2',
                    msg.type === 'enhanced_ai_thinking' 
                      ? 'bg-orange-50 dark:bg-orange-900/20 border-orange-300 dark:border-orange-600'
                      : 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-600'
                  )}
                >
                  <div className="flex items-start space-x-2">
                    <span className="flex-shrink-0">
                      {msg.emoji || '🧠'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {msg.thought || msg.content}
                      </p>
                      {msg.stage && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Этап: {msg.stage}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Статус Ollama */}
        {latestMessage.type === 'ollama' && latestMessage.info && (
          <div className="mb-3">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Статус Ollama
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {formatTime(latestMessage.timestamp)}
              </span>
            </div>
            
            <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
              {latestMessage.info.status && (
                <p>Статус: {latestMessage.info.status}</p>
              )}
              {latestMessage.info.processing_time && (
                <p>Время обработки: {latestMessage.info.processing_time}</p>
              )}
              {latestMessage.info.batch && (
                <p>Батч: {latestMessage.info.batch}</p>
              )}
            </div>
          </div>
        )}

        {/* Ошибки */}
        {latestMessage.type === 'error' && (
          <div className="mb-3">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm font-medium text-red-700 dark:text-red-400">
                Ошибка
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {formatTime(latestMessage.timestamp)}
              </span>
            </div>
            
            <div className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-md">
              {latestMessage.message || latestMessage.error}
            </div>
          </div>
        )}

        {/* Общая статистика */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
          <span>
            Сообщений: {messages.length}
          </span>
          <span>
            Последнее: {formatTime(latestMessage.timestamp)}
          </span>
        </div>
      </Card>
    </div>
  );
} 