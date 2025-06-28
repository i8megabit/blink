import { useState, useEffect, useCallback, useRef } from 'react'

export function useWebSocket({ onMessage, onConnect, onDisconnect, onError }) {
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  const connectWebSocket = useCallback((clientId) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`
      
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        setConnectionStatus('connected')
        onConnect && onConnect()
      }
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage && onMessage(data)
        } catch (error) {
          console.error('Ошибка парсинга WebSocket сообщения:', error)
        }
      }
      
      wsRef.current.onclose = () => {
        setConnectionStatus('disconnected')
        onDisconnect && onDisconnect()
        
        // Попытка переподключения через 3 секунды
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket(clientId)
        }, 3000)
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket ошибка:', error)
        onError && onError(error)
      }
      
    } catch (error) {
      console.error('Ошибка создания WebSocket:', error)
      onError && onError(error)
    }
  }, [onMessage, onConnect, onDisconnect, onError])

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setConnectionStatus('disconnected')
  }, [])

  useEffect(() => {
    return () => {
      disconnectWebSocket()
    }
  }, [disconnectWebSocket])

  return {
    connectionStatus,
    connectWebSocket,
    disconnectWebSocket
  }
} 