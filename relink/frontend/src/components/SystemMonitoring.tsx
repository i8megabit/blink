// ===== СИСТЕМНЫЙ МОНИТОРИНГ КОМПОНЕНТ =====

import React, { useState } from 'react'
import { useSystemMonitoring, useServicesHealth } from '../hooks/useMicroservices'
import { Microservice } from '../types/microservices'
import { Card, Button, Badge, Progress } from './ui'

interface SystemMonitoringProps {
  className?: string
}

export const SystemMonitoring: React.FC<SystemMonitoringProps> = ({ className = '' }) => {
  const { health, loading: healthLoading, error: healthError, acknowledgeAlert } = useSystemMonitoring()
  const { services, loading: servicesLoading, error: servicesError } = useServicesHealth()
  const [selectedService, setSelectedService] = useState<Microservice | null>(null)
  const [showAlerts, setShowAlerts] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green'
      case 'warning': return 'yellow'
      case 'critical': return 'red'
      case 'unknown': return 'gray'
      default: return 'gray'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✅'
      case 'warning': return '⚠️'
      case 'critical': return '❌'
      case 'unknown': return '❓'
      default: return '❓'
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatUptime = (percentage: number) => {
    return `${percentage.toFixed(2)}%`
  }

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await acknowledgeAlert(alertId)
    } catch (error) {
      console.error('Ошибка подтверждения алерта:', error)
    }
  }

  if (healthLoading || servicesLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка данных мониторинга...</p>
        </div>
      </div>
    )
  }

  if (healthError || servicesError) {
    return (
      <div className={`p-4 ${className}`}>
        <Card className="border-red-200 bg-red-50">
          <div className="text-center">
            <p className="text-red-600 mb-2">❌ Ошибка загрузки мониторинга</p>
            <p className="text-red-500 text-sm">{healthError || servicesError}</p>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            📊 Системный мониторинг
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Мониторинг состояния системы и сервисов
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={() => setShowAlerts(!showAlerts)}
            className={`${showAlerts ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-600 hover:bg-gray-700'} text-white`}
          >
            {showAlerts ? '📋 Скрыть алерты' : '🚨 Показать алерты'}
          </Button>
        </div>
      </div>

      {/* Общий статус системы */}
      {health && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Общее состояние системы
            </h3>
            <div className="flex items-center space-x-2">
              <span className="text-2xl">{getStatusIcon(health.overall_status)}</span>
              <Badge color={getStatusColor(health.overall_status)}>
                {health.overall_status}
              </Badge>
            </div>
          </div>

          {/* Использование ресурсов */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">CPU:</span>
                <span className="font-medium">{health.resources.cpu.usage_percent.toFixed(1)}%</span>
              </div>
              <Progress 
                value={health.resources.cpu.usage_percent} 
                max={100}
                className="h-2"
                color={health.resources.cpu.usage_percent > 80 ? 'red' : health.resources.cpu.usage_percent > 60 ? 'yellow' : 'green'}
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Память:</span>
                <span className="font-medium">{health.resources.memory.usage_percent.toFixed(1)}%</span>
              </div>
              <Progress 
                value={health.resources.memory.usage_percent} 
                max={100}
                className="h-2"
                color={health.resources.memory.usage_percent > 80 ? 'red' : health.resources.memory.usage_percent > 60 ? 'yellow' : 'green'}
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Диск:</span>
                <span className="font-medium">{health.resources.disk.usage_percent.toFixed(1)}%</span>
              </div>
              <Progress 
                value={health.resources.disk.usage_percent} 
                max={100}
                className="h-2"
                color={health.resources.disk.usage_percent > 80 ? 'red' : health.resources.disk.usage_percent > 60 ? 'yellow' : 'green'}
              />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Сеть:</span>
                <span className="font-medium">{health.resources.network.connections}</span>
              </div>
              <div className="text-xs text-gray-500">
                {formatBytes(health.resources.network.bytes_sent)} / {formatBytes(health.resources.network.bytes_received)}
              </div>
            </div>
          </div>

          {/* Детальная информация о ресурсах */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Использовано памяти:</span>
                <span className="font-medium">{formatBytes(health.resources.memory.used_mb * 1024 * 1024)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Всего памяти:</span>
                <span className="font-medium">{formatBytes(health.resources.memory.total_mb * 1024 * 1024)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Использовано диска:</span>
                <span className="font-medium">{formatBytes(health.resources.disk.used_gb * 1024 * 1024 * 1024)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Всего диска:</span>
                <span className="font-medium">{formatBytes(health.resources.disk.total_gb * 1024 * 1024 * 1024)}</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Ядра CPU:</span>
                <span className="font-medium">{health.resources.cpu.cores}</span>
              </div>
              {health.resources.cpu.temperature && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Температура CPU:</span>
                  <span className="font-medium">{health.resources.cpu.temperature}°C</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Активные соединения:</span>
                <span className="font-medium">{health.resources.network.connections}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Последняя проверка:</span>
                <span className="font-medium">{new Date(health.last_check).toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Алерты */}
      {showAlerts && health && health.alerts.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            🚨 Активные алерты ({health.alerts.length})
          </h3>
          <div className="space-y-3">
            {health.alerts.map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  <span className="text-xl">
                    {alert.level === 'critical' ? '🔴' : alert.level === 'warning' ? '🟡' : '🔵'}
                  </span>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{alert.title}</div>
                    <div className="text-sm text-gray-600">{alert.message}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Сервис: {alert.service} • {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {!alert.acknowledged && (
                    <Button
                      size="sm"
                      onClick={() => handleAcknowledgeAlert(alert.id)}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      Подтвердить
                    </Button>
                  )}
                  <Badge color={alert.acknowledged ? 'green' : 'red'}>
                    {alert.acknowledged ? 'Подтвержден' : 'Новый'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Статус сервисов */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          🔧 Статус сервисов ({services.length})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((service) => (
            <div
              key={service.name}
              className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedService(service)}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900 dark:text-white">{service.name}</h4>
                <div className="flex items-center space-x-1">
                  <span className="text-lg">{getStatusIcon(service.status)}</span>
                  <Badge color={getStatusColor(service.status)}>
                    {service.status}
                  </Badge>
                </div>
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                <div>Версия: {service.version}</div>
                <div>Время отклика: {service.response_time_ms}ms</div>
                <div>Аптайм: {formatUptime(service.uptime_percentage)}</div>
                <div>Эндпоинтов: {service.endpoints.length}</div>
              </div>
              <div className="mt-3 text-xs text-gray-500">
                Последний heartbeat: {new Date(service.last_heartbeat).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Детальная информация о сервисе */}
      {selectedService && (
        <ServiceDetailsModal
          service={selectedService}
          onClose={() => setSelectedService(null)}
        />
      )}
    </div>
  )
}

// Модальное окно с деталями сервиса
interface ServiceDetailsModalProps {
  service: Microservice
  onClose: () => void
}

const ServiceDetailsModal: React.FC<ServiceDetailsModalProps> = ({ service, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Детали сервиса: {service.name}
          </h3>
          <Button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </Button>
        </div>

        <div className="space-y-4">
          {/* Основная информация */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Версия</label>
              <div className="text-sm text-gray-900">{service.version}</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Статус</label>
              <Badge color={service.status === 'healthy' ? 'green' : service.status === 'warning' ? 'yellow' : 'red'}>
                {service.status}
              </Badge>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Время отклика</label>
              <div className="text-sm text-gray-900">{service.response_time_ms}ms</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Аптайм</label>
              <div className="text-sm text-gray-900">{service.uptime_percentage.toFixed(2)}%</div>
            </div>
          </div>

          {/* URL сервиса */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">URL сервиса</label>
            <div className="text-sm text-gray-900 break-all">{service.health_url}</div>
          </div>

          {/* Эндпоинты */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Эндпоинты ({service.endpoints.length})</label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {service.endpoints.map((endpoint, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div className="flex items-center space-x-2">
                    <Badge color={endpoint.method === 'GET' ? 'green' : endpoint.method === 'POST' ? 'blue' : 'orange'}>
                      {endpoint.method}
                    </Badge>
                    <span className="text-sm font-mono">{endpoint.path}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {endpoint.requires_auth && (
                      <Badge color="red" size="sm">Auth</Badge>
                    )}
                    {endpoint.deprecated && (
                      <Badge color="gray" size="sm">Deprecated</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Метаданные */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Последний heartbeat</label>
              <div className="text-sm text-gray-900">
                {new Date(service.last_heartbeat).toLocaleString()}
              </div>
            </div>
            {service.metrics_url && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL метрик</label>
                <div className="text-sm text-gray-900 break-all">{service.metrics_url}</div>
              </div>
            )}
            {service.documentation_url && (
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">URL документации</label>
                <div className="text-sm text-gray-900 break-all">{service.documentation_url}</div>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
} 