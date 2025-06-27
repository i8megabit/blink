// @ts-nocheck
import React, { useState, useEffect } from 'react'
import Header from './components/Header'
import { DomainInput } from './components/DomainInput'
import { DomainsList } from './components/DomainsList'
import { AnalysisProgress } from './components/AnalysisProgress'
import { Recommendations } from './components/Recommendations'
import { Notifications } from './components/Notifications'
import { OllamaStatus } from './components/OllamaStatus'
import { AIAnalysisFlow } from './components/AIAnalysisFlow'
import Metrics from './components/Metrics'
import Charts from './components/Charts'
import Export from './components/Export'
import { AnalysisHistory } from './components/AnalysisHistory'
import { Benchmarks } from './components/Benchmarks'
import { BenchmarkDetails } from './components/BenchmarkDetails'
import { Settings } from './components/Settings'
import Insights from './components/Insights'
import Analytics from './components/Analytics'
import { useWebSocket } from './hooks/useWebSocket'
import { useNotifications } from './hooks/useNotifications'
import { Domain, Recommendation, AnalysisStats, AIThought, OllamaStatus as OllamaStatusType, WebSocketMessage, BenchmarkHistory } from './types'

function App() {
  // Основные состояния
  const [domain] = useState('')
  const [domains, setDomains] = useState<Domain[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  
  // Состояния анализа
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisStats, setAnalysisStats] = useState<AnalysisStats | null>(null)
  const [analysisStep, setAnalysisStep] = useState('')
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [aiThoughts, setAiThoughts] = useState<AIThought[]>([])
  const [showAIAnalysis, setShowAIAnalysis] = useState(false)
  
  // Состояния интерфейса
  const [activeTab, setActiveTab] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedBenchmark, setSelectedBenchmark] = useState<BenchmarkHistory | null>(null)
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatusType>({
    ready_for_work: false,
    server_available: false,
    model_loaded: false,
    message: 'Проверка статуса...',
    status: 'connecting',
    connection: '',
    models_count: 0,
    available_models: [],
    timestamp: '',
    last_check: ''
  })

  // Состояния метрик
  const [metrics, setMetrics] = useState({
    totalDomains: 0,
    totalAnalyses: 0,
    totalRecommendations: 0,
    avgAnalysisTime: 0,
    successRate: 0,
    activeModels: 0
  })

  // Генерация уникального ID клиента
  const clientId = React.useMemo(() => `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`, [])

  // WebSocket и уведомления
  const { lastMessage } = useWebSocket({
    url: 'ws://localhost:8000/ws',
    clientId,
    reconnectInterval: 5000
  })
  const { notifications, addNotification, removeNotification } = useNotifications()

  // Загрузка доменов при монтировании
  useEffect(() => {
    loadDomains()
    checkOllamaStatus()
    loadMetrics()
    
    // Периодическая проверка статуса Ollama
    const interval = setInterval(checkOllamaStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  // Обработка WebSocket сообщений
  useEffect(() => {
    if (lastMessage) {
      handleWebSocketMessage(lastMessage)
    }
  }, [lastMessage])

  function handleWebSocketMessage(data: WebSocketMessage) {
    console.log('📡 WebSocket сообщение:', data.type, data)

    switch (data.type) {
      case 'progress':
        setAnalysisStep(data.step || '')
        setAnalysisProgress(data.percentage || 0)
        setAnalysisStats({
          current: data.current || 0,
          total: data.total || 0,
          details: data.details || ''
        })
        break

      case 'ai_thinking':
        setAiThoughts(prev => [...prev, {
          id: Date.now().toString(),
          type: 'ai_thinking',
          thought: data.thought || '',
          thinking_stage: data.thinking_stage || '',
          emoji: data.emoji || '',
          stage: data.stage || '',
          content: data.content || '',
          confidence: data.confidence || 0,
          semantic_weight: data.semantic_weight || 0,
          related_concepts: data.related_concepts || [],
          reasoning_chain: data.reasoning_chain || [],
          timestamp: data.timestamp || new Date().toISOString()
        }])
        break

      case 'enhanced_ai_thinking':
        setAiThoughts(prev => [...prev, {
          id: data.thought_id || Date.now().toString(),
          type: 'enhanced_ai_thinking',
          stage: data.stage || '',
          content: data.content || '',
          confidence: data.confidence || 0,
          semantic_weight: data.semantic_weight || 0,
          related_concepts: data.related_concepts || [],
          reasoning_chain: data.reasoning_chain || [],
          timestamp: data.timestamp || new Date().toISOString()
        }])
        break

      case 'ollama':
        console.log('🤖 Ollama статус:', data.info)
        break

      case 'error':
        addNotification('error', data.message || 'Неизвестная ошибка', 'Ошибка анализа')
        setIsAnalyzing(false)
        break

      case 'ping':
        // Поддержание соединения
        break

      default:
        console.log('📡 Неизвестный тип сообщения:', data.type)
    }
  }

  // Загрузка доменов
  async function loadDomains() {
    try {
      const response = await fetch('/api/v1/domains')
      if (response.ok) {
        const data = await response.json()
        setDomains(data.domains || [])
      }
    } catch (error) {
      console.error('❌ Ошибка загрузки доменов:', error)
      addNotification('error', 'Не удалось загрузить список доменов', 'Ошибка загрузки')
    }
  }

  // Загрузка метрик
  async function loadMetrics() {
    try {
      // Здесь можно добавить реальный API для метрик
      // Пока используем моковые данные
      setMetrics({
        totalDomains: domains.length,
        totalAnalyses: 42,
        totalRecommendations: 156,
        avgAnalysisTime: 2.3,
        successRate: 94,
        activeModels: 2
      })
    } catch (error) {
      console.error('❌ Ошибка загрузки метрик:', error)
    }
  }

  // Проверка статуса Ollama
  async function checkOllamaStatus() {
    try {
      const response = await fetch('/api/v1/ollama_status')
      if (response.ok) {
        const status = await response.json()
        setOllamaStatus(status)
      }
    } catch (error) {
      console.error('❌ Ошибка проверки статуса Ollama:', error)
      setOllamaStatus({
        ready_for_work: false,
        server_available: false,
        model_loaded: false,
        message: 'Ошибка подключения к Ollama',
        status: 'error',
        connection: '',
        models_count: 0,
        available_models: [],
        timestamp: '',
        last_check: ''
      })
    }
  }

  // Анализ домена
  async function handleAnalyzeDomain(domainToAnalyze: string, comprehensive: boolean = true) {
    if (!domainToAnalyze.trim()) {
      addNotification('warning', 'Введите домен для анализа', 'Внимание')
      return
    }

    if (!ollamaStatus.ready_for_work) {
      addNotification('warning', 'Ollama не готова к работе', 'Система не готова')
      return
    }

    setIsAnalyzing(true)
    setAnalysisStep('Начало анализа...')
    setAnalysisProgress(0)
    setAnalysisStats(null)
    setAiThoughts([])
    setShowAIAnalysis(true)
    setRecommendations([])

    try {
      const response = await fetch('/api/v1/wp_index', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: domainToAnalyze.trim(),
          client_id: clientId,
          comprehensive: comprehensive
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.status === 'success') {
        setRecommendations(data.recommendations || [])
        addNotification('success', `Найдено ${data.recommendations?.length || 0} рекомендаций для ${data.posts_found || 0} статей`, 'Анализ завершен')
        
        // Обновляем метрики после успешного анализа
        loadMetrics()
      } else {
        throw new Error(data.error || 'Неизвестная ошибка')
      }

    } catch (error) {
      console.error('❌ Ошибка анализа:', error)
      const errorMessage = error instanceof Error ? error.message : 'Неизвестная ошибка'
      addNotification('error', errorMessage, 'Ошибка анализа')
    } finally {
      setIsAnalyzing(false)
      setAnalysisStep('')
      setAnalysisProgress(100)
    }
  }

  const handleCloseAIAnalysis = () => {
    setShowAIAnalysis(false)
  }

  const handleExport = (format: string) => {
    addNotification('success', `Данные экспортированы в формате ${format.toUpperCase()}`, 'Экспорт завершен')
  }

  // Рендер контента в зависимости от активной вкладки
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            {/* Метрики */}
            <Metrics metrics={metrics} />
            
            {/* Анализ домена */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">Анализ домена</div>
              </div>
              <div className="card-content">
                <DomainInput 
                  onAnalyze={handleAnalyzeDomain}
                  isLoading={isAnalyzing}
                />
              </div>
            </div>

            {isAnalyzing && (
              <div className="card">
                <div className="card-header">
                  <div className="card-title">Прогресс анализа</div>
                </div>
                <div className="card-content">
                  <AnalysisProgress
                    isVisible={isAnalyzing}
                    onClose={() => setIsAnalyzing(false)}
                    currentStep={analysisStep}
                    progress={analysisProgress}
                    current={analysisStats?.current || 0}
                    total={analysisStats?.total || 0}
                    details={analysisStats?.details || ''}
                  />
                </div>
              </div>
            )}

            {recommendations.length > 0 && (
              <div className="card">
                <div className="card-header">
                  <div className="card-title">Рекомендации</div>
                </div>
                <div className="card-content">
                  <Recommendations 
                    recommendations={recommendations}
                    domain={domain}
                  />
                </div>
              </div>
            )}

            {/* Графики */}
            <Charts 
              analysisHistory={[
                { date: '2024-01-01', value: 12 },
                { date: '2024-01-02', value: 18 },
                { date: '2024-01-03', value: 15 },
                { date: '2024-01-04', value: 22 },
                { date: '2024-01-05', value: 28 }
              ]}
              domainStats={[
                { label: 'example.com', value: 45 },
                { label: 'test.ru', value: 32 },
                { label: 'demo.org', value: 28 },
                { label: 'sample.net', value: 19 }
              ]}
              modelPerformance={[
                { label: 'qwen2.5:7b-turbo', value: 65 },
                { label: 'qwen2.5:7b-instruct', value: 35 }
              ]}
            />
          </div>
        )

      case 'domains':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold">Домены</h2>
              <button 
                className="btn btn-primary"
                onClick={loadDomains}
              >
                Обновить
              </button>
            </div>
            <DomainsList 
              domains={domains} 
              onAnalyze={handleAnalyzeDomain}
            />
          </div>
        )

      case 'history':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold">История анализов</h2>
            <AnalysisHistory />
          </div>
        )

      case 'benchmarks':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold">Бенчмарки моделей</h2>
            <Benchmarks 
              onViewBenchmark={setSelectedBenchmark}
            />
          </div>
        )

      case 'export':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold">Экспорт данных</h2>
            <Export 
              recommendations={recommendations.map(rec => ({
                from: rec.source_post?.title || 'Неизвестно',
                to: rec.target_post?.title || 'Неизвестно',
                anchor: rec.anchor_text,
                comment: rec.reasoning
              }))}
              domain={domain}
              onExport={handleExport}
            />
          </div>
        )

      case 'status':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold">Статус системы</h2>
            <OllamaStatus 
              status={ollamaStatus} 
              onRefresh={checkOllamaStatus} 
            />
          </div>
        )

      case 'settings':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold">Настройки</h2>
            <Settings />
          </div>
        )

      case 'insights':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold">AI Инсайты</h2>
            <Insights domain={domain} />
          </div>
        )

      case 'analytics':
        return (
          <div className="space-y-6">
            <Analytics domain={domain} />
          </div>
        )

      default:
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-semibold mb-4">Добро пожаловать</h2>
            <p className="text-muted">Выберите раздел в боковой панели</p>
          </div>
        )
    }
  }

  const getTabTitle = () => {
    const titles: Record<string, string> = {
      dashboard: 'Дашборд',
      domains: 'Домены',
      history: 'История анализов',
      benchmarks: 'Бенчмарки',
      export: 'Экспорт данных',
      status: 'Статус системы',
      settings: 'Настройки',
      insights: 'AI Инсайты',
      analytics: 'Аналитика'
    }
    return titles[activeTab] || 'Blink'
  }

  return (
    <div className="app-container">
      {/* Боковая панель */}
      <aside className={`sidebar ${!sidebarOpen ? 'hidden' : ''}`}>
        <div className="sidebar-header">
          <div 
            className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => setActiveTab('dashboard')}
          >
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-semibold">
              🔗
            </div>
            <h1 className="text-lg font-semibold">Blink</h1>
          </div>
        </div>
        
        <div className="sidebar-content">
          <nav className="space-y-2">
            {[
              { id: 'dashboard', label: '📊 Дашборд', icon: '📊' },
              { id: 'domains', label: '🌐 Домены', icon: '🌐' },
              { id: 'history', label: '📋 История', icon: '📋' },
              { id: 'benchmarks', label: '⚡ Бенчмарки', icon: '⚡' },
              { id: 'export', label: '📤 Экспорт', icon: '📤' },
              { id: 'status', label: '⚙️ Статус', icon: '⚙️' },
              { id: 'settings', label: '🔧 Настройки', icon: '🔧' },
              { id: 'insights', label: '📊 AI Инсайты', icon: '📊' },
              { id: 'analytics', label: '📊 Аналитика', icon: '📊' }
            ].map((tab) => (
              <button
                key={tab.id}
                className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                  activeTab === tab.id 
                    ? 'bg-accent text-accent-foreground' 
                    : 'hover:bg-accent hover:text-accent-foreground'
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </aside>

      {/* Основной контент */}
      <main className="main-content">
        <Header 
          title={getTabTitle()}
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
          actions={
            activeTab === 'dashboard' && recommendations.length > 0 ? (
              <button 
                className="btn btn-secondary"
                onClick={() => setActiveTab('export')}
              >
                📤 Экспорт
              </button>
            ) : undefined
          }
        />
        
        <div className="content-body">
          {renderContent()}
        </div>
      </main>

      {/* Уведомления */}
      <Notifications 
        notifications={notifications} 
        onRemove={removeNotification}
        onClear={() => {
          // Очистка всех уведомлений
          notifications.forEach(notification => removeNotification(notification.id))
        }}
      />

      {/* AI Analysis Flow */}
      <AIAnalysisFlow
        isOpen={showAIAnalysis}
        onClose={handleCloseAIAnalysis}
        aiThoughts={aiThoughts}
        analysisProgress={analysisProgress}
        analysisStep={analysisStep}
      />

      {/* Benchmark Details Modal */}
      <BenchmarkDetails
        benchmark={selectedBenchmark}
        onClose={() => setSelectedBenchmark(null)}
      />
    </div>
  )
}

export default App 