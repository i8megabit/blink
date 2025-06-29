import React from 'react';
import { useMicroservices } from '@/hooks/useMicroservices';
import { RelinkService } from '@/components/RelinkService';
import type { HealthStatus } from '@/types/microservices';

export function Services() {
  const { servicesHealth, loading, error } = useMicroservices();

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Services</h1>
          <p className="mt-1 text-sm text-gray-500">
            Управление микросервисами
          </p>
        </div>
        <div className="card">
          <p className="text-gray-600">Загрузка сервисов...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Services</h1>
          <p className="mt-1 text-sm text-gray-500">
            Управление микросервисами
          </p>
        </div>
        <div className="card">
          <p className="text-red-600">Ошибка загрузки сервисов: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Services</h1>
        <p className="mt-1 text-sm text-gray-500">
          Управление микросервисами reLink
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* reLink SEO Service */}
        <RelinkService 
          serviceName="reLink SEO Service"
          description="Анализ внутренних ссылок и SEO оптимизация"
        />

        {/* Другие сервисы */}
        {Object.entries(servicesHealth).map(([serviceName, health]) => (
          <div key={serviceName} className="card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold capitalize">{serviceName}</h3>
                <p className="text-gray-600">
                  {health.status === 'healthy' ? 'Сервис работает' : 'Проблемы с подключением'}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded text-xs ${
                  health.status === 'healthy' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {health.status}
                </span>
                <button 
                  onClick={() => window.open(`http://localhost:3000/api/${serviceName}/docs`, '_blank')}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  API Docs
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 