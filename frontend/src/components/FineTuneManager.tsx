import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Progress, Modal, Select } from './ui';

interface FineTuneJob {
  job_id: string;
  collection: string;
  status: string; // pending, running, completed, failed, cancelled
  started_at: number;
  finished_at?: number;
  progress: number;
  logs?: string[];
  error?: string;
  model_version?: string;
}

interface FineTuneManagerProps {
  routerUrl?: string;
}

export const FineTuneManager: React.FC<FineTuneManagerProps> = ({
  routerUrl = 'http://localhost:8004'
}) => {
  const [jobs, setJobs] = useState<FineTuneJob[]>([]);
  const [collections, setCollections] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [showStartModal, setShowStartModal] = useState(false);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadJobs();
    loadCollections();
    
    // Запуск polling для активных задач
    const interval = setInterval(() => {
      loadJobs();
    }, 5000);
    setPollingInterval(interval);

    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, []);

  const loadJobs = async () => {
    try {
      // Получаем все задачи fine-tune
      const response = await fetch(`${routerUrl}/api/v1/fine-tune/jobs`);
      if (response.ok) {
        const data = await response.json();
        setJobs(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки задач fine-tune:', error);
    }
  };

  const loadCollections = async () => {
    try {
      const response = await fetch(`${routerUrl}/api/v1/collections`);
      if (response.ok) {
        const data = await response.json();
        setCollections(data.map((col: any) => col.name));
      }
    } catch (error) {
      console.error('Ошибка загрузки коллекций:', error);
    }
  };

  const startFineTune = async () => {
    if (!selectedCollection) return;

    setLoading(true);
    try {
      const response = await fetch(`${routerUrl}/api/v1/fine-tune/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ collection: selectedCollection })
      });

      if (response.ok) {
        setShowStartModal(false);
        setSelectedCollection('');
        loadJobs();
      }
    } catch (error) {
      console.error('Ошибка запуска fine-tune:', error);
    } finally {
      setLoading(false);
    }
  };

  const cancelFineTune = async (jobId: string) => {
    if (!confirm(`Отменить задачу fine-tune ${jobId}?`)) return;

    try {
      const response = await fetch(`${routerUrl}/api/v1/fine-tune/${jobId}/cancel`, {
        method: 'POST'
      });

      if (response.ok) {
        loadJobs();
      }
    } catch (error) {
      console.error('Ошибка отмены fine-tune:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'warning';
      case 'failed': return 'error';
      case 'cancelled': return 'secondary';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return 'Ожидает';
      case 'running': return 'Выполняется';
      case 'completed': return 'Завершено';
      case 'failed': return 'Ошибка';
      case 'cancelled': return 'Отменено';
      default: return status;
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const formatDuration = (start: number, end?: number) => {
    const endTime = end || Date.now() / 1000;
    const duration = endTime - start;
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = Math.floor(duration % 60);
    
    if (hours > 0) {
      return `${hours}ч ${minutes}м ${seconds}с`;
    } else if (minutes > 0) {
      return `${minutes}м ${seconds}с`;
    } else {
      return `${seconds}с`;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Управление Fine-Tuning</h2>
        <Button onClick={() => setShowStartModal(true)}>
          Запустить Fine-Tune
        </Button>
      </div>

      <div className="grid gap-4">
        {jobs.map((job) => (
          <Card key={job.job_id} className="p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <h3 className="text-lg font-semibold">Задача {job.job_id}</h3>
                  <Badge variant={getStatusColor(job.status)}>
                    {getStatusText(job.status)}
                  </Badge>
                </div>
                <p className="text-gray-600">Коллекция: {job.collection}</p>
                <p className="text-gray-600 text-sm">
                  Начало: {formatDate(job.started_at)}
                </p>
                {job.finished_at && (
                  <p className="text-gray-600 text-sm">
                    Завершение: {formatDate(job.finished_at)}
                  </p>
                )}
                <p className="text-gray-600 text-sm">
                  Длительность: {formatDuration(job.started_at, job.finished_at)}
                </p>
                {job.model_version && (
                  <p className="text-gray-600 text-sm">
                    Версия модели: {job.model_version}
                  </p>
                )}
              </div>
              <div className="flex space-x-2">
                {(job.status === 'pending' || job.status === 'running') && (
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => cancelFineTune(job.job_id)}
                  >
                    Отменить
                  </Button>
                )}
              </div>
            </div>

            {job.status === 'running' && (
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>Прогресс</span>
                  <span>{Math.round(job.progress * 100)}%</span>
                </div>
                <Progress value={job.progress * 100} className="w-full" />
              </div>
            )}

            {job.error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
                <p className="text-red-800 text-sm font-medium">Ошибка:</p>
                <p className="text-red-700 text-sm">{job.error}</p>
              </div>
            )}

            {job.logs && job.logs.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-medium">Логи:</h4>
                <div className="max-h-40 overflow-y-auto bg-gray-50 p-3 rounded">
                  {job.logs.map((log, index) => (
                    <div key={index} className="text-sm font-mono text-gray-700">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        ))}

        {jobs.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Нет активных задач fine-tuning
          </div>
        )}
      </div>

      {/* Модальное окно запуска fine-tune */}
      <Modal
        isOpen={showStartModal}
        onClose={() => setShowStartModal(false)}
        title="Запустить Fine-Tuning"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Коллекция</label>
            <Select
              value={selectedCollection}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedCollection(e.target.value)}
            >
              <option value="">Выберите коллекцию</option>
              {collections.map((collection) => (
                <option key={collection} value={collection}>
                  {collection}
                </option>
              ))}
            </Select>
          </div>
          
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-sm text-blue-800">
              Fine-tuning будет запущен для выбранной коллекции. 
              Процесс может занять значительное время.
            </p>
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowStartModal(false)}>
              Отмена
            </Button>
            <Button 
              onClick={startFineTune} 
              disabled={!selectedCollection || loading}
            >
              {loading ? 'Запуск...' : 'Запустить'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}; 