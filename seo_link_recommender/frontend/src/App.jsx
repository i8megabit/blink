import React, { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import DomainInput from './components/DomainInput'
import DomainsList from './components/DomainsList'
import AnalysisProgress from './components/AnalysisProgress'
import Recommendations from './components/Recommendations'
import Notifications from './components/Notifications'
import OllamaStatus from './components/OllamaStatus'
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
  const [analysisError, setAnalysisError] = useState(null)
  
  // Состояния Ollama
  const [ollamaStatus, setOllamaStatus] = useState({
    status: 'unknown',
    message: 'Проверка статуса...',
    models_count: 0,
    available_models: []
  })
  
  // AI состояния
  const [aiThoughts, setAiThoughts] = useState([])
  const [currentThought, setCurrentThought] = useState(null)
  
  // Хуки
  const { notifications, addNotification, removeNotification } = useNotifications()
  const { 
    connectionStatus, 
    connectWebSocket, 
    disconnectWebSocket 
  } = useWebSocket({
    onMessage: handleWebSocketMessage,
    onConnect: () => addNotification('success', 'WebSocket соединение установлено'),
    onDisconnect: () => addNotification('warning', 'WebSocket соединение потеряно'),
    onError: () => addNotification('error', 'Ошибка WebSocket соединения')
  })

  // Инициализация приложения
  useEffect(() => {
    console.log('🚀 SEO Link Recommender (Vite) загружен')
    
    const clientId = 'client_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    
    // Загружаем данные
    loadDomains()
    checkOllamaStatus()
    connectWebSocket(clientId)
    
    // Проверяем статус Ollama каждые 30 секунд
    const ollamaInterval = setInterval(checkOllamaStatus, 30000)
    
    return () => {
      disconnectWebSocket()
      clearInterval(ollamaInterval)
    }
  }, [])

  // Загрузка доменов
  async function loadDomains() {
    try {
      const response = await fetch('/api/v1/domains')
      const data = await response.json()
      setDomains(data.domains || [])
    } catch (error) {
      console.error('Ошибка загрузки доменов:', error)
      addNotification('error', 'Не удалось загрузить список доменов')
    }
  }

  // Проверка статуса Ollama
  async function checkOllamaStatus() {
    try {
      const response = await fetch('/api/v1/ollama_status')
      const data = await response.json()
      setOllamaStatus(data)
    } catch (error) {
      console.error('Ошибка проверки Ollama:', error)
      setOllamaStatus({
        status: 'error',
        message: 'Не удалось подключиться к Ollama',
        models_count: 0,
        available_models: []
      })
    }
  }

  // Обработка WebSocket сообщений
  function handleWebSocketMessage(data) {
    console.log('📨 WebSocket сообщение:', data)
    
    switch (data.type) {
      case 'progress':
        setAnalysisStats({
          step: data.step,
          current: data.current,
          total: data.total,
          percentage: data.percentage,
          details: data.details
        })
        break
        
      case 'ai_thinking':
        setCurrentThought({
          content: data.thought,
          stage: data.thinking_stage,
          emoji: data.emoji,
          timestamp: data.timestamp
        })
        
        setAiThoughts(prev => [...prev.slice(-9), {
          id: Date.now(),
          content: data.thought,
          stage: data.thinking_stage,
          emoji: data.emoji,
          timestamp: data.timestamp
        }])
        break
        
      case 'enhanced_ai_thinking':
        const enhancedThought = {
          id: data.thought_id,
          content: data.content,
          stage: data.stage,
          confidence: data.confidence,
          concepts: data.related_concepts,
          reasoning: data.reasoning_chain,
          timestamp: data.timestamp
        }
        
        setCurrentThought(enhancedThought)
        setAiThoughts(prev => [...prev.slice(-9), enhancedThought])
        break
        
      case 'ollama':
        if (data.info) {
          addNotification('info', 'Ollama статус', data.info.status || 'Обновление статуса')
        }
        break
        
      case 'error':
        setAnalysisError(data.message)
        addNotification('error', 'Ошибка анализа', data.details)
        setIsAnalyzing(false)
        break
        
      case 'ping':
        // Игнорируем ping сообщения
        break
        
      default:
        console.log('Неизвестный тип сообщения:', data.type)
    }
  }

  // Анализ домена
  async function handleAnalyzeDomain() {
    const targetDomain = domain.trim()
    
    if (!targetDomain) {
      addNotification('warning', 'Введите домен для анализа')
      return
    }

    setIsAnalyzing(true)
    setAnalysisError(null)
    setAnalysisStats(null)
    setRecommendations([])
    setAiThoughts([])
    setCurrentThought(null)

    try {
      addNotification('info', `Начинаем анализ домена ${targetDomain}`)
      
      const response = await fetch('/api/v1/wp_index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: targetDomain,
          comprehensive: true,
          client_id: connectionStatus === 'connected' ? 'vite_client' : null
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        setRecommendations(result.recommendations || [])
        addNotification('success', 'Анализ завершен', 
          `Найдено ${result.recommendations?.length || 0} рекомендаций`)
        
        // Обновляем список доменов
        loadDomains()
      } else {
        throw new Error(result.error || 'Неизвестная ошибка')
      }
    } catch (error) {
      console.error('Ошибка анализа:', error)
      setAnalysisError(error.message)
      addNotification('error', 'Ошибка анализа', error.message)
    } finally {
      setIsAnalyzing(false)
      setAnalysisStats(null)
      setCurrentThought(null)
    }
  }

  return (
    <div>
      <Header />
      
      <nav className="nav-apple">
        <div className="apple-container">
          <div className="nav-buttons">
            <button 
              className="btn-apple btn-secondary" 
              onClick={checkOllamaStatus}
            >
              🔄 Обновить статус
            </button>
            <button 
              className="btn-apple btn-secondary" 
              onClick={loadDomains}
            >
              📊 Обновить домены
            </button>
          </div>
        </div>
      </nav>

      <main className="apple-container" style={{ paddingTop: '40px', paddingBottom: '40px' }}>
        <OllamaStatus 
          ollamaStatus={ollamaStatus} 
          onRefresh={checkOllamaStatus} 
        />
        
        <DomainInput 
          domain={domain}
          setDomain={setDomain}
          onAnalyze={handleAnalyzeDomain}
          isAnalyzing={isAnalyzing}
        />
        
        <AnalysisProgress 
          analysisStats={analysisStats}
          currentThought={currentThought}
          aiThoughts={aiThoughts}
        />
        
        <DomainsList domains={domains} />
        
        <Recommendations recommendations={recommendations} />
        
        {analysisError && (
          <div className="step-card">
            <div className="step-number">!</div>
            <h3 className="step-title">Ошибка анализа</h3>
            <div className="status-indicator status-error">
              {analysisError}
            </div>
          </div>
        )}
      </main>
      
      <Notifications 
        notifications={notifications} 
        removeNotification={removeNotification} 
      />
    </div>
  )
}

export default App 