import React, { useState, useEffect, useCallback } from 'react';
import { useMicroservices } from '../hooks/useMicroservices';
import { Microservice, ServiceDocumentation } from '../types/microservices';

interface MicroservicesDocsProps {
  className?: string;
}

const MicroservicesDocs: React.FC<MicroservicesDocsProps> = ({ className = '' }) => {
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [serviceDocs, setServiceDocs] = useState<ServiceDocumentation | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [syncStatus, setSyncStatus] = useState<string>('');

  const { 
    services, 
    loading: servicesLoading, 
    error: servicesError,
    discoverServices,
    syncServiceDocumentation,
    searchDocumentation
  } = useMicroservices();

  // Загрузка сервисов при монтировании
  useEffect(() => {
    discoverServices();
  }, [discoverServices]);

  // Загрузка документации выбранного сервиса
  const loadServiceDocumentation = useCallback(async (serviceName: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/services/${serviceName}`);
      if (response.ok) {
        const data = await response.json();
        setServiceDocs(data.data);
      }
    } catch (error) {
      console.error('Error loading service documentation:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Обработчик выбора сервиса
  const handleServiceSelect = useCallback((serviceName: string) => {
    setSelectedService(serviceName);
    loadServiceDocumentation(serviceName);
  }, [loadServiceDocumentation]);

  // Синхронизация документации сервиса
  const handleSyncService = useCallback(async (serviceName: string) => {
    setSyncStatus(`Синхронизация ${serviceName}...`);
    try {
      const response = await fetch(`/api/v1/services/${serviceName}/sync`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        setSyncStatus(`Синхронизация ${serviceName} завершена`);
        if (selectedService === serviceName) {
          loadServiceDocumentation(serviceName);
        }
      }
    } catch (error) {
      setSyncStatus(`Ошибка синхронизации ${serviceName}`);
      console.error('Error syncing service:', error);
    }
  }, [selectedService, loadServiceDocumentation]);

  // Поиск по документации
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;

    try {
      const response = await fetch('/api/v1/docs/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: searchQuery,
          limit: 20,
          offset: 0
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.data.results || []);
      }
    } catch (error) {
      console.error('Error searching documentation:', error);
    }
  }, [searchQuery]);

  // Группировка сервисов по категориям
  const groupedServices = services.reduce((acc: Record<string, Microservice[]>, service: Microservice) => {
    const category = service.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(service);
    return acc;
  }, {});

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '🟢';
      case 'warning': return '🟡';
      case 'critical': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <div className={`bg-gray-900 text-white min-h-screen ${className}`}>
      {/* Заголовок */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-2">
            📚 Документация Микросервисов
          </h1>
          <p className="text-gray-300">
            Автоматическое обнаружение и синхронизация документации всех микросервисов
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {/* Поиск */}
        <div className="mb-8 bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">🔍 Поиск по документации</h2>
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Поиск по документации..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSearch}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-medium transition-colors"
            >
              Поиск
            </button>
          </div>

          {/* Результаты поиска */}
          {searchResults.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3">Результаты поиска</h3>
              <div className="space-y-3">
                {searchResults.map((result, index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm bg-blue-600 px-2 py-1 rounded">
                        {result.type}
                      </span>
                      <span className="text-sm text-gray-400">
                        {result.service}
                      </span>
                    </div>
                    <h4 className="font-medium text-blue-400 mb-1">
                      {result.title}
                    </h4>
                    <p className="text-gray-300 text-sm">
                      {result.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Статус синхронизации */}
        {syncStatus && (
          <div className="mb-6 bg-blue-900 border border-blue-700 rounded-lg p-4">
            <p className="text-blue-200">{syncStatus}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Список сервисов */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">🚀 Микросервисы</h2>
                <button
                  onClick={() => discoverServices()}
                  className="text-blue-400 hover:text-blue-300 text-sm"
                >
                  Обновить
                </button>
              </div>

              {servicesLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="text-gray-400 mt-2">Загрузка сервисов...</p>
                </div>
              ) : servicesError ? (
                <div className="text-red-400 text-center py-4">
                  Ошибка загрузки сервисов
                </div>
              ) : (
                <div className="space-y-4">
                  {Object.entries(groupedServices).map(([category, categoryServices]) => (
                    <div key={category}>
                      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-2">
                        {category}
                      </h3>
                      <div className="space-y-2">
                        {categoryServices.map((service) => (
                          <div
                            key={service.name}
                            className={`p-3 rounded-lg cursor-pointer transition-colors ${
                              selectedService === service.name
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-700 hover:bg-gray-600'
                            }`}
                            onClick={() => handleServiceSelect(service.name)}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-sm">{getStatusIcon(service.status)}</span>
                                <span className="font-medium">{service.display_name}</span>
                              </div>
                              <span className={`text-xs ${getStatusColor(service.status)}`}>
                                {service.status}
                              </span>
                            </div>
                            <p className="text-xs text-gray-400 mt-1">
                              v{service.version}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Документация выбранного сервиса */}
          <div className="lg:col-span-3">
            {selectedService ? (
              <div className="bg-gray-800 rounded-lg p-6">
                {loading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                    <p className="text-gray-400 mt-4">Загрузка документации...</p>
                  </div>
                ) : serviceDocs ? (
                  <div>
                    {/* Заголовок сервиса */}
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h2 className="text-2xl font-bold text-white mb-2">
                          {serviceDocs.service.display_name}
                        </h2>
                        <p className="text-gray-300 mb-2">
                          {serviceDocs.service.description}
                        </p>
                        <div className="flex items-center gap-4 text-sm text-gray-400">
                          <span>Версия: {serviceDocs.service.version}</span>
                          <span>Категория: {serviceDocs.service.category}</span>
                          <span className={getStatusColor(serviceDocs.service.status)}>
                            {getStatusIcon(serviceDocs.service.status)} {serviceDocs.service.status}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleSyncService(selectedService)}
                        className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg font-medium transition-colors"
                      >
                        🔄 Синхронизировать
                      </button>
                    </div>

                    {/* README */}
                    {serviceDocs.readme && (
                      <div className="mb-8">
                        <h3 className="text-xl font-semibold mb-4 text-white">
                          📖 README
                        </h3>
                        <div className="bg-gray-700 rounded-lg p-4">
                          <div 
                            className="prose prose-invert max-w-none"
                            dangerouslySetInnerHTML={{ __html: serviceDocs.readme }}
                          />
                        </div>
                      </div>
                    )}

                    {/* API Документация */}
                    {serviceDocs.api_docs && serviceDocs.api_docs.length > 0 && (
                      <div className="mb-8">
                        <h3 className="text-xl font-semibold mb-4 text-white">
                          🔌 API Документация
                        </h3>
                        <div className="space-y-4">
                          {serviceDocs.api_docs.map((endpoint, index) => (
                            <div key={index} className="bg-gray-700 rounded-lg p-4">
                              <div className="flex items-center gap-3 mb-2">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  endpoint.method === 'GET' ? 'bg-green-600' :
                                  endpoint.method === 'POST' ? 'bg-blue-600' :
                                  endpoint.method === 'PUT' ? 'bg-yellow-600' :
                                  endpoint.method === 'DELETE' ? 'bg-red-600' :
                                  'bg-gray-600'
                                }`}>
                                  {endpoint.method}
                                </span>
                                <code className="text-blue-400 font-mono">
                                  {endpoint.path}
                                </code>
                                {endpoint.requires_auth && (
                                  <span className="text-xs bg-red-600 px-2 py-1 rounded">
                                    Auth
                                  </span>
                                )}
                                {endpoint.deprecated && (
                                  <span className="text-xs bg-yellow-600 px-2 py-1 rounded">
                                    Deprecated
                                  </span>
                                )}
                              </div>
                              <p className="text-gray-300 text-sm">
                                {endpoint.description}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Ссылки */}
                    <div className="flex gap-4">
                      {serviceDocs.service.health_url && (
                        <a
                          href={serviceDocs.service.health_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-medium transition-colors"
                        >
                          🏥 Health Check
                        </a>
                      )}
                      {serviceDocs.service.docs_url && (
                        <a
                          href={serviceDocs.service.docs_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg font-medium transition-colors"
                        >
                          📚 API Docs
                        </a>
                      )}
                      {serviceDocs.service.api_url && (
                        <a
                          href={serviceDocs.service.api_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-medium transition-colors"
                        >
                          🔗 OpenAPI
                        </a>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-400">Документация не найдена</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <div className="text-6xl mb-4">📚</div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  Выберите микросервис
                </h3>
                <p className="text-gray-400">
                  Выберите микросервис из списка слева для просмотра его документации
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MicroservicesDocs; 