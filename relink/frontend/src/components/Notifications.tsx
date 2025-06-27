import { useState } from 'react';
import { Notification } from '../types';
import { cn } from '../lib/utils';
import { Button } from './ui/Button';
import { Card } from './ui/Card';

interface NotificationsProps {
  notifications: Notification[];
  onRemove: (id: string) => void;
  onClear: () => void;
}

const notificationIcons = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️'
};

const notificationColors = {
  success: 'border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-900/20 dark:text-green-200',
  error: 'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-200',
  warning: 'border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200',
  info: 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-200'
};

export function Notifications({ notifications, onRemove, onClear }: NotificationsProps) {
  const [expandedNotification, setExpandedNotification] = useState<string | null>(null);

  if (notifications.length === 0) {
    return null;
  }

  const handleNotificationClick = (notification: Notification) => {
    setExpandedNotification(
      expandedNotification === notification.id ? null : notification.id
    );
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return 'только что';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}м назад`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}ч назад`;
    return date.toLocaleDateString('ru-RU');
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md w-full">
      {notifications.length > 1 && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {notifications.length} уведомлений
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            className="text-xs"
          >
            Очистить все
          </Button>
        </div>
      )}
      
      {notifications.map((notification) => (
        <Card
          key={notification.id}
          className={cn(
            'p-4 border-l-4 transition-all duration-300 ease-in-out cursor-pointer',
            'hover:shadow-lg hover:scale-[1.02]',
            notificationColors[notification.type],
            expandedNotification === notification.id && 'ring-2 ring-blue-500'
          )}
          onClick={() => handleNotificationClick(notification)}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-1">
              <span className="text-lg flex-shrink-0">
                {notificationIcons[notification.type]}
              </span>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-sm leading-tight">
                    {notification.title}
                  </h4>
                  <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                    {formatTime(notification.timestamp)}
                  </span>
                </div>
                
                <p className="text-sm mt-1 leading-relaxed">
                  {notification.message}
                </p>
              </div>
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onRemove(notification.id);
              }}
              className="ml-2 flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ✕
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
} 