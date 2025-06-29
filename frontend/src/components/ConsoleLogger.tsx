import React, { useEffect, useState } from 'react';
import { useLogger } from '@/utils/logger';

interface ConsoleLoggerProps {
  enabled?: boolean;
  showStats?: boolean;
  maxLogs?: number;
}

interface LogDisplay {
  id: string;
  timestamp: string;
  level: string;
  message: string;
  data?: any;
  context?: string;
  performance?: any;
  request?: any;
}

export const ConsoleLogger: React.FC<ConsoleLoggerProps> = ({
  enabled = true,
  showStats = true,
  maxLogs = 100
}) => {
  const logger = useLogger('ConsoleLogger');
  const [logs, setLogs] = useState<LogDisplay[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (!enabled) return;

    // Перехватываем console.log для отображения в компоненте
    const originalConsoleLog = console.log;
    const originalConsoleInfo = console.info;
    const originalConsoleWarn = console.warn;
    const originalConsoleError = console.error;
    const originalConsoleDebug = console.debug;

    const addLog = (level: string, message: string, data?: any) => {
      const logEntry: LogDisplay = {
        id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        level,
        message,
        data
      };

      setLogs(prev => {
        const newLogs = [...prev, logEntry];
        if (newLogs.length > maxLogs) {
          return newLogs.slice(-maxLogs);
        }
        return newLogs;
      });
    };

    // Переопределяем методы консоли
    console.log = (...args) => {
      originalConsoleLog(...args);
      addLog('INFO', args[0], args.slice(1));
    };

    console.info = (...args) => {
      originalConsoleInfo(...args);
      addLog('INFO', args[0], args.slice(1));
    };

    console.warn = (...args) => {
      originalConsoleWarn(...args);
      addLog('WARN', args[0], args.slice(1));
    };

    console.error = (...args) => {
      originalConsoleError(...args);
      addLog('ERROR', args[0], args.slice(1));
    };

    console.debug = (...args) => {
      originalConsoleDebug(...args);
      addLog('DEBUG', args[0], args.slice(1));
    };

    // Логируем инициализацию
    logger.info('🔧 ConsoleLogger компонент инициализирован', {
      enabled,
      showStats,
      maxLogs
    });

    // Обновляем статистику каждые 5 секунд
    const statsInterval = setInterval(() => {
      if (showStats) {
        setStats(logger.getStats());
      }
    }, 5000);

    return () => {
      // Восстанавливаем оригинальные методы
      console.log = originalConsoleLog;
      console.info = originalConsoleInfo;
      console.warn = originalConsoleWarn;
      console.error = originalConsoleError;
      console.debug = originalConsoleDebug;
      
      clearInterval(statsInterval);
    };
  }, [enabled, showStats, maxLogs, logger]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'DEBUG': return 'text-gray-500';
      case 'INFO': return 'text-blue-600';
      case 'WARN': return 'text-yellow-600';
      case 'ERROR': return 'text-red-600';
      case 'FATAL': return 'text-red-800 bg-red-100';
      default: return 'text-gray-700';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'DEBUG': return '🔍';
      case 'INFO': return 'ℹ️';
      case 'WARN': return '⚠️';
      case 'ERROR': return '❌';
      case 'FATAL': return '💥';
      default: return '📝';
    }
  };

  const clearLogs = () => {
    setLogs([]);
    logger.info('🧹 Логи очищены');
  };

  const exportLogs = () => {
    const logData = {
      timestamp: new Date().toISOString(),
      logs: logs,
      stats: stats
    };
    
    const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `relink-logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    logger.info('📤 Логи экспортированы');
  };

  if (!enabled) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Кнопка переключения видимости */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg shadow-lg mb-2 flex items-center gap-2"
      >
        📊 {isVisible ? 'Скрыть' : 'Показать'} логи
        {logs.length > 0 && (
          <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
            {logs.length}
          </span>
        )}
      </button>

      {isVisible && (
        <div className="bg-white border border-gray-300 rounded-lg shadow-xl w-96 max-h-96 overflow-hidden">
          {/* Заголовок */}
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-300 flex justify-between items-center">
            <h3 className="font-semibold text-gray-800">Консоль логов</h3>
            <div className="flex gap-2">
              <button
                onClick={clearLogs}
                className="text-xs bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded"
              >
                Очистить
              </button>
              <button
                onClick={exportLogs}
                className="text-xs bg-green-500 hover:bg-green-600 text-white px-2 py-1 rounded"
              >
                Экспорт
              </button>
            </div>
          </div>

          {/* Статистика */}
          {showStats && stats && (
            <div className="bg-blue-50 px-4 py-2 border-b border-gray-300 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div>Запросы: {stats.requestCount}</div>
                <div>Ошибки: {stats.errorCount}</div>
                <div>Предупреждения: {stats.warningCount}</div>
                <div>Активные: {stats.activeRequests}</div>
              </div>
            </div>
          )}

          {/* Логи */}
          <div className="max-h-64 overflow-y-auto p-2 space-y-1">
            {logs.length === 0 ? (
              <div className="text-gray-500 text-center py-4">
                Логи пока не появились...
              </div>
            ) : (
              logs.map((log) => (
                <div
                  key={log.id}
                  className={`text-xs p-2 rounded border-l-4 ${
                    log.level === 'ERROR' || log.level === 'FATAL'
                      ? 'bg-red-50 border-red-400'
                      : log.level === 'WARN'
                      ? 'bg-yellow-50 border-yellow-400'
                      : 'bg-gray-50 border-gray-300'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg">{getLevelIcon(log.level)}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`font-mono ${getLevelColor(log.level)}`}>
                          {log.level}
                        </span>
                        <span className="text-gray-500 text-xs">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-gray-800 mt-1">{log.message}</div>
                      
                      {/* Дополнительные данные */}
                      {log.data && (
                        <details className="mt-1">
                          <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                            📋 Данные
                          </summary>
                          <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                            {JSON.stringify(log.data, null, 2)}
                          </pre>
                        </details>
                      )}
                      
                      {/* Информация о производительности */}
                      {log.performance && (
                        <details className="mt-1">
                          <summary className="cursor-pointer text-green-600 hover:text-green-800">
                            ⚡ Производительность
                          </summary>
                          <pre className="text-xs bg-green-50 p-2 rounded mt-1 overflow-x-auto">
                            {JSON.stringify(log.performance, null, 2)}
                          </pre>
                        </details>
                      )}
                      
                      {/* Информация о запросе */}
                      {log.request && (
                        <details className="mt-1">
                          <summary className="cursor-pointer text-purple-600 hover:text-purple-800">
                            🌐 Запрос
                          </summary>
                          <pre className="text-xs bg-purple-50 p-2 rounded mt-1 overflow-x-auto">
                            {JSON.stringify(log.request, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Футер */}
          <div className="bg-gray-100 px-4 py-2 border-t border-gray-300 text-xs text-gray-600">
            Всего логов: {logs.length} | Максимум: {maxLogs}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConsoleLogger; 