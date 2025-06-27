import React, { useState, useEffect, useCallback } from 'react';
import { 
  Domain, 
  Recommendation, 
  WebSocketMessage, 
  OllamaStatus,
  AIThought,
  AnalysisStats
} from './types';
import { useNotifications } from './hooks/useNotifications';
import { useWebSocket } from './hooks/useWebSocket';
import { Notifications } from './components/Notifications';
import { AnalysisProgress } from './components/AnalysisProgress';
import { Recommendations } from './components/Recommendations';
import { DomainInput } from './components/DomainInput';
import { DomainsList } from './components/DomainsList';
import { OllamaStatus as OllamaStatusComponent } from './components/OllamaStatus';
import { AIAnalysisFlow } from './components/AIAnalysisFlow';
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
  BarChart3,
  Settings,
  History,
  Target,
  Menu,
  X
} from 'lucide-react';

function App() {
  // Основные состояния
  const [domains, setDomains] = useState<Domain[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [currentDomain, setCurrentDomain] = useState<string>('');
  
  // Состояния анализа
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStats, setAnalysisStats] = useState<AnalysisStats | null>(null);
  const [analysisStep, setAnalysisStep] = useState('');
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [aiThoughts, setAiThoughts] = useState<AIThought[]>([]);
  const [showAIAnalysis, setShowAIAnalysis] = useState(false);
  const [analysisError, setAnalysisError] = useState<string>('');
  
  // Состояния интерфейса
  const [activeTab, setActiveTab] = useState<'dashboard' | 'analysis' | 'history' | 'benchmarks' | 'settings'>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus>({
    status: 'connecting',
    connection: 'connecting',
    models_count: 0,
    available_models: [],
    timestamp: new Date().toISOString(),
    ready_for_work: false,
    server_available: false,
    model_loaded: false,
    message: 'Проверка статуса...',
    last_check: new Date().toISOString()
  });

  // Генерация уникального ID клиента
  const clientId = React.useMemo(() => `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`, []);

  // WebSocket и уведомления
  const { notifications, addNotification, removeNotification, clearNotifications } = useNotifications();
  const { connectionStatus, connectWebSocket, disconnectWebSocket } = useWebSocket({
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('WebSocket подключен');
      addNotification({
        type: 'success',
        title: 'Подключение установлено',
        message: 'WebSocket соединение активно'
      });
    },
    onDisconnect: () => {
      console.log('WebSocket отключен');
      addNotification({
        type: 'warning',
        title: 'Соединение потеряно',
        message: 'Попытка переподключения...'
      });
    },
    onError: (error) => {
      console.error('WebSocket ошибка:', error);
      addNotification({
        type: 'error',
        title: 'Ошибка соединения',
        message: 'Не удалось подключиться к серверу'
      });
    }
  });

  function handleWebSocketMessage(data: WebSocketMessage) {
    console.log('WebSocket сообщение:', data);

    switch (data.type) {
      case 'progress':
        if (data.step) setAnalysisStep(data.step);
        if (data.percentage !== undefined) setAnalysisProgress(data.percentage);
        if (data.details) {
          addNotification({
            type: 'info',
            title: data.step || 'Прогресс',
            message: data.details
          });
        }
        break;

      case 'ai_thinking':
        if (data.thought) {
          const thought: AIThought = {
            id: Date.now().toString(),
            stage: data.thinking_stage || 'analyzing',
            content: data.thought,
            confidence: 0.7,
            semantic_weight: 0.5,
            related_concepts: [],
            reasoning_chain: [],
            timestamp: data.timestamp
          };
          setAiThoughts(prev => [...prev, thought]);
        }
        break;

      case 'enhanced_ai_thinking':
        if (data.thought_id && data.content) {
          const thought: AIThought = {
            id: data.thought_id,
            stage: data.stage || 'analyzing',
            content: data.content,
            confidence: data.confidence || 0.7,
            semantic_weight: data.semantic_weight || 0.5,
            related_concepts: data.related_concepts || [],
            reasoning_chain: data.reasoning_chain || [],
            timestamp: data.timestamp
          };
          setAiThoughts(prev => [...prev, thought]);
        }
        break;

      case 'error':
        setAnalysisError(data.message || data.error || 'Неизвестная ошибка');
        setIsAnalyzing(false);
        addNotification({
          type: 'error',
          title: 'Ошибка анализа',
          message: data.message || data.error || 'Неизвестная ошибка'
        });
        break;

      case 'ollama':
        if (data.info) {
          addNotification({
            type: 'info',
            title: 'Ollama статус',
            message: `Батч ${data.info.batch}: ${data.info.processing_time || 'обработка...'}`
          });
        }
        break;
    }
  }

  // Загрузка доменов
  const loadDomains = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/domains');
      if (response.ok) {
        const data = await response.json();
        setDomains(data.domains || []);
      } else {
        throw new Error('Не удалось загрузить домены');
      }
    } catch (error) {
      console.error('Ошибка загрузки доменов:', error);
      addNotification({
        type: 'error',
        title: 'Ошибка загрузки',
        message: 'Не удалось загрузить список доменов'
      });
    }
  }, [addNotification]);

  // Проверка статуса Ollama
  const checkOllamaStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/ollama_status');
      if (response.ok) {
        const status = await response.json();
        setOllamaStatus(status);
      } else {
        throw new Error('Не удалось проверить статус Ollama');
      }
    } catch (error) {
      console.error('Ошибка проверки статуса Ollama:', error);
      setOllamaStatus(prev => ({
        ...prev,
        status: 'error',
        connection: 'error',
        ready_for_work: false,
        server_available: false,
        model_loaded: false,
        message: 'Ошибка подключения к Ollama'
      }));
    }
  }, []);

  // Анализ домена
  const handleAnalyzeDomain = useCallback(async (domain: string, comprehensive: boolean = true) => {
    if (!domain.trim()) {
      addNotification({
        type: 'error',
        title: 'Ошибка',
        message: 'Введите домен для анализа'
      });
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError('');
    setAnalysisProgress(0);
    setAnalysisStep('Подготовка к анализу...');
    setAiThoughts([]);
    setCurrentDomain(domain);
    setShowAIAnalysis(true);

    // Подключаем WebSocket если не подключен
    if (connectionStatus !== 'connected') {
      connectWebSocket();
    }

    try {
      const response = await fetch('/api/v1/wp_index', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: domain.trim(),
          comprehensive,
          client_id: clientId
        }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        setRecommendations(data.recommendations || []);
        setAnalysisStats({
          postsAnalyzed: data.posts_found,
          connectionsFound: data.recommendations?.length || 0,
          recommendationsGenerated: data.recommendations?.length || 0,
          processingTime: data.analysis_time
        });
        
        addNotification({
          type: 'success',
          title: 'Анализ завершен',
          message: `Найдено ${data.recommendations?.length || 0} рекомендаций для ${domain}`
        });

        // Обновляем список доменов
        await loadDomains();
      } else {
        throw new Error(data.error || 'Ошибка анализа');
      }
    } catch (error) {
      console.error('Ошибка анализа домена:', error);
      setAnalysisError(error instanceof Error ? error.message : 'Неизвестная ошибка');
      addNotification({
        type: 'error',
        title: 'Ошибка анализа',
        message: error instanceof Error ? error.message : 'Неизвестная ошибка'
      });
    } finally {
      setIsAnalyzing(false);
      setAnalysisProgress(100);
      setAnalysisStep('Анализ завершен');
    }
  }, [addNotification, clientId, connectionStatus, connectWebSocket, loadDomains]);

  const handleCloseAIAnalysis = () => {
    setShowAIAnalysis(false);
    setAiThoughts([]);
  };

  // Загрузка данных при монтировании
  useEffect(() => {
    loadDomains();
    checkOllamaStatus();
    
    // Периодическая проверка статуса Ollama
    const interval = setInterval(checkOllamaStatus, 30000);
    
    return () => {
      clearInterval(interval);
      disconnectWebSocket();
    };
  }, [loadDomains, checkOllamaStatus, disconnectWebSocket]);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <DomainInput 
                onAnalyze={handleAnalyzeDomain}
                isLoading={isAnalyzing}
              />
              <OllamaStatusComponent 
                status={ollamaStatus}
                onRefresh={checkOllamaStatus}
              />
            </div>
            
            {isAnalyzing && (
              <AnalysisProgress
                isActive={isAnalyzing}
                currentStep={analysisStep}
                progress={analysisProgress}
                totalSteps={12}
                aiThoughts={aiThoughts}
                analysisStats={analysisStats}
                error={analysisError}
              />
            )}

            {recommendations.length > 0 && (
              <Recommendations
                recommendations={recommendations}
                domain={currentDomain}
                isLoading={isAnalyzing}
              />
            )}

            <Stats 
              domain={domains.find(d => d.name === currentDomain)}
              analysisHistory={[]}
            />
          </div>
        );

      case 'analysis':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Анализ доменов
                </CardTitle>
              </CardHeader>
              <CardContent>
                <DomainsList
                  domains={domains}
                  onAnalyze={handleAnalyzeDomain}
                  isLoading={isAnalyzing}
                />
              </CardContent>
            </Card>
          </div>
        );

      case 'history':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="w-5 h-5" />
                  История анализов
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  История анализов будет отображаться здесь
                </p>
              </CardContent>
            </Card>
          </div>
        );

      case 'benchmarks':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Бенчмарки моделей
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Бенчмарки моделей будут отображаться здесь
                </p>
              </CardContent>
            </Card>
          </div>
        );

      case 'settings':
        return (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Настройки
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Настройки приложения будут отображаться здесь
                </p>
              </CardContent>
            </Card>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Уведомления */}
      <Notifications
        notifications={notifications}
        onRemove={removeNotification}
        onClear={clearNotifications}
      />

      {/* AI Анализ Flow */}
      <AIAnalysisFlow
        isVisible={showAIAnalysis}
        onClose={handleCloseAIAnalysis}
        aiThoughts={aiThoughts}
        currentStage={analysisStep}
        progress={analysisProgress}
      />

      <div className="flex">
        {/* Боковая панель */}
        <div className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}>
          <div className="flex flex-col h-full">
            {/* Заголовок */}
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-2">
                <Globe className="w-6 h-6 text-blue-600" />
                <h1 className="text-lg font-semibold">SEO Link Recommender</h1>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Навигация */}
            <nav className="flex-1 p-4 space-y-2">
              {[
                { id: 'dashboard', label: 'Дашборд', icon: <Activity className="w-4 h-4" /> },
                { id: 'analysis', label: 'Анализ', icon: <Target className="w-4 h-4" /> },
                { id: 'history', label: 'История', icon: <History className="w-4 h-4" /> },
                { id: 'benchmarks', label: 'Бенчмарки', icon: <BarChart3 className="w-4 h-4" /> },
                { id: 'settings', label: 'Настройки', icon: <Settings className="w-4 h-4" /> }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors",
                    activeTab === tab.id
                      ? "bg-blue-50 text-blue-700 border border-blue-200"
                      : "text-gray-600 hover:bg-gray-50"
                  )}
                >
                  {tab.icon}
                  <span className="font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>

            {/* Статус */}
            <div className="p-4 border-t">
              <div className="flex items-center gap-2 mb-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  connectionStatus === 'connected' ? "bg-green-500" : "bg-red-500"
                )} />
                <span className="text-sm text-gray-600">
                  {connectionStatus === 'connected' ? 'Подключено' : 'Отключено'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  ollamaStatus.ready_for_work ? "bg-green-500" : "bg-yellow-500"
                )} />
                <span className="text-sm text-gray-600">
                  {ollamaStatus.ready_for_work ? 'Ollama готова' : 'Ollama загружается'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Основной контент */}
        <div className="flex-1 flex flex-col">
          {/* Верхняя панель */}
          <header className="bg-white shadow-sm border-b">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(true)}
                  className="lg:hidden"
                >
                  <Menu className="w-5 h-5" />
                </Button>
                <h2 className="text-xl font-semibold text-gray-900">
                  {activeTab === 'dashboard' && 'Дашборд'}
                  {activeTab === 'analysis' && 'Анализ доменов'}
                  {activeTab === 'history' && 'История анализов'}
                  {activeTab === 'benchmarks' && 'Бенчмарки моделей'}
                  {activeTab === 'settings' && 'Настройки'}
                </h2>
              </div>
              
              <div className="flex items-center gap-2">
                <Badge variant="outline">
                  {domains.length} доменов
                </Badge>
                {isAnalyzing && (
                  <Badge variant="default" className="bg-blue-100 text-blue-800">
                    <Activity className="w-3 h-3 mr-1 animate-pulse" />
                    Анализ
                  </Badge>
                )}
              </div>
            </div>
          </header>

          {/* Контент */}
          <main className="flex-1 p-6 overflow-y-auto">
            {renderContent()}
          </main>
        </div>
      </div>
    </div>
  );
}

export default App; 