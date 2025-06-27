import { useState, useCallback, useRef } from 'react'

export function useNotifications() {
  const [notifications, setNotifications] = useState([])
  const [selectedNotification, setSelectedNotification] = useState(null)
  const timeoutsRef = useRef(new Map())

  const addNotification = useCallback((type, message, details = '') => {
    const id = Date.now() + Math.random()
    const newNotification = {
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

  const removeNotification = useCallback((id) => {
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

  const pauseNotification = useCallback((id) => {
    // Приостанавливаем автоудаление
    const timeoutId = timeoutsRef.current.get(id)
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutsRef.current.delete(id)
    }
  }, [])

  const resumeNotification = useCallback((id) => {
    // Возобновляем автоудаление через 10 секунд
    const timeoutId = setTimeout(() => {
      removeNotification(id)
    }, 10000)
    
    timeoutsRef.current.set(id, timeoutId)
  }, [removeNotification])

  const showNotificationDetails = useCallback((notification) => {
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

  const getNotificationsByType = useCallback((type) => {
    return notifications.filter(notification => notification.type === type)
  }, [notifications])

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
    hasNotifications: notifications.length > 0,
    notificationsCount: notifications.length
  }
} 