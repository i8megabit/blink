// ===== ГЛОБАЛЬНЫЙ ПОИСК КОМПОНЕНТ =====

import React, { useState, useEffect, useRef } from 'react'
import { useGlobalSearch } from '../hooks/useMicroservices'
import { GlobalSearchQuery } from '../types/microservices'
import { Card, Button, Badge } from './ui'

interface GlobalSearchProps {
  className?: string
}

export const GlobalSearch: React.FC<GlobalSearchProps> = ({ className = '' }) => {
  const { searchResults, loading, error, search, getSuggestions } = useGlobalSearch()
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [filters, setFilters] = useState({
    services: [] as string[],
    categories: [] as string[],
    date_from: '',
    date_to: ''
  })
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const searchInputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // Загрузка истории поиска из localStorage
  useEffect(() => {
    const history = localStorage.getItem('searchHistory')
    if (history) {
      setSearchHistory(JSON.parse(history))
    }
  }, [])

  // Обработка клика вне поля поиска
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Получение подсказок при вводе
  useEffect(() => {
    if (query.length > 2) {
      const timeoutId = setTimeout(async () => {
        try {
          const suggestions = await getSuggestions(query)
          setSuggestions(suggestions)
          setShowSuggestions(true)
        } catch (error) {
          console.error('Ошибка получения подсказок:', error)
        }
      }, 300)

      return () => clearTimeout(timeoutId)
    } else {
      setSuggestions([])
      setShowSuggestions(false)
    }
    return undefined;
  }, [query, getSuggestions])

  const handleSearch = async (searchQuery: string = query) => {
    if (!searchQuery.trim()) return

    try {
      const searchData: GlobalSearchQuery = {
        query: searchQuery,
        filters,
        limit: 20,
        offset: 0
      }

      await search(searchData)

      // Сохранение в историю
      const newHistory = [searchQuery, ...searchHistory.filter(item => item !== searchQuery)].slice(0, 10)
      setSearchHistory(newHistory)
      localStorage.setItem('searchHistory', JSON.stringify(newHistory))

      setShowSuggestions(false)
    } catch (error) {
      console.error('Ошибка поиска:', error)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    handleSearch(suggestion)
  }

  const handleHistoryClick = (historyItem: string) => {
    setQuery(historyItem)
    handleSearch(historyItem)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'domain': return '🌐'
      case 'analysis': return '📊'
      case 'benchmark': return '🏆'
      case 'documentation': return '📚'
      case 'test': return '🧪'
      default: return '📄'
    }
  }

  const getResultColor = (type: string) => {
    switch (type) {
      case 'domain': return 'blue'
      case 'analysis': return 'green'
      case 'benchmark': return 'purple'
      case 'documentation': return 'orange'
      case 'test': return 'red'
      default: return 'gray'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Заголовок */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          🔍 Глобальный поиск
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Поиск по всем сервисам и данным reLink
        </p>
      </div>

      {/* Поле поиска */}
      <div className="relative" ref={suggestionsRef}>
        <div className="flex space-x-2">
          <div className="flex-1 relative">
            <input
              ref={searchInputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Введите запрос для поиска..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {loading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
              </div>
            )}
          </div>
          <Button
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6"
          >
            {loading ? 'Поиск...' : 'Найти'}
          </Button>
        </div>

        {/* Подсказки и история */}
        {showSuggestions && (suggestions.length > 0 || searchHistory.length > 0) && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
            {/* Подсказки */}
            {suggestions.length > 0 && (
              <div className="p-2">
                <div className="text-xs font-medium text-gray-500 mb-2 px-2">Подсказки</div>
                {suggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="px-2 py-2 hover:bg-gray-100 rounded cursor-pointer text-sm"
                  >
                    {suggestion}
                  </div>
                ))}
              </div>
            )}

            {/* История поиска */}
            {searchHistory.length > 0 && (
              <div className="p-2 border-t border-gray-200">
                <div className="text-xs font-medium text-gray-500 mb-2 px-2">История поиска</div>
                {searchHistory.map((historyItem, index) => (
                  <div
                    key={index}
                    onClick={() => handleHistoryClick(historyItem)}
                    className="px-2 py-2 hover:bg-gray-100 rounded cursor-pointer text-sm flex items-center"
                  >
                    <span className="text-gray-400 mr-2">🕒</span>
                    {historyItem}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Фильтры */}
      <Card className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Фильтры</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Сервисы</label>
            <select
              multiple
              value={filters.services}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value)
                setFilters({ ...filters, services: values })
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="backend">Backend</option>
              <option value="llm_tuning">LLM Tuning</option>
              <option value="monitoring">Monitoring</option>
              <option value="testing">Testing</option>
              <option value="docs">Documentation</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Категории</label>
            <select
              multiple
              value={filters.categories}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value)
                setFilters({ ...filters, categories: values })
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="models">Модели</option>
              <option value="analyses">Анализы</option>
              <option value="benchmarks">Бенчмарки</option>
              <option value="tests">Тесты</option>
              <option value="docs">Документация</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Дата от</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Дата до</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </Card>

      {/* Результаты поиска */}
      {searchResults && (
        <div className="space-y-4">
          {/* Статистика поиска */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Найдено {searchResults.total} результатов за {searchResults.query_time_ms}ms
            </div>
            {searchResults.suggestions.length > 0 && (
              <div className="text-sm text-gray-600">
                Возможно вы искали: {searchResults.suggestions.join(', ')}
              </div>
            )}
          </div>

          {/* Фасеты */}
          {searchResults.facets.length > 0 && (
            <Card className="p-4">
              <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">Фильтры по результатам</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {searchResults.facets.map((facet) => (
                  <div key={facet.name}>
                    <div className="text-sm font-medium text-gray-700 mb-2">{facet.name}</div>
                    <div className="space-y-1">
                      {facet.values.slice(0, 5).map((value) => (
                        <div key={value.value} className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">{value.value}</span>
                          <Badge color="gray" size="sm">{value.count}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Список результатов */}
          <div className="space-y-3">
            {searchResults.results.map((result) => (
              <Card key={result.id} className="p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">{getResultIcon(result.type)}</div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {result.title}
                      </h3>
                      <Badge color={getResultColor(result.type)}>
                        {result.type}
                      </Badge>
                      <Badge color="gray" size="sm">
                        {result.service}
                      </Badge>
                    </div>
                    <p className="text-gray-600 mb-2">{result.description}</p>
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <div className="flex items-center space-x-4">
                        <span>Релевантность: {result.relevance_score.toFixed(2)}</span>
                        <span>Создано: {formatDate(result.created_at)}</span>
                        {result.updated_at !== result.created_at && (
                          <span>Обновлено: {formatDate(result.updated_at)}</span>
                        )}
                      </div>
                      <Button
                        size="sm"
                        onClick={() => window.open(result.url, '_blank')}
                        className="bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        Открыть
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Пагинация */}
          {searchResults.total > 20 && (
            <div className="flex items-center justify-center space-x-2">
              <Button
                disabled={true}
                className="bg-gray-300 text-gray-500 cursor-not-allowed"
              >
                ← Предыдущая
              </Button>
              <span className="text-sm text-gray-600">
                Страница 1 из {Math.ceil(searchResults.total / 20)}
              </span>
              <Button
                disabled={true}
                className="bg-gray-300 text-gray-500 cursor-not-allowed"
              >
                Следующая →
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Ошибка */}
      {error && (
        <Card className="border-red-200 bg-red-50 p-4">
          <div className="text-center">
            <p className="text-red-600 mb-2">❌ Ошибка поиска</p>
            <p className="text-red-500 text-sm">{error}</p>
          </div>
        </Card>
      )}
    </div>
  )
} 