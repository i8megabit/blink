import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketMessage, WebSocketStatus } from '../types';

interface UseWebSocketOptions {
  url: string;
  clientId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  status: WebSocketStatus;
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  error: string | null;
  reconnect: () => void;
}

export function useWebSocket({
  url,
  clientId,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  onClose,
  reconnectAttempts = 3,
  reconnectInterval = 5000
}: UseWebSocketOptions): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>('connecting');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    try {
      setStatus('connecting');
      setError(null);

      const ws = new WebSocket(`${url}/${clientId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setStatus('connected');
        setAttempts(0);
        console.log('🔌 WebSocket подключен:', clientId);
        if (onConnect) {
          onConnect();
        }
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          if (onMessage) {
            onMessage(message);
          }
        } catch (err) {
          console.error('❌ Ошибка парсинга WebSocket сообщения:', err);
          setError('Ошибка обработки сообщения');
        }
      };

      ws.onerror = (event) => {
        if (!mountedRef.current) return;
        console.error('❌ WebSocket ошибка:', event);
        setError('Ошибка соединения');
        setStatus('error');
        
        if (onError) {
          onError(event);
        }
      };

      ws.onclose = (event) => {
        if (!mountedRef.current) return;
        console.log('🔌 WebSocket отключен:', event.code, event.reason);
        setStatus('disconnected');
        
        if (onClose) {
          onClose();
        }

        if (onDisconnect) {
          onDisconnect();
        }

        // Автоматическое переподключение
        if (attempts < reconnectAttempts && mountedRef.current) {
          const timeout = window.setTimeout(() => {
            if (mountedRef.current) {
              setAttempts(prev => prev + 1);
              connect();
            }
          }, reconnectInterval);
          
          reconnectTimeoutRef.current = timeout;
        }
      };

    } catch (err) {
      console.error('❌ Ошибка создания WebSocket:', err);
      setError('Не удалось создать соединение');
      setStatus('error');
    }
  }, [url, clientId, onMessage, onConnect, onDisconnect, onError, onClose, attempts, reconnectAttempts, reconnectInterval]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (err) {
        console.error('❌ Ошибка отправки сообщения:', err);
        setError('Ошибка отправки сообщения');
      }
    } else {
      console.warn('⚠️ WebSocket не подключен, сообщение не отправлено');
      setError('Соединение не установлено');
    }
  }, []);

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setAttempts(0);
    connect();
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    status,
    sendMessage,
    lastMessage,
    error,
    reconnect
  };
} 