import React from 'react'

function Notifications({ notifications, removeNotification }) {
  return (
    <div id="notifications">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`notification ${notification.type}`}
          onClick={() => removeNotification(notification.id)}
          style={{ cursor: 'pointer' }}
        >
          {notification.message}
          {notification.details && (
            <div style={{ fontSize: '12px', opacity: 0.8, marginTop: '4px' }}>
              {notification.details}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default Notifications 