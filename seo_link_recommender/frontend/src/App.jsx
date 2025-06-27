import React, { useState, useEffect, useCallback, useRef } from 'react'
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
  const [currentView, setCurrentView] = useState('domains')
  const [domains, setDomains] = useState([])
  const [selectedDomain, setSelectedDomain] = useState(null)
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
    onConnect: () => addNotification('success', 'Соединение установлено', 'WebSocket готов к работе'),
    onDisconnect: () => addNotification('warning', 'Соединение потеряно', 'Переподключение...'),
    onError: () => addNotification('error', 'Ошибка соединения', 'Проблема с WebSocket')
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
      addNotification('error', 'Ошибка загрузки', 'Не удалось загрузить список доменов')
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
  async function handleAnalyzeDomain(domainToAnalyze = null) {
    const targetDomain = domainToAnalyze || domain.trim()
    
    if (!targetDomain) {
      addNotification('warning', 'Введите домен', 'Необходимо указать домен для анализа')
      return
    }

    setIsAnalyzing(true)
    setAnalysisError(null)
    setAnalysisStats(null)
    setRecommendations([])
    setAiThoughts([])
    setCurrentThought(null)

    try {
      addNotification('info', 'Начинаем анализ', `Анализируем домен ${targetDomain}`)
      
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
        await loadDomains()
        
        // Переключаемся на вкладку результатов если есть рекомендации
        if (result.recommendations?.length > 0) {
          setCurrentView('recommendations')
        }
      } else {
        throw new Error(result.error || 'Неизвестная ошибка анализа')
      }
      
    } catch (error) {
      console.error('Ошибка анализа домена:', error)
      setAnalysisError(error.message)
      addNotification('error', 'Ошибка анализа', error.message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-700 to-blue-800">
      {/* Шапка */}
      <Header />
      
      {/* Навигация */}
      <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-lg border-b border-black/5">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="flex justify-center gap-3">
            {[
              { id: 'domains', label: '🌐 Домены', icon: '🌐' },
              { id: 'analysis', label: '🔍 Анализ', icon: '🔍' },
              { id: 'recommendations', label: '🔗 Рекомендации', icon: '🔗', badge: recommendations.length },
              { id: 'status', label: '🤖 Ollama', icon: '🤖' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setCurrentView(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200
                  ${currentView === tab.id 
                    ? 'bg-blue-500 text-white shadow-lg transform scale-105' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:scale-102'
                  }
                `}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
                {tab.badge > 0 && (
                  <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                    {tab.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Уведомления */}
      <Notifications 
        notifications={notifications} 
        onRemove={removeNotification} 
      />

      {/* Основной контент */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Вкладка Домены */}
        {currentView === 'domains' && (
          <div className="space-y-6">
            <DomainInput 
              domain={domain}
              setDomain={setDomain}
              onAnalyze={handleAnalyzeDomain}
              isAnalyzing={isAnalyzing}
            />
            <DomainsList 
              domains={domains}
              onAnalyze={handleAnalyzeDomain}
              onSelect={setSelectedDomain}
              selectedDomain={selectedDomain}
            />
          </div>
        )}

        {/* Вкладка Анализ */}
        {currentView === 'analysis' && (
          <div className="space-y-6">
            {isAnalyzing && (
              <AnalysisProgress 
                stats={analysisStats}
                currentThought={currentThought}
                aiThoughts={aiThoughts}
              />
            )}
            
            {analysisError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">❌</span>
                  <div>
                    <h3 className="font-semibold text-red-800">Ошибка анализа</h3>
                    <p className="text-red-600">{analysisError}</p>
                  </div>
                </div>
              </div>
            )}
            
            {!isAnalyzing && !analysisError && (
              <div className="text-center py-12">
                <span className="text-6xl mb-4 block">🔍</span>
                <h2 className="text-xl font-semibold text-white mb-2">Готов к анализу</h2>
                <p className="text-white/80">Выберите домен на вкладке "Домены" для начала анализа</p>
              </div>
            )}
          </div>
        )}

        {/* Вкладка Рекомендации */}
        {currentView === 'recommendations' && (
          <Recommendations 
            recommendations={recommendations}
            domain={selectedDomain?.name}
          />
        )}

        {/* Вкладка Статус Ollama */}
        {currentView === 'status' && (
          <OllamaStatus 
            status={ollamaStatus}
            onRefresh={checkOllamaStatus}
          />
        )}
      </main>
    </div>
  )
}

export default App 