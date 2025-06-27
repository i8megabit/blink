import React from 'react'

function Notifications({ 
  notifications, 
  removeNotification, 
  selectedNotification,
  showNotificationDetails,
  hideNotificationDetails,
  pauseNotification,
  resumeNotification
}) {
  const getTypeIcon = (type) => {
    switch (type) {
      case 'success': return '✅'
      case 'error': return '❌'
      case 'warning': return '⚠️'
      case 'info': return 'ℹ️'
      default: return '📢'
    }
  }

  const getTypeColor = (type) => {
    switch (type) {
      case 'success': return 'var(--apple-green)'
      case 'error': return 'var(--apple-red)'
      case 'warning': return 'var(--apple-orange)'
      case 'info': return 'var(--apple-blue)'
      default: return 'var(--apple-gray)'
    }
  }

  return (
    <>
      {/* Основные уведомления */}
      <div id="notifications" style={{ position: 'fixed', top: '20px', right: '20px', zIndex: 1000 }}>
        {notifications.map((notification) => (
          <div
            key={notification.id}
            className="notification"
            style={{
              background: getTypeColor(notification.type),
              color: 'white',
              padding: '16px',
              marginBottom: '12px',
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              maxWidth: '400px',
              animation: 'slideIn 0.3s ease-out'
            }}
            onClick={() => showNotificationDetails(notification)}
            onMouseEnter={() => pauseNotification(notification.id)}
            onMouseLeave={() => resumeNotification(notification.id)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <span style={{ fontSize: '18px' }}>{getTypeIcon(notification.type)}</span>
              <span style={{ fontWeight: '600', fontSize: '14px' }}>{notification.message}</span>
            </div>
            
            {notification.details && (
              <div style={{ 
                fontSize: '12px', 
                opacity: 0.9, 
                marginTop: '4px',
                lineHeight: '1.4'
              }}>
                {notification.details.length > 100 
                  ? `${notification.details.substring(0, 100)}...` 
                  : notification.details
                }
              </div>
            )}
            
            <div style={{ 
              fontSize: '10px', 
              opacity: 0.7, 
              marginTop: '8px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span>{notification.timestamp.toLocaleTimeString()}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  removeNotification(notification.id)
                }}
                style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '2px 6px',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: '10px'
                }}
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Модальное окно с деталями */}
      {selectedNotification && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            backdropFilter: 'blur(4px)',
            zIndex: 2000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
          onClick={hideNotificationDetails}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '32px',
              maxWidth: '600px',
              width: '100%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
              border: '1px solid rgba(255, 255, 255, 0.2)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <span style={{ fontSize: '24px' }}>{getTypeIcon(selectedNotification.type)}</span>
              <h3 style={{ 
                margin: 0, 
                fontSize: '20px', 
                fontWeight: '600',
                color: getTypeColor(selectedNotification.type)
              }}>
                {selectedNotification.message}
              </h3>
            </div>
            
            {selectedNotification.details && (
              <div style={{ 
                background: '#f8f9fa',
                padding: '16px',
                borderRadius: '8px',
                marginBottom: '20px',
                fontSize: '14px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap'
              }}>
                {selectedNotification.details}
              </div>
            )}
            
            <div style={{ 
              fontSize: '12px', 
              color: '#666',
              marginBottom: '20px',
              padding: '12px',
              background: '#f1f3f4',
              borderRadius: '6px'
            }}>
              <strong>Время:</strong> {selectedNotification.timestamp.toLocaleString('ru-RU')}
            </div>
            
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={hideNotificationDetails}
                style={{
                  background: '#6c757d',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                Закрыть
              </button>
              <button
                onClick={() => {
                  removeNotification(selectedNotification.id)
                  hideNotificationDetails()
                }}
                style={{
                  background: getTypeColor(selectedNotification.type),
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                Удалить
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default Notifications 