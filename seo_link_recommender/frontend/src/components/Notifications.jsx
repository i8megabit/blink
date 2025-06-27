import React from 'react'

function Notifications({ notifications, onRemove }) {
  if (!notifications || notifications.length === 0) {
    return null
  }

  return (
    <div className="notifications-container">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`notification notification-${notification.type}`}
        >
          <div className="notification-header">
            <div className="notification-title">
              {notification.title}
            </div>
            <button
              className="notification-close"
              onClick={() => onRemove(notification.id)}
            >
              ✕
            </button>
          </div>
          
          <div className="notification-message">
            {notification.message}
          </div>
        </div>
      ))}
    </div>
  )
}

export default Notifications 