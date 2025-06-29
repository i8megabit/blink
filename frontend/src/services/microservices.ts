import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { Microservice, HealthStatus, ServiceAPI } from '@/types/microservices';

// Конфигурация микросервисов
const MICROSERVICES_CONFIG = {
  'llm-tuning': { port: 8000, description: 'LLM Tuning Service' },
  'backend': { port: 8000, description: 'Main Backend' },
  'router': { port: 8002, description: 'LLM Router' },
  'benchmark': { port: 8001, description: 'Benchmark Service' },
  'monitoring': { port: 8006, description: 'Monitoring Service' },
  'rag': { port: 8003, description: 'RAG Service' },
} as const;

class MicroservicesClient {
  private clients: Map<string, AxiosInstance> = new Map();
  private healthCache: Map<string, HealthStatus> = new Map();
  private cacheTimeout = 30000; // 30 секунд

  constructor() {
    this.initializeClients();
  }

  private initializeClients() {
    Object.entries(MICROSERVICES_CONFIG).forEach(([name]) => {
      const client = axios.create({
        baseURL: `/api/${name}`,
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Добавляем интерцепторы для логирования и обработки ошибок
      client.interceptors.request.use(
        (config) => {
          console.log(`🚀 ${config.method?.toUpperCase()} ${config.url}`);
          return config;
        },
        (error) => {
          console.error('❌ Request error:', error);
          return Promise.reject(error);
        }
      );

      client.interceptors.response.use(
        (response) => {
          console.log(`✅ ${response.status} ${response.config.url}`);
          return response;
        },
        (error) => {
          console.error('❌ Response error:', error);
          return Promise.reject(error);
        }
      );

      this.clients.set(name, client);
    });
  }

  async getServiceHealth(serviceName: string): Promise<HealthStatus> {
    const cached = this.healthCache.get(serviceName);
    if (cached && Date.now() - new Date(cached.timestamp).getTime() < this.cacheTimeout) {
      return cached;
    }

    try {
      const client = this.clients.get(serviceName);
      if (!client) {
        throw new Error(`Service ${serviceName} not found`);
      }

      const startTime = Date.now();
      await client.get('/health');
      const responseTime = Date.now() - startTime;

      const health: HealthStatus = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        response_time: responseTime,
      };

      this.healthCache.set(serviceName, health);
      return health;
    } catch (error) {
      const health: HealthStatus = {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      };

      this.healthCache.set(serviceName, health);
      return health;
    }
  }

  async getAllServicesHealth(): Promise<Record<string, HealthStatus>> {
    const healthPromises = Object.keys(MICROSERVICES_CONFIG).map(async (serviceName) => {
      const health = await this.getServiceHealth(serviceName);
      return [serviceName, health] as const;
    });

    const results = await Promise.allSettled(healthPromises);
    const healthData: Record<string, HealthStatus> = {};

    results.forEach((result) => {
      if (result.status === 'fulfilled') {
        const [serviceName, health] = result.value;
        healthData[serviceName] = health;
      }
    });

    return healthData;
  }

  async getServiceAPI(serviceName: string): Promise<ServiceAPI | null> {
    try {
      const client = this.clients.get(serviceName);
      if (!client) {
        return null;
      }

      const response = await client.get('/api/v1/endpoints');
      return {
        service: serviceName,
        base_url: `/api/${serviceName}`,
        endpoints: response.data.endpoints || [],
        swagger_url: `/api/${serviceName}/docs`,
      };
    } catch (error) {
      console.error(`Failed to get API for ${serviceName}:`, error);
      return null;
    }
  }

  async callService<T = any>(
    serviceName: string,
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' = 'GET',
    data?: any
  ): Promise<T> {
    const client = this.clients.get(serviceName);
    if (!client) {
      throw new Error(`Service ${serviceName} not found`);
    }

    const response: AxiosResponse<T> = await client.request({
      method,
      url: endpoint,
      data,
    });

    return response.data;
  }

  getServiceClient(serviceName: string): AxiosInstance | null {
    return this.clients.get(serviceName) || null;
  }

  getAvailableServices(): string[] {
    return Object.keys(MICROSERVICES_CONFIG);
  }

  getServiceConfig(serviceName: string) {
    return MICROSERVICES_CONFIG[serviceName as keyof typeof MICROSERVICES_CONFIG];
  }
}

// Создаем глобальный экземпляр
export const microservicesClient = new MicroservicesClient();

// Экспортируем типы для удобства
export type { Microservice, HealthStatus, ServiceAPI }; 