import React, { useEffect, useState } from 'react';
import { useNotifications } from '../hooks/useNotifications';
import { Card } from './ui/Card';
import { Button } from './ui/Button';

interface AnalysisRecord {
  id: string;
  domain: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  results?: any;
  metadata?: Record<string, any>;
}

const AnalysisHistory: React.FC = () => {
  const [analyses, setAnalyses] = useState<AnalysisRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const { showNotification } = useNotifications();

  const loadAnalysisHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/analysis/history?limit=50');
      if (!response.ok) {
        throw new Error('Failed to load analysis history');
      }
      const data = await response.json();
      setAnalyses(data);
    } catch (error) {
      showNotification('error', 'Ошибка загрузки истории анализов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysisHistory();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      case 'running': return 'text-blue-500';
      case 'pending': return 'text-yellow-500';
      default: return 'text-gray-400';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Загрузка истории анализов...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          История анализов
        </h1>
        <Button onClick={loadAnalysisHistory}>
          Обновить
        </Button>
      </div>

      <Card>
        <div className="space-y-4">
          {analyses.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              История анализов пуста
            </div>
          ) : (
            analyses.map((analysis) => (
              <div
                key={analysis.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {analysis.domain}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(analysis.status)}`}>
                      {analysis.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Создан: {formatDate(analysis.created_at)}
                    {analysis.completed_at && (
                      <span className="ml-4">
                        Завершен: {formatDate(analysis.completed_at)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      // TODO: Добавить просмотр деталей анализа
                      showNotification('info', 'Функция просмотра деталей в разработке');
                    }}
                  >
                    Детали
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};

export default AnalysisHistory;