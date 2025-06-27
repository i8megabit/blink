import { useState, useCallback, useRef } from 'react';
import { Notification } from '../types';

interface UseNotificationsReturn {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  updateNotification: (id: string, updates: Partial<Notification>) => void;
}

export function useNotifications(): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const timeoutRefs = useRef<Map<string, number>>(new Map());

  const addNotification = useCallback((
    notification: Omit<Notification, 'id' | 'timestamp'>
  ) => {
    const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date().toISOString()
    };

    setNotifications(prev => [...prev, newNotification]);

    // Автоматическое удаление через duration или 15 секунд по умолчанию
    const duration = notification.duration || 15000;
    if (duration > 0) {
      const timeoutId = window.setTimeout(() => {
        removeNotification(id);
      }, duration);
      
      timeoutRefs.current.set(id, timeoutId);
    }
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
    
    // Очищаем timeout
    const timeoutId = timeoutRefs.current.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutRefs.current.delete(id);
    }
  }, []);

  const clearNotifications = useCallback(() => {
    // Очищаем все timeouts
    timeoutRefs.current.forEach(timeoutId => {
      clearTimeout(timeoutId);
    });
    timeoutRefs.current.clear();
    
    setNotifications([]);
  }, []);

  const updateNotification = useCallback((id: string, updates: Partial<Notification>) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, ...updates }
          : notification
      )
    );
  }, []);

  return {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    updateNotification
  };
} 