import { useState, useEffect, useRef, useCallback } from 'react'

export function useWebSocket({ onMessage, onConnect, onDisconnect, onError }) {
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [lastMessage, setLastMessage] = useState(null)
  const websocketRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const clientIdRef = useRef(null)
  const maxReconnectAttempts = 5
  const reconnectAttemptsRef = useRef(0)

  const connectWebSocket = useCallback((clientId) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket уже подключен')
      return
    }

    clientIdRef.current = clientId
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`

    console.log('🔌 Подключение к WebSocket:', wsUrl)
    
    try {
      const ws = new WebSocket(wsUrl)
      websocketRef.current = ws

      ws.onopen = () => {
        console.log('✅ WebSocket подключен')
        setConnectionStatus('connected')
        reconnectAttemptsRef.current = 0
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          onMessage?.(data)
        } catch (error) {
          console.error('Ошибка парсинга WebSocket сообщения:', error)
        }
      }

      ws.onclose = (event) => {
        console.log('🔌 WebSocket отключен:', event.code, event.reason)
        setConnectionStatus('disconnected')
        onDisconnect?.()

        // Автоматическое переподключение
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
          
          console.log(`🔄 Переподключение через ${delay}ms (попытка ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (clientIdRef.current) {
              connectWebSocket(clientIdRef.current)
            }
          }, delay)
        } else {
          console.log('❌ Превышено максимальное количество попыток переподключения')
          setConnectionStatus('failed')
        }
      }

      ws.onerror = (error) => {
        console.error('❌ Ошибка WebSocket:', error)
        setConnectionStatus('error')
        onError?.(error)
      }

    } catch (error) {
      console.error('❌ Ошибка создания WebSocket:', error)
      setConnectionStatus('error')
      onError?.(error)
    }
  }, [onMessage, onConnect, onDisconnect, onError])

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (websocketRef.current) {
      websocketRef.current.close()
      websocketRef.current = null
    }

    setConnectionStatus('disconnected')
    clientIdRef.current = null
    reconnectAttemptsRef.current = 0
  }, [])

  const sendMessage = useCallback((message) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message))
      return true
    } else {
      console.warn('WebSocket не подключен, сообщение не отправлено:', message)
      return false
    }
  }, [])

  // Очистка при размонтировании
  useEffect(() => {
    return () => {
      disconnectWebSocket()
    }
  }, [disconnectWebSocket])

  return {
    connectionStatus,
    lastMessage,
    connectWebSocket,
    disconnectWebSocket,
    sendMessage,
    isConnected: connectionStatus === 'connected',
    isConnecting: connectionStatus === 'connecting',
    isDisconnected: connectionStatus === 'disconnected'
  }
} 