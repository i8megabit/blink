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

  // Обработка WebSocket сообщений
  function handleWebSocketMessage(data) {
    console.log('📡 WebSocket сообщение:', data)

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
          thought: data.thought,
          stage: data.thinking_stage,
          emoji: data.emoji,
          timestamp: data.timestamp
        }])
        break

      case 'enhanced_ai_thinking':
        setAiThoughts(prev => [...prev, {
          id: data.thought_id,
          thought: data.content,
          stage: data.stage,
          confidence: data.confidence,
          semantic_weight: data.semantic_weight,
          related_concepts: data.related_concepts,
          reasoning_chain: data.reasoning_chain,
          timestamp: data.timestamp
        }])
        break

      case 'ollama':
        setOllamaStatus(prev => ({
          ...prev,
          ...data.info
        }))
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
      addNotification('warning', 'Ollama не готова', 'Дождитесь готовности модели')
      return
    }

    setIsAnalyzing(true)
    setAnalysisStep('')
    setAnalysisProgress(0)
    setAnalysisStats(null)
    setAiThoughts([])
    setShowAIAnalysis(true)
    setRecommendations([])

    addNotification('info', 'Анализ запущен', `Начинаю анализ домена ${domain}`)

    try {
      // Подключаемся к WebSocket
      sendMessage(JSON.stringify({
        type: 'connect',
        client_id: clientId
      }))

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

      const result = await response.json()

      if (result.status === 'success') {
        setRecommendations(result.recommendations || [])
        addNotification('success', 'Анализ завершен', 
          `Найдено ${result.recommendations?.length || 0} рекомендаций для ${result.posts_found || 0} статей`)
      } else {
        throw new Error(result.error || 'Неизвестная ошибка')
      }

    } catch (error) {
      console.error('❌ Ошибка анализа:', error)
      addNotification('error', 'Ошибка анализа', error.message)
    } finally {
      setIsAnalyzing(false)
      setAnalysisStep('')
      setAnalysisProgress(0)
    }
  }

  // Закрытие AI анализа
  const handleCloseAIAnalysis = () => {
    setShowAIAnalysis(false)
    setAiThoughts([])
  }

  // Навигационные элементы
  const navItems = [
    {
      id: 'dashboard',
      label: 'Панель управления',
      icon: '📊',
      component: (
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <div>
                <div className="card-title">Анализ домена</div>
                <div className="card-subtitle">Введите домен WordPress для генерации внутренних ссылок</div>
              </div>
            </div>
            <DomainInput 
              domain={domain}
              setDomain={setDomain}
              onAnalyze={handleAnalyzeDomain}
              isAnalyzing={isAnalyzing}
              ollamaStatus={ollamaStatus}
            />
          </div>

          {showAIAnalysis && (
            <AIAnalysisFlow
              isVisible={showAIAnalysis}
              onClose={handleCloseAIAnalysis}
              aiThoughts={aiThoughts}
              analysisStep={analysisStep}
              analysisProgress={analysisProgress}
              analysisStats={analysisStats}
            />
          )}

          {recommendations.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">Рекомендации</div>
                <div className="badge badge-primary">{recommendations.length}</div>
              </div>
              <Recommendations recommendations={recommendations} />
            </div>
          )}
        </div>
      )
    },
    {
      id: 'domains',
      label: 'Домены',
      icon: '🌐',
      component: (
        <div className="card">
          <div className="card-header">
            <div className="card-title">Управление доменами</div>
            <button 
              className="btn btn-secondary btn-sm"
              onClick={loadDomains}
            >
              Обновить
            </button>
          </div>
          <DomainsList domains={domains} onRefresh={loadDomains} />
        </div>
      )
    },
    {
      id: 'status',
      label: 'Статус системы',
      icon: '⚙️',
      component: (
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <div className="card-title">Статус Ollama</div>
            </div>
            <OllamaStatus status={ollamaStatus} onRefresh={checkOllamaStatus} />
          </div>
          
          <div className="card">
            <div className="card-header">
              <div className="card-title">Доступные модели</div>
            </div>
            <div className="p-4">
              <div className="text-muted text-sm mb-4">
                Проверяем доступные модели Ollama...
              </div>
              <button 
                className="btn btn-secondary btn-sm"
                onClick={checkOllamaStatus}
              >
                Обновить статус
              </button>
            </div>
          </div>
        </div>
      )
    }
  ]

  const activeComponent = navItems.find(item => item.id === activeTab)?.component

  return (
    <div className="app-container">
      {/* Боковая панель */}
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">🔗</div>
            SEO Link AI
          </div>
        </div>
        
        <div className="sidebar-content">
          <div className="sidebar-section">
            <div className="sidebar-section-title">Навигация</div>
            {navItems.map(item => (
              <div
                key={item.id}
                className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <span className="sidebar-item-icon">{item.icon}</span>
                {item.label}
              </div>
            ))}
          </div>
          
          <div className="sidebar-section">
            <div className="sidebar-section-title">Система</div>
            <div className="sidebar-item">
              <span className="sidebar-item-icon">📊</span>
              Статистика
            </div>
            <div className="sidebar-item">
              <span className="sidebar-item-icon">⚙️</span>
              Настройки
            </div>
          </div>
        </div>
      </div>

      {/* Основной контент */}
      <div className="main-content">
        {/* Заголовок */}
        <div className="content-header">
          <div className="flex items-center gap-4">
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              ☰
            </button>
            <div className="content-title">
              {navItems.find(item => item.id === activeTab)?.label}
            </div>
          </div>
          
          <div className="content-actions">
            <div className="status-indicator status-loading">
              <div className="loading-spinner"></div>
              {ollamaStatus.ready_for_work ? 'Готов' : 'Загрузка'}
            </div>
          </div>
        </div>

        {/* Контент */}
        <div className="flex-1 p-6">
          {activeComponent}
        </div>
      </div>

      {/* Уведомления */}
      <Notifications 
        notifications={notifications}
        onRemove={removeNotification}
      />
    </div>
  )
}

export default App 