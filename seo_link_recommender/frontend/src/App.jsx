import React, { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import DomainInput from './components/DomainInput'
import DomainsList from './components/DomainsList'
import AnalysisProgress from './components/AnalysisProgress'
import Recommendations from './components/Recommendations'
import Notifications from './components/Notifications'
import OllamaStatus from './components/OllamaStatus'
import AIAnalysisFlow from './components/AIAnalysisFlow'
import { useWebSocket } from './hooks/useWebSocket'
import { useNotifications } from './hooks/useNotifications'

function App() {
  // Основные состояния
  const [domain, setDomain] = useState('')
  const [domains, setDomains] = useState([])
  const [recommendations, setRecommendations] = useState([])
  
  // Состояния анализа
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisStats, setAnalysisStats] = useState(null)
  const [analysisStep, setAnalysisStep] = useState('')
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [aiThoughts, setAiThoughts] = useState([])
  const [showAIAnalysis, setShowAIAnalysis] = useState(false)
  
  // Состояния интерфейса
  const [activeTab, setActiveTab] = useState('dashboard')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [ollamaStatus, setOllamaStatus] = useState({
    ready_for_work: false,
    server_available: false,
    model_loaded: false,
    message: 'Проверка статуса...'
  })

  // WebSocket и уведомления
  const { sendMessage, lastMessage } = useWebSocket()
  const { notifications, addNotification, removeNotification } = useNotifications()

  // Генерация уникального ID клиента
  const clientId = React.useMemo(() => `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`, [])

  // Загрузка доменов при монтировании
  useEffect(() => {
    loadDomains()
    checkOllamaStatus()
    
    // Периодическая проверка статуса Ollama
    const interval = setInterval(checkOllamaStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  // Обработка WebSocket сообщений
  useEffect(() => {
    if (lastMessage) {
      handleWebSocketMessage(JSON.parse(lastMessage))
    }
  }, [lastMessage])

  function handleWebSocketMessage(data) {
    console.log('📡 WebSocket сообщение:', data.type, data)

    switch (data.type) {
      case 'progress':
        setAnalysisStep(data.step)
        setAnalysisProgress(data.percentage)
        setAnalysisStats({
          current: data.current,
          total: data.total,
          details: data.details
        })
        break

      case 'ai_thinking':
        setAiThoughts(prev => [...prev, {
          id: Date.now(),
          type: 'ai_thinking',
          thought: data.thought,
          thinking_stage: data.thinking_stage,
          emoji: data.emoji,
          timestamp: data.timestamp
        }])
        break

      case 'enhanced_ai_thinking':
        setAiThoughts(prev => [...prev, {
          id: data.thought_id,
          type: 'enhanced_ai_thinking',
          stage: data.stage,
          content: data.content,
          confidence: data.confidence,
          semantic_weight: data.semantic_weight,
          related_concepts: data.related_concepts,
          reasoning_chain: data.reasoning_chain,
          timestamp: data.timestamp
        }])
        break

      case 'ollama':
        console.log('🤖 Ollama статус:', data.info)
        break

      case 'error':
        addNotification('error', 'Ошибка анализа', data.message)
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
      addNotification('error', 'Ошибка загрузки', 'Не удалось загрузить список доменов')
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
        message: 'Ошибка подключения к Ollama'
      })
    }
  }

  // Анализ домена
  async function handleAnalyzeDomain() {
    if (!domain.trim()) {
      addNotification('warning', 'Внимание', 'Введите домен для анализа')
      return
    }

    if (!ollamaStatus.ready_for_work) {
      addNotification('warning', 'Система не готова', 'Ollama не готова к работе')
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
          domain: domain.trim(),
          client_id: clientId,
          comprehensive: true
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (data.status === 'success') {
        setRecommendations(data.recommendations || [])
        addNotification('success', 'Анализ завершен', 
          `Найдено ${data.recommendations?.length || 0} рекомендаций для ${data.posts_found || 0} статей`)
      } else {
        throw new Error(data.error || 'Неизвестная ошибка')
      }

    } catch (error) {
      console.error('❌ Ошибка анализа:', error)
      addNotification('error', 'Ошибка анализа', error.message)
    } finally {
      setIsAnalyzing(false)
      setAnalysisStep('')
      setAnalysisProgress(100)
    }
  }

  const handleCloseAIAnalysis = () => {
    setShowAIAnalysis(false)
  }

  // Рендер контента в зависимости от активной вкладки
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <div className="card-title">Анализ домена</div>
              </div>
              <div className="card-content">
                <DomainInput 
                  domain={domain}
                  setDomain={setDomain}
                  onAnalyze={handleAnalyzeDomain}
                  isAnalyzing={isAnalyzing}
                  ollamaStatus={ollamaStatus}
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
                    step={analysisStep}
                    progress={analysisProgress}
                    stats={analysisStats}
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
                  <Recommendations recommendations={recommendations} />
                </div>
              </div>
            )}
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
            <DomainsList domains={domains} onRefresh={loadDomains} />
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

      default:
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-semibold mb-4">Добро пожаловать</h2>
            <p className="text-muted">Выберите раздел в боковой панели</p>
          </div>
        )
    }
  }

  return (
    <div className="app-container">
      {/* Боковая панель */}
      <aside className={`sidebar ${!sidebarOpen ? 'hidden' : ''}`}>
        <div className="sidebar-header">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-semibold">
              🔗
            </div>
            <h1 className="text-lg font-semibold">SEO Link Recommender</h1>
          </div>
        </div>
        
        <div className="sidebar-content">
          <nav className="space-y-2">
            <button
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                activeTab === 'dashboard' 
                  ? 'bg-accent text-accent-foreground' 
                  : 'hover:bg-accent hover:text-accent-foreground'
              }`}
              onClick={() => setActiveTab('dashboard')}
            >
              📊 Дашборд
            </button>
            
            <button
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                activeTab === 'domains' 
                  ? 'bg-accent text-accent-foreground' 
                  : 'hover:bg-accent hover:text-accent-foreground'
              }`}
              onClick={() => setActiveTab('domains')}
            >
              🌐 Домены
            </button>
            
            <button
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                activeTab === 'status' 
                  ? 'bg-accent text-accent-foreground' 
                  : 'hover:bg-accent hover:text-accent-foreground'
              }`}
              onClick={() => setActiveTab('status')}
            >
              ⚙️ Статус
            </button>
          </nav>
        </div>
      </aside>

      {/* Основной контент */}
      <main className="main-content">
        <Header 
          title={activeTab === 'dashboard' ? 'Дашборд' : 
                 activeTab === 'domains' ? 'Домены' : 
                 activeTab === 'status' ? 'Статус системы' : 'SEO Link Recommender'}
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        />
        
        <div className="content-body">
          {renderContent()}
        </div>
      </main>

      {/* Уведомления */}
      <Notifications 
        notifications={notifications} 
        onRemove={removeNotification} 
      />

      {/* AI Analysis Flow */}
      <AIAnalysisFlow
        isVisible={showAIAnalysis}
        messages={aiThoughts}
        onClose={handleCloseAIAnalysis}
      />
    </div>
  )
}

export default App 