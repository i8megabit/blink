import React, { useState, useEffect, useCallback } from 'react';
import { 
  Domain, 
  Recommendation, 
  WebSocketMessage, 
  Notification,
  OllamaStatus 
} from './types';
import { useWebSocket } from './hooks/useWebSocket';
import { useNotifications } from './hooks/useNotifications';
import { useDomains, useOllamaStatus } from './hooks/useApi';
import { useAnalysisHistory } from './hooks/useAnalysisHistory';
import { Notifications } from './components/Notifications';
import { AnalysisProgress } from './components/AnalysisProgress';
import { Recommendations } from './components/Recommendations';
import { Stats } from './components/Stats';
import { Button } from './components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/Card';
import { Badge } from './components/ui/Badge';
import { cn } from './lib/utils';
import { 
  Globe, 
  Play, 
  RefreshCw, 
  Activity,
  CheckCircle,
  AlertCircle,
  Settings,
  BarChart3
} from 'lucide-react';

function App() {
  // Состояние приложения
  const [domains, setDomains] = useState<Domain[]>([]);
  const [currentDomain, setCurrentDomain] = useState<Domain | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisMessages, setAnalysisMessages] = useState<WebSocketMessage[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus | null>(null);
  const [showStats, setShowStats] = useState(false);

  // Хуки
  const { notifications, addNotification, removeNotification, clearNotifications } = useNotifications();
  const { data: domainsData, loading: domainsLoading, execute: loadDomains } = useDomains();
  const { data: ollamaData, loading: ollamaLoading, execute: checkOllamaStatus } = useOllamaStatus();
  const { 
    data: analysisHistory, 
    loading: historyLoading, 
    execute: loadAnalysisHistory 
  } = useAnalysisHistory({
    limit: 5,
    autoRefresh: false
  });

  // WebSocket для анализа
  const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const { status: wsStatus } = useWebSocket({
    url: 'ws://localhost:8000/ws',
    clientId,
    onMessage: handleWebSocketMessage,
    onError: handleWebSocketError
  });

  // Обработчики WebSocket
  function handleWebSocketMessage(message: WebSocketMessage) {
    setAnalysisMessages(prev => [...prev, message]);

    // Обработка различных типов сообщений
    switch (message.type) {
      case 'progress':
        if (message.percentage === 100) {
          setIsAnalyzing(false);
          addNotification({
            type: 'success',
            title: 'Анализ завершен',
            message: `Анализ домена ${currentDomain?.name} успешно завершен`,
            details: `Обработано ${message.current} из ${message.total} шагов`
          });
          // Обновляем историю после завершения анализа
          if (currentDomain?.id) {
            loadAnalysisHistory(currentDomain.id);
          }
        }
        break;

      case 'error':
        setIsAnalyzing(false);
        addNotification({
          type: 'error',
          title: 'Ошибка анализа',
          message: message.message || 'Произошла ошибка во время анализа',
          details: message.error || 'Детали ошибки недоступны'
        });
        break;

      case 'ai_thinking':
      case 'enhanced_ai_thinking':
        // Можно добавить логику для отображения мыслей ИИ
        break;
    }
  }

  function handleWebSocketError(error: Event) {
    console.error('WebSocket ошибка:', error);
    addNotification({
      type: 'error',
      title: 'Ошибка соединения',
      message: 'Потеряно соединение с сервером анализа',
      details: 'Попытка переподключения...'
    });
  }

  // Загрузка данных при монтировании
  useEffect(() => {
    loadDomains();
    checkOllamaStatus();
  }, []);

  // Обновление состояния при получении данных
  useEffect(() => {
    if (domainsData) {
      setDomains(domainsData);
    }
  }, [domainsData]);

  useEffect(() => {
    if (ollamaData) {
      setOllamaStatus(ollamaData);
    }
  }, [ollamaData]);

  // Загрузка истории при выборе домена
  useEffect(() => {
    if (currentDomain?.id) {
      loadAnalysisHistory(currentDomain.id);
    }
  }, [currentDomain?.id, loadAnalysisHistory]);

  // Обработчики действий
  const handleAnalyzeDomain = useCallback(async (domain: Domain) => {
    if (!ollamaStatus?.ready_for_work) {
      addNotification({
        type: 'warning',
        title: 'Ollama не готова',
        message: 'Дождитесь готовности Ollama перед началом анализа',
        details: ollamaStatus?.message || 'Статус неизвестен'
      });
      return;
    }

    setIsAnalyzing(true);
    setAnalysisMessages([]);
    setCurrentDomain(domain);
    setRecommendations([]);

    addNotification({
      type: 'info',
      title: 'Анализ запущен',
      message: `Начинаю анализ домена ${domain.name}`,
      details: 'Подключение к WebSocket...'
    });

    try {
      const response = await fetch('/api/v1/wp_index', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: domain.name,
          comprehensive: true,
          client_id: clientId
        }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        setRecommendations(data.recommendations || []);
        addNotification({
          type: 'success',
          title: 'Анализ завершен',
          message: `Найдено ${data.recommendations?.length || 0} рекомендаций`,
          details: `Время анализа: ${data.analysis_time?.toFixed(1)}с`
        });
      } else {
        throw new Error(data.error || 'Неизвестная ошибка');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Ошибка сети';
      addNotification({
        type: 'error',
        title: 'Ошибка анализа',
        message: errorMessage,
        details: 'Проверьте подключение к серверу'
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [ollamaStatus, clientId, addNotification, loadAnalysisHistory]);

  const handleCopyRecommendation = useCallback((recommendation: Recommendation) => {
    addNotification({
      type: 'success',
      title: 'Скопировано',
      message: 'Рекомендация скопирована в буфер обмена',
      duration: 3000
    });
  }, [addNotification]);

  const handleCloseAnalysis = useCallback(() => {
    setIsAnalyzing(false);
    setAnalysisMessages([]);
  }, []);

  const handleSelectDomain = useCallback((domain: Domain) => {
    setCurrentDomain(domain);
    setShowStats(true);
  }, []);

  // Рендер компонентов
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Уведомления */}
      <Notifications
        notifications={notifications}
        onRemove={removeNotification}
        onClear={clearNotifications}
      />

      {/* Прогресс анализа */}
      <AnalysisProgress
        messages={analysisMessages}
        isActive={isAnalyzing}
        onClose={handleCloseAnalysis}
      />

      {/* Основной контент */}
      <div className="container mx-auto px-4 py-8">
        {/* Заголовок */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            SEO Link Recommender
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Интеллектуальная система генерации внутренних ссылок
          </p>
        </div>

        {/* Статус Ollama */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={cn(
                  'w-3 h-3 rounded-full',
                  ollamaStatus?.ready_for_work 
                    ? 'bg-green-500' 
                    : ollamaLoading 
                      ? 'bg-yellow-500' 
                      : 'bg-red-500'
                )} />
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  Статус Ollama
                </span>
                <Badge 
                  variant={ollamaStatus?.ready_for_work ? 'success' : 'warning'}
                  className="flex items-center space-x-1"
                >
                  {ollamaStatus?.ready_for_work ? (
                    <>
                      <CheckCircle className="w-3 h-3" />
                      <span>Готов</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-3 h-3" />
                      <span>Не готов</span>
                    </>
                  )}
                </Badge>
              </div>
              <div className="flex items-center space-x-2">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  {ollamaLoading ? 'Проверка...' : ollamaStatus?.message || 'Неизвестно'}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={checkOllamaStatus}
                  disabled={ollamaLoading}
                  icon={<RefreshCw className="w-4 h-4" />}
                >
                  Обновить
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Домены */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                <Globe className="w-5 h-5" />
                <span>Домены ({domains.length})</span>
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={loadDomains}
                disabled={domainsLoading}
                icon={<RefreshCw className="w-4 h-4" />}
              >
                Обновить
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {domainsLoading ? (
              <div className="grid gap-4">
                {[...Array(3)].map((_, index) => (
                  <div key={index} className="animate-pulse bg-gray-200 dark:bg-gray-700 h-16 rounded"></div>
                ))}
              </div>
            ) : domains.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <div className="text-4xl mb-4">🌐</div>
                <h3 className="text-lg font-medium mb-2">Домены не найдены</h3>
                <p className="text-sm">Добавьте домен для начала анализа</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {domains.map((domain) => (
                  <div
                    key={domain.id}
                    className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                    onClick={() => handleSelectDomain(domain)}
                  >
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">
                        {domain.display_name || domain.name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {domain.total_posts} постов • {domain.total_analyses} анализов
                      </p>
                      {domain.last_analysis_at && (
                        <p className="text-xs text-gray-400 dark:text-gray-500">
                          Последний анализ: {new Date(domain.last_analysis_at).toLocaleDateString('ru-RU')}
                        </p>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {domain.is_indexed && (
                        <Badge variant="success" size="sm">
                          Индексирован
                        </Badge>
                      )}
                      
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAnalyzeDomain(domain);
                        }}
                        disabled={isAnalyzing || !ollamaStatus?.ready_for_work}
                        icon={<Play className="w-4 h-4" />}
                      >
                        {isAnalyzing && currentDomain?.id === domain.id ? 'Анализирую...' : 'Анализировать'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Статистика и рекомендации */}
        {currentDomain && (
          <div className="space-y-6">
            {/* Переключатель вкладок */}
            <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
              <Button
                variant={showStats ? 'ghost' : 'primary'}
                size="sm"
                onClick={() => setShowStats(true)}
                icon={<BarChart3 className="w-4 h-4" />}
              >
                Статистика
              </Button>
              <Button
                variant={!showStats ? 'ghost' : 'primary'}
                size="sm"
                onClick={() => setShowStats(false)}
                icon={<Activity className="w-4 h-4" />}
              >
                Рекомендации
              </Button>
            </div>

            {/* Контент вкладок */}
            {showStats ? (
              <Stats 
                domain={currentDomain}
                analysisHistory={analysisHistory}
              />
            ) : (
              <Recommendations
                recommendations={recommendations}
                domain={currentDomain.name}
                isLoading={isAnalyzing}
                onCopy={handleCopyRecommendation}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App; 