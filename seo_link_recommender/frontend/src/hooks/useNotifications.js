import { useState, useCallback } from 'react'

export function useNotifications() {
  const [notifications, setNotifications] = useState([])

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
    
    // Автоматически удаляем через 5 секунд
    setTimeout(() => {
      removeNotification(id)
    }, 5000)
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const clearAllNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  const getNotificationsByType = useCallback((type) => {
    return notifications.filter(notification => notification.type === type)
  }, [notifications])

  return {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    getNotificationsByType,
    hasNotifications: notifications.length > 0,
    notificationsCount: notifications.length
  }
} 