import React from 'react'

function Notifications({ notifications, onRemove }) {
  if (!notifications.length) return null

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success': return '✅'
      case 'error': return '❌'
      case 'warning': return '⚠️'
      case 'info': return 'ℹ️'
      default: return '📢'
    }
  }

  const getNotificationClass = (type) => {
    switch (type) {
      case 'success': return 'notification-success'
      case 'error': return 'notification-error'
      case 'warning': return 'notification-warning'
      case 'info': return 'notification-info'
      default: return 'notification-info'
    }
  }

  return (
    <div className="fixed top-20 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`
            ${getNotificationClass(notification.type)}
            p-4 rounded-lg shadow-lg animate-slide-in
            border-l-4 backdrop-blur-sm
          `}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <span className="text-lg flex-shrink-0 mt-0.5">
                {getNotificationIcon(notification.type)}
              </span>
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-sm">{notification.title}</h4>
                {notification.message && (
                  <p className="text-sm opacity-90 mt-1">{notification.message}</p>
                )}
                <p className="text-xs opacity-70 mt-1">
                  {new Date(notification.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
            <button
              onClick={() => onRemove(notification.id)}
              className="ml-2 text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
              aria-label="Закрыть уведомление"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default Notifications 