import { useState, useCallback, useRef } from 'react'

export interface Notification {
  id: number;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  details?: string;
  timestamp: Date;
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null)
  const timeoutsRef = useRef(new Map<number, NodeJS.Timeout>())

  const addNotification = useCallback((type: Notification['type'], message: string, details: string = '') => {
    const id = Date.now() + Math.random()
    const newNotification: Notification = {
      id,
      type,
      message,
      details,
      timestamp: new Date()
    }
    
    setNotifications(prev => [...prev, newNotification])
    
    // Автоматически удаляем через 15 секунд (увеличено с 5)
    const timeoutId = setTimeout(() => {
      removeNotification(id)
    }, 15000)
    
    timeoutsRef.current.set(id, timeoutId)
  }, [])

  const removeNotification = useCallback((id: number) => {
    // Очищаем таймаут
    const timeoutId = timeoutsRef.current.get(id)
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutsRef.current.delete(id)
    }
    
    setNotifications(prev => prev.filter(n => n.id !== id))
    
    // Закрываем модальное окно, если это было выбранное уведомление
    if (selectedNotification?.id === id) {
      setSelectedNotification(null)
    }
  }, [selectedNotification])

  const pauseNotification = useCallback((id: number) => {
    // Приостанавливаем автоудаление
    const timeoutId = timeoutsRef.current.get(id)
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutsRef.current.delete(id)
    }
  }, [])

  const resumeNotification = useCallback((id: number) => {
    // Возобновляем автоудаление через 10 секунд
    const timeoutId = setTimeout(() => {
      removeNotification(id)
    }, 10000)
    
    timeoutsRef.current.set(id, timeoutId)
  }, [removeNotification])

  const showNotificationDetails = useCallback((notification: Notification) => {
    setSelectedNotification(notification)
    // Приостанавливаем автоудаление при показе деталей
    pauseNotification(notification.id)
  }, [pauseNotification])

  const hideNotificationDetails = useCallback(() => {
    if (selectedNotification) {
      // Возобновляем автоудаление при скрытии деталей
      resumeNotification(selectedNotification.id)
    }
    setSelectedNotification(null)
  }, [selectedNotification, resumeNotification])

  const clearAllNotifications = useCallback(() => {
    // Очищаем все таймауты
    timeoutsRef.current.forEach(timeoutId => clearTimeout(timeoutId))
    timeoutsRef.current.clear()
    
    setNotifications([])
    setSelectedNotification(null)
  }, [])

  const getNotificationsByType = useCallback((type: Notification['type']) => {
    return notifications.filter(notification => notification.type === type)
  }, [notifications])

  const showNotification = useCallback((type: Notification['type'], message: string, details?: string) => {
    addNotification(type, message, details || '')
  }, [addNotification])

  return {
    notifications,
    selectedNotification,
    addNotification,
    removeNotification,
    pauseNotification,
    resumeNotification,
    showNotificationDetails,
    hideNotificationDetails,
    clearAllNotifications,
    getNotificationsByType,
    showNotification,
    hasNotifications: notifications.length > 0,
    notificationsCount: notifications.length
  }
} 