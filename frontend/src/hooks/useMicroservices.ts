import { useState, useEffect, useCallback } from 'react';
import { microservicesClient } from '@/services/microservices';
import type { HealthStatus, ServiceAPI } from '@/types/microservices';

export function useMicroservices() {
  const [servicesHealth, setServicesHealth] = useState<Record<string, HealthStatus>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const health = await microservicesClient.getAllServicesHealth();
      setServicesHealth(health);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch services health');
    } finally {
      setLoading(false);
    }
  }, []);

  const getServiceHealth = useCallback(async (serviceName: string) => {
    try {
      const health = await microservicesClient.getServiceHealth(serviceName);
      setServicesHealth(prev => ({
        ...prev,
        [serviceName]: health
      }));
      return health;
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to fetch ${serviceName} health`);
      throw err;
    }
  }, []);

  const callService = useCallback(async <T = any>(
    serviceName: string,
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' = 'GET',
    data?: any
  ): Promise<T> => {
    try {
      return await microservicesClient.callService<T>(serviceName, endpoint, method, data);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to call ${serviceName} ${endpoint}`);
      throw err;
    }
  }, []);

  const getServiceAPI = useCallback(async (serviceName: string): Promise<ServiceAPI | null> => {
    try {
      return await microservicesClient.getServiceAPI(serviceName);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to get API for ${serviceName}`);
      return null;
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    
    // Автоматическое обновление каждые 30 секунд
    const interval = setInterval(refreshHealth, 30000);
    
    return () => clearInterval(interval);
  }, [refreshHealth]);

  return {
    servicesHealth,
    loading,
    error,
    refreshHealth,
    getServiceHealth,
    callService,
    getServiceAPI,
    availableServices: microservicesClient.getAvailableServices(),
  };
}

export function useServiceHealth(serviceName: string) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const serviceHealth = await microservicesClient.getServiceHealth(serviceName);
      setHealth(serviceHealth);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch service health');
    } finally {
      setLoading(false);
    }
  }, [serviceName]);

  useEffect(() => {
    refreshHealth();
    
    // Обновление каждые 10 секунд для конкретного сервиса
    const interval = setInterval(refreshHealth, 10000);
    
    return () => clearInterval(interval);
  }, [refreshHealth]);

  return {
    health,
    loading,
    error,
    refreshHealth,
  };
} 