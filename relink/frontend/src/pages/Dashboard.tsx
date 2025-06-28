// ===== ГЛАВНЫЙ ДАШБОРД =====

import React, { useState } from 'react'
import { LLMModels } from '../components/LLMModels'
import { SystemMonitoring } from '../components/SystemMonitoring'
import { GlobalSearch } from '../components/GlobalSearch'
import { ABTesting } from '../components/ABTesting'
import { Benchmarks } from '../components/Benchmarks'
import { Card, Button, Badge } from '../components/ui'

interface DashboardProps {
  className?: string
}

export const Dashboard: React.FC<DashboardProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const tabs = [
    { id: 'overview', name: 'Обзор', icon: '📊' },
    { id: 'models', name: 'LLM Модели', icon: '🧠' },
    { id: 'monitoring', name: 'Мониторинг', icon: '📈' },
    { id: 'ab-testing', name: 'A/B Тесты', icon: '🧪' },
    { id: 'benchmarks', name: 'Бенчмарки', icon: '🏆' },
    { id: 'search', name: 'Поиск', icon: '🔍' }
  ]

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />
      case 'models':
        return <LLMModels />
      case 'monitoring':
        return <SystemMonitoring />
      case 'ab-testing':
        return <ABTesting />
      case 'benchmarks':
        return <Benchmarks />
      case 'search':
        return <GlobalSearch />
      default:
        return <OverviewTab />
    }
  }

  return (
    <div className={`flex h-screen bg-gray-50 dark:bg-gray-900 ${className}`}>
      {/* Боковая панель */}
      <div className={`bg-white dark:bg-gray-800 shadow-lg transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            {!sidebarCollapsed && (
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                reLink
              </h1>
            )}
            <Button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 text-gray-500 hover:text-gray-700"
            >
              {sidebarCollapsed ? '→' : '←'}
            </Button>
          </div>
        </div>

        <nav className="p-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg mb-1 transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              {!sidebarCollapsed && (
                <span className="font-medium">{tab.name}</span>
              )}
            </button>
          ))}
        </nav>

        {/* Статус сервисов */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Статус сервисов
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Backend</span>
                <Badge color="green" size="sm">Online</Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">LLM Tuning</span>
                <Badge color="green" size="sm">Online</Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Monitoring</span>
                <Badge color="green" size="sm">Online</Badge>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Основной контент */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Верхняя панель */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between px-6 py-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {tabs.find(tab => tab.id === activeTab)?.name}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {getTabDescription(activeTab)}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {new Date().toLocaleDateString('ru-RU', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </div>
              <Button className="bg-blue-600 hover:bg-blue-700 text-white">
                ⚙️ Настройки
              </Button>
            </div>
          </div>
        </header>

        {/* Контент */}
        <main className="flex-1 overflow-auto p-6">
          {renderTabContent()}
        </main>
      </div>
    </div>
  )
}

// Вкладка обзора
const OverviewTab: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Приветствие */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">
          Добро пожаловать в reLink! 🚀
        </h1>
        <p className="text-blue-100 text-lg">
          Мощная платформа для анализа и оптимизации SEO с использованием AI
        </p>
      </div>

      {/* Быстрые действия */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <div className="text-center">
            <div className="text-3xl mb-2">🧠</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Управление моделями
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Создавайте и настраивайте LLM модели для ваших задач
            </p>
            <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
              Перейти к моделям
            </Button>
          </div>
        </Card>

        <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <div className="text-center">
            <div className="text-3xl mb-2">🧪</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              A/B Тестирование
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Сравнивайте производительность разных моделей
            </p>
            <Button className="w-full bg-green-600 hover:bg-green-700 text-white">
              Создать тест
            </Button>
          </div>
        </Card>

        <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <div className="text-center">
            <div className="text-3xl mb-2">🏆</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Бенчмарки
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Измеряйте производительность и качество моделей
            </p>
            <Button className="w-full bg-purple-600 hover:bg-purple-700 text-white">
              Запустить бенчмарк
            </Button>
          </div>
        </Card>

        <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <div className="text-center">
            <div className="text-3xl mb-2">🔍</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Глобальный поиск
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Ищите по всем данным и сервисам платформы
            </p>
            <Button className="w-full bg-orange-600 hover:bg-orange-700 text-white">
              Начать поиск
            </Button>
          </div>
        </Card>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            📊 Статистика системы
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Активных моделей:</span>
              <span className="font-medium">12</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Запущенных тестов:</span>
              <span className="font-medium">3</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Завершенных бенчмарков:</span>
              <span className="font-medium">8</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Алертов:</span>
              <span className="font-medium text-green-600">0</span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            ⚡ Производительность
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">CPU</span>
                <span className="font-medium">45%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: '45%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Память</span>
                <span className="font-medium">62%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full" style={{ width: '62%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Диск</span>
                <span className="font-medium">28%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-yellow-600 h-2 rounded-full" style={{ width: '28%' }}></div>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            🔥 Последние действия
          </h3>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div className="flex-1">
                <div className="text-sm font-medium">Запущен A/B тест</div>
                <div className="text-xs text-gray-500">2 минуты назад</div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <div className="text-sm font-medium">Завершен бенчмарк</div>
                <div className="text-xs text-gray-500">15 минут назад</div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <div className="flex-1">
                <div className="text-sm font-medium">Добавлена новая модель</div>
                <div className="text-xs text-gray-500">1 час назад</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Интеграции */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          🔗 Интеграции с сервисами
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="font-medium">Backend API</span>
            </div>
            <p className="text-sm text-gray-600">Основной API сервис</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="font-medium">LLM Tuning</span>
            </div>
            <p className="text-sm text-gray-600">Микросервис настройки моделей</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="font-medium">Monitoring</span>
            </div>
            <p className="text-sm text-gray-600">Система мониторинга</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="font-medium">Search</span>
            </div>
            <p className="text-sm text-gray-600">Глобальный поиск</p>
          </div>
        </div>
      </Card>
    </div>
  )
}

// Вспомогательная функция для получения описания вкладки
const getTabDescription = (tabId: string): string => {
  switch (tabId) {
    case 'overview':
      return 'Общий обзор системы и быстрые действия'
    case 'models':
      return 'Управление LLM моделями и их настройками'
    case 'monitoring':
      return 'Мониторинг состояния системы и сервисов'
    case 'ab-testing':
      return 'A/B тестирование производительности моделей'
    case 'benchmarks':
      return 'Бенчмарки и тестирование качества'
    case 'search':
      return 'Глобальный поиск по всем данным'
    default:
      return ''
  }
} 