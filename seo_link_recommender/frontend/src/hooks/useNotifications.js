import { useState, useCallback } from 'react'

export function useNotifications() {
  const [notifications, setNotifications] = useState([])

  const addNotification = useCallback((type, title, message, duration = 5000) => {
    const id = Date.now() + Math.random()
    
    const notification = {
      id,
      type,
      title,
      message,
      timestamp: new Date().toISOString(),
      duration
    }

    setNotifications(prev => [...prev, notification])

    // Автоматическое удаление через duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }

    return id
  }, [])

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id))
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